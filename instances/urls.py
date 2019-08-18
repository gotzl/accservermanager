from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='instances'),
    path('start', views.create, name='start'),
    path('<name>/', views.instance, name='instance'),
    path('<name>/start', views.start, name='start'),
    path('<name>/stop', views.stop, name='stop'),
    path('<name>/delete', views.delete, name='delete'),
    path('<name>/stderr', views.stderr, name='stderr'),
    path('<name>/stdout', views.stdout, name='stdout'),
    path('<name>/configuration', views.download_configuration_file, name='configuration'),
    path('<name>/event', views.download_event_file, name='event'),
    path('<name>/settings', views.download_settings_file, name='settings'),
    path('<name>/entrylist', views.download_entrylist_file, name='entrylist'),
]