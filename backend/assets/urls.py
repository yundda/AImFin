from django.urls import path
from rest_framework.response import Response
from rest_framework.decorators import api_view
from . import views


urlpatterns = [
    path("ping", views.ping),
    path("compare", views.compare, name="analysis.compare"),  # POST /api/analysis/compare
    path("analyze", views.single_analyze, name="analysis.analyze"),  # POST /api/analysis/analyze
    path("survey_analyze", views.survey_analyze, name="analysis.survey_analyze"),  # POST
]