from django.urls import path
from . import views

urlpatterns = [
    path("ping", views.portfolio_ping),  # GET /api/portfolio/ping
    path("save", views.portfolio_save_test, name="portfolio.save"),  # POST /api/portfolio/save
    path("list", views.portfolio_list_test, name="portfolio.list"),  # GET /api/portfolio/list
    path("representative", views.portfolio_representative_test, name="portfolio.representative"),  # GET/POST
    path("<int:portfolio_id>", views.portfolio_detail_test, name="portfolio.detail"),  # GET /api/portfolio/{id}
]