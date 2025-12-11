# analysis/views_recommend.py
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers

from analysis.services.recommend import recommend_portfolio
from analysis.serializers import RecommendInputSerializer

class RecommendRequestSerializer(serializers.Serializer):
    amount_krw = serializers.IntegerField(min_value=1)
    horizon = serializers.ChoiceField(choices=["<1y","1_3y","3_5y",">=5y"])
    must_buckets = serializers.ListField(
        child=serializers.ChoiceField(choices=["STOCKS_KR","STOCKS_GLB","BONDS_KR","BONDS_GLB","FUNDS","ALTERNATIVES","CASH"]),
        required=False,
        allow_empty=True,
    )

    def to_human_horizon(self, code: str) -> str:
        return {
            "<1y": "1년 이하",
            "1_3y": "1~3년",
            "3_5y": "3~5년",
            ">=5y": "5년 이상",
        }[code]


class RecommendPortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = RecommendInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        v = ser.validated_data

        result = recommend_portfolio(
            user=request.user,
            amount_krw=v["amount_krw"],
            horizon_desc=v["horizon_desc"],        # ← 정규화된 키 사용
            must_buckets=v.get("must_buckets", []),
        )
        return Response(result, status=200)