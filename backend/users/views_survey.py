from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics

from users.models import SurveyResult
from users.serializers import SurveyResultSerializer
from users.services.survey_service import save_survey_and_update_snapshot

class SurveySaveView(APIView):
    """
    POST /api/users/survey/save
    - 본문: 설문 원문 payload(JSON)
    - 동작: 점수 계산 → SurveyResult 저장 → 스냅샷 갱신
    - 응답: 방금 저장된 SurveyResult
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # request.data = 프론트 설문 원문
        sr = save_survey_and_update_snapshot(request.user, request.data)
        return Response(SurveyResultSerializer(sr).data, status=201)


class SurveyCurrentView(APIView):
    """
    GET /api/users/survey/current
    - 현재(스냅샷) 설문 결과를 O(1)로 반환
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        snap = getattr(request.user, "risk_snapshot", None)
        if not snap:
            return Response({"detail": "no survey yet"}, status=404)
        return Response(SurveyResultSerializer(snap.latest_result).data)


# class RiskHistoryView(generics.ListAPIView):
#     """
#     GET /api/users/risk/history?page=1
#     - 설문 이력 페이지네이션
#     """
#     permission_classes = [IsAuthenticated]
#     serializer_class = SurveyResultSerializer

#     def get_queryset(self):
#         return SurveyResult.objects.filter(user=self.request.user).order_by("-created_at")