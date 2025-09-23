from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

class KhachHangManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email phải được cung cấp')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', 1)
        return self.create_user(email, password, **extra_fields)

class KhachHang(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    so_dien_thoai = models.CharField(max_length=20)
    ho_va_ten = models.CharField(max_length=255)
    password = models.CharField(max_length=128)  # AbstractBaseUser đã có, nhưng để rõ ràng
    hash_reset = models.CharField(max_length=255, null=True, blank=True)
    hash_active = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.IntegerField(default=0)
    is_block = models.IntegerField(default=0)
    is_staff = models.BooleanField(default=False)  # Để dùng admin
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['ho_va_ten', 'so_dien_thoai']

    objects = KhachHangManager()

    def __str__(self):
        return self.email