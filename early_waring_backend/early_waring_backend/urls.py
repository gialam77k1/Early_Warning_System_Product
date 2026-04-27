"""
URL configuration for early_waring_backend project.

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
from django.urls import path, include, re_path
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
import os


def health_check(request):
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health-check'),
    path('api/', include('core.urls')),
    
    # ── FRONTEND HTML ──
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('home.html', TemplateView.as_view(template_name='home.html')),
    path('index.html', TemplateView.as_view(template_name='index.html')),
    path('register.html', TemplateView.as_view(template_name='register.html')),
    path('admin.html', TemplateView.as_view(template_name='admin.html')),
    path('teacher.html', TemplateView.as_view(template_name='teacher.html')),
    path('student.html', TemplateView.as_view(template_name='student.html')),

    # ── SERVE CSS/JS/ASSETS DIRECTLY ──
    re_path(r'^css/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.PROJECT_ROOT, 'frontend', 'css')}),
    re_path(r'^js/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.PROJECT_ROOT, 'frontend', 'js')}),
    re_path(r'^img/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.PROJECT_ROOT, 'frontend', 'img')}),
    re_path(r'^favicon.ico$', serve, {'document_root': os.path.join(settings.PROJECT_ROOT, 'frontend', 'img'), 'path': 'logo.png'}),
]
