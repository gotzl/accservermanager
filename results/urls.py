from django.urls import re_path, path

from . import views

urlpatterns = [
    path('', views.resultSelect, name='instances'),
    re_path(r'^([^/]+)/?(.*)', views.index, name='results'),
]