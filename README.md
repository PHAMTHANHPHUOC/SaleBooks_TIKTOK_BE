# Django Backend Project

## Cấu trúc Project
```
backend/
├── config/                 # Cấu hình chính của Django
│   ├── __init__.py
│   ├── settings.py        # Cài đặt Django
│   ├── urls.py           # URL routing chính
│   ├── wsgi.py           # WSGI configuration
│   └── asgi.py           # ASGI configuration
├── core/                  # App chính của project
│   ├── __init__.py
│   ├── apps.py           # App configuration
│   ├── models/           # Thư mục chứa models
│   ├── views.py          # Views
│   ├── urls.py           # URL routing cho app
│   └── tests.py          # Unit tests
├── manage.py             # Django management script
├── requirements.txt      # Python dependencies
└── db.sqlite3           # Database file
```

## Setup Instructions

### 1. Tạo Virtual Environment
```bash
python -m venv venv
```

### 2. Kích hoạt Virtual Environment
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Cài đặt Dependencies
```bash
pip install -r requirements.txt
```

### 4. Chạy Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Tạo Superuser (tùy chọn)
```bash
python manage.py createsuperuser
```

### 6. Chạy Development Server
```bash
python manage.py runserver
```

## Database Configuration
Project được cấu hình để sử dụng MySQL database với thông tin:
- Database: thenewmoon
- User: root
- Password: Phuoc1512.
- Host: 127.0.0.1
- Port: 3306

## URLs
- Admin Panel: http://localhost:8000/admin/
- Main App: http://localhost:8000/ 