import re
from django.contrib.auth import get_user_model
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .serializers import RegisterSerializer
from .models import SurveyResult  # 설문 이력 카운트용

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

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user

        # 최신 성향: 스냅샷 우선
        snap = getattr(u, "risk_snapshot", None)
        sr = getattr(snap, "latest_result", None) if snap else None

        data = {
            "id": u.id,
            "email": u.email,
            "nickname": u.nickname or "",

            # 최신 성향 요약(없으면 null)
            "survey_profile": sr.profile if sr else None,                 # 예: "BALANCED"
            "survey_profile_label": sr.get_profile_display() if sr else None,  # 예: "중립형"
            "survey_total_score": float(sr.total_score) if sr else None,  # 예: 73.33
            "last_survey_at": sr.created_at.isoformat() if sr else None,

            # 이력/온보딩 편의정보
            "survey_count": SurveyResult.objects.filter(user=u).count(),
            "needs_nickname": not bool((u.nickname or "").strip()),
            "has_survey": bool(sr),
        }
        return Response(data, status=status.HTTP_200_OK)
class NicknameView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """현재 사용자 닉네임 조회"""
        return Response({"nickname": request.user.nickname or ""}, status=status.HTTP_200_OK)

    def patch(self, request):
        """닉네임 설정/수정"""
        nick = (request.data.get("nickname") or "").strip()

        if not nick:
            return Response({"detail": "nickname is required"}, status=status.HTTP_400_BAD_REQUEST)
        if len(nick) > 20:
            return Response({"detail": "nickname too long (max 20)"}, status=status.HTTP_400_BAD_REQUEST)
        if not re.fullmatch(r"[A-Za-z0-9가-힣 _.\-]{1,20}", nick):
            return Response({"detail": "invalid nickname (allowed: letters, digits, 한글, space, . _ -)"}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        user.nickname = nick
        user.save(update_fields=["nickname"])
        return Response({"id": user.id, "email": user.email, "nickname": user.nickname}, status=status.HTTP_200_OK)