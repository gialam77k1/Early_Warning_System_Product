"""
=============================================================
  Early Warning System - API Views
  REST API cho 5 models + Auth + ML Predict + Dashboard
=============================================================
"""

import sys
import os
import io
import json
import threading
from datetime import datetime
from django.conf import settings
from django.db.models import Count, Avg, Q
from django.contrib.auth import login, logout
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import RefreshToken

from .models import NguoiDung, LopHoc, HocVien, BangDiem, DuDoanML
from .serializers import (
    LoginSerializer, RegisterSerializer, NguoiDungSerializer,
    LopHocSerializer, LopHocDetailSerializer,
    HocVienSerializer, HocVienDetailSerializer,
    BangDiemSerializer, BangDiemCreateSerializer,
    DuDoanMLSerializer,
    PredictInputSerializer, PredictBatchSerializer, PredictManualSerializer,
)


RETRAIN_STATUS_FILENAME = 'retrain_status.json'


# =============================================================
#  HELPER: Lấy JWT tokens cho user
# =============================================================

def get_tokens_for_user(user):
    """Tạo JWT refresh + access token cho user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def generate_student_code():
    """Sinh mã học viên tăng dần theo định dạng HV0001."""
    last_hv = HocVien.objects.order_by('-id').first()
    next_id = (last_hv.id + 1) if last_hv else 1
    return f'HV{next_id:04d}'


# =============================================================
#  PERMISSION CLASSES
# =============================================================

class IsAdmin(permissions.BasePermission):
    """Chỉ Admin mới được truy cập"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.vai_tro == 'admin'


class IsAdminOrTeacher(permissions.BasePermission):
    """Admin hoặc Giáo viên mới được truy cập"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.vai_tro in ['admin', 'teacher']


class IsTeacher(permissions.BasePermission):
    """Chỉ Giáo viên mới được truy cập"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.vai_tro == 'teacher'


# =============================================================
#  AUTH VIEWS
# =============================================================

class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { username, password }
    Returns: { user, access, refresh }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)

        return Response({
            'message': f'Đăng nhập thành công! Chào {user.ho_ten or user.username}',
            'user': NguoiDungSerializer(user).data,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        }, status=status.HTTP_200_OK)


class RegisterView(APIView):
    """
    POST /api/auth/register/
    Chỉ Admin được tạo tài khoản mới (chọn role bất kỳ)
    Body: { username, password, email, ho_ten, vai_tro, so_dien_thoai }
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        return Response({
            'message': f'Tạo tài khoản thành công!',
            'user': NguoiDungSerializer(user).data,
        }, status=status.HTTP_201_CREATED)


class PublicRegisterView(APIView):
    """
    POST /api/auth/public-register/
    Đăng ký tài khoản công khai — luôn tạo role student
    Body: { username, password, email, ho_ten }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        data = request.data.copy()
        data['vai_tro'] = 'student'  # Luôn tạo student
        serializer = RegisterSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'message': 'Đăng ký thành công!',
            'user': NguoiDungSerializer(user).data,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
        }, status=status.HTTP_201_CREATED)


class MeView(APIView):
    """
    GET  /api/auth/me/       — Xem thông tin bản thân
    PUT  /api/auth/me/       — Cập nhật thông tin bản thân
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = NguoiDungSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = NguoiDungSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Body: { refresh }  — Blacklist refresh token
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Đăng xuất thành công!'})
        except Exception:
            return Response({'message': 'Đăng xuất thành công!'})


# =============================================================
#  LOP HOC VIEWS
# =============================================================

class LopHocListView(APIView):
    """
    GET  /api/classes/   — Danh sách lớp học
    POST /api/classes/   — Tạo lớp mới (Admin)
    """
    permission_classes = [IsAdminOrTeacher]

    def get(self, request):
        user = request.user
        if user.vai_tro == 'admin':
            lop_hocs = LopHoc.objects.all()
        else:
            # Giáo viên chỉ xem lớp của mình
            lop_hocs = LopHoc.objects.filter(giao_vien=user)

        serializer = LopHocSerializer(lop_hocs, many=True)
        return Response({
            'count': lop_hocs.count(),
            'results': serializer.data
        })

    def post(self, request):
        if request.user.vai_tro != 'admin':
            return Response(
                {'error': 'Chỉ Admin mới được tạo lớp học.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = LopHocSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        lop = serializer.save()
        return Response(LopHocSerializer(lop).data, status=status.HTTP_201_CREATED)


class LopHocDetailView(APIView):
    """
    GET    /api/classes/<id>/   — Chi tiết lớp (kèm danh sách học viên)
    PUT    /api/classes/<id>/   — Cập nhật lớp (Admin)
    DELETE /api/classes/<id>/   — Xóa lớp (Admin)
    """
    permission_classes = [IsAdminOrTeacher]

    def get_object(self, pk, user):
        try:
            lop = LopHoc.objects.get(pk=pk)
            if user.vai_tro == 'teacher' and lop.giao_vien != user:
                return None, Response(
                    {'error': 'Bạn không có quyền xem lớp này.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return lop, None
        except LopHoc.DoesNotExist:
            return None, Response(
                {'error': 'Lớp học không tồn tại.'},
                status=status.HTTP_404_NOT_FOUND
            )

    def get(self, request, pk):
        lop, err = self.get_object(pk, request.user)
        if err:
            return err
        serializer = LopHocDetailSerializer(lop)
        return Response(serializer.data)

    def put(self, request, pk):
        if request.user.vai_tro != 'admin':
            return Response({'error': 'Chỉ Admin mới được sửa lớp học.'}, status=status.HTTP_403_FORBIDDEN)
        lop, err = self.get_object(pk, request.user)
        if err:
            return err
        serializer = LopHocSerializer(lop, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        if request.user.vai_tro != 'admin':
            return Response({'error': 'Chỉ Admin mới được xóa lớp học.'}, status=status.HTTP_403_FORBIDDEN)
        lop, err = self.get_object(pk, request.user)
        if err:
            return err
        lop.delete()
        return Response({'message': 'Đã xóa lớp học.'}, status=status.HTTP_204_NO_CONTENT)


# =============================================================
#  HOC VIEN VIEWS
# =============================================================

class HocVienListView(APIView):
    """
    GET  /api/students/   — Danh sách học viên
    POST /api/students/   — Tạo học viên mới (Admin)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        lop_id = request.query_params.get('lop_id')
        search = request.query_params.get('search', '').strip()

        if user.vai_tro == 'admin':
            hoc_viens = HocVien.objects.select_related('nguoi_dung', 'lop').all()
        elif user.vai_tro == 'teacher':
            # Giáo viên chỉ xem học viên trong lớp mình dạy
            lop_ids = LopHoc.objects.filter(giao_vien=user).values_list('id', flat=True)
            hoc_viens = HocVien.objects.filter(lop__in=lop_ids).select_related('nguoi_dung', 'lop')
        else:
            # Học viên chỉ thấy chính mình
            hoc_viens = HocVien.objects.filter(nguoi_dung=user).select_related('nguoi_dung', 'lop')

        if lop_id:
            hoc_viens = hoc_viens.filter(lop_id=lop_id)
        if search:
            hoc_viens = hoc_viens.filter(
                Q(nguoi_dung__ho_ten__icontains=search) | Q(ma_hoc_vien__icontains=search)
            )

        serializer = HocVienSerializer(hoc_viens, many=True)
        return Response({
            'count': hoc_viens.count(),
            'results': serializer.data,
        })

    def post(self, request):
        if request.user.vai_tro != 'admin':
            return Response({'error': 'Chỉ Admin mới được thêm học viên.'}, status=403)

        nguoi_dung_id = request.data.get('nguoi_dung')
        lop_id = request.data.get('lop')
        ma_hoc_vien = request.data.get('ma_hoc_vien', '')
        ngay_sinh = request.data.get('ngay_sinh', None)
        gioi_tinh = request.data.get('gioi_tinh', 'nam')

        if not nguoi_dung_id:
            return Response({'error': 'Thiếu nguoi_dung.'}, status=400)
        try:
            nd = NguoiDung.objects.get(pk=nguoi_dung_id)
        except NguoiDung.DoesNotExist:
            return Response({'error': 'Người dùng không tồn tại.'}, status=404)

        if nd.vai_tro != 'student':
            return Response({'error': 'Người dùng này không có vai trò student.'}, status=400)

        if HocVien.objects.filter(nguoi_dung=nd).exists():
            return Response({'error': 'Người dùng này đã có hồ sơ học viên.'}, status=400)

        if lop_id and not LopHoc.objects.filter(pk=lop_id).exists():
            return Response({'error': 'Lớp học không tồn tại.'}, status=400)

        if not ma_hoc_vien:
            ma_hoc_vien = generate_student_code()

        hv = HocVien.objects.create(
            nguoi_dung=nd,
            ma_hoc_vien=ma_hoc_vien,
            lop_id=lop_id if lop_id else None,
            ngay_sinh=ngay_sinh,
            gioi_tinh=gioi_tinh,
        )
        return Response(HocVienSerializer(hv).data, status=201)


class HocVienDetailView(APIView):
    """
    GET    /api/students/<id>/   — Chi tiết học viên (+ bảng điểm + dự đoán)
    PUT    /api/students/<id>/   — Cập nhật học viên (Admin)
    DELETE /api/students/<id>/   — Xóa hồ sơ học viên (Admin)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        try:
            hv = HocVien.objects.select_related('nguoi_dung', 'lop').get(pk=pk)
            # Student chỉ được xem hồ sơ của chính mình
            if user.vai_tro == 'student' and hv.nguoi_dung != user:
                return None, Response({'error': 'Không có quyền truy cập.'}, status=403)
            # Teacher chỉ xem HS trong lớp mình
            if user.vai_tro == 'teacher':
                lop_ids = LopHoc.objects.filter(giao_vien=user).values_list('id', flat=True)
                if hv.lop_id not in lop_ids:
                    return None, Response({'error': 'Học viên không thuộc lớp bạn quản lý.'}, status=403)
            return hv, None
        except HocVien.DoesNotExist:
            return None, Response({'error': 'Học viên không tồn tại.'}, status=404)

    def get(self, request, pk):
        hv, err = self.get_object(pk, request.user)
        if err:
            return err
        serializer = HocVienDetailSerializer(hv)
        return Response(serializer.data)

    def put(self, request, pk):
        if request.user.vai_tro != 'admin':
            return Response({'error': 'Chỉ Admin mới được cập nhật học viên.'}, status=403)

        hv, err = self.get_object(pk, request.user)
        if err:
            return err

        serializer = HocVienSerializer(hv, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        if request.user.vai_tro != 'admin':
            return Response({'error': 'Chỉ Admin mới được xóa học viên.'}, status=403)

        hv, err = self.get_object(pk, request.user)
        if err:
            return err

        hv.delete()
        return Response({'message': 'Đã xóa hồ sơ học viên.'}, status=204)


class HocVienProgressView(APIView):
    """
    GET /api/students/<id>/progress/   — Tiến độ chi tiết của học viên
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        hv, err = HocVienDetailView().get_object(pk, request.user)
        if err:
            return err

        bang_diems = BangDiem.objects.filter(hoc_vien=hv).prefetch_related('du_doan')
        if request.user.vai_tro == 'student':
            bang_diems = bang_diems.filter(is_approved=True)
        bang_diem_data = BangDiemSerializer(bang_diems, many=True).data

        # Tổng hợp tiến độ
        progress = {
            'ma_hoc_vien': hv.ma_hoc_vien,
            'ho_ten': hv.nguoi_dung.ho_ten,
            'lop': hv.lop.ten_lop if hv.lop else None,
            'bang_diem': bang_diem_data,
            'tong_bai_nop': bang_diems.count(),
        }

        if bang_diems.exists():
            latest = bang_diems.first()
            progress['diem_moi_nhat'] = {
                'final_score': latest.final_score,
                'performance_label': latest.performance_label,
            }
            if hasattr(latest, 'du_doan') and latest.du_doan:
                progress['du_doan_moi_nhat'] = DuDoanMLSerializer(latest.du_doan).data

        return Response(progress)


# =============================================================
#  BANG DIEM VIEWS
# =============================================================

class BangDiemListView(APIView):
    """
    GET  /api/scores/   — Danh sách bảng điểm
    POST /api/scores/   — Giáo viên nhập điểm mới
    """
    permission_classes = [IsAdminOrTeacher]

    def get(self, request):
        user = request.user
        hoc_vien_id = request.query_params.get('hoc_vien_id')
        lop_id = request.query_params.get('lop_id')

        bang_diems = BangDiem.objects.select_related(
            'hoc_vien', 'hoc_vien__nguoi_dung', 'hoc_vien__lop'
        ).prefetch_related('du_doan')

        if user.vai_tro == 'teacher':
            lop_ids = LopHoc.objects.filter(giao_vien=user).values_list('id', flat=True)
            bang_diems = bang_diems.filter(hoc_vien__lop__in=lop_ids)

        if hoc_vien_id:
            bang_diems = bang_diems.filter(hoc_vien_id=hoc_vien_id)
        if lop_id:
            bang_diems = bang_diems.filter(hoc_vien__lop_id=lop_id)

        serializer = BangDiemSerializer(bang_diems, many=True)
        return Response({'count': bang_diems.count(), 'results': serializer.data})

    def post(self, request):
        if request.user.vai_tro not in ['admin', 'teacher']:
            return Response({'error': 'Không có quyền nhập điểm.'}, status=403)

        serializer = BangDiemCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra giáo viên có dạy lớp này không
        hoc_vien_id = serializer.validated_data['hoc_vien'].id
        if request.user.vai_tro == 'teacher':
            lop_ids = LopHoc.objects.filter(giao_vien=request.user).values_list('id', flat=True)
            hv = HocVien.objects.filter(id=hoc_vien_id, lop__in=lop_ids).first()
            if not hv:
                return Response(
                    {'error': 'Học viên không thuộc lớp bạn quản lý.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        bang_diem = serializer.save()
        if request.user.vai_tro == 'teacher':
            bang_diem.is_approved = False
            bang_diem.approved_by = None
            bang_diem.save(update_fields=['is_approved', 'approved_by', 'updated_at'])
        else:
            bang_diem.is_approved = True
            bang_diem.approved_by = request.user
            bang_diem.save(update_fields=['is_approved', 'approved_by', 'updated_at'])

        # Tự động chạy ML predict sau khi nhập điểm
        _auto_predict(bang_diem)

        return Response(
            BangDiemSerializer(bang_diem).data,
            status=status.HTTP_201_CREATED
        )


class BangDiemDetailView(APIView):
    """
    GET    /api/scores/<id>/   — Chi tiết bảng điểm
    PUT    /api/scores/<id>/   — Cập nhật điểm (Giáo viên / Admin)
    DELETE /api/scores/<id>/   — Xóa bảng điểm (Admin)
    """
    permission_classes = [IsAdminOrTeacher]

    def get_object(self, pk):
        try:
            return BangDiem.objects.select_related(
                'hoc_vien', 'hoc_vien__nguoi_dung'
            ).prefetch_related('du_doan').get(pk=pk)
        except BangDiem.DoesNotExist:
            return None

    def get(self, request, pk):
        bd = self.get_object(pk)
        if not bd:
            return Response({'error': 'Bảng điểm không tồn tại.'}, status=404)
        return Response(BangDiemSerializer(bd).data)

    def put(self, request, pk):
        bd = self.get_object(pk)
        if not bd:
            return Response({'error': 'Bảng điểm không tồn tại.'}, status=404)

        if request.user.vai_tro == 'teacher':
            lop_ids = LopHoc.objects.filter(giao_vien=request.user).values_list('id', flat=True)
            if bd.hoc_vien.lop_id not in lop_ids:
                return Response({'error': 'Bạn không có quyền sửa điểm của học viên này.'}, status=403)

        serializer = BangDiemCreateSerializer(bd, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        bang_diem = serializer.save()
        if request.user.vai_tro == 'teacher':
            bang_diem.is_approved = False
            bang_diem.approved_by = None
            bang_diem.save(update_fields=['is_approved', 'approved_by', 'updated_at'])
        elif request.user.vai_tro == 'admin':
            bang_diem.is_approved = True
            bang_diem.approved_by = request.user
            bang_diem.save(update_fields=['is_approved', 'approved_by', 'updated_at'])

        # Tái dự đoán sau khi cập nhật điểm
        _auto_predict(bang_diem)

        return Response(BangDiemSerializer(bang_diem).data)

    def delete(self, request, pk):
        if request.user.vai_tro != 'admin':
            return Response({'error': 'Chỉ Admin mới được xóa bảng điểm.'}, status=403)
        bd = self.get_object(pk)
        if not bd:
            return Response({'error': 'Bảng điểm không tồn tại.'}, status=404)
        bd.delete()
        return Response({'message': 'Đã xóa bảng điểm.'}, status=status.HTTP_204_NO_CONTENT)


# =============================================================
#  ML PREDICT VIEWS
# =============================================================

def _load_predictor():
    """Load StudentPredictor từ ml/predict.py — lazy loading"""
    ml_root = os.path.join(settings.ML_MODEL_DIR, '..', '..')
    ml_dir = os.path.join(settings.BASE_DIR, '..', 'ml')
    ml_dir = os.path.abspath(ml_dir)
    if ml_dir not in sys.path:
        sys.path.insert(0, ml_dir)
    from predict import StudentPredictor
    return StudentPredictor()


def _get_model_name():
    """Đọc tên model thực tế từ model_metadata.json (tránh hardcode)."""
    import json
    try:
        metadata_path = os.path.join(
            os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'ml')),
            'saved_models', 'model_metadata.json'
        )
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        return metadata.get('model_name', 'Unknown')
    except Exception:
        return 'Unknown'


def _get_model_metadata():
    metadata_path = os.path.join(
        os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'ml')),
        'saved_models', 'model_metadata.json'
    )
    return _read_json_file(metadata_path, default={})


def _get_model_dir():
    return os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'ml', 'saved_models'))


def _get_retrain_status_path():
    return os.path.join(_get_model_dir(), RETRAIN_STATUS_FILENAME)


def _read_json_file(path, default=None):
    if default is None:
        default = {}
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def _write_json_file(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def _set_retrain_status(state, **extra):
    payload = {
        'state': state,
        'updated_at': datetime.now().isoformat(),
        **extra,
    }
    _write_json_file(_get_retrain_status_path(), payload)
    return payload


def _infer_performance_label_from_score(score):
    if score is None:
        return None
    try:
        numeric_score = float(score)
    except (TypeError, ValueError):
        return None
    if numeric_score < 5.0:
        return BangDiem.PerformanceLabel.WEAK
    if numeric_score < 6.5:
        return BangDiem.PerformanceLabel.AVERAGE
    if numeric_score < 8.0:
        return BangDiem.PerformanceLabel.GOOD
    return BangDiem.PerformanceLabel.EXCELLENT


def _build_label_distribution(score_queryset):
    distribution = {
        BangDiem.PerformanceLabel.EXCELLENT: 0,
        BangDiem.PerformanceLabel.GOOD: 0,
        BangDiem.PerformanceLabel.AVERAGE: 0,
        BangDiem.PerformanceLabel.WEAK: 0,
    }
    for score in score_queryset:
        label = score.performance_label or _infer_performance_label_from_score(score.final_score)
        if label in distribution:
            distribution[label] += 1
    return {label: count for label, count in distribution.items() if count}


def _auto_predict(bang_diem: BangDiem):
    """
    Tự động chạy ML predict và lưu kết quả vào DuDoanML.
    Được gọi sau khi nhập / cập nhật điểm.
    """
    try:
        predictor = _load_predictor()
        features = bang_diem.get_features()
        result = predictor.predict_single(**features)

        proba = result['probabilities']
        # Upsert DuDoanML (tạo mới hoặc cập nhật nếu đã tồn tại)
        DuDoanML.objects.update_or_create(
            bang_diem=bang_diem,
            defaults={
                'predicted_label': result['predicted_label'],
                'prob_weak': proba.get('Weak', 0),
                'prob_average': proba.get('Average', 0),
                'prob_good': proba.get('Good', 0),
                'prob_excellent': proba.get('Excellent', 0),
                'model_name': _get_model_name(),
            }
        )
    except Exception as e:
        # Không raise — predict lỗi không ảnh hưởng việc lưu điểm
        print(f"[WARN] Auto-predict thất bại: {e}")


class PredictView(APIView):
    """
    POST /api/predict/
    Dự đoán ML cho 1 bảng điểm đã có trong DB
    Body: { bang_diem_id: int }
    """
    permission_classes = [IsAdminOrTeacher]

    def post(self, request):
        serializer = PredictInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        bang_diem_id = serializer.validated_data['bang_diem_id']
        try:
            bd = BangDiem.objects.select_related('hoc_vien', 'hoc_vien__nguoi_dung').get(pk=bang_diem_id)
        except BangDiem.DoesNotExist:
            return Response({'error': 'Bảng điểm không tồn tại.'}, status=404)

        try:
            predictor = _load_predictor()
            features = bd.get_features()
            result = predictor.predict_single(**features)
        except Exception as e:
            return Response({'error': f'Lỗi khi dự đoán: {str(e)}'}, status=500)

        proba = result['probabilities']
        du_doan, created = DuDoanML.objects.update_or_create(
            bang_diem=bd,
            defaults={
                'predicted_label': result['predicted_label'],
                'prob_weak': proba.get('Weak', 0),
                'prob_average': proba.get('Average', 0),
                'prob_good': proba.get('Good', 0),
                'prob_excellent': proba.get('Excellent', 0),
                'model_name': _get_model_name(),
            }
        )

        return Response({
            'bang_diem_id': bang_diem_id,
            'hoc_vien': bd.hoc_vien.ma_hoc_vien,
            'predicted_label': result['predicted_label'],
            'final_score': result['final_score'],
            'probabilities': proba,
            'risk_level': du_doan.risk_level,
            'created': created,
        })


class PredictBatchView(APIView):
    """
    POST /api/predict/batch/
    Dự đoán ML cho nhiều bảng điểm cùng lúc
    Body: { bang_diem_ids: [int, ...] }
    """
    permission_classes = [IsAdminOrTeacher]

    def post(self, request):
        serializer = PredictBatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        ids = serializer.validated_data['bang_diem_ids']
        try:
            predictor = _load_predictor()
        except Exception as e:
            return Response({'error': f'Không load được model: {str(e)}'}, status=500)

        results = []
        for bd_id in ids:
            try:
                bd = BangDiem.objects.get(pk=bd_id)
                features = bd.get_features()
                result = predictor.predict_single(**features)
                proba = result['probabilities']

                du_doan, _ = DuDoanML.objects.update_or_create(
                    bang_diem=bd,
                    defaults={
                        'predicted_label': result['predicted_label'],
                        'prob_weak': proba.get('Weak', 0),
                        'prob_average': proba.get('Average', 0),
                        'prob_good': proba.get('Good', 0),
                        'prob_excellent': proba.get('Excellent', 0),
                        'model_name': _get_model_name(),
                    }
                )
                results.append({
                    'bang_diem_id': bd_id,
                    'hoc_vien': bd.hoc_vien.ma_hoc_vien,
                    'predicted_label': result['predicted_label'],
                    'risk_level': du_doan.risk_level,
                    'final_score': result['final_score'],
                })
            except BangDiem.DoesNotExist:
                results.append({'bang_diem_id': bd_id, 'error': 'Không tìm thấy bảng điểm.'})
            except Exception as e:
                results.append({'bang_diem_id': bd_id, 'error': str(e)})

        return Response({'count': len(results), 'results': results})


class PredictManualView(APIView):
    """
    POST /api/predict/manual/
    Dự đoán thủ công — không cần bảng điểm trong DB
    Body: { homework_1, homework_2, ..., attendance_rate }
    """
    permission_classes = [IsAdminOrTeacher]

    def post(self, request):
        serializer = PredictManualSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        try:
            predictor = _load_predictor()
            result = predictor.predict_single(**serializer.validated_data)
        except Exception as e:
            return Response({'error': f'Lỗi khi dự đoán: {str(e)}'}, status=500)

        risk = predictor.get_risk_level(result['predicted_label'])
        return Response({
            'predicted_label': result['predicted_label'],
            'final_score': result['final_score'],
            'probabilities': result['probabilities'],
            'risk_level': risk,
        })


class RetrainView(APIView):
    """
    POST /api/admin/retrain/
    Trigger lại pipeline MLOps (ml_retrain) trong background thread.
    Chỉ Admin mới được gọi.
    Trả về ngay lập tức (202 Accepted), pipeline chạy nền.
    """
    permission_classes = [IsAdmin]

    def post(self, request):
        from django.core.management import call_command

        current_status = _read_json_file(_get_retrain_status_path(), default={})
        if current_status.get('state') == 'running':
            return Response({
                'status': 'running',
                'message': 'MLOps pipeline đang chạy. Vui lòng đợi tiến trình hiện tại hoàn tất.',
                'retrain_status': current_status,
            }, status=409)

        started_at = datetime.now().isoformat()
        _set_retrain_status(
            'queued',
            requested_by=request.user.username,
            started_at=started_at,
            message='Yêu cầu retrain đã được đưa vào hàng chờ nội bộ.',
        )

        def run_retrain():
            log_output = io.StringIO()
            try:
                _set_retrain_status(
                    'running',
                    requested_by=request.user.username,
                    started_at=started_at,
                    message='Pipeline đang huấn luyện lại model trên server.',
                )
                call_command('ml_retrain', stdout=log_output, stderr=log_output)
                _set_retrain_status(
                    'completed',
                    requested_by=request.user.username,
                    started_at=started_at,
                    finished_at=datetime.now().isoformat(),
                    message='Retrain hoàn tất.',
                    last_output=log_output.getvalue()[-4000:],
                )
            except Exception as e:
                error_output = log_output.getvalue()
                if error_output:
                    error_output += '\n'
                error_output += f'[ERROR] {str(e)}'
                _set_retrain_status(
                    'failed',
                    requested_by=request.user.username,
                    started_at=started_at,
                    finished_at=datetime.now().isoformat(),
                    message='Retrain thất bại.',
                    last_output=error_output[-4000:],
                )

        thread = threading.Thread(target=run_retrain, daemon=True)
        thread.start()

        return Response({
            'status': 'started',
            'message': 'MLOps pipeline đã được khởi chạy trong background trên backend hiện tại.',
            'retrain_status': _read_json_file(_get_retrain_status_path(), default={}),
        }, status=202)


class MlopsStatusView(APIView):
    """
    GET /api/admin/mlops/status/   — Trạng thái model + lần retrain gần nhất
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        model_dir = _get_model_dir()
        result_path = os.path.join(model_dir, 'last_retrain_result.json')
        status_path = _get_retrain_status_path()

        metadata = _get_model_metadata()
        last_result = _read_json_file(result_path, default={})
        retrain_status = _read_json_file(status_path, default={'state': 'idle'})
        current_metrics = metadata.get('metrics', {})
        fallback_run_time = metadata.get('created_at') or metadata.get('updated_at')
        if fallback_run_time and 'run_time' not in last_result:
            last_result['run_time'] = fallback_run_time
        if current_metrics and 'new_f1' not in last_result:
            last_result['new_f1'] = current_metrics.get('f1_macro')
        if current_metrics and 'accuracy' not in last_result:
            last_result['accuracy'] = current_metrics.get('accuracy')
        if current_metrics and 'recall_macro' not in last_result:
            last_result['recall_macro'] = current_metrics.get('recall_macro')
        if metadata.get('model_name') and 'winning_model' not in last_result:
            last_result['winning_model'] = metadata.get('model_name')
        if 'reason' not in last_result and os.path.exists(os.path.join(model_dir, 'best_model.pkl')):
            last_result['reason'] = 'Current production model loaded from metadata.'

        return Response({
            'model_name': metadata.get('model_name', 'Unknown'),
            'model_exists': os.path.exists(os.path.join(model_dir, 'best_model.pkl')),
            'current_model': {
                'metrics': current_metrics,
                'created_at': metadata.get('created_at'),
                'updated_at': metadata.get('updated_at'),
            },
            'last_retrain': last_result,
            'retrain_status': retrain_status,
        })


# =============================================================
#  ADMIN USER MANAGEMENT VIEWS
# =============================================================

class AdminUserListView(APIView):
    """
    GET /api/admin/users/         — Danh sách tất cả users
    GET /api/admin/users/?search= — Tìm kiếm theo tên / username
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        users = NguoiDung.objects.all().order_by('-created_at')
        if search:
            users = users.filter(
                Q(ho_ten__icontains=search) | Q(username__icontains=search) | Q(email__icontains=search)
            )
        serializer = NguoiDungSerializer(users, many=True)
        return Response({
            'count': users.count(),
            'results': serializer.data
        })


class AdminUserUpdateRoleView(APIView):
    """
    PUT /api/admin/users/<id>/role/   — Thay đổi vai trò user
    Body: { vai_tro: 'admin' | 'teacher' | 'student' }
    """
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        try:
            user = NguoiDung.objects.get(pk=pk)
        except NguoiDung.DoesNotExist:
            return Response({'error': 'Người dùng không tồn tại.'}, status=404)

        if user == request.user:
            return Response({'error': 'Không thể thay đổi vai trò của chính mình.'}, status=400)

        new_role = request.data.get('vai_tro')
        if new_role not in ['admin', 'teacher', 'student']:
            return Response({'error': 'Vai trò không hợp lệ.'}, status=400)

        old_role = user.vai_tro
        user.vai_tro = new_role
        user.save()

        # Nếu chuyển thành student và chưa có HocVien → tạo HocVien
        if new_role == 'student':
            if not HocVien.objects.filter(nguoi_dung=user).exists():
                HocVien.objects.create(
                    nguoi_dung=user,
                    ma_hoc_vien=generate_student_code(),
                )

        return Response({
            'message': f'Đã đổi vai trò thành {new_role}.',
            'user': NguoiDungSerializer(user).data,
        })


class AdminUserDeleteView(APIView):
    """
    DELETE /api/admin/users/<id>/   — Xóa tài khoản
    """
    permission_classes = [IsAdmin]

    def delete(self, request, pk):
        try:
            user = NguoiDung.objects.get(pk=pk)
        except NguoiDung.DoesNotExist:
            return Response({'error': 'Người dùng không tồn tại.'}, status=404)

        if user == request.user:
            return Response({'error': 'Không thể xóa chính mình.'}, status=400)

        username = user.username
        user.delete()
        return Response({'message': f'Đã xóa tài khoản {username}.'}, status=status.HTTP_204_NO_CONTENT)

# =============================================================
#  SCORE APPROVAL VIEWS
# =============================================================

class ApproveScoreView(APIView):
    """
    PUT /api/admin/scores/<id>/approve/   — Admin duyệt điểm
    Body: { action: 'approve' | 'reject' }
    """
    permission_classes = [IsAdmin]

    def put(self, request, pk):
        try:
            bd = BangDiem.objects.get(pk=pk)
        except BangDiem.DoesNotExist:
            return Response({'error': 'Bảng điểm không tồn tại.'}, status=404)

        action = request.data.get('action', 'approve')
        if action == 'approve':
            bd.is_approved = True
            bd.approved_by = request.user
            bd.save()
            _auto_predict(bd)
            return Response({'message': 'Đã duyệt điểm.', 'is_approved': True})
        elif action == 'reject':
            bd.delete()
            return Response({'message': 'Đã từ chối và xóa bảng điểm.'}, status=204)
        return Response({'error': 'Action không hợp lệ.'}, status=400)


class AdminTeacherListView(APIView):
    """
    GET /api/admin/teachers/   — Danh sách giáo viên
    GET /api/admin/teachers/?search=name  — Tìm kiếm theo tên
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        search = request.query_params.get('search', '').strip()
        teachers = NguoiDung.objects.filter(vai_tro='teacher').order_by('ho_ten')
        if search:
            teachers = teachers.filter(
                Q(ho_ten__icontains=search) | Q(username__icontains=search)
            )
        serializer = NguoiDungSerializer(teachers, many=True)
        return Response({'count': teachers.count(), 'results': serializer.data})


# =============================================================
#  DU DOAN (PREDICTION HISTORY) VIEWS
# =============================================================

class DuDoanListView(APIView):
    """
    GET /api/predictions/           — Tất cả dự đoán
    GET /api/predictions/?risk=high_risk  — Lọc theo mức rủi ro
    """
    permission_classes = [IsAdminOrTeacher]

    def get(self, request):
        user = request.user
        risk = request.query_params.get('risk')

        du_doans = DuDoanML.objects.select_related(
            'bang_diem', 'bang_diem__hoc_vien', 'bang_diem__hoc_vien__nguoi_dung',
            'bang_diem__hoc_vien__lop'
        )

        if user.vai_tro == 'teacher':
            lop_ids = LopHoc.objects.filter(giao_vien=user).values_list('id', flat=True)
            du_doans = du_doans.filter(bang_diem__hoc_vien__lop__in=lop_ids)

        if risk:
            du_doans = du_doans.filter(risk_level=risk)

        serializer = DuDoanMLSerializer(du_doans, many=True)
        return Response({'count': du_doans.count(), 'results': serializer.data})


class WarningListView(APIView):
    """
    GET /api/predictions/warnings/   — Danh sách HS cần cảnh báo (high / medium risk)
    """
    permission_classes = [IsAdminOrTeacher]

    def get(self, request):
        user = request.user
        lop_id = request.query_params.get('lop_id')

        du_doans = DuDoanML.objects.filter(
            risk_level__in=['high_risk', 'medium_risk'],
            bang_diem__is_approved=True,
        ).select_related(
            'bang_diem__hoc_vien__nguoi_dung',
            'bang_diem__hoc_vien__lop'
        ).order_by('risk_level', '-predicted_at')

        if user.vai_tro == 'teacher':
            lop_ids = LopHoc.objects.filter(giao_vien=user).values_list('id', flat=True)
            du_doans = du_doans.filter(bang_diem__hoc_vien__lop__in=lop_ids)

        if lop_id:
            du_doans = du_doans.filter(bang_diem__hoc_vien__lop_id=lop_id)

        results = []
        for dd in du_doans:
            hv = dd.bang_diem.hoc_vien
            results.append({
                'hoc_vien_id': hv.id,
                'ma_hoc_vien': hv.ma_hoc_vien,
                'ho_ten': hv.nguoi_dung.ho_ten,
                'lop': hv.lop.ten_lop if hv.lop else None,
                'predicted_label': dd.predicted_label,
                'risk_level': dd.risk_level,
                'final_score': dd.bang_diem.final_score,
                'predicted_at': dd.predicted_at,
            })

        return Response({'count': len(results), 'results': results})


# =============================================================
#  DASHBOARD VIEWS
# =============================================================

class DashboardView(APIView):
    """
    GET /api/dashboard/   — Dashboard tổng quan (Admin)
    """
    permission_classes = [IsAdmin]

    def get(self, request):
        tong_hv = HocVien.objects.count()
        tong_lop = LopHoc.objects.count()
        tong_gv = NguoiDung.objects.filter(vai_tro='teacher').count()
        approved_scores = BangDiem.objects.filter(is_approved=True)
        tong_bd = approved_scores.count()
        tong_dd = DuDoanML.objects.filter(bang_diem__is_approved=True).count()

        # Phân bố theo risk_level
        risk_counts = DuDoanML.objects.filter(bang_diem__is_approved=True).values('risk_level').annotate(so_luong=Count('id'))
        phan_bo_risk = {r['risk_level']: r['so_luong'] for r in risk_counts}

        # Phân bố theo performance_label
        phan_bo_label = _build_label_distribution(approved_scores)

        # HS cần cảnh báo (high_risk)
        canh_bao = DuDoanML.objects.filter(risk_level='high_risk', bang_diem__is_approved=True).select_related(
            'bang_diem__hoc_vien__nguoi_dung',
            'bang_diem__hoc_vien__lop'
        )[:10]
        hv_canh_bao = [
            {
                'ma_hoc_vien': dd.bang_diem.hoc_vien.ma_hoc_vien,
                'ho_ten': dd.bang_diem.hoc_vien.nguoi_dung.ho_ten,
                'lop': dd.bang_diem.hoc_vien.lop.ten_lop if dd.bang_diem.hoc_vien.lop else None,
                'final_score': dd.bang_diem.final_score,
                'risk_level': dd.risk_level,
            }
            for dd in canh_bao
        ]

        # Điểm trung bình toàn hệ thống
        from django.db.models import Avg
        avg_score = approved_scores.aggregate(avg=Avg('final_score'))['avg']
        diem_tb = round(avg_score * 10, 1) if avg_score else 0  # Đổi sang thang 100

        # Điểm pending chờ duyệt
        pending_count = BangDiem.objects.filter(is_approved=False).count()

        return Response({
            'tong_hoc_vien': tong_hv,
            'tong_lop_hoc': tong_lop,
            'tong_giao_vien': tong_gv,
            'tong_bang_diem': tong_bd,
            'tong_du_doan': tong_dd,
            'diem_trung_binh_he_thong': diem_tb,
            'pending_approvals': pending_count,
            'phan_bo_risk': phan_bo_risk,
            'phan_bo_label': phan_bo_label,
            'hoc_vien_canh_bao': hv_canh_bao,
        })


class DashboardClassView(APIView):
    """
    GET /api/dashboard/class/<id>/   — Dashboard 1 lớp học (Admin, Teacher)
    """
    permission_classes = [IsAdminOrTeacher]

    def get(self, request, pk):
        try:
            lop = LopHoc.objects.get(pk=pk)
        except LopHoc.DoesNotExist:
            return Response({'error': 'Lớp học không tồn tại.'}, status=404)

        # Teacher chỉ xem lớp mình dạy
        if request.user.vai_tro == 'teacher' and lop.giao_vien != request.user:
            return Response({'error': 'Không có quyền xem lớp này.'}, status=403)

        hoc_viens = HocVien.objects.filter(lop=lop)
        bang_diems = BangDiem.objects.filter(hoc_vien__lop=lop, is_approved=True)
        du_doans = DuDoanML.objects.filter(bang_diem__hoc_vien__lop=lop, bang_diem__is_approved=True)

        # Thống kê điểm
        avg_score = bang_diems.aggregate(avg=Avg('final_score'))['avg'] or 0

        # Phân bố label
        phan_bo_label = _build_label_distribution(bang_diems)

        # Phân bố risk
        risk_counts = du_doans.values('risk_level').annotate(so_luong=Count('id'))
        phan_bo_risk = {r['risk_level']: r['so_luong'] for r in risk_counts}

        # HS yếu cần cảnh báo
        canh_bao_ids = du_doans.filter(risk_level='high_risk').values_list('bang_diem__hoc_vien_id', flat=True)
        ds_canh_bao = hoc_viens.filter(id__in=canh_bao_ids)

        return Response({
            'lop_id': lop.id,
            'ten_lop': lop.ten_lop,
            'giao_vien': lop.giao_vien.ho_ten if lop.giao_vien else None,
            'nam_hoc': lop.nam_hoc,
            'hoc_ky': lop.hoc_ky,
            'tong_hoc_vien': hoc_viens.count(),
            'tong_bang_diem': bang_diems.count(),
            'diem_trung_binh': round(avg_score, 2),
            'phan_bo_label': phan_bo_label,
            'phan_bo_risk': phan_bo_risk,
            'so_hs_canh_bao': ds_canh_bao.count(),
            'ds_hoc_vien': HocVienSerializer(hoc_viens, many=True).data,
        })
