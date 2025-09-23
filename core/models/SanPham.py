from django.db import models
from django.utils import timezone
from rest_framework import serializers

# Bảng loại sản phẩm
class LoaiSanPham(models.Model):
    ten_loai = models.CharField(max_length=100, unique=True)  # Tên loại sản phẩm
    tinh_trang = models.IntegerField(default=0)
    layout = models.IntegerField(default=0)
    link_danh_muc = models.URLField(blank=True, null=True)  
    
    # Mô tả loại sản phẩm (tuỳ chọn)
    
    def __str__(self):
        return self.ten_loai


# Bảng sản phẩm
class SanPham(models.Model):
    ten_san_pham = models.CharField(max_length=255)   
    duong_dan_ngoai = models.URLField(blank=True, null=True)  
    gia_mac_dinh = models.CharField(max_length=50)
    tinh_trang = models.IntegerField(default=0)
    anh_dai_dien = models.ImageField(upload_to='avatars/', blank=True, null=True)

    loai_san_pham = models.ManyToManyField(
        LoaiSanPham,
        through="SanPhamLoai",
        blank=True,
        related_name='san_phams'
    )

    def __str__(self):
        return self.ten_san_pham

class SanPhamView(models.Model):
    san_pham = models.ForeignKey(
        SanPham,
        on_delete=models.CASCADE,
        related_name="views"
    )
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
class SanPhamLoai(models.Model):
    san_pham = models.ForeignKey("SanPham", on_delete=models.CASCADE)
    loai = models.ForeignKey("LoaiSanPham", on_delete=models.CASCADE)
    order = models.IntegerField(default=0)  # <--- quan trọng: vị trí trong loại

    class Meta:
        unique_together = ("san_pham", "loai")  # tránh trùng lặp
        ordering = ["order"]

    def __str__(self):
        return f"{self.san_pham.ten_san_pham} trong {self.loai.ten_loai} (order={self.order})"
