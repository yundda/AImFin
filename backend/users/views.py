from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# Create your views here.
@api_view(["GET"])
# @permission_classes([AllowAny])
def users_ping(request):
    return Response({"api": "users.ping", "ok": True})