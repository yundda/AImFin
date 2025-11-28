from django.shortcuts import render

# Create your views here.
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(["GET"])
# @permission_classes([AllowAny])
def portfolio_ping(request):
    return Response({"api": "portfolio.ping", "ok": True})

@api_view(["POST"])
# @permission_classes([AllowAny])
def portfolio_save(request):
    return Response({"api": "portfolio.save", "echo": request.data})

@api_view(["GET"])
# @permission_classes([AllowAny])
def portfolio_list(request):
    return Response({"api": "portfolio.list", "results": []})

@api_view(["GET", "POST"])
# @permission_classes([AllowAny])
def portfolio_representative(request):
    if request.method == "GET":
        return Response({"api": "portfolio.representative.get", "representative": None})
    return Response({"api": "portfolio.representative.post", "echo": request.data})

@api_view(["GET"])
# @permission_classes([AllowAny])
def portfolio_detail_test(request, portfolio_id: int):
    return Response({"api": "portfolio.detail", "id": portfolio_id})
