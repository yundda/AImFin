# analysis/services/rebalance.py
from __future__ import annotations
from typing import List, Dict

from django.utils import timezone
from jsonschema import validate

from analysis.schemas.recommend_response import RECOMMEND_RESPONSE_SCHEMA
from analysis.clients.gpt_client import complete_json
from analysis.services.metrics import compute_portfolio_metrics
from analysis.prompts.util import render_prompt

from portfolios.models import Portfolio
from portfolios.services.portfolio_rules import get_universe_rules_for, BucketRule
from portfolios.services.policy import (
    reconcile_proposed_allocations,
    normalize_assets_within_bucket,
)

# ---------------------------------------------------------------------

def _format_allocations_lines(allocs: List[dict]) -> str:
    # - STOCKS_KR: 18.00%
    # - BONDS_KR:  25.00%
    lines = []
    for row in allocs or []:
        b = row["bucket"]
        w = float(row.get("weight_pct", 0))
        lines.append(f"- {b}: {w:.2f}%")
    return "\n".join(lines)

def _assets_fix_to_bucket(entry: dict) -> dict:
    assets = entry.get("assets") or []
    w = float(entry.get("weight_pct", 0.0))
    if not assets:
        return {"bucket": entry["bucket"], "weight_pct": round(w, 2), "assets": []}
    fixed = normalize_assets_within_bucket(w, assets)
    return {"bucket": entry["bucket"], "weight_pct": round(w, 2), "assets": fixed}

def _apply_must_buckets_min(rules: Dict[str, BucketRule], must_buckets: List[str], must_min: float = 3.0) -> None:
    for b in must_buckets or []:
        if b in rules:
            r = rules[b]
            if r.min < must_min:
                r.min = must_min
                if r.target < r.min:
                    r.target = r.min

def _risk_score_from_metrics(metrics: dict) -> float:
    # 0(안전) ~ 100(위험). 변동성 25% ≈ 100
    vol = float(metrics.get("volatility_pct", 0.0))
    score = max(0.0, min(100.0, (vol / 25.0) * 100.0))
    return float(f"{score:.2f}")

# ---- 메인: 리밸런싱 '평가만' 수행 ------------------------------------------
def evaluate_rebalance(
    *,
    user,
    portfolio_id: int,
    allocations_input: List[dict],
) -> dict:
    """
    - 기존 포트폴리오의 메타(금액/기간/must_buckets)와 사용자 정책/유니버스를 사용
    - 입력된 버킷 비중(allocations_input)을 '현재 구성'으로 간주해 GPT 코멘트 요청
    - 정책 집행으로 최종 100.00% 정규화
    - 서버 계산식으로 expected_return_pct / risk_score 산출
    - 응답 스키마는 recommend와 동일
    """
    # 0) 원본 포트폴리오 로드(소유권은 뷰에서 체크)
    p = Portfolio.objects.get(pk=portfolio_id, user=user)
    amount_krw = int(p.amount_krw)
    horizon_desc = p.horizon_desc
    must_buckets = list(p.must_buckets or [])

    # 1) 정책/유니버스 수집
    uni = get_universe_rules_for(user)  # {"rules": ..., "policy_summary": ..., "buckets":[{bucket, eligible_assets}, ...]}
    rules: Dict[str, BucketRule] = uni["rules"]
    _apply_must_buckets_min(rules, must_buckets, must_min=3.0)

    # 2) 버킷별 편입 가능 종목 텍스트
    elig_map: Dict[str, List[str]] = {b["bucket"]: list(b.get("eligible_assets") or []) for b in uni.get("buckets", [])}
    eligible_assets_by_bucket = "\n".join(
        f"- {bk}: [{', '.join(elig_map.get(bk, []))}]" if elig_map.get(bk) else f"- {bk}: []"
        for bk in elig_map.keys()
    )

    # 3) 프롬프트 구성(공용 유틸로 $-변수 템플릿 안전 치환)
    prompt = render_prompt(
        "rebalance_eval_prompt.txt",
        {
            "amount_krw": f"{amount_krw:,} KRW",
            "risk_profile": p.profile,
            "risk_label": p.profile_label,
            "horizon_desc": horizon_desc,
            "current_allocations": _format_allocations_lines(allocations_input),
            "must_buckets": must_buckets,
            "policy_summary": uni.get("policy_summary", ""),
            "eligible_assets_by_bucket": eligible_assets_by_bucket,
        },
    )

    # 4) GPT 호출 + 스키마 검증
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA)
    validate(instance=raw, schema=RECOMMEND_RESPONSE_SCHEMA)

    # 5) 정책 하에서 버킷 가중치 정규화
    proposed = raw.get("allocations", [])
    final_allocs, notes = reconcile_proposed_allocations(rules=rules, proposed_allocs=proposed)

    # 6) 버킷 내부 종목 비중 보정(있는 경우만)
    proposed_map = {a["bucket"]: a for a in proposed}
    final_with_assets = []
    for row in final_allocs:
        src = proposed_map.get(row["bucket"], {"assets": []})
        merged = {"bucket": row["bucket"], "weight_pct": row["weight_pct"], "assets": src.get("assets", [])}
        final_with_assets.append(_assets_fix_to_bucket(merged))

    # 7) 서버 계산 지표 → 두 값만 노출
    metrics_all = compute_portfolio_metrics(final_with_assets)
    expected_return_pct = float(f"{float(metrics_all.get('expected_return_pct', 0.0)):.2f}")
    risk_score = _risk_score_from_metrics(metrics_all)

    # 8) 최종 응답(recommend와 동일 포맷)
    return {
        "profile": p.profile,
        "profile_label": p.profile_label,
        "amount_krw": amount_krw,
        "horizon_desc": horizon_desc,
        "must_buckets": must_buckets,
        "proposed_allocations": proposed,        # GPT 원안
        "final_allocations": final_with_assets,  # 정책 보정
        "corrections": notes,                    # 보정 로그
        "rationale": raw.get("rationale", ""),
        "summary": raw.get("summary", ""),
        "risks": raw.get("risks", ""),
        "metrics": {
            "expected_return_pct": expected_return_pct,
            "risk_score": risk_score,
        },
        "generated_at": timezone.now().isoformat(),
    }