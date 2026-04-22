"""
Management command: Tạo dữ liệu mẫu cho hệ thống
Chạy: python manage.py seed_data
"""

import random
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from core.models import NguoiDung, LopHoc, HocVien, BangDiem


class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho Early Warning System'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Bắt đầu tạo dữ liệu mẫu...\n")

        # ========== 1. Tạo Admin ==========
        admin, created = NguoiDung.objects.get_or_create(
            username='admin',
            defaults={
                'ho_ten': 'Quản Trị Viên',
                'email': 'admin@earlywarning.edu.vn',
                'vai_tro': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS("✅ Tạo Admin: admin / admin123"))
        else:
            self.stdout.write("   Admin đã tồn tại")

        # ========== 2. Tạo Giáo viên ==========
        teachers_data = [
            {'username': 'gv_nguyen', 'ho_ten': 'Nguyễn Văn An', 'email': 'an.gv@earlywarning.edu.vn'},
            {'username': 'gv_tran', 'ho_ten': 'Trần Thị Bình', 'email': 'binh.gv@earlywarning.edu.vn'},
            {'username': 'gv_le', 'ho_ten': 'Lê Hoàng Cường', 'email': 'cuong.gv@earlywarning.edu.vn'},
        ]

        teachers = []
        for td in teachers_data:
            teacher, created = NguoiDung.objects.get_or_create(
                username=td['username'],
                defaults={
                    'ho_ten': td['ho_ten'],
                    'email': td['email'],
                    'vai_tro': 'teacher',
                    'is_staff': True,
                }
            )
            if created:
                teacher.set_password('teacher123')
                teacher.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Tạo GV: {td['username']} / teacher123"))
            teachers.append(teacher)

        # ========== 3. Tạo Lớp học ==========
        classes_data = [
            {'ten_lop': 'Toán Nâng Cao A1', 'giao_vien': teachers[0]},
            {'ten_lop': 'Anh Văn B2', 'giao_vien': teachers[1]},
            {'ten_lop': 'Lý Thuyết C1', 'giao_vien': teachers[2]},
        ]

        classes = []
        for cd in classes_data:
            lop, created = LopHoc.objects.get_or_create(
                ten_lop=cd['ten_lop'],
                defaults={
                    'giao_vien': cd['giao_vien'],
                    'nam_hoc': '2025-2026',
                    'hoc_ky': 2,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ Tạo lớp: {cd['ten_lop']}"))
            classes.append(lop)

        # ========== 4. Tạo Học viên ==========
        ho_list = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng']
        ten_dem = ['Văn', 'Thị', 'Hoàng', 'Minh', 'Thanh', 'Quốc', 'Ngọc', 'Đức']
        ten_list = ['Hùng', 'Dũng', 'Hương', 'Lan', 'Mai', 'Tuấn', 'Phong', 'Linh',
                    'Thảo', 'Trang', 'Khôi', 'Bảo', 'Anh', 'Quân', 'Đạt']

        student_count = 0
        for class_idx, lop in enumerate(classes):
            for i in range(10):  # 10 HS mỗi lớp
                student_count += 1
                ma_hv = f"HV{2025}{student_count:03d}"
                username = f"hv_{student_count:03d}"
                ho_ten = f"{random.choice(ho_list)} {random.choice(ten_dem)} {random.choice(ten_list)}"

                user, created = NguoiDung.objects.get_or_create(
                    username=username,
                    defaults={
                        'ho_ten': ho_ten,
                        'email': f'{username}@earlywarning.edu.vn',
                        'vai_tro': 'student',
                    }
                )
                if created:
                    user.set_password('student123')
                    user.save()

                hoc_vien, hv_created = HocVien.objects.get_or_create(
                    nguoi_dung=user,
                    defaults={
                        'lop': lop,
                        'ma_hoc_vien': ma_hv,
                        'gioi_tinh': random.choice(['nam', 'nu']),
                    }
                )

                if hv_created:
                    # Tạo bảng điểm ngẫu nhiên
                    level = random.choice(['weak', 'average', 'good', 'excellent'])
                    if level == 'weak':
                        score_range = (0.5, 4.5)
                        att = round(random.uniform(0.4, 0.7), 1)
                    elif level == 'average':
                        score_range = (4.5, 6.5)
                        att = round(random.uniform(0.6, 0.85), 1)
                    elif level == 'good':
                        score_range = (6.5, 8.5)
                        att = round(random.uniform(0.75, 0.95), 1)
                    else:
                        score_range = (8.0, 10.0)
                        att = round(random.uniform(0.9, 1.0), 1)

                    BangDiem.objects.create(
                        hoc_vien=hoc_vien,
                        homework_1=round(random.uniform(*score_range), 1),
                        homework_2=round(random.uniform(*score_range), 1),
                        homework_3=round(random.uniform(*score_range), 1),
                        quiz_1=round(random.uniform(*score_range), 1),
                        quiz_2=round(random.uniform(*score_range), 1),
                        midterm_score=round(random.uniform(*score_range), 1),
                        final_exam=round(random.uniform(*score_range), 1),
                        attendance_rate=att,
                    )

        self.stdout.write(self.style.SUCCESS(f"✅ Tạo {student_count} học viên + bảng điểm"))

        # ========== Tổng kết ==========
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("🎉 TẠO DỮ LIỆU MẪU HOÀN TẤT!"))
        self.stdout.write(f"   👤 Admin:    1 (admin / admin123)")
        self.stdout.write(f"   👨‍🏫 Giáo viên: {len(teachers)} (gv_nguyen / teacher123)")
        self.stdout.write(f"   🏫 Lớp học:  {len(classes)}")
        self.stdout.write(f"   👨‍🎓 Học viên: {student_count} (hv_001 / student123)")
        self.stdout.write(f"   📝 Bảng điểm: {student_count}")
        self.stdout.write("=" * 50)
