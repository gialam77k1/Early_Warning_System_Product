# 🚀 Hướng Dẫn Deploy Early Warning System lên Render.com

> **Chiến lược deploy:** 1 Web Service (Django serve cả API + Frontend qua WhiteNoise) + 1 PostgreSQL Database (free tier)

---

## PHẦN 1: Chuẩn Bị Code Trước Khi Deploy

Các thay đổi đã thực hiện trong source code để đảm bảo chạy được trên Render:

### 1.1. `settings.py` — Chuẩn hoá cho production
- **SECRET_KEY**: Đọc từ environment variable thay vì hardcode
- **DEBUG**: Đọc từ env, mặc định `False` trên production
- **ALLOWED_HOSTS**: Thêm `*.onrender.com`
- **Database**: Đọc thẳng `DB_HOST` từ env (bỏ logic `RUNNING_IN_DOCKER`)
- **WhiteNoise**: Thêm middleware để serve static files không cần Nginx

```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-prod')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    os.environ.get('RENDER_EXTERNAL_HOSTNAME', ''),
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'early_warning_db'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

### 1.2. `requirements.txt` — Thêm 2 thư viện production
```
gunicorn==21.2.0      # Production WSGI server (thay thế runserver)
whitenoise==6.8.2     # Serve static files không cần Nginx
```

### 1.3. `Dockerfile` — Dùng Gunicorn thay `runserver`
```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

WORKDIR /app/early_waring_backend

# Collect static khi build (whitenoise sẽ serve)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["gunicorn", "early_waring_backend.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
```

### 1.4. `entrypoint.sh` — Script khởi động production
```bash
#!/bin/bash
set -e

echo "=== Applying migrations... ==="
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "=== Collecting static files... ==="
python manage.py collectstatic --noinput

echo "=== Seeding data... ==="
python manage.py seed_data

echo "=== Starting Gunicorn... ==="
exec gunicorn early_waring_backend.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --log-level info
```

### 1.5. `urls.py` — Thêm health check endpoint
Render cần endpoint `/api/health/` để biết app đã khởi động thành công:

```python
from django.http import JsonResponse

def health_check(request):
    """Health check endpoint để Render xác nhận app đã chạy."""
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/health/', health_check, name='health-check'),  # ← thêm dòng này
    ...
]
```

### 1.6. `render.yaml` — Blueprint tự động hoá (tuỳ chọn)
File này cho phép Render tự tạo services theo cấu hình:

```yaml
services:
  - type: web
    name: ews-backend
    env: docker
    dockerContext: .
    dockerfilePath: Dockerfile
    plan: free
    healthCheckPath: /api/health/
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: "False"
      - key: DB_NAME
        fromDatabase:
          name: ews-db
          property: database
      - key: DB_USER
        fromDatabase:
          name: ews-db
          property: user
      - key: DB_PASSWORD
        fromDatabase:
          name: ews-db
          property: password
      - key: DB_HOST
        fromDatabase:
          name: ews-db
          property: host
      - key: DB_PORT
        fromDatabase:
          name: ews-db
          property: port
      - key: MLFLOW_TRACKING_URI
        value: "file:///app/mlruns"

databases:
  - name: ews-db
    databaseName: early_warning_db
    user: ews_user
    plan: free
```

---

## PHẦN 2: Push Code Lên GitHub

Sau khi sửa xong tất cả file trên:

```bash
git add .
git commit -m "chore: configure for Render deployment"
git push origin main
```

---

## PHẦN 3: Setup Trên Render Dashboard

### BƯỚC 1: Tạo PostgreSQL Database

1. Vào [dashboard.render.com](https://dashboard.render.com) → đăng nhập
2. Nhấn **`New +`** → chọn **`PostgreSQL`**
3. Điền form:

| Field | Giá trị |
|-------|---------|
| **Name** | `ews-db` |
| **Database** | `early_warning_db` |
| **User** | `ewsuser` ⚠️ (không dùng dấu `_` underscore) |
| **Region** | `Singapore (Southeast Asia)` — gần VN nhất |
| **PostgreSQL Version** | `16` |
| **Plan** | `Free` |

4. Nhấn **`Create Database`** → chờ status chuyển sang **`Available`** ✅ (~2 phút)

> ⚠️ **Lưu ý quan trọng:** Render không cho phép dấu gạch dưới `_` trong tên User. Dùng `ewsuser` thay vì `ews_user`.

---

### BƯỚC 2: Lấy Thông Tin Kết Nối Database

Sau khi database Available:
1. Nhấn vào **`ews-db`**
2. Cuộn xuống phần **`Connections`**
3. Copy các giá trị sau để dùng ở Bước 3:

```
Host:      dpg-xxxxxxxxxx.singapore-postgres.render.com
Username:  ewsuser
Password:  (chuỗi ký tự dài ngẫu nhiên)
Database:  early_warning_db
Port:      5432
```

---

### BƯỚC 3: Tạo Web Service

1. Nhấn **`New +`** → chọn **`Web Service`**
2. Chọn tab **`Git Provider`** → tìm repo `Early_Warning_System_Product`
   - Nếu không thấy: nhấn dropdown **`Credentials`** → chọn đúng GitHub account
3. Nhấn **`Connect`** bên cạnh repo

---

### BƯỚC 4: Cấu Hình Web Service

Điền form theo thứ tự:

| Field | Giá trị |
|-------|---------|
| **Name** | `ews-backend` |
| **Region** | `Singapore` (khớp với DB) |
| **Branch** | `main` |
| **Language** | `Docker` ← quan trọng |
| **Instance Type** | `Free` |

---

### BƯỚC 5: Thêm Environment Variables

Nhấn **`Add Environment Variable`**, điền từng dòng:

| Key | Value | Ghi chú |
|-----|-------|---------|
| `SECRET_KEY` | *(nhấn nút Generate)* | Render tự tạo key ngẫu nhiên |
| `DEBUG` | `False` | |
| `DB_NAME` | `early_warning_db` | |
| `DB_USER` | `ewsuser` | |
| `DB_PASSWORD` | *(copy từ Bước 2)* | |
| `DB_HOST` | *(copy Internal Host từ Bước 2)* | |
| `DB_PORT` | `5432` | |
| `MLFLOW_TRACKING_URI` | `file:///app/mlruns` | Lưu MLflow local |

---

### BƯỚC 6: Deploy

Nhấn **`Create Web Service`** → Render sẽ:
1. Pull code từ GitHub
2. Build Docker image
3. Chạy `collectstatic`
4. Khởi động Gunicorn

Chờ build xong (~5-10 phút), status chuyển thành **`Live`** ✅

---

## PHẦN 4: Kiểm Tra Sau Deploy

| Kiểm tra | URL |
|----------|-----|
| Health check | `https://ews-backend.onrender.com/api/health/` |
| Django Admin | `https://ews-backend.onrender.com/admin/` |
| Frontend | `https://ews-backend.onrender.com/` |
| API | `https://ews-backend.onrender.com/api/` |

Health check trả về `{"status": "ok"}` → deploy thành công! 🎉

---

## Lưu Ý Quan Trọng

- **Free tier PostgreSQL** tự xóa sau **90 ngày** nếu không hoạt động
- **Free tier Web Service** sẽ **ngủ sau 15 phút** không có request → lần đầu truy cập sau đó sẽ chậm ~30 giây
- Mỗi lần push lên branch `main`, Render sẽ **tự động redeploy**
- Log xem tại: Dashboard → `ews-backend` → tab **`Logs`**
