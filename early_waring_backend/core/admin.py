"""
Early Warning System - Django Admin Configuration
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import NguoiDung, LopHoc, HocVien, BangDiem, DuDoanML


@admin.register(NguoiDung)
class NguoiDungAdmin(UserAdmin):
    list_display = ['username', 'ho_ten', 'email', 'vai_tro', 'is_active']
    list_filter = ['vai_tro', 'is_active']
    search_fields = ['username', 'ho_ten', 'email']
    
    # Thêm trường custom vào form
    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('vai_tro', 'ho_ten', 'so_dien_thoai')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Thông tin bổ sung', {
            'fields': ('vai_tro', 'ho_ten', 'email')
        }),
    )


@admin.register(LopHoc)
class LopHocAdmin(admin.ModelAdmin):
    list_display = ['ten_lop', 'giao_vien', 'nam_hoc', 'hoc_ky', 'so_hoc_vien', 'is_active']
    list_filter = ['nam_hoc', 'hoc_ky', 'is_active']
    search_fields = ['ten_lop']


@admin.register(HocVien)
class HocVienAdmin(admin.ModelAdmin):
    list_display = ['ma_hoc_vien', 'nguoi_dung', 'lop', 'gioi_tinh', 'ngay_sinh']
    list_filter = ['lop', 'gioi_tinh']
    search_fields = ['ma_hoc_vien', 'nguoi_dung__ho_ten']


@admin.register(BangDiem)
class BangDiemAdmin(admin.ModelAdmin):
    list_display = [
        'hoc_vien', 'homework_1', 'homework_2', 'homework_3',
        'quiz_1', 'quiz_2', 'midterm_score', 'final_exam',
        'attendance_rate', 'final_score', 'performance_label'
    ]
    list_filter = ['performance_label']
    search_fields = ['hoc_vien__ma_hoc_vien', 'hoc_vien__nguoi_dung__ho_ten']
    readonly_fields = ['final_score']


@admin.register(DuDoanML)
class DuDoanMLAdmin(admin.ModelAdmin):
    list_display = [
        'bang_diem', 'predicted_label', 'risk_level',
        'prob_weak', 'prob_average', 'prob_good', 'prob_excellent',
        'model_name', 'predicted_at'
    ]
    list_filter = ['predicted_label', 'risk_level', 'model_name']
    readonly_fields = ['predicted_at']
