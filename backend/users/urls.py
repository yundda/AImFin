from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,  # POST {email, password} → {access, refresh}
    TokenRefreshView,     # POST {refresh} → {access}
    TokenVerifyView,      # POST {token} → 200/401
)
from . import views,views_social


urlpatterns = [
    path("auth/signup", views.signup, name="register"),
    path("auth/login", TokenObtainPairView.as_view(), name="login"),
    path("auth/refresh", TokenRefreshView.as_view(), name="refresh"),
    path("auth/verify", TokenVerifyView.as_view(), name="verify"),
    path("auth/logout", views.LogoutView.as_view(), name="logout"),

    # 구글 OAuth (서버 주도 + PKCE)
    path("auth/google/start", views_social.GoogleStartView.as_view(), name="google-start"),
    path("auth/google/callback", views_social.GoogleCallbackView.as_view(), name="google-callback"),
]
