from django.urls import path
from . import views

app_name = "detector"

urlpatterns = [
    path("", views.home, name="home"),
    path("buscar/", views.buscar, name="buscar"),
    path("analizar/", views.analizar, name="analizar"),
    path("app/<slug:slug>/", views.detalle_app, name="detalle"),
]
