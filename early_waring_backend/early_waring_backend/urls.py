"""
URL configuration for early_waring_backend project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from django.conf import settings
from django.http import JsonResponse
import os


def health_check(request):
    """Health check endpoint để Render xác nhận app đã chạy."""
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),

    # ── HEALTH CHECK (bắt buộc cho Render) ──
    path('api/health/', health_check, name='health-check'),

    # ── FRONTEND HTML ──
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('index.html', TemplateView.as_view(template_name='index.html')),
    path('admin.html', TemplateView.as_view(template_name='admin.html')),
    path('teacher.html', TemplateView.as_view(template_name='teacher.html')),
    path('student.html', TemplateView.as_view(template_name='student.html')),

    # ── SERVE CSS/JS/ASSETS DIRECTLY ──
    re_path(r'^css/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.PROJECT_ROOT, 'frontend', 'css')}),
    re_path(r'^js/(?P<path>.*)$', serve, {'document_root': os.path.join(settings.PROJECT_ROOT, 'frontend', 'js')}),
    re_path(r'^favicon.ico$', serve, {'document_root': os.path.join(settings.PROJECT_ROOT, 'frontend'), 'path': 'favicon.ico'}),
]
