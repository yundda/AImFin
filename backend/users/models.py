from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class User(AbstractUser):
    # 인증은 email로만: 기존 username 필드 제거
    username = None

    # 고유 이메일 (로그인 ID)
    email = models.EmailField(unique=True)

    # 표시용 닉네임(중복 허용, 선택 입력)
    nickname = models.CharField(max_length=30, blank=True, default="", db_index=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # createsuperuser 시 추가 필드 요구 X

    def __str__(self):
        return self.nickname or self.email



class SurveyResult(models.Model):
    """
    설문 1회 응답 + 계산 결과(점수, 프로필)를 '이력'으로 저장.
    - 입력 원문(survey_json)
    - 계산 브레이크다운(breakdown_json)
    - 총점(total_score), 최종 프로필(profile)
    """
    # 최종 프로필(리스크 성향) 코드값: 계산 로직과 정확히 일치
    RISK_PROFILE_CHOICES = [
        ("ANJUNG", "안정형"),
        ("ANJUNG_CHUGU", "안정추구형"),
        ("BALANCED", "중립형"),
        ("JEOGEUG", "적극투자형"),
        ("AGGRESSIVE", "공격투자형"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="survey_results",
    )
    # 설문 입력 원문: 위의 SurveyInput에 상응하는 payload 전체
    survey_json = models.JSONField(default=dict)  # {"products": [...], "history_period": "...", ...}

    # 계산 결과
    total_score = models.DecimalField(max_digits=5, decimal_places=2)  # 예: 0.00 ~ 100.00
    profile = models.CharField(max_length=20, choices=RISK_PROFILE_CHOICES)

    # 세부 점수(브레이크다운): {experience_raw, afford_raw, purpose_raw, risk_raw, period_raw}
    breakdown_json = models.JSONField(default=dict)

    # 설문 버전/출처(Optional)
    version = models.CharField(max_length=20, blank=True, default="v1")
    source = models.CharField(max_length=20, blank=True, default="WEB")  # WEB/MOBILE 등

    # 감사/디버그(Optional)
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "survey_result"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["profile"]),
        ]

    def __str__(self):
        return f"SurveyResult(user={self.user_id}, profile={self.profile}, score={self.total_score})"


class UserRiskSnapshot(models.Model):
    """
    '현재' 투자 성향(최신 설문)을 빠르게 조회하기 위한 스냅샷.
    - 앱 로직에서 설문 저장 직후 이 포인터를 최신 SurveyResult로 갱신.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="risk_snapshot",
    )
    latest_result = models.OneToOneField(
        SurveyResult,
        on_delete=models.CASCADE,
        related_name="as_current_for",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_risk_snapshot"

    def __str__(self):
        return f"UserRiskSnapshot(user={self.user_id}, profile={self.latest_result.profile})"
