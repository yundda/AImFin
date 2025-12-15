# portfolios/serializers.py
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any

from django.db import transaction
from rest_framework import serializers

from portfolios.models import Portfolio
from assets.enums import AssetType
from assets.models import Asset  # code / asset_type / is_enabled

# 서버 계산 지표(없어도 동작)
try:
    from analysis.services.metrics import compute_portfolio_metrics
except Exception:  # pragma: no cover
    compute_portfolio_metrics = None


# ---------- 공통 유틸 ----------
def q2f(x: float | int | Decimal | None) -> float:
    if x is None:
        return 0.0
    d = Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(d)


# ---------- 입력 스키마 ----------
class PortfolioAssetInSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=32)
    weight_pct = serializers.FloatField(min_value=0.0)


class PortfolioAllocationInSerializer(serializers.Serializer):
    bucket = serializers.ChoiceField(choices=AssetType.choices)
    weight_pct = serializers.FloatField(min_value=0.0)
    assets = PortfolioAssetInSerializer(many=True, required=False)

    def validate(self, data):
        # (1) assets 합계 == bucket weight_pct (소수 2자리 기준)
        assets = data.get("assets") or []
        bw = q2f(data["weight_pct"])
        if assets:
            s = q2f(sum(a["weight_pct"] for a in assets))
            if abs(s - bw) > 0.01:
                raise serializers.ValidationError(
                    f"assets 합({s:.2f}) != 버킷 비중({bw:.2f})"
                )

        # (2) 자산 코드 존재/활성 + 버킷 일치
        for a in assets:
            code = a["code"]
            qs = Asset.objects.filter(code=code, is_enabled=True)
            if not qs.exists():
                raise serializers.ValidationError(f"자산 코드 미존재/비활성: {code}")
            asset = qs.first()
            if asset.asset_type != data["bucket"]:
                raise serializers.ValidationError(
                    f"코드 {code} 의 버킷({asset.asset_type}) != 요청 버킷({data['bucket']})"
                )
        return data


class PortfolioCreateSerializer(serializers.Serializer):
    # 기본 메타
    name = serializers.CharField(max_length=120, required=False, allow_blank=True, default="")
    amount_krw = serializers.IntegerField(min_value=0)
    profile = serializers.CharField(max_length=32)
    profile_label = serializers.CharField(max_length=64)
    horizon_desc = serializers.CharField(max_length=64)

    # 정책/선호
    must_buckets = serializers.ListField(
        child=serializers.ChoiceField(choices=AssetType.choices),
        allow_empty=True,
        required=False,
        default=list,
    )

    # 서술
    rationale = serializers.CharField(required=False, allow_blank=True, default="")
    summary = serializers.CharField(required=False, allow_blank=True, default="")
    risks = serializers.CharField(required=False, allow_blank=True, default="")

    # 최종 구성(필수)
    allocations = PortfolioAllocationInSerializer(many=True)

    # 저장 옵션 (대표 지정)
    set_representative = serializers.BooleanField(required=False, default=False)

    def validate_allocations(self, value: List[dict]):
        # (A) 총합 100.00 고정
        total = q2f(sum(row.get("weight_pct", 0) for row in value))
        if abs(total - 100.00) > 0.01:
            raise serializers.ValidationError(f"버킷 합계가 100.00이 아닙니다: {total:.2f}")

        # (B) 버킷 중복 금지
        buckets = [row["bucket"] for row in value]
        if len(buckets) != len(set(buckets)):
            raise serializers.ValidationError("동일 버킷이 중복되었습니다.")
        return value

    @staticmethod
    def _normalize_allocations_for_storage(allocs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """모델 JSON 저장용으로 소수 2자리 고정."""
        out: List[Dict[str, Any]] = []
        for row in allocs:
            item = {
                "bucket": row["bucket"],
                "weight_pct": q2f(row["weight_pct"]),
            }
            assets = row.get("assets") or []
            norm_assets = [{"code": a["code"], "weight_pct": q2f(a["weight_pct"])} for a in assets]
            if norm_assets:
                item["assets"] = norm_assets
            else:
                item["assets"] = []
            out.append(item)
        return out

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user

        allocations = validated_data.pop("allocations")
        set_rep = validated_data.pop("set_representative", False)

        # JSON 필드용 정규화(2-dec)
        norm_allocs = self._normalize_allocations_for_storage(allocations)

        # 서버 계산 지표(없으면 None)
        metrics_dict = {"expected_return_pct": None, "risk_score": None}
        if compute_portfolio_metrics:
            try:
                m = compute_portfolio_metrics(norm_allocs)
                metrics_dict = {
                    "expected_return_pct": q2f(m.get("expected_return_pct")),
                    "risk_score": q2f(m.get("risk_score")),
                }
            except Exception:
                # 계산 실패해도 저장은 진행
                pass

        # 포트폴리오 생성(JSON 필드에 직접 저장)
        portfolio = Portfolio.objects.create(
            user=user,
            allocations=norm_allocs,
            metrics=metrics_dict,
            source=Portfolio.Source.AI,
            **validated_data,
        )

        # 대표 설정 옵션 처리
        if set_rep:
            portfolio.set_representative()

        return portfolio


# ---------- 출력 스키마 ----------
class PortfolioDetailSerializer(serializers.ModelSerializer):
    # allocations / metrics 는 JSONField 그대로 전달
    class Meta:
        model = Portfolio
        fields = (
            "id", "name", "source",
            "amount_krw", "profile", "profile_label", "horizon_desc",
            "must_buckets", "corrections",
            "rationale", "summary", "risks",
            "ai_proposed_allocations", "is_representative",
            "generated_at", "created_at", "updated_at",
            "allocations", "metrics",
        )


class PortfolioListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = (
            "id", "name", "is_representative", "created_at",
            "amount_krw", "profile", "profile_label", "horizon_desc",
            "metrics",
        )
