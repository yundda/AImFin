from django.urls import path
from . import views

urlpatterns = [
    path("ping", views.users_ping),  # GET /api/users/ping
]
