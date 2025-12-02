# users/views_social.py
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import redirect

from rest_framework_simplejwt.tokens import RefreshToken

from .oauth_google import gen_pkce, build_auth_url, exchange_code_for_token, OIDCIdToken
from .utils.pkce_store import save_verifier, pop_verifier

User = get_user_model()

def issue_tokens(user):
    r = RefreshToken.for_user(user)
    return {"access": str(r.access_token), "refresh": str(r)}

class GoogleStartView(APIView):
    def get(self, request):
        state = get_random_string(32)
        code_verifier, code_challenge = gen_pkce()
        save_verifier(state, code_verifier)
        url = build_auth_url(state, code_challenge)
        return Response({"auth_url": url})

class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code or not state:
            return Response({"detail": "missing code/state"}, status=400)

        code_verifier = pop_verifier(state)
        if not code_verifier:
            return Response({"detail": "invalid state"}, status=400)

        token_json = exchange_code_for_token(code, code_verifier)
        id_token = token_json.get("id_token")
        if not id_token:
            return Response({"detail": "no id_token"}, status=400)

        # TODO: JWKS 서명 검증 추가 (현재는 payload만 파싱 + 기본 필드 검증)
        idp = OIDCIdToken.from_jwt(id_token)
        idp.basic_validate()

        email = idp.email or f"google_{idp.sub}@google.local"
        user, _ = User.objects.get_or_create(email=email)

        tokens = issue_tokens(user)

        # (임시) 프런트로 토큰 전달 — 개발 중엔 쿼리로, 운영은 HttpOnly 쿠키 권장
        return redirect(f"{settings.FRONTEND_URL}/auth/success#access={tokens['access']}&refresh={tokens['refresh']}")
