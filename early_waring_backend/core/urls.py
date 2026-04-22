"""
Early Warning System - core app URL patterns
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # ── AUTH ──────────────────────────────────────────────────
    path('auth/login/',    views.LoginView.as_view(),   name='auth-login'),
    path('auth/logout/',   views.LogoutView.as_view(),  name='auth-logout'),
    path('auth/register/', views.RegisterView.as_view(), name='auth-register'),
    path('auth/me/',       views.MeView.as_view(),      name='auth-me'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # ── LOP HOC ───────────────────────────────────────────────
    path('classes/',       views.LopHocListView.as_view(),   name='lophoc-list'),
    path('classes/<int:pk>/', views.LopHocDetailView.as_view(), name='lophoc-detail'),

    # ── HOC VIEN ──────────────────────────────────────────────
    path('students/',            views.HocVienListView.as_view(),    name='hocvien-list'),
    path('students/<int:pk>/',   views.HocVienDetailView.as_view(),  name='hocvien-detail'),
    path('students/<int:pk>/progress/', views.HocVienProgressView.as_view(), name='hocvien-progress'),

    # ── BANG DIEM ─────────────────────────────────────────────
    path('scores/',            views.BangDiemListView.as_view(),   name='bangdiem-list'),
    path('scores/<int:pk>/',   views.BangDiemDetailView.as_view(), name='bangdiem-detail'),

    # ── ML PREDICT ────────────────────────────────────────────
    path('predict/',         views.PredictView.as_view(),       name='predict'),
    path('predict/batch/',   views.PredictBatchView.as_view(),  name='predict-batch'),
    path('predict/manual/',  views.PredictManualView.as_view(), name='predict-manual'),

    # ── DU DOAN (HISTORY) ─────────────────────────────────────
    path('predictions/',           views.DuDoanListView.as_view(),  name='dudoan-list'),
    path('predictions/warnings/',  views.WarningListView.as_view(), name='dudoan-warnings'),

    # ── DASHBOARD ─────────────────────────────────────────────
    path('dashboard/',              views.DashboardView.as_view(),      name='dashboard'),
    path('dashboard/class/<int:pk>/', views.DashboardClassView.as_view(), name='dashboard-class'),

    # ── MLOPS ADMIN ───────────────────────────────────────────
    path('admin/retrain/', views.RetrainView.as_view(), name='admin-retrain'),
]
