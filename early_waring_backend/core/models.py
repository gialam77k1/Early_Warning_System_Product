"""
=============================================================
  Early Warning System - Django Models
  5 bảng chính theo sơ đồ ERD:
  NguoiDung, LopHoc, HocVien, BangDiem, DuDoanML
=============================================================
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


class NguoiDung(AbstractUser):
    """
    Bảng Người Dùng - Mở rộng từ Django User
    Vai trò: admin / teacher / student
    """
    class VaiTro(models.TextChoices):
        ADMIN = 'admin', 'Quản trị viên'
        TEACHER = 'teacher', 'Giáo viên'
        STUDENT = 'student', 'Học viên'

    vai_tro = models.CharField(
        max_length=10,
        choices=VaiTro.choices,
        default=VaiTro.STUDENT,
        verbose_name='Vai trò'
    )
    ho_ten = models.CharField(max_length=150, verbose_name='Họ tên', blank=True)
    so_dien_thoai = models.CharField(max_length=15, blank=True, verbose_name='Số điện thoại')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        verbose_name = 'Người dùng'
        verbose_name_plural = 'Người dùng'
        db_table = 'nguoi_dung'

    def __str__(self):
        return f"{self.ho_ten or self.username} ({self.get_vai_tro_display()})"


class LopHoc(models.Model):
    """
    Bảng Lớp Học
    Mỗi lớp có 1 giáo viên phụ trách
    """
    ten_lop = models.CharField(max_length=100, verbose_name='Tên lớp')
    mo_ta = models.TextField(blank=True, verbose_name='Mô tả')
    giao_vien = models.ForeignKey(
        NguoiDung,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        limit_choices_to={'vai_tro': 'teacher'},
        related_name='lop_phu_trach',
        verbose_name='Giáo viên'
    )
    nam_hoc = models.CharField(max_length=20, default='2025-2026', verbose_name='Năm học')
    hoc_ky = models.PositiveSmallIntegerField(default=1, verbose_name='Học kỳ')
    is_active = models.BooleanField(default=True, verbose_name='Đang hoạt động')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        verbose_name = 'Lớp học'
        verbose_name_plural = 'Lớp học'
        db_table = 'lop_hoc'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ten_lop} ({self.nam_hoc} - HK{self.hoc_ky})"

    @property
    def so_hoc_vien(self):
        return self.hoc_vien_list.count()


class HocVien(models.Model):
    """
    Bảng Học Viên
    Liên kết NguoiDung (vai_tro=student) với LopHoc
    """
    nguoi_dung = models.OneToOneField(
        NguoiDung,
        on_delete=models.CASCADE,
        limit_choices_to={'vai_tro': 'student'},
        related_name='hoc_vien',
        verbose_name='Tài khoản'
    )
    lop = models.ForeignKey(
        LopHoc,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='hoc_vien_list',
        verbose_name='Lớp học'
    )
    ma_hoc_vien = models.CharField(
        max_length=20, unique=True,
        verbose_name='Mã học viên'
    )
    ngay_sinh = models.DateField(null=True, blank=True, verbose_name='Ngày sinh')
    gioi_tinh = models.CharField(
        max_length=5,
        choices=[('nam', 'Nam'), ('nu', 'Nữ')],
        default='nam',
        verbose_name='Giới tính'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')

    class Meta:
        verbose_name = 'Học viên'
        verbose_name_plural = 'Học viên'
        db_table = 'hoc_vien'
        ordering = ['ma_hoc_vien']

    def __str__(self):
        return f"{self.ma_hoc_vien} - {self.nguoi_dung.ho_ten}"


# Validators cho điểm 0-10
score_validators = [MinValueValidator(0.0), MaxValueValidator(10.0)]
rate_validators = [MinValueValidator(0.0), MaxValueValidator(1.0)]


class BangDiem(models.Model):
    """
    Bảng Điểm - Lưu điểm số của học viên
    8 features + final_score (tính toán) + performance_label
    """
    hoc_vien = models.ForeignKey(
        HocVien,
        on_delete=models.CASCADE,
        related_name='bang_diem_list',
        verbose_name='Học viên'
    )

    # 3 bài tập
    homework_1 = models.FloatField(
        default=0, validators=score_validators,
        verbose_name='Bài tập 1'
    )
    homework_2 = models.FloatField(
        default=0, validators=score_validators,
        verbose_name='Bài tập 2'
    )
    homework_3 = models.FloatField(
        default=0, validators=score_validators,
        verbose_name='Bài tập 3'
    )

    # 2 kiểm tra nhanh
    quiz_1 = models.FloatField(
        default=0, validators=score_validators,
        verbose_name='Kiểm tra 1'
    )
    quiz_2 = models.FloatField(
        default=0, validators=score_validators,
        verbose_name='Kiểm tra 2'
    )

    # Giữa kỳ & cuối kỳ
    midterm_score = models.FloatField(
        default=0, validators=score_validators,
        verbose_name='Điểm giữa kỳ'
    )
    final_exam = models.FloatField(
        default=0, validators=score_validators,
        verbose_name='Điểm cuối kỳ'
    )

    # Tỷ lệ chuyên cần (0.0 - 1.0)
    attendance_rate = models.FloatField(
        default=0, validators=rate_validators,
        verbose_name='Tỷ lệ chuyên cần'
    )

    # Trường tính toán
    final_score = models.FloatField(
        default=0, verbose_name='Điểm tổng kết',
        help_text='= 0.2*homework_avg + 0.2*quiz_avg + 0.25*midterm + 0.35*final_exam'
    )

    # Label
    class PerformanceLabel(models.TextChoices):
        WEAK = 'Weak', 'Yếu'
        AVERAGE = 'Average', 'Trung bình'
        GOOD = 'Good', 'Khá'
        EXCELLENT = 'Excellent', 'Giỏi'

    performance_label = models.CharField(
        max_length=15,
        choices=PerformanceLabel.choices,
        blank=True,
        verbose_name='Xếp loại'
    )

    is_approved = models.BooleanField(default=False, verbose_name='Đã duyệt')
    approved_by = models.ForeignKey(
        NguoiDung, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='approved_scores', verbose_name='Người duyệt'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Ngày tạo')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ngày cập nhật')

    class Meta:
        verbose_name = 'Bảng điểm'
        verbose_name_plural = 'Bảng điểm'
        db_table = 'bang_diem'
        ordering = ['-updated_at']

    def __str__(self):
        return f"Điểm {self.hoc_vien.ma_hoc_vien} - {self.final_score}"

    def calculate_final_score(self):
        """Tính điểm tổng kết: 0.2*hw + 0.2*quiz + 0.25*midterm + 0.35*final"""
        homework_avg = (self.homework_1 + self.homework_2 + self.homework_3) / 3
        quiz_avg = (self.quiz_1 + self.quiz_2) / 2
        self.final_score = round(
            0.2 * homework_avg + 0.2 * quiz_avg + 0.25 * self.midterm_score + 0.35 * self.final_exam,
            2
        )
        return self.final_score

    def calculate_performance_label(self):
        """Suy ra xếp loại từ điểm tổng kết theo thang 10."""
        if self.final_score < 5.0:
            self.performance_label = self.PerformanceLabel.WEAK
        elif self.final_score < 6.5:
            self.performance_label = self.PerformanceLabel.AVERAGE
        elif self.final_score < 8.0:
            self.performance_label = self.PerformanceLabel.GOOD
        else:
            self.performance_label = self.PerformanceLabel.EXCELLENT
        return self.performance_label

    def get_features(self):
        """Trả về 7 features để đưa vào model ML.
        Lưu ý: final_exam không được bao gồm vì nó chỉ có sau khi thi.
        Đây mới là ý nghĩa đúng của 'Early Warning'.
        """
        return {
            'homework_1':     self.homework_1,
            'homework_2':     self.homework_2,
            'homework_3':     self.homework_3,
            'quiz_1':         self.quiz_1,
            'quiz_2':         self.quiz_2,
            'midterm_score':  self.midterm_score,
            'attendance_rate': self.attendance_rate,
            # final_exam cố tình KHÔNG đưa vào đây
        }

    def save(self, *args, **kwargs):
        """Auto tính final_score và performance_label khi save"""
        self.calculate_final_score()
        self.calculate_performance_label()
        super().save(*args, **kwargs)


class DuDoanML(models.Model):
    """
    Bảng Dự Đoán ML - Lưu kết quả dự đoán từ model
    """
    bang_diem = models.OneToOneField(
        BangDiem,
        on_delete=models.CASCADE,
        related_name='du_doan',
        verbose_name='Bảng điểm'
    )
    predicted_label = models.CharField(
        max_length=15,
        choices=BangDiem.PerformanceLabel.choices,
        verbose_name='Dự đoán'
    )

    # Xác suất từng label
    prob_weak = models.FloatField(default=0, verbose_name='% Yếu')
    prob_average = models.FloatField(default=0, verbose_name='% Trung bình')
    prob_good = models.FloatField(default=0, verbose_name='% Khá')
    prob_excellent = models.FloatField(default=0, verbose_name='% Giỏi')

    # Mức độ rủi ro
    class RiskLevel(models.TextChoices):
        HIGH = 'high_risk', 'Rủi ro cao'
        MEDIUM = 'medium_risk', 'Rủi ro trung bình'
        LOW = 'low_risk', 'Rủi ro thấp'
        NONE = 'no_risk', 'Không rủi ro'

    risk_level = models.CharField(
        max_length=15,
        choices=RiskLevel.choices,
        default=RiskLevel.NONE,
        verbose_name='Mức rủi ro'
    )

    model_name = models.CharField(max_length=50, default='XGBoost', verbose_name='Model sử dụng')
    predicted_at = models.DateTimeField(auto_now=True, verbose_name='Thời gian dự đoán')

    class Meta:
        verbose_name = 'Dự đoán ML'
        verbose_name_plural = 'Dự đoán ML'
        db_table = 'du_doan_ml'
        ordering = ['-predicted_at']

    def __str__(self):
        return f"Dự đoán: {self.predicted_label} ({self.bang_diem.hoc_vien.ma_hoc_vien})"

    def set_risk_level(self):
        """Tự động xác định mức rủi ro"""
        risk_map = {
            'Weak': self.RiskLevel.HIGH,
            'Average': self.RiskLevel.MEDIUM,
            'Good': self.RiskLevel.LOW,
            'Excellent': self.RiskLevel.NONE,
        }
        self.risk_level = risk_map.get(self.predicted_label, self.RiskLevel.NONE)

    def save(self, *args, **kwargs):
        self.set_risk_level()
        super().save(*args, **kwargs)
