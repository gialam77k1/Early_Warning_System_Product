<div align="center">

# 🎓 Early Warning System

### Hệ thống Theo dõi Tiến độ Học tập Real-time bằng Machine Learning

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)](https://djangoproject.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-F1%3D0.978-FF6600?style=for-the-badge)](https://xgboost.readthedocs.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)

> **Môn học:** Công Nghệ Mới Trong Phát Triển Ứng Dụng (CNMTPTUD)  
> **Trường:** Đại học Công Nghiệp TP.HCM (IUH) — Năm 4, Kỳ 2, 2026

</div>

---

## 📌 Giới thiệu

**Early Warning System (EWS)** là hệ thống web giúp **theo dõi tiến độ học tập thời gian thực** cho các trung tâm học thêm. Khi giáo viên nhập điểm, model **Machine Learning** lập tức dự đoán nguy cơ học lực của học viên và phát cảnh báo sớm — **trước khi thi cuối kỳ**.

### 🎯 Điểm nổi bật

| Tính năng | Chi tiết |
|-----------|---------|
| 🤖 **ML Real-time** | Dự đoán ngay khi nhập điểm, không cần thao tác thêm |
| ⚠️ **Cảnh báo sớm** | Phát hiện học viên có nguy cơ yếu trước khi thi cuối kỳ |
| 📊 **Dashboard đa vai trò** | Giao diện riêng cho Admin, Giáo viên, Học viên |
| 🔄 **MLOps tích hợp** | Drift Detection + Auto-retraining + MLflow tracking |
| 🔒 **Bảo mật JWT** | Xác thực token, phân quyền theo vai trò |

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────┐
│                   FRONTEND (Nginx)                   │
│         admin.html │ teacher.html │ student.html     │
└─────────────────────┬───────────────────────────────┘
                      │ REST API (JWT Auth)
┌─────────────────────▼───────────────────────────────┐
│              BACKEND (Django REST Framework)         │
│                                                     │
│  Auth API  │  CRUD API  │  ML Predict API           │
│                         │                           │
│            ┌────────────▼────────────┐              │
│            │   ML Module (Python)    │              │
│            │  XGBoost │ RF │ LR      │              │
│            │  Drift Detection        │              │
│            │  MLflow Tracking        │              │
│            └─────────────────────────┘              │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              DATABASE (PostgreSQL)                   │
│  NguoiDung │ LopHoc │ HocVien │ BangDiem │ DuDoanML │
└─────────────────────────────────────────────────────┘
```

---

## ✨ Chức năng theo vai trò

### 🛡️ Admin (Quản trị viên)
- Quản lý toàn bộ người dùng (tạo tài khoản giáo viên, học viên)
- Quản lý lớp học và phân công giáo viên
- Dashboard tổng quan: thống kê toàn trường, phân bố học lực, danh sách cảnh báo
- Kích hoạt pipeline MLOps retraining từ giao diện
- Xem lịch sử tất cả dự đoán ML

### 👨‍🏫 Teacher (Giáo viên)
- Quản lý lớp học được phân công
- **Nhập điểm** (Bài tập ×3, Kiểm tra ×2, Giữa kỳ, Cuối kỳ, Chuyên cần)
- **Kết quả ML hiển thị ngay** sau khi lưu điểm
- Xem danh sách cảnh báo học viên cần hỗ trợ
- Dự đoán nhanh không cần lưu vào DB

### 🎓 Student (Học viên)
- Xem điểm số và tiến độ học tập cá nhân
- Xem kết quả dự đoán ML + mức rủi ro + lời khuyên
- Biểu đồ trực quan (Bar chart xác suất, Radar chart điểm thành phần)

---

## 🧠 Machine Learning Pipeline

```
UCI Dataset (395 mẫu)
    ↓ Tăng cường Synthetic Data
Dataset (~3,950 mẫu)
    ↓
7 Features input (HW1/2/3, Quiz1/2, Midterm, Attendance)
    ↓ final_exam KHÔNG dùng — dự đoán TRƯỚC khi thi
Huấn luyện 3 Model:
  ├── Random Forest   → F1 = 0.976
  ├── Logistic Reg.   → F1 = 0.929
  └── 🏆 XGBoost      → F1 = 0.978  ← Best Model
    ↓
Phân loại: Weak │ Average │ Good │ Excellent
    ↓
Risk Level: high_risk │ medium_risk │ low_risk │ no_risk
```

---

## 📡 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| `POST` | `/api/auth/login/` | Đăng nhập, nhận JWT |
| `GET/PUT` | `/api/auth/me/` | Thông tin cá nhân |
| `GET/POST` | `/api/classes/` | Danh sách / Tạo lớp |
| `GET` | `/api/students/<id>/progress/` | Tiến độ học viên |
| `GET/POST` | `/api/scores/` | Bảng điểm (POST → auto ML predict) |
| `POST` | `/api/predict/` | ML dự đoán theo bảng điểm |
| `POST` | `/api/predict/manual/` | Dự đoán thủ công |
| `GET` | `/api/predictions/warnings/` | Danh sách cảnh báo |
| `GET` | `/api/dashboard/` | Dashboard tổng quan |
| `POST` | `/api/admin/retrain/` | Kích hoạt MLOps retraining |

---

## 🚀 Hướng dẫn cài đặt

### Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu |
|---------|-------------------|
| Python | 3.10+ |
| PostgreSQL | 14+ |
| Docker Desktop | 24+ (chỉ cần nếu dùng Docker) |

---

## 🐳 Cách 1: Chạy bằng Docker (Khuyên dùng)

> Không cần cài Python hay PostgreSQL thủ công. Chỉ cần Docker Desktop.

### Bước 1 — Chuẩn bị biến môi trường

```bash
# Sao chép file env mẫu
cp .env.example .env
```

Mở `.env` và chỉnh sửa nếu cần (mặc định đã hoạt động với Docker):

```env
DB_NAME=early_warning_db
DB_USER=postgres
DB_PASSWORD=123456
DB_HOST=db          # <-- giữ nguyên "db" khi chạy Docker
DB_PORT=5432
MLFLOW_TRACKING_URI=http://mlflow:5000   # <-- giữ nguyên khi chạy Docker
```

### Bước 2 — Build và khởi động

```bash
docker-compose up --build
```

> Lần đầu chạy sẽ mất 2–5 phút để build image và khởi tạo database.

### Bước 3 — Tạo dữ liệu mẫu

Mở terminal mới (để terminal trên vẫn chạy), chạy:

```bash
docker exec -it ews_backend python manage.py seed_data
```

### Bước 4 — Truy cập hệ thống

| URL | Mô tả |
|-----|-------|
| http://localhost | 🖥️ Giao diện chính (Login) |
| http://localhost/admin | ⚙️ Django Admin Panel |
| http://localhost:5050 | 📈 MLflow UI |
| http://localhost:8000/api/ | 🔌 REST API (Browsable) |

### Dừng hệ thống

```bash
# Dừng nhưng giữ dữ liệu
docker-compose down

# Dừng và xóa toàn bộ dữ liệu (reset hoàn toàn)
docker-compose down -v
```

---

## 💻 Cách 2: Chạy Local (Thủ công)

### Bước 1 — Clone và tạo môi trường ảo

```bash
# Tạo môi trường ảo Python
python -m venv venv

# Kích hoạt (Windows)
.\venv\Scripts\activate

# Kích hoạt (macOS/Linux)
source venv/bin/activate
```

### Bước 2 — Cài đặt thư viện

```bash
pip install -r requirements.txt
```

### Bước 3 — Chuẩn bị file .env

```bash
cp .env.example .env
```

Mở `.env` và chỉnh để kết nối PostgreSQL local:

```env
DB_NAME=early_warning_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password
DB_HOST=localhost       # <-- đổi thành localhost
DB_PORT=5432
MLFLOW_TRACKING_URI=http://localhost:5050
```

### Bước 4 — Chuẩn bị PostgreSQL

Dùng psql hoặc pgAdmin để tạo database:

```sql
CREATE DATABASE early_warning_db;
```

### Bước 5 — Train model ML

> Bước này cần thiết vì `ml/saved_models/` không được đẩy lên git.

```bash
# Chạy từ thư mục gốc dự án
python ml/train_model.py
```

Sau khi chạy xong, kiểm tra:
```
ml/saved_models/best_model.pkl      ✅
ml/saved_models/label_encoder.pkl   ✅
ml/saved_models/model_metadata.json ✅
```

### Bước 6 — Migrate và tạo dữ liệu mẫu

```bash
cd early_waring_backend

python manage.py migrate
python manage.py seed_data
```

### Bước 7 — Chạy server

```bash
# Vẫn trong thư mục early_waring_backend
python manage.py runserver
```

Truy cập:
- **Frontend**: Mở file `frontend/index.html` bằng trình duyệt (hoặc dùng Live Server)
- **API**: http://127.0.0.1:8000/api/
- **Admin**: http://127.0.0.1:8000/admin/

> 💡 **Lưu ý:** Khi chạy local, frontend cần được serve qua HTTP (không phải `file://`). Dùng [Live Server extension](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer) trong VS Code, hoặc `python -m http.server 3000` trong thư mục `frontend/`.

---

## 👤 Tài khoản mặc định (sau `seed_data`)

| Vai trò | Username | Password |
|---------|----------|----------|
| Admin | `admin` | `admin123` |
| Giáo viên | `gv_nguyen` | `teacher123` |
| Giáo viên | `gv_tran` | `teacher123` |
| Học viên | `hv_001` → `hv_030` | `student123` |

---

## 🔄 Quy trình MLOps

Sau khi hệ thống tích lũy đủ dữ liệu thực tế, có thể kích hoạt pipeline tái huấn luyện:

### Qua giao diện Admin
Đăng nhập với tài khoản Admin → mục **MLOps** → nhấn **"Retrain Model"**.

### Qua command line

```bash
# Local
python manage.py ml_retrain

# Docker
docker exec -it ews_backend python manage.py ml_retrain
```

Pipeline sẽ tự động:
1. **Load dữ liệu thực tế** từ PostgreSQL
2. **Kiểm tra Data Drift** (Kolmogorov-Smirnov test) so với dữ liệu gốc
3. **Train lại 3 model** (Random Forest, Logistic Regression, XGBoost)
4. **Chọn model tốt nhất** theo F1-score
5. **Log lên MLflow** — xem kết quả tại http://localhost:5050
6. **Cập nhật `best_model.pkl`** để API dùng ngay

---

## 🛠️ Công nghệ sử dụng

| Layer | Công nghệ |
|-------|-----------|
| **ML / Data** | Python · pandas · NumPy · scikit-learn · XGBoost · SciPy |
| **Backend** | Django 5.1 · Django REST Framework · SimpleJWT · django-cors-headers |
| **Database** | PostgreSQL 16 · psycopg2 |
| **MLOps** | MLflow · Kolmogorov-Smirnov Drift Detection |
| **Frontend** | HTML5 · CSS3 (Glassmorphism) · Vanilla JS · Chart.js 4.4 |
| **Deployment** | Docker · Docker Compose · Nginx |

---

## 📁 Cấu trúc dự án

```
Early-Warning-System/
├── .env.example                 # 🔑 Mẫu biến môi trường
├── .gitignore
├── docker-compose.yml           # 🐳 Cấu hình Docker (4 services)
├── Dockerfile                   # Image cho Django backend
├── nginx.conf                   # Cấu hình Nginx reverse proxy
├── requirements.txt
│
├── ml/                          # 🤖 Module Machine Learning
│   ├── train_model.py           # Pipeline training (RF, LR, XGBoost)
│   ├── predict.py               # StudentPredictor class
│   ├── drift_detection.py       # Kolmogorov-Smirnov drift check
│   ├── mlflow_manager.py        # MLflow experiment tracking
│   └── saved_models/            # ⚠️ Không có trong git — phải train
│
├── data_train/
│   ├── student-mat.csv          # UCI dataset gốc (395 mẫu)
│   └── train_dataset.csv        # Dataset mở rộng (~3,950 mẫu)
│
├── early_waring_backend/        # 🌐 Django Backend
│   ├── manage.py
│   ├── early_waring_backend/
│   │   ├── settings.py
│   │   └── urls.py
│   ├── entrypoint.sh            # Script khởi động Docker
│   └── core/
│       ├── models.py            # 5 models: NguoiDung, LopHoc, HocVien, BangDiem, DuDoanML
│       ├── views.py             # API Views (Auth, CRUD, ML, Dashboard)
│       ├── serializers.py
│       ├── urls.py              # 19 API endpoints
│       ├── admin.py
│       └── management/commands/
│           ├── seed_data.py     # Tạo dữ liệu mẫu
│           └── ml_retrain.py    # MLOps retraining pipeline
│
└── frontend/                    # 🖥️ Giao diện người dùng
    ├── index.html               # Trang Login
    ├── admin.html               # Dashboard Admin
    ├── teacher.html             # Dashboard Giáo viên
    ├── student.html             # Dashboard Học viên
    ├── css/style.css
    └── js/api.js                # Shared API utility + JWT handler
```

---

## 🐞 Xử lý lỗi thường gặp

### ❌ `ModuleNotFoundError: No module named 'predict'`
Model ML chưa được train. Chạy: `python ml/train_model.py`

### ❌ `connection to server on socket failed` (PostgreSQL)
- **Local:** Kiểm tra PostgreSQL đang chạy và thông tin trong `.env` đúng
- **Docker:** Đảm bảo `DB_HOST=db` (không phải `localhost`)

### ❌ `CORS error` khi gọi API từ Frontend
Mở `frontend/js/api.js`, kiểm tra `BASE_URL` trỏ đúng địa chỉ backend.

### ❌ Frontend hiển thị lỗi khi mở bằng `file://`
Dùng Live Server hoặc `python -m http.server 3000` trong thư mục `frontend/`.

---

## 👨‍💻 Tác giả

**Gia Lam** — Sinh viên năm 4, Đại học Công Nghiệp TP.HCM (IUH)  
Môn: Công Nghệ Mới Trong Phát Triển Ứng Dụng — 2026
