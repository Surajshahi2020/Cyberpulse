# collect/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('/newsfeed', views.dashboard, name='dashboard'),
]