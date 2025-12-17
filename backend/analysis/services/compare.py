# analysis/services/compare.py
from __future__ import annotations
from typing import List, Dict, Any, Optional
from string import Template

from django.utils import timezone
from django.conf import settings
from jsonschema import validate


from analysis.clients.gpt_client import complete_json
from analysis.services.metrics import compute_portfolio_metrics
from analysis.prompts.util import render_prompt
from analysis.schemas.compare_response import COMPARE_RESPONSE_SCHEMA

from portfolios.services.portfolio_rules import get_universe_rules_for


# ---------------- 유틸 ----------------

def _read_compare_prompt_template() -> Template:
    """
    analysis/prompts/compare_prompt.txt 를 Template 로드 ($플레이스홀더 방식)
    """
    path = settings.BASE_DIR / "analysis" / "prompts" / "compare_prompt.txt"
    return Template(path.read_text(encoding="utf-8"))

def _fmt_alloc_lines(allocs: List[Dict[str, Any]]) -> str:
    """
    [{"bucket":"STOCKS_KR","weight_pct":18.57}, ...] -> "- STOCKS_KR: 18.57%\n- ..."
    """
    lines = []
    for a in allocs or []:
        b = a.get("bucket", "")
        w = float(a.get("weight_pct", 0.0))
        lines.append(f"- {b}: {w:.2f}%")
    return "\n".join(lines)

def _compute_metrics_safe(allocs: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    서버 계산식으로 기대수익/위험점수 산출.
    - expected_return_pct: 소수 2자리
    - risk_score: 소수 2자리
    """
    try:
        m = compute_portfolio_metrics(allocs) or {}
        er = float(m.get("expected_return_pct", 0.0))
        rs = float(m.get("risk_score", 0.0))
        return {
            "expected_return_pct": float(f"{er:.2f}"),
            "risk_score": float(f"{rs:.2f}"),
        }
    except Exception:
        return {"expected_return_pct": 0.0, "risk_score": 0.0}

def _build_compare_prompt(
    *,
    user,
    left_allocs: List[Dict[str, Any]],
    right_allocs: List[Dict[str, Any]],
) -> str:
    """
    프롬프트 구성:
    - 좌/우 버킷 라인
    - 좌/우 기대수익/위험점수
    - 정책 요약(유니버스 룰의 policy_summary)
    """
    uni = get_universe_rules_for(user)  # {"policy_summary": "...", ...}
    policy_summary = uni.get("policy_summary", "")

    lm = _compute_metrics_safe(left_allocs)
    rm = _compute_metrics_safe(right_allocs)

    ctx = {
        "left_alloc_lines": _fmt_alloc_lines(left_allocs),
        "right_alloc_lines": _fmt_alloc_lines(right_allocs),
        "left_er_pct": f"{lm.get('expected_return_pct', 0.0):.2f}",
        "left_risk_score": f"{lm.get('risk_score', 0.0):.2f}",
        "right_er_pct": f"{rm.get('expected_return_pct', 0.0):.2f}",
        "right_risk_score": f"{rm.get('risk_score', 0.0):.2f}",
        "policy_summary": policy_summary,
    }
    return render_prompt("compare_prompt.txt", ctx)

def _coerce_allocations(spec_or_allocs: Any) -> List[Dict[str, Any]]:
    """
    - 리스트로 직접 들어오면 그대로 반환
    - 딕셔너리이면 spec_or_allocs['allocations']를 기대
    - None 이면 빈 리스트
    """
    if spec_or_allocs is None:
        return []
    if isinstance(spec_or_allocs, list):
        return spec_or_allocs
    if isinstance(spec_or_allocs, dict):
        allocs = spec_or_allocs.get("allocations")
        return allocs if isinstance(allocs, list) else []
    # 알 수 없는 타입 방어
    return []


# ------------- 메인 서비스 -------------

def evaluate_comparison(
    *,
    user,
    left_allocations: List[Dict[str, Any]],
    right_allocations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    비교 분석 메인 엔트리.
    - 입력: 좌/우 버킷 비중(가중치 합=100.00 가정)
    - 출력: {"rationale": str, "summary": str, "risks": str, "generated_at": iso str}
    """
    prompt = _build_compare_prompt(
        user=user,
        left_allocs=left_allocations,
        right_allocs=right_allocations,
    )

    raw = complete_json(prompt, schema=COMPARE_RESPONSE_SCHEMA if COMPARE_RESPONSE_SCHEMA else None)
    if validate and COMPARE_RESPONSE_SCHEMA:
        try:
            validate(instance=raw, schema=COMPARE_RESPONSE_SCHEMA)
        except Exception:
            pass

    return {
        "rationale": raw.get("rationale", ""),
        "summary":   raw.get("summary", ""),
        "risks":     raw.get("risks", ""),
        "generated_at": timezone.now().isoformat(),
    }


# 호환용 래퍼: 호출자가 left_spec/right_spec 을 넘겨도, left_allocations/right_allocations 을 넘겨도 동작
def compare_portfolios(
    *,
    user,
    left_spec: Optional[Dict[str, Any]] = None,
    right_spec: Optional[Dict[str, Any]] = None,
    left_allocations: Optional[List[Dict[str, Any]]] = None,
    right_allocations: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    허용 인자:
    - left_allocations/right_allocations (권장)
    - 또는 left_spec/right_spec (각각에 'allocations' 키 포함)
    """
    l = left_allocations if left_allocations is not None else _coerce_allocations(left_spec)
    r = right_allocations if right_allocations is not None else _coerce_allocations(right_spec)

    return evaluate_comparison(
        user=user,
        left_allocations=l,
        right_allocations=r,
    )