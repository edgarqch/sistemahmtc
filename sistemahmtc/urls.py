"""
URL configuration for sistemahmtc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.conf import settings # se importo para los archivos media
from django.views.static import serve # se importo para los archivos media
from django.urls import path, include, re_path # se importo include
from apps.biblioteca.views import Home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('biblioteca/', include(('apps.biblioteca.urls','biblioteca'))),
    path('', Home, name='index'),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve,{
        'document_root': settings.MEDIA_ROOT,
    })
]
