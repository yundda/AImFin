# portfolios/models.py
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from users.models import RiskProfileCode  # TextChoices 가정
from assets.enums import AssetType        # TextChoices 가정


def q2(x: Decimal | float | int) -> Decimal:
    """소수 둘째 자리 반올림(은행식 아님)"""
    if not isinstance(x, Decimal):
        x = Decimal(str(x))
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Portfolio(models.Model):
    class Source(models.TextChoices):
        AI = "AI", "AI"
        MANUAL = "MANUAL", "MANUAL"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="portfolios",
    )

    name = models.CharField(max_length=120, blank=True, default="")
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.AI)

    # 요약 메타
    amount_krw = models.BigIntegerField()
    profile = models.CharField(max_length=32, choices=RiskProfileCode.choices)
    profile_label = models.CharField(max_length=64)
    horizon_desc = models.CharField(max_length=64)

    # 프론트 입력/정책 정보
    must_buckets = models.JSONField(default=list)   # ["STOCKS_KR", ...]
    corrections = models.JSONField(default=list, blank=True)  # 정책 조정 로그(문자열 리스트)

    # 서술(라쇼날/요약/리스크)
    rationale = models.TextField(blank=True, default="")
    summary = models.TextField(blank=True, default="")
    risks = models.TextField(blank=True, default="")

    # AI 원문 보존(선택)
    ai_proposed_allocations = models.JSONField(null=True, blank=True)  # GPT 제안 원문
    ai_raw_response = models.JSONField(null=True, blank=True)          # GPT 응답 전체(필요 시)

    # 대표 포트폴리오 플래그
    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    generated_at = models.DateTimeField(default=timezone.now)  # 추천 생성 기준시각

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        title = self.name or f"{self.profile_label}·{self.horizon_desc}"
        return f"[{self.user_id}] {title}"

    @transaction.atomic
    def set_primary(self) -> None:
        """이 유저의 다른 대표를 해제하고 자신을 대표로"""
        Portfolio.objects.select_for_update().filter(
            user=self.user, is_primary=True
        ).exclude(pk=self.pk).update(is_primary=False)
        if not self.is_primary:
            self.is_primary = True
            self.save(update_fields=["is_primary"])


class PortfolioAllocation(models.Model):
    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="allocations"
    )
    bucket = models.CharField(max_length=32, choices=AssetType.choices)
    weight_pct = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = (("portfolio", "bucket"),)
        indexes = [
            models.Index(fields=["portfolio", "bucket"]),
        ]
        ordering = ["bucket"]

    def save(self, *args, **kwargs):
        self.weight_pct = q2(self.weight_pct)
        return super().save(*args, **kwargs)


class PortfolioAsset(models.Model):
    allocation = models.ForeignKey(
        PortfolioAllocation, on_delete=models.CASCADE, related_name="assets"
    )
    code = models.CharField(max_length=32)
    weight_pct = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        unique_together = (("allocation", "code"),)
        indexes = [
            models.Index(fields=["allocation", "code"]),
        ]
        ordering = ["code"]

    def save(self, *args, **kwargs):
        self.weight_pct = q2(self.weight_pct)
        return super().save(*args, **kwargs)


class PortfolioMetrics(models.Model):
    portfolio = models.OneToOneField(
        Portfolio, on_delete=models.CASCADE, related_name="metrics"
    )
    expected_return_pct = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0~100
    computed_at = models.DateTimeField(auto_now_add=True)

    def as_dict(self) -> dict:
        return {
            "expected_return_pct": float(self.expected_return_pct) if self.expected_return_pct is not None else None,
            "risk_score": float(self.risk_score) if self.risk_score is not None else None,
        }