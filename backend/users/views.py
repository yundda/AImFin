from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .serializer import RegisterSerializer

User = get_user_model()

@api_view(["POST"])
def signup(request):
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    ser.save()
    return Response(ser.data, status=status.HTTP_201_CREATED)

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # 클라이언트가 보낸 refresh 토큰을 블랙리스트 처리(없어도 205 반환)
        refresh = request.data.get("refresh")
        if refresh:
            try:
                token = RefreshToken(refresh)
                token.blacklist()
            except Exception:
                pass
        resp = Response(status=status.HTTP_205_RESET_CONTENT)
        resp.delete_cookie("access")
        resp.delete_cookie("refresh")
        return resp

class CookieRefreshView(APIView):
    def post(self, request):
        refresh = request.COOKIES.get("refresh") or request.data.get("refresh")
        if not refresh:
            return Response({"detail": "no refresh"}, status=400)
        try:
            token = RefreshToken(refresh)
            new_access = str(token.access_token)
            new_refresh = str(token)  # 회전 설정 시 새 토큰 생성됨
        except TokenError:
            return Response({"detail": "invalid refresh"}, status=401)

        resp = Response({"detail": "rotated"})
        resp.set_cookie("access", new_access, httponly=True, samesite="None", secure=False)
        resp.set_cookie("refresh", new_refresh, httponly=True, samesite="None", secure=False)
        return resp