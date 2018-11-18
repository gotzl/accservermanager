from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='instances'),
    path('start/', views.start, name='start'),
    path('<name>/stderr', views.stderr, name='stderr'),
    path('<name>/stdout', views.stdout, name='stdout'),
    path('<name>/stop', views.startstop, {'start':False}, name='stop'),
]