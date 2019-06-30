"""accservermanager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='main.html'), name='login'),
    path('cfgs/', include('cfgs.urls')),
    path('booking/', include('booking.urls')),
    path('instances/', include('instances.urls')),
    path('results/', include('results.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]


def on_startup():
    import os, shutil
    from accservermanager import settings
    if not os.path.exists(settings.CONFIGS): os.makedirs(settings.CONFIGS)
    if not os.path.exists(settings.INSTANCES): os.makedirs(settings.INSTANCES)
    # make sure that there is always a cfg in the cfg folder
    if len(os.listdir(settings.CONFIGS) ) == 0:
        shutil.copy(os.path.join(settings.ACCSERVER,'cfg','event.json'),
                os.path.join(settings.CONFIGS,'event.json'))

on_startup()
