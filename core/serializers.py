from rest_framework import serializers
from core.models.SanPham import SanPham,LoaiSanPham
class SanPhamSerializer(serializers.ModelSerializer):
    gia_mac_dinh = serializers.CharField() 
    loai_san_pham = serializers.PrimaryKeyRelatedField(
        queryset=LoaiSanPham.objects.all(),
        many=True
    )
    class Meta:
        model = SanPham
        fields = '__all__'  
