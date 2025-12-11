# users/views_preference.py
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    InvestmentPreferenceCreateSerializer,
    InvestmentPreferenceSerializer,
)
from .services.preference_service import save_preference_and_update_snapshot


class PreferenceSaveView(APIView):
    """
    POST /api/users/preference/save
      - body: { amount_krw, horizon_code, include_products: string[] }
      - return: 저장된 InvestmentPreference
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pref = save_preference_and_update_snapshot(request.user, request.data)
        return Response(InvestmentPreferenceSerializer(pref).data, status=201)


class PreferenceCurrentView(APIView):
    """
    GET /api/users/preference/current
      - return: 최신 InvestmentPreference (스냅샷)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        snap = getattr(request.user, "preference_snapshot", None)
        if not snap:
            return Response({"detail": "no preference yet"}, status=404)
        return Response(InvestmentPreferenceSerializer(snap.latest_pref).data, status=200)