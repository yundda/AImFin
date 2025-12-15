# analysis/services/recommend.py
from __future__ import annotations
from typing import Dict, List
from django.utils import timezone
from django.conf import settings
from jsonschema import validate

from analysis.schemas.recommend_response import RECOMMEND_RESPONSE_SCHEMA
from analysis.clients.gpt_client import complete_json
from analysis.services.metrics import compute_portfolio_metrics
from portfolios.services.portfolio_rules import get_universe_rules_for, BucketRule
from portfolios.services.policy import (
    reconcile_proposed_allocations,
    normalize_assets_within_bucket,
    _round2,
)
from users.models import RiskProfileCode  # type hint/clarity


def _read_prompt_template() -> str:
    path = settings.BASE_DIR / "analysis" / "prompts" / "recommend_prompt.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(*, user, amount_krw: int, horizon_desc: str, must_buckets: List[str]) -> str:
    policy = get_universe_rules_for(user)  # rules + eligible
    # GPT에 전달할 버킷별 편입 가능 종목 텍스트
    eligible_lines = []
    for b in [r["bucket"] for r in policy["buckets"]]:
        assets = [a for a in next(x for x in policy["buckets"] if x["bucket"] == b)["eligible_assets"]]
        eligible_lines.append(f"- {b}: [{', '.join(assets)}]" if assets else f"- {b}: []")
    eligible_assets_by_bucket = "\n".join(eligible_lines)

    tpl = _read_prompt_template()
    return tpl.format(
        risk_profile=policy["profile"],
        risk_label=user.risk_snapshot.latest_result.get_profile_display(),
        amount_krw=f"{amount_krw:,} KRW",
        horizon_desc=horizon_desc,
        must_buckets=must_buckets,
        policy_summary=policy["policy_summary"],
        eligible_assets_by_bucket=eligible_assets_by_bucket,
    )

# ---- 로컬 헬퍼들 -------------------------------------------------------------

def _assets_fix_to_bucket(entry: dict) -> dict:
    """
    entry = {"bucket": "...", "weight_pct": float, "assets": [{code, weight_pct}, ...]}
    자산 리스트가 있으면 합이 정확히 bucket weight와 일치하도록 2-dec로 정규화.
    없으면 그대로 반환.
    """
    assets = entry.get("assets") or []
    w = float(entry.get("weight_pct", 0.0))
    if not assets:
        return {"bucket": entry["bucket"], "weight_pct": round(w, 2), "assets": []}
    fixed = normalize_assets_within_bucket(w, assets)
    return {"bucket": entry["bucket"], "weight_pct": round(w, 2), "assets": fixed}

def _apply_must_buckets_min(rules: Dict[str, BucketRule], must_buckets: List[str], must_min: float = 3.0) -> None:
    """
    요청에 들어온 must_buckets에 대해 해당 버킷의 min을 must_min 이상으로 상향.
    (기존 min이 더 크면 그대로)
    """
    for b in must_buckets or []:
        if b in rules:
            r = rules[b]
            if r.min < must_min:
                r.min = must_min
                if r.target < r.min:
                    r.target = r.min

def _risk_score_from_metrics(metrics: dict) -> float:
    """
    0(안전) ~ 100(위험). 기본 스케일: 변동성 25% ≈ 위험 100.
    필요 시 가중치/함수 형태는 쉽게 교체 가능.
    """
    vol = float(metrics.get("volatility_pct", 0.0))
    score = (vol / 25.0) * 100.0
    if score < 0:
        score = 0.0
    if score > 100:
        score = 100.0
    # 소수 2자리 고정
    return float(f"{score:.2f}")

# ---- (필수) 서버 계산 메트릭 함수: 프로젝트에 이미 있다면 그대로 사용) ----
# 기대수익/변동성 등을 계산하는 기존 함수가 있다면 그대로 import해서 쓰면 됩니다.
# 여기서는 expected_return_pct / volatility_pct만 쓰고, 응답에는 두 개만 노출합니다.
from analysis.services.metrics import compute_portfolio_metrics  # 기존 구현 재사용 가정

# ---- 메인 함수 ---------------------------------------------------------------

def recommend_portfolio(
    *,
    user,
    amount_krw: int,
    horizon_desc: str,
    must_buckets: List[str],
) -> dict:
    """
    - 사용자 최신 설문 스냅샷 + 선호 스냅샷을 사용해 정책/유니버스 취득
    - GPT 제안 수신 → 정책 집행으로 100.00% 정규화
    - 버킷 내부 종목 비중 합도 정확히 맞춤
    - 서버 계산식으로 기대수익/위험점수 산출 후 (두 값만) 응답에 노출
    """

    # 1) 프롬프트 구성 (프롬프트 함수는 기존 그대로 사용)
    prompt = build_prompt(
        user=user,
        amount_krw=amount_krw,
        horizon_desc=horizon_desc,
        must_buckets=must_buckets,
    )

    # 2) GPT 호출 + 스키마 검증
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA)
    validate(instance=raw, schema=RECOMMEND_RESPONSE_SCHEMA)

    # 3) 정책/유니버스 로드 (+ must_buckets min 보정)
    uni = get_universe_rules_for(user)  # {"rules": RuleTable, "policy_summary": ..., ...}
    rules = uni["rules"]               # Dict[str, BucketRule]
    _apply_must_buckets_min(rules, must_buckets, must_min=3.0)

    # 4) 정책 하에서 버킷 가중치 정규화
    proposed = raw.get("allocations", [])
    final_allocs, notes = reconcile_proposed_allocations(
        rules=rules,
        proposed_allocs=proposed,
    )

    # 5) 버킷 내부 종목 비중 재정렬(있는 경우)
    proposed_map = {a["bucket"]: a for a in proposed}
    final_with_assets = []
    for row in final_allocs:
        src = proposed_map.get(row["bucket"], {"assets": []})
        merged = {"bucket": row["bucket"], "weight_pct": row["weight_pct"], "assets": src.get("assets", [])}
        final_with_assets.append(_assets_fix_to_bucket(merged))

    # 6) **서버 계산식(metrics) 산출 → 기대수익/위험점수만 노출**
    metrics_all = compute_portfolio_metrics(final_with_assets)  # 기존 함수 사용
    expected_return_pct = float(metrics_all.get("expected_return_pct", 0.0))
    risk_score = _risk_score_from_metrics(metrics_all)

    # 7) 최종 응답 (메트릭은 2가지만 노출)
    snap = user.risk_snapshot.latest_result
    result = {
        "profile": snap.profile,
        "profile_label": snap.get_profile_display(),
        "amount_krw": amount_krw,
        "horizon_desc": horizon_desc,
        "must_buckets": must_buckets,
        "proposed_allocations": proposed,       # GPT 원안 (로그/디버깅용)
        "final_allocations": final_with_assets, # 정책 보정 결과
        "corrections": notes,                   # 보정 로그
        "rationale": raw.get("rationale", ""),
        "summary": raw.get("summary", ""),
        "risks": raw.get("risks", ""),
        "metrics": {                            # ✅ 노출 축소본
            "expected_return_pct": float(f"{expected_return_pct:.2f}"),
            "risk_score": float(f"{risk_score:.2f}"),  # 0~100
        },
        "generated_at": timezone.now().isoformat(),
    }
    return result
