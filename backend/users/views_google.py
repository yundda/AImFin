# users/views_social.py
from django.conf import settings
from django.shortcuts import redirect
from django.utils.crypto import get_random_string
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model

from .utils.pkce_store import save_verifier, pop_verifier, save_nonce, pop_nonce
from .utils.oauth_google import gen_pkce, build_auth_url, exchange_code_for_token
from .oauth_google_jwks import verify_id_token
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

def issue_tokens(user):
    r = RefreshToken.for_user(user)
    return {"access": str(r.access_token), "refresh": str(r)}

class GoogleStartView(APIView):
    def get(self, request):
        state = get_random_string(32)
        nonce = get_random_string(32)
        code_verifier, code_challenge = gen_pkce()
        save_verifier(state, code_verifier)
        save_nonce(state, nonce)
        # build_auth_url 내부에서 settings.GOOGLE_REDIRECT_URI 사용하도록 구현되어 있어야 함
        url = build_auth_url(state, code_challenge) + f"&nonce={nonce}"
        return Response({"auth_url": url})

class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code or not state:
            return Response({"detail": "missing code/state"}, status=400)

        code_verifier = pop_verifier(state)
        nonce = pop_nonce(state)
        if not code_verifier or not nonce:
            return Response({"detail": "invalid state/nonce"}, status=400)

        # 1) 코드→토큰 교환
        try:
            token_json = exchange_code_for_token(code, code_verifier)
        except Exception as e:
            return Response({"detail": f"token exchange failed: {e}"}, status=400)

        id_token = token_json.get("id_token")
        access_token = token_json.get("access_token")
        if not id_token:
            return Response({"detail": "no id_token"}, status=400)

        # 2) JWKS 서명 검증 + aud/iss/exp + nonce + at_hash(access_token 필요)
        try:
            payload = verify_id_token(id_token, nonce=nonce, access_token=access_token)
        except Exception as e:
            return Response({"detail": f"id_token verify failed: {e}"}, status=400)

        email = payload.get("email") or f"google_{payload['sub']}@google.local"
        # 닉네임 없으면 기본값
        defaults = {"nickname": payload.get("name") or email.split("@")[0]}
        user, created = User.objects.get_or_create(email=email, defaults=defaults)

        # 3) JWT 발급
        tokens = issue_tokens(user)

        # 4) 쿠키 발급 (개발/운영 분기)
        is_secure = not settings.DEBUG
        # SameSite 규칙:
        # - 운영(https, 크로스사이트): SameSite=None + Secure=True 필수
        # - 로컬(http): SameSite="Lax", Secure=False 권장
        samesite = "None" if is_secure else "Lax"

        has_nick = bool(getattr(user, "nickname", "") and user.nickname.strip())
        redirect_path = "/onboarding/nickname" if (created or not has_nick) else "/"

        resp = redirect(f"{settings.FRONTEND_URL}{redirect_path}")
        resp.set_cookie("access", tokens["access"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        resp.set_cookie("refresh", tokens["refresh"], httponly=True, secure=is_secure, samesite=samesite, path="/")
        return resp