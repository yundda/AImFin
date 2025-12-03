# users/views_social.py
from django.utils.crypto import get_random_string
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.shortcuts import redirect
from .oauth_google_jwks import verify_id_token
from .utils.pkce_store import save_verifier, pop_verifier, save_nonce, pop_nonce
from django.utils.crypto import get_random_string

from .oauth_google import gen_pkce, build_auth_url, exchange_code_for_token, OIDCIdToken
from .utils.pkce_store import save_verifier, pop_verifier

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

        token_json = exchange_code_for_token(code, code_verifier)
        id_token = token_json.get("id_token")
        if not id_token:
            return Response({"detail": "no id_token"}, status=400)


        # ✅ JWKS 서명 검증 + nonce 확인
        payload = verify_id_token(id_token, nonce=nonce)
        email = payload.get("email") or f"google_{payload['sub']}@google.local"

        user, _ = User.objects.get_or_create(email=email)
        tokens = issue_tokens(user)

        # ✅ HttpOnly/Secure 쿠키 발급 (개발 중엔 Secure 빼도 무방, 운영은 필수)
        resp = redirect(f"{settings.FRONTEND_URL}/auth/success")
        resp.set_cookie("access", tokens["access"], httponly=True, samesite="None", secure=False)
        resp.set_cookie("refresh", tokens["refresh"], httponly=True, samesite="None", secure=False)
        return resp