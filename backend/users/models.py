from django.contrib.auth.models import AbstractUser
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
        return self.display_name or self.email