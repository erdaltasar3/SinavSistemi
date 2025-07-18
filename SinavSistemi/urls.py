"""
URL configuration for SinavSistemi project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

# core.views içinden index fonksiyonunu import et
from core import views as core_views

def accounts_login_redirect(request):
    """accounts/login/ URL'ini kendi giris sayfamıza yönlendir"""
    return redirect('core:giris')

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", core_views.index, name="index"),
    path("yks/", include("yks.urls")),
    path("", include("core.urls")),
    path("accounts/login/", accounts_login_redirect, name="accounts_login"),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
