from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index),
    path('<object>/', views.showObject),
    path('<object>/<pk>/', views.showObject),
    path('<object>/<pk>/<action>', views.showObject),
]