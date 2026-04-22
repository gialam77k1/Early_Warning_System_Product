"""
Early Warning System - DRF Serializers
Serializers cho 5 models + Auth
"""

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import NguoiDung, LopHoc, HocVien, BangDiem, DuDoanML


# =============================================================
#  AUTH SERIALIZERS
# =============================================================

class LoginSerializer(serializers.Serializer):
    """Serializer đăng nhập"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Tên đăng nhập hoặc mật khẩu không đúng.')
        if not user.is_active:
            raise serializers.ValidationError('Tài khoản đã bị khóa.')
        data['user'] = user
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer đăng ký (chỉ Admin mới được tạo)"""
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = NguoiDung
        fields = ['username', 'password', 'email', 'ho_ten', 'vai_tro', 'so_dien_thoai']

    def create(self, validated_data):
        user = NguoiDung.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', ''),
            ho_ten=validated_data.get('ho_ten', ''),
            vai_tro=validated_data.get('vai_tro', 'student'),
            so_dien_thoai=validated_data.get('so_dien_thoai', ''),
        )
        return user


class NguoiDungSerializer(serializers.ModelSerializer):
    """Serializer thông tin người dùng"""
    vai_tro_display = serializers.CharField(source='get_vai_tro_display', read_only=True)

    class Meta:
        model = NguoiDung
        fields = [
            'id', 'username', 'email', 'ho_ten', 'vai_tro',
            'vai_tro_display', 'so_dien_thoai', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'created_at', 'updated_at']


# =============================================================
#  LOP HOC SERIALIZERS
# =============================================================

class LopHocSerializer(serializers.ModelSerializer):
    """Serializer lớp học"""
    giao_vien_ten = serializers.CharField(source='giao_vien.ho_ten', read_only=True, default='')
    so_hoc_vien = serializers.IntegerField(read_only=True)

    class Meta:
        model = LopHoc
        fields = [
            'id', 'ten_lop', 'mo_ta', 'giao_vien', 'giao_vien_ten',
            'nam_hoc', 'hoc_ky', 'is_active', 'so_hoc_vien', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class LopHocDetailSerializer(serializers.ModelSerializer):
    """Serializer chi tiết lớp học (kèm danh sách học viên)"""
    giao_vien_ten = serializers.CharField(source='giao_vien.ho_ten', read_only=True, default='')
    so_hoc_vien = serializers.IntegerField(read_only=True)
    hoc_vien_list = serializers.SerializerMethodField()

    class Meta:
        model = LopHoc
        fields = [
            'id', 'ten_lop', 'mo_ta', 'giao_vien', 'giao_vien_ten',
            'nam_hoc', 'hoc_ky', 'is_active', 'so_hoc_vien',
            'hoc_vien_list', 'created_at'
        ]

    def get_hoc_vien_list(self, obj):
        hoc_viens = obj.hoc_vien_list.all()
        return HocVienSerializer(hoc_viens, many=True).data


# =============================================================
#  HOC VIEN SERIALIZERS
# =============================================================

class HocVienSerializer(serializers.ModelSerializer):
    """Serializer học viên"""
    ho_ten = serializers.CharField(source='nguoi_dung.ho_ten', read_only=True)
    email = serializers.CharField(source='nguoi_dung.email', read_only=True)
    lop_ten = serializers.CharField(source='lop.ten_lop', read_only=True, default='')

    class Meta:
        model = HocVien
        fields = [
            'id', 'nguoi_dung', 'ma_hoc_vien', 'ho_ten', 'email',
            'lop', 'lop_ten', 'ngay_sinh', 'gioi_tinh', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class HocVienDetailSerializer(serializers.ModelSerializer):
    """Serializer chi tiết học viên (kèm bảng điểm + dự đoán)"""
    ho_ten = serializers.CharField(source='nguoi_dung.ho_ten', read_only=True)
    email = serializers.CharField(source='nguoi_dung.email', read_only=True)
    lop_ten = serializers.CharField(source='lop.ten_lop', read_only=True, default='')
    bang_diem = serializers.SerializerMethodField()

    class Meta:
        model = HocVien
        fields = [
            'id', 'nguoi_dung', 'ma_hoc_vien', 'ho_ten', 'email',
            'lop', 'lop_ten', 'ngay_sinh', 'gioi_tinh',
            'bang_diem', 'created_at'
        ]

    def get_bang_diem(self, obj):
        bang_diems = obj.bang_diem_list.all()
        return BangDiemSerializer(bang_diems, many=True).data


# =============================================================
#  BANG DIEM SERIALIZERS
# =============================================================

class DuDoanMLSerializer(serializers.ModelSerializer):
    """Serializer dự đoán ML"""
    risk_level_display = serializers.CharField(source='get_risk_level_display', read_only=True)

    class Meta:
        model = DuDoanML
        fields = [
            'id', 'bang_diem', 'predicted_label',
            'prob_weak', 'prob_average', 'prob_good', 'prob_excellent',
            'risk_level', 'risk_level_display',
            'model_name', 'predicted_at'
        ]
        read_only_fields = ['id', 'predicted_at']


class BangDiemSerializer(serializers.ModelSerializer):
    """Serializer bảng điểm"""
    hoc_vien_ma = serializers.CharField(source='hoc_vien.ma_hoc_vien', read_only=True)
    hoc_vien_ten = serializers.CharField(source='hoc_vien.nguoi_dung.ho_ten', read_only=True)
    du_doan = DuDoanMLSerializer(read_only=True)

    class Meta:
        model = BangDiem
        fields = [
            'id', 'hoc_vien', 'hoc_vien_ma', 'hoc_vien_ten',
            'homework_1', 'homework_2', 'homework_3',
            'quiz_1', 'quiz_2',
            'midterm_score', 'final_exam', 'attendance_rate',
            'final_score', 'performance_label',
            'du_doan',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'final_score', 'created_at', 'updated_at']


class BangDiemCreateSerializer(serializers.ModelSerializer):
    """Serializer tạo/cập nhật bảng điểm (giáo viên nhập điểm)"""

    class Meta:
        model = BangDiem
        fields = [
            'id', 'hoc_vien',
            'homework_1', 'homework_2', 'homework_3',
            'quiz_1', 'quiz_2',
            'midterm_score', 'final_exam', 'attendance_rate',
            'performance_label'
        ]
        read_only_fields = ['id']


# =============================================================
#  PREDICT SERIALIZER
# =============================================================

class PredictInputSerializer(serializers.Serializer):
    """Input cho API predict"""
    bang_diem_id = serializers.IntegerField(
        help_text='ID của bảng điểm cần dự đoán'
    )


class PredictBatchSerializer(serializers.Serializer):
    """Input cho batch predict"""
    bang_diem_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text='Danh sách ID bảng điểm'
    )


class PredictManualSerializer(serializers.Serializer):
    """Input predict thủ công (không cần bảng điểm sẵn)"""
    homework_1 = serializers.FloatField(min_value=0, max_value=10)
    homework_2 = serializers.FloatField(min_value=0, max_value=10)
    homework_3 = serializers.FloatField(min_value=0, max_value=10)
    quiz_1 = serializers.FloatField(min_value=0, max_value=10)
    quiz_2 = serializers.FloatField(min_value=0, max_value=10)
    midterm_score = serializers.FloatField(min_value=0, max_value=10)
    final_exam = serializers.FloatField(min_value=0, max_value=10)
    attendance_rate = serializers.FloatField(min_value=0, max_value=1)


# =============================================================
#  DASHBOARD SERIALIZERS
# =============================================================

class DashboardSerializer(serializers.Serializer):
    """Serializer cho dashboard tổng quan"""
    tong_hoc_vien = serializers.IntegerField()
    tong_lop_hoc = serializers.IntegerField()
    tong_giao_vien = serializers.IntegerField()
    tong_bang_diem = serializers.IntegerField()
    tong_du_doan = serializers.IntegerField()
    phan_bo_risk = serializers.DictField()
    phan_bo_label = serializers.DictField()
    hoc_vien_canh_bao = serializers.ListField()
