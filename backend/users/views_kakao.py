# users/views_social_kakao.py
from django.conf import settings
from django.shortcuts import redirect
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .utils.pkce_store import save_nonce, pop_nonce  # state 재사용: nonce 키만 써도 ok
from .utils.oauth_kakao import build_auth_url, exchange_code_for_token, fetch_userinfo
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def issue_tokens(user):
    r = RefreshToken.for_user(user)
    return {"access": str(r.access_token), "refresh": str(r)}

class KakaoStartView(APIView):
    def get(self, request):
        state = get_random_string(32)
        # 구글처럼 같은 저장소를 재활용 (이름은 nonce지만 state 저장용으로 사용)
        save_nonce(state, "1")  # 값 의미 없음, 유효성만 보자
        url = build_auth_url(state)
        return Response({"auth_url": url})

class KakaoCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code or not state:
            return Response({"detail": "missing code/state"}, status=400)

        # state 검증
        marker = pop_nonce(state)
        if not marker:
            return Response({"detail": "invalid state"}, status=400)

        # 1) 코드 → 토큰
        try:
            token_json = exchange_code_for_token(code)
        except Exception as e:
            return Response({"detail": f"token exchange failed: {e}"}, status=400)

        access_token = token_json.get("access_token")
        if not access_token:
            return Response({"detail": "no access_token"}, status=400)

        # 2) 사용자 정보 조회
        try:
            info = fetch_userinfo(access_token)
        except Exception as e:
            return Response({"detail": f"userinfo failed: {e}"}, status=400)

        kakao_id = info.get("id")
        kakao_account = (info.get("kakao_account") or {})
        email = kakao_account.get("email")
        profile = kakao_account.get("profile") or {}
        nickname_from_kakao = profile.get("nickname")

        # 이메일이 동의 항목에 없을 수 있음 → 서비스 정책에 맞춰 대체 이메일 생성
        if not email:
            email = f"kakao_{kakao_id}@kakao.local"

        defaults = {
            "nickname": nickname_from_kakao or email.split("@")[0],
        }
        user, created = User.objects.get_or_create(email=email, defaults=defaults)

        # JWT 발급 + 쿠키
        tokens = issue_tokens(user)
        is_secure = not settings.DEBUG
        samesite = "None" if is_secure else "Lax"

        # 닉네임 온보딩 분기 (구글과 동일 로직)
        has_nick = bool(getattr(user, "nickname", "") and user.nickname.strip())
        redirect_path = "/onboarding/nickname" if (created or not has_nick) else "/"

        resp = redirect(f"{settings.FRONTEND_URL}{redirect_path}")
        resp.set_cookie("access", tokens["access"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        resp.set_cookie("refresh", tokens["refresh"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        return resp
