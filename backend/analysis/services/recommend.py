# analysis/services/recommend.py
from __future__ import annotations
from typing import Dict, List
from django.utils import timezone
from django.conf import settings
from jsonschema import validate
from string import Template

from analysis.schemas.recommend_response import RECOMMEND_RESPONSE_SCHEMA
from analysis.clients.gpt_client import complete_json
from analysis.services.metrics import compute_portfolio_metrics
from portfolios.services.portfolio_rules import get_universe_rules_for, BucketRule
from portfolios.services.policy import (
    reconcile_proposed_allocations,
    normalize_assets_within_bucket,
)
from users.models import RiskProfileCode  # type hint/clarity


def _read_prompt_template() -> Template:
    """
    프롬프트 파일을 읽어 Template 객체로 반환.
    파일은 $profile, $profile_label, $amount_krw, $horizon_desc,
    $must_buckets, $policy_summary, $eligible_assets_by_bucket 를 사용해야 한다.
    """
    path = settings.BASE_DIR / "analysis" / "prompts" / "recommend_prompt.txt"
    text = path.read_text(encoding="utf-8")
    return Template(text)


def build_prompt(*, user, amount_krw: int, horizon_desc: str, must_buckets: List[str]) -> str:
    """
    파일 기반 템플릿($변수)로 안전 치환(safe_substitute). 중괄호 {} 충돌로 인한 KeyError 방지.
    """
    policy = get_universe_rules_for(user)  # rules + eligible + policy_summary 등

    # 버킷별 편입 가능 종목 텍스트
    lines: List[str] = []
    for b in policy["buckets"]:
        codes = b.get("eligible_assets") or []
        if codes:
            lines.append(f"- {b['bucket']}: [{', '.join(codes)}]")
        else:
            lines.append(f"- {b['bucket']}: []")
    eligible_assets_by_bucket = "\n".join(lines)

    # must_buckets 표기 문자열
    must_txt = ", ".join(must_buckets) if must_buckets else "없음"

    tmpl = _read_prompt_template()
    # amount는 텍스트로만 쓰므로 표시용 포맷 적용(쉼표 + KRW)
    return tmpl.safe_substitute(
        profile=policy["profile"],
        profile_label=user.risk_snapshot.latest_result.get_profile_display(),
        amount_krw=f"{amount_krw:,} KRW",
        horizon_desc=horizon_desc,
        must_buckets=must_txt,
        policy_summary=policy["policy_summary"],
        eligible_assets_by_bucket=eligible_assets_by_bucket,
    )


# ---- 로컬 헬퍼들 -------------------------------------------------------------

def _assets_fix_to_bucket(entry: dict) -> dict:
    """
    entry = {"bucket": "...", "weight_pct": float, "assets": [{code, weight_pct}, ...]}
    자산 리스트가 있으면 합이 정확히 bucket weight와 일치하도록 2-dec로 정규화.
    없으면 빈 배열로 통일.
    """
    assets = entry.get("assets") or []
    w = float(entry.get("weight_pct", 0.0))
    if not assets:
        return {"bucket": entry["bucket"], "weight_pct": round(w, 2), "assets": []}
    fixed = normalize_assets_within_bucket(w, assets)
    return {"bucket": entry["bucket"], "weight_pct": round(w, 2), "assets": fixed}


def _apply_must_buckets_min(rules: Dict[str, BucketRule], must_buckets: List[str], must_min: float = 3.0) -> None:
    """
    요청의 must_buckets에 대해 해당 버킷 min을 최소 must_min까지 상향.
    (기존 min이 더 크면 그대로 유지, target < min 이면 target= min 로 보정)
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
    0(안전) ~ 100(위험) 스케일. 기본: volatility_pct 25% ≈ 100점.
    """
    vol = float(metrics.get("volatility_pct", 0.0))
    score = (vol / 25.0) * 100.0
    score = 0.0 if score < 0 else (100.0 if score > 100 else score)
    return float(f"{score:.2f}")


# ---- 메인 함수 ---------------------------------------------------------------

def recommend_portfolio(
    *,
    user,
    amount_krw: int,
    horizon_desc: str,
    must_buckets: List[str],
) -> dict:
    """
    - 사용자 최신 설문 스냅샷 + 선호 스냅샷으로 정책/유니버스 획득
    - GPT 제안 수신 → 정책 집행으로 100.00% 정규화
    - 버킷 내부 종목 비중까지 정확히 맞춤
    - 서버 계산식으로 기대수익/위험점수 산출(두 값만 노출)
    """

    # 1) 프롬프트
    prompt = build_prompt(
        user=user,
        amount_krw=amount_krw,
        horizon_desc=horizon_desc,
        must_buckets=must_buckets,
    )

    # 2) GPT 호출 + 스키마 검증
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA)
    validate(instance=raw, schema=RECOMMEND_RESPONSE_SCHEMA)

    # 3) 정책/유니버스 + must_buckets min 보정
    uni = get_universe_rules_for(user)     # {"rules": RuleTable, ...}
    rules = uni["rules"]                   # Dict[str, BucketRule]
    _apply_must_buckets_min(rules, must_buckets, must_min=3.0)

    # 4) 정책 하에서 가중치 정규화
    proposed = raw.get("allocations", [])
    final_allocs, notes = reconcile_proposed_allocations(
        rules=rules,
        proposed_allocs=proposed,
    )

    # 5) 버킷 내부 종목 비중 정규화
    proposed_map = {a["bucket"]: a for a in proposed}
    final_with_assets = []
    for row in final_allocs:
        src = proposed_map.get(row["bucket"], {"assets": []})
        merged = {"bucket": row["bucket"], "weight_pct": row["weight_pct"], "assets": src.get("assets", [])}
        final_with_assets.append(_assets_fix_to_bucket(merged))

    # 6) 서버 계산식(metrics) → 기대수익/위험점수만 노출
    metrics_all = compute_portfolio_metrics(final_with_assets)
    expected_return_pct = float(metrics_all.get("expected_return_pct", 0.0))
    risk_score = _risk_score_from_metrics(metrics_all)

    # 7) 최종 응답
    snap = user.risk_snapshot.latest_result
    result = {
        "profile": snap.profile,
        "profile_label": snap.get_profile_display(),
        "amount_krw": amount_krw,
        "horizon_desc": horizon_desc,
        "must_buckets": must_buckets,
        "proposed_allocations": proposed,        # GPT 원안(로그)
        "final_allocations": final_with_assets,  # 정책 보정 결과
        "corrections": notes,                    # 보정 로그
        "rationale": raw.get("rationale", ""),
        "summary": raw.get("summary", ""),
        "risks": raw.get("risks", ""),
        "metrics": {                             # 응답 축소본(2개만)
            "expected_return_pct": float(f"{expected_return_pct:.2f}"),
            "risk_score": float(f"{risk_score:.2f}"),
        },
        "generated_at": timezone.now().isoformat(),
    }
    return result
