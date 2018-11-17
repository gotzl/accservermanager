from django.urls import path, re_path

from . import views

urlpatterns = [
    path(r'', views.confSelect, name='confSelect'),
    re_path(r'^([^/]+)/?(.*)', views.formForKey, name='formForKey'),
]