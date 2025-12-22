# analysis/views_compare.py
from __future__ import annotations

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, serializers

from analysis.services.compare import compare_portfolios

# 버킷 코드는 영문 코드만 허용 (라벨은 프롬프트에서 한글화)
BUCKET_CHOICES = [
    "STOCKS_KR", "STOCKS_GLB",
    "BONDS_KR", "BONDS_GLB",
    "ALTERNATIVES", "FUNDS", "CASH",
]

class AllocationItemSerializer(serializers.Serializer):
    bucket = serializers.ChoiceField(choices=BUCKET_CHOICES)
    weight_pct = serializers.IntegerField(min_value=0, max_value=100)

class CompareSideSerializer(serializers.Serializer):
    # {"type":"id","id":3}  또는  {"type":"allocations","allocations":[...]}
    type = serializers.ChoiceField(choices=["id", "allocations"])
    id = serializers.IntegerField(required=False)
    allocations = serializers.ListField(
        child=AllocationItemSerializer(),
        required=False,
        allow_empty=False
    )

    def validate(self, attrs):
        t = attrs.get("type")
        if t == "id":
            if "id" not in attrs:
                raise serializers.ValidationError({"id": "type이 'id'이면 id가 필요합니다."})
        elif t == "allocations":
            allocs = attrs.get("allocations")
            if not isinstance(allocs, list) or not allocs:
                raise serializers.ValidationError({"allocations": "비중 목록이 필요합니다."})
            # 합계 100 검증(정확한 비교를 위해 강제)
            s = sum(int(a.get("weight_pct", 0)) for a in allocs)
            if s != 100:
                raise serializers.ValidationError({"allocations": f"weight_pct 합계는 100이어야 합니다. (현재 {s})"})
        return attrs

class CompareInputSerializer(serializers.Serializer):
    left = CompareSideSerializer()
    right = CompareSideSerializer()

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def compare_portfolio(request):
    """
    POST /api/analysis/compare/portfolio

    Body (세 모드 중 하나)
    1) {"left":{"type":"id","id":2}, "right":{"type":"id","id":5}}
    2) {"left":{"type":"id","id":2}, "right":{"type":"allocations","allocations":[...]}}
    3) {"left":{"type":"allocations","allocations":[...]}, "right":{"type":"allocations","allocations":[...]}}

    응답: {"rationale": str, "summary": str, "risks": str, "generated_at": iso str}
    """
    ser = CompareInputSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    v = ser.validated_data

    try:
        out = compare_portfolios(
            user=request.user,
            left_spec=v["left"],    # {"type":"id","id":...} 또는 {"type":"allocations","allocations":[...]}
            right_spec=v["right"],
        )
        return Response(out, status=status.HTTP_200_OK)
    except Exception as e:
        # 서비스/DB 에러도 400으로 래핑해 원인 노출
        return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)