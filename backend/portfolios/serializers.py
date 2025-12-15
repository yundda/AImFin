# portfolios/serializers.py
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List

from django.db import transaction
from rest_framework import serializers

from portfolios.models import (
    Portfolio, PortfolioAllocation, PortfolioAsset, PortfolioMetrics
)
from assets.enums import AssetType
from assets.models import Asset  # code / asset_type / is_enabled 가정

# 서버 계산 지표
try:
    from analysis.services.metrics import compute_portfolio_metrics
except Exception:
    compute_portfolio_metrics = None


def q2f(x: float | int | Decimal) -> float:
    d = Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(d)


class PortfolioAssetInSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=32)
    weight_pct = serializers.FloatField(min_value=0.0)


class PortfolioAllocationInSerializer(serializers.Serializer):
    bucket = serializers.ChoiceField(choices=AssetType.choices)
    weight_pct = serializers.FloatField(min_value=0.0)
    assets = PortfolioAssetInSerializer(many=True, required=False)

    def validate(self, data):
        # assets 합계 == bucket weight_pct
        assets = data.get("assets") or []
        bw = q2f(data["weight_pct"])
        if assets:
            s = q2f(sum(a["weight_pct"] for a in assets))
            if abs(s - bw) > 0.01:
                raise serializers.ValidationError(
                    f"assets 합({s:.2f}) != 버킷 비중({bw:.2f})"
                )
        # 코드-버킷 정합성 검증(존재/타입)
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

    # 원문/로그(선택)
    ai_proposed_allocations = serializers.ListField(child=serializers.DictField(), required=False)
    corrections = serializers.ListField(child=serializers.CharField(), required=False)

    # 최종 구성(필수)
    allocations = PortfolioAllocationInSerializer(many=True)

    # 저장 옵션
    set_primary = serializers.BooleanField(required=False, default=False)

    def validate_allocations(self, value: List[dict]):
        # 총합 100.00
        total = q2f(sum(row.get("weight_pct", 0) for row in value))
        if abs(total - 100.00) > 0.01:
            raise serializers.ValidationError(f"버킷 합계가 100.00이 아닙니다: {total:.2f}")
        # 버킷 중복 방지
        buckets = [row["bucket"] for row in value]
        if len(buckets) != len(set(buckets)):
            raise serializers.ValidationError("동일 버킷이 중복되었습니다.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        user = self.context["request"].user

        allocations = validated_data.pop("allocations")
        set_primary = validated_data.pop("set_primary", False)

        portfolio = Portfolio.objects.create(
            user=user,
            **validated_data,
            source=Portfolio.Source.AI,
        )

        # 버킷/자산 저장
        alloc_objs = []
        for row in allocations:
            alloc = PortfolioAllocation.objects.create(
                portfolio=portfolio,
                bucket=row["bucket"],
                weight_pct=q2f(row["weight_pct"]),
            )
            alloc_objs.append(alloc)
            assets = row.get("assets") or []
            for a in assets:
                PortfolioAsset.objects.create(
                    allocation=alloc,
                    code=a["code"],
                    weight_pct=q2f(a["weight_pct"]),
                )

        # 메트릭스 계산(서버 공식)
        metrics_dict = {"expected_return_pct": None, "risk_score": None}
        if compute_portfolio_metrics:
            final_allocs = []
            for alloc in alloc_objs:
                final_allocs.append({
                    "bucket": alloc.bucket,
                    "weight_pct": float(alloc.weight_pct),
                    "assets": [{"code": pa.code, "weight_pct": float(pa.weight_pct)} for pa in alloc.assets.all()],
                })
            try:
                m = compute_portfolio_metrics(final_allocs)
                metrics_dict = {
                    "expected_return_pct": q2f(m.get("expected_return_pct")),
                    "risk_score": q2f(m.get("risk_score")),
                }
            except Exception:
                pass

        PortfolioMetrics.objects.create(
            portfolio=portfolio,
            expected_return_pct=metrics_dict["expected_return_pct"],
            risk_score=metrics_dict["risk_score"],
        )

        if set_primary:
            portfolio.set_primary()

        return portfolio


class PortfolioAssetOutSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioAsset
        fields = ("code", "weight_pct")


class PortfolioAllocationOutSerializer(serializers.ModelSerializer):
    assets = PortfolioAssetOutSerializer(many=True)

    class Meta:
        model = PortfolioAllocation
        fields = ("bucket", "weight_pct", "assets")


class PortfolioDetailSerializer(serializers.ModelSerializer):
    allocations = PortfolioAllocationOutSerializer(many=True)
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = (
            "id", "name", "source",
            "amount_krw", "profile", "profile_label", "horizon_desc",
            "must_buckets", "corrections",
            "rationale", "summary", "risks",
            "ai_proposed_allocations", "is_primary",
            "generated_at", "created_at", "updated_at",
            "allocations", "metrics",
        )

    def get_metrics(self, obj: Portfolio) -> dict:
        if hasattr(obj, "metrics") and obj.metrics:
            return obj.metrics.as_dict()
        return {"expected_return_pct": None, "risk_score": None}


class PortfolioListSerializer(serializers.ModelSerializer):
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ("id", "name", "is_primary", "created_at", "amount_krw", "profile", "profile_label", "horizon_desc", "metrics")

    def get_metrics(self, obj: Portfolio) -> dict:
        if hasattr(obj, "metrics") and obj.metrics:
            return obj.metrics.as_dict()
        return {"expected_return_pct": None, "risk_score": None}