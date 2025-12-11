# portfolios/services/policy.py
from __future__ import annotations
from typing import Dict, List, Tuple

from assets.enums import AssetType
from portfolios.services.portfolio_rules import BucketRule, RuleTable


def _round2(x: float) -> float:
    # 소수 둘째 자리 반올림
    return float(f"{x:.2f}")


def _largest_remainder_to_100(values: Dict[AssetType, float]) -> Dict[AssetType, float]:
    """
    실수 합을 정확히 100.00으로 만드는 2-decimal 라운딩(최대잔여 방식).
    """
    # 1) 내림(2자리) + 잔여 계산
    floored = {k: int(values[k] * 100) / 100.0 for k in values}
    remainders: List[Tuple[AssetType, float]] = []
    for k, v in values.items():
        remainders.append((k, v - floored[k]))

    # 2) 남은 센트 배분
    diff = round(100.0 - sum(floored.values()), 2)
    cents = int(round(diff * 100))
    remainders.sort(key=lambda x: x[1], reverse=True)
    res = floored.copy()
    i = 0
    while cents > 0 and i < len(remainders):
        k, _ = remainders[i]
        res[k] = round(res[k] + 0.01, 2)
        cents -= 1
        i = (i + 1) if (i + 1) < len(remainders) else 0  # tie 시 분산
    return res


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _waterfill_to_limits(
    rules: RuleTable,
    proposed: Dict[AssetType, float],
) -> Dict[AssetType, float]:
    """
    - 시작: 각 버킷을 '하한(min)'으로 초기화
    - 잔여(100 - sum(min))를 '희망 증가량(proposed_clamped - min)' 비율대로 물붓기(water-filling)
    - 상한(max) 도달 버킷은 고정하고 나머지에게 재분배(포화 반복)
    """
    mins = {b: r.min for b, r in rules.items()}
    maxs = {b: r.max for b, r in rules.items()}
    base = mins.copy()  # 현재 할당

    total_min = sum(mins.values())
    total_min = _round2(total_min)
    if total_min > 100.0:
        # 정책이 과도하게 타이트한 경우: min을 균등비로 축소
        scale = 100.0 / total_min
        for b in base:
            base[b] = _round2(base[b] * scale)
        return _largest_remainder_to_100(base)

    # 제안치 클리핑
    proposed_clamped = {b: _clamp(proposed.get(b, 0.0), mins[b], maxs[b]) for b in rules}

    remaining = 100.0 - total_min
    remaining = max(0.0, remaining)

    # 희망 증가량 = 제안치 - min (음수면 0)
    desire = {b: max(0.0, proposed_clamped[b] - mins[b]) for b in rules}
    capacity = {b: max(0.0, maxs[b] - mins[b]) for b in rules}

    active = set(rules.keys())
    alloc_extra = {b: 0.0 for b in rules}

    while remaining > 1e-9 and active:
        desire_sum = sum(desire[b] for b in active)
        if desire_sum <= 1e-9:
            # 더 원하는 곳이 없으면 target 기준으로 배분
            target_bias = {b: max(0.0, rules[b].target - mins[b]) for b in active}
            bias_sum = sum(target_bias.values()) or len(active)
            for b in list(active):
                add = remaining * (target_bias.get(b, 1.0) / bias_sum)
                add = min(add, capacity[b] - alloc_extra[b])
                alloc_extra[b] += add
                if abs(alloc_extra[b] - capacity[b]) < 1e-9:
                    active.remove(b)
            break

        for b in list(active):
            share = remaining * (desire[b] / desire_sum)
            share = min(share, capacity[b] - alloc_extra[b])
            alloc_extra[b] += share
            if abs(alloc_extra[b] - capacity[b]) < 1e-9:
                active.remove(b)

        remaining = 100.0 - sum(mins[b] + alloc_extra[b] for b in rules)

        # 남은 값이 음수/미세 오차면 정리
        if remaining < 0:
            remaining = 0.0

    result = {b: mins[b] + alloc_extra[b] for b in rules}
    # 마지막 100.00 보장 라운딩
    return _largest_remainder_to_100(result)


def reconcile_proposed_allocations(
    rules: RuleTable,
    proposed_allocs: List[dict],
) -> Tuple[List[dict], List[str]]:
    """
    GPT 제안(proposed_allocs [{bucket, weight_pct}, ...])을
    정책(min/max) 내에서 100.00%로 정규화하고, 조정 내역 메모를 반환.
    """
    notes: List[str] = []
    proposed_map: Dict[AssetType, float] = {a["bucket"]: float(a.get("weight_pct", 0.0)) for a in proposed_allocs}

    # 룰에 없는 버킷 제안은 무시
    for b in list(proposed_map.keys()):
        if b not in rules:
            notes.append(f"unknown bucket dropped: {b}")
            proposed_map.pop(b, None)

    # 빠진 버킷은 0으로 채워 넣기(룰은 항상 7버킷을 가짐)
    for b in rules:
        proposed_map.setdefault(b, 0.0)

    # --- min/max 초과/미달 사전 체크(정보만) ---
    for b, r in rules.items():
        v = proposed_map[b]
        if v < r.min:
            notes.append(f"{b} raised to min {r.min:.2f} from {v:.2f}")
        if v > r.max:
            notes.append(f"{b} clipped to max {r.max:.2f} from {v:.2f}")

    # --- NEW: 타깃 근접 유도를 위한 부드러운 블렌딩 ---
    # 타깃과 50:50로 섞어 과도한 극단값을 완화(시그니처 변경 없음)
    BLEND = 0.5  # 0~1 (값이 클수록 GPT 제안 가중)
    target_map: Dict[AssetType, float] = {b: rules[b].target for b in rules}
    blended_map: Dict[AssetType, float] = {
        b: BLEND * proposed_map[b] + (1 - BLEND) * target_map[b]
        for b in rules
    }

    # --- 물붓기로 min/max 내부에서 100.00 맞춤 ---
    adjusted_map = _waterfill_to_limits(rules, blended_map)
    adjusted_map = _largest_remainder_to_100(adjusted_map)

    final_allocs = [{"bucket": b, "weight_pct": _round2(adjusted_map[b])} for b in rules]
    final_allocs.sort(key=lambda x: x["bucket"])  # 안정적 출력

    notes.append("normalized to 100.00 (target-blended)")
    return final_allocs, notes

def normalize_assets_within_bucket(
    bucket_weight: float,
    assets: List[dict],
) -> List[dict]:
    """
    버킷 내부 종목 가중치의 합을 bucket_weight와 정확히 맞춤(2-decimal).
    assets = [{"code": "AAA", "weight_pct": 10.0}, ...]
    """
    if not assets:
        return []

    total = sum(float(a.get("weight_pct", 0.0)) for a in assets)
    if total <= 0:
        # 균등 분배
        equal = bucket_weight / len(assets)
        raw = [equal for _ in assets]
    else:
        scale = bucket_weight / total
        raw = [float(a.get("weight_pct", 0.0)) * scale for a in assets]

    # Largest Remainder(2-dec)로 합치기
    floored = [int(x * 100) / 100.0 for x in raw]
    cents_needed = int(round(bucket_weight * 100 - sum(int(x * 100) for x in floored)))
    rema = [(i, raw[i] - floored[i]) for i in range(len(raw))]
    rema.sort(key=lambda x: x[1], reverse=True)

    res = floored[:]
    idx = 0
    while cents_needed > 0 and idx < len(res):
        res[rema[idx][0]] = round(res[rema[idx][0]] + 0.01, 2)
        cents_needed -= 1
        idx = (idx + 1) if (idx + 1) < len(res) else 0

    out = []
    for i, a in enumerate(assets):
        out.append({"code": a["code"], "weight_pct": _round2(res[i])})
    return out