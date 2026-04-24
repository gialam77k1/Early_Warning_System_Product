# Sử dụng Python 3.12 slim cho hiệu suất và nhẹ
FROM python:3.12-slim

# Thiếp lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH=/app

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt các thư viện hệ thống cần thiết cho psycopg2 và các thư viện khác
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

# Chuyển vào thư mục backend để chạy lệnh
WORKDIR /app/early_waring_backend

# Collect static trong quá trình build để WhiteNoise có sẵn assets
RUN python manage.py collectstatic --noinput || true

# Port mà Django sẽ chạy
EXPOSE 8000

CMD ["bash", "entrypoint.sh"]
