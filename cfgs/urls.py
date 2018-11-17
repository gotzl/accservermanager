from django.urls import path, re_path

from . import views

urlpatterns = [
    path(r'', views.confSelect, name='confSelect'),
    path(r'delete/', views.confDelete, name='confDelete'),
    path(r'create/', views.confCreate, name='confCreate'),
    re_path(r'^([^/]+)/?(.*)', views.formForKey, name='formForKey'),
]