# Sử dụng Python 3.12 slim cho hiệu suất và nhẹ
FROM python:3.12-slim

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code vào container
COPY . /app/

# Chuyển vào thư mục backend
WORKDIR /app/early_waring_backend

# Collect static files khi build (whitenoise sẽ serve chúng)
RUN python manage.py collectstatic --noinput || true

# Port mặc định (Render sẽ override bằng biến PORT)
EXPOSE 8000

# ✅ Dùng gunicorn (production WSGI server) thay vì runserver
CMD ["gunicorn", "early_waring_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
