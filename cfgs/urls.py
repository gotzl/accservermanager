from django.urls import path, re_path

from . import views

urlpatterns = [
    path(r'', views.confSelect, name='confSelect'),
    path(r'delete', views.confDelete, name='confDelete'),
    path(r'create', views.confCreate, name='confCreate'),
    path(r'rename', views.confRename, name='confRename'),
    path(r'clone', views.confClone, name='confClone'),
    re_path(r'^([^/]+)/?(.*)', views.formForKey, name='formForKey'),
]