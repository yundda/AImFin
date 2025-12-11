# analysis/services/recommend.py
from __future__ import annotations
from typing import Dict, List, Any
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from string import Template                 # ✅ 추가
import json                                 # ✅ 추가

from analysis.schemas.recommend_response import RECOMMEND_RESPONSE_SCHEMA
from portfolios.services.portfolio_rules import get_universe_rules_for  # ← 정책/유니버스 일원화 사용
from portfolios.services.policy import reconcile_proposed_allocations, normalize_assets_within_bucket
from analysis.clients.gpt_client import complete_json
from jsonschema import validate


def _read_prompt_template() -> str:
    path = settings.BASE_DIR / "analysis" / "prompts" / "recommend_prompt.txt"
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def build_prompt(
    risk_profile: str,
    risk_label: str,
    amount_krw: int,
    horizon_desc: str,
    must_buckets: List[str],
    policy: dict,
) -> str:
    """
    ⚠️ Template.safe_substitute 로 ${...} 자리표시자만 치환.
       프롬프트 안의 JSON { } 는 전혀 건드리지 않음.
    """
    tpl = _read_prompt_template()

    # 정책 요약 텍스트 (portfolio_rules.get_universe_rules_for 가 넘겨준 값 우선)
    policy_summary = policy.get("policy_summary") or ""

    # 버킷별 편입 가능 종목 요약 (있으면 더 친절)
    eligible_lines = []
    for b in policy.get("buckets", []):
        codes = b.get("eligible_assets", []) or []
        if codes:
            # 너무 길면 앞 10개만 노출
            show = codes[:10]
            more = f" (+{len(codes)-10})" if len(codes) > 10 else ""
            eligible_lines.append(f"- {b['bucket']}: {', '.join(show)}{more}")
    eligible_assets_text = "\n".join(eligible_lines) if eligible_lines else "(등록된 종목 없음)"

    # 자리표시자 값 준비
    data = {
        "risk_profile": risk_profile,
        "risk_label": risk_label,
        "amount_krw": f"{amount_krw:,} KRW",
        "horizon_desc": horizon_desc,
        "must_buckets": ", ".join(must_buckets) if must_buckets else "없음",
        "policy_summary": policy_summary,
        "eligible_assets_by_bucket": eligible_assets_text,
    }

    return Template(tpl).safe_substitute(**data)


def recommend_portfolio(
    *,
    user,
    amount_krw: int,
    horizon_desc: str,
    must_buckets: List[str],
) -> dict:
    # 1) 사용자 위험 성향 로드
    snap = getattr(user, "risk_snapshot", None)
    if not snap or not snap.latest_result:
        raise ValueError("No risk snapshot. 설문/성향 진단이 필요합니다.")
    profile_code = snap.latest_result.profile
    risk_label = snap.latest_result.get_profile_display()

    # 2) 정책/유니버스 취득 (버킷 min/max/target + eligible_assets 포함)
    policy = get_universe_rules_for(user)

    # 3) 프롬프트 빌드
    prompt = build_prompt(
        risk_profile=profile_code,
        risk_label=risk_label,
        amount_krw=amount_krw,
        horizon_desc=horizon_desc,
        must_buckets=must_buckets,
        policy=policy,
    )

    # 4) GPT 호출 → JSON 파싱/검증
    raw = complete_json(prompt, schema=RECOMMEND_RESPONSE_SCHEMA)
    validate(instance=raw, schema=RECOMMEND_RESPONSE_SCHEMA)

    # 5) 정책 보정(버킷 수준)
    #   rules: {bucket -> BucketRule}; proposed_allocs: [{"bucket","weight_pct",("assets":...)}]
    rules = {b["bucket"]: b for b in policy["buckets"]}
    proposed_allocs = raw["allocations"]

    # reconcile: min/max 내로 100% 정규화
    # → 우리 policy.reconcile_proposed_allocations 시그니처에 맞게 변환
    from portfolios.services.portfolio_rules import AssetType  # 타입 힌트용(선택)
    # RuleTable 재구성: bucket -> BucketRule
    from portfolios.services.portfolio_rules import BucketRule
    rule_table = {b["bucket"]: BucketRule(b["bucket"], b["min"], b["max"], b["target"])
                  for b in policy["buckets"]}

    final_bucket_allocs, notes = reconcile_proposed_allocations(
        rules=rule_table,
        proposed_allocs=proposed_allocs,
    )

    # 6) 버킷 내부 종목 가중치 정합성(있다면)
    #    assets 합이 버킷 비중과 정확히 일치하도록 보정
    bucket_map = {a["bucket"]: a for a in proposed_allocs}
    final_allocs = []
    for fb in final_bucket_allocs:
        b = fb["bucket"]
        w = float(fb["weight_pct"])
        assets = bucket_map.get(b, {}).get("assets", [])
        norm_assets = normalize_assets_within_bucket(w, assets)
        final_allocs.append({"bucket": b, "weight_pct": w, "assets": norm_assets})

    result = {
        "profile": profile_code,
        "profile_label": risk_label,
        "amount_krw": amount_krw,
        "horizon_desc": horizon_desc,
        "must_buckets": must_buckets,
        "proposed_allocations": proposed_allocs,
        "final_allocations": final_allocs,
        "corrections": notes,
        "rationale": raw.get("rationale", ""),
        "summary":   raw.get("summary", ""),
        "risks":     raw.get("risks", ""),
        "generated_at": timezone.now().isoformat(),
    }
    return result