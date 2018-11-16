from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='instances'),
    path('start/', views.startstop, name='start'),
    path('stop/', views.startstop, {'start':False}, name='stop'),
]