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
    path('', TemplateView.as_view(template_name='base.html'), name='login'),
    path('cfgs/', include('cfgs.urls')),
    path('instances/', include('instances.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
]


def on_startup():
    import os, shutil
    from accservermanager import settings
    directory = os.path.join(settings.ACCSERVER,'cfg','custom')
    if not os.path.exists(directory):
        os.makedirs(directory)
        cfg = os.path.join(settings.ACCSERVER,'cfg','custom.json'), \
              os.path.join(directory,'custom.json')
        shutil.copy(cfg[0], cfg[0]+'.bkup')
        os.rename(cfg[0], cfg[1])
        os.symlink(cfg[1], cfg[0])

on_startup()
