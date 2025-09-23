
from core.models.SanPham import SanPham,LoaiSanPham,SanPhamView,SanPhamLoai
from django.shortcuts import get_object_or_404
from core.serializers import SanPhamSerializer
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
import logging
from datetime import timedelta
from django.db.models import Count
from django.utils.timezone import now
from datetime import datetime, time
from django.utils.timezone import make_aware, get_current_timezone

logger = logging.getLogger(__name__)
from rest_framework.parsers import MultiPartParser, FormParser


from django.utils.timezone import make_aware
@api_view(["POST"])
def update_product_order(request):
    try:
        loai_id = request.data.get("loai_id")
        product_ids = request.data.get("product_ids", [])

        for index, sp_id in enumerate(product_ids):
            SanPhamLoai.objects.filter(loai_id=loai_id, san_pham_id=sp_id).update(order=index)

        return Response({"status": True, "message": "Cập nhật thứ tự thành công"})
    except Exception as e:
        return Response({"status": False, "message": str(e)}, status=500)

from django.utils.timezone import now, make_aware
from datetime import datetime, time, timedelta

@require_GET
def top_san_pham(request):
    loai = request.GET.get("loai", "ngay")
    today = now().date()
    tz = get_current_timezone()

    if loai == "ngay":
        start = make_aware(datetime.combine(today, time.min), timezone=tz)
        end = make_aware(datetime.combine(today, time.max), timezone=tz)
    elif loai == "tuan":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
        start = make_aware(datetime.combine(start_date, time.min), timezone=tz)
        end = make_aware(datetime.combine(end_date, time.max), timezone=tz)
    elif loai == "thang":
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        start = make_aware(datetime.combine(start_date, time.min), timezone=tz)
        end = make_aware(datetime.combine(end_date, time.max), timezone=tz)
    elif loai == "nam":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(month=12, day=31)
        start = make_aware(datetime.combine(start_date, time.min), timezone=tz)
        end = make_aware(datetime.combine(end_date, time.max), timezone=tz)
    else:
        return JsonResponse({"error": "Tham số 'loai' không hợp lệ"}, status=400)


    views = (
        SanPhamView.objects.filter(
            created_at__gte=start,
            created_at__lte=end
        )
        .values("san_pham__id", "san_pham__ten_san_pham", "san_pham__anh_dai_dien")
        .annotate(so_luot=Count("id"))
        .order_by("-so_luot")[:10]
    )


    data = [
        {
            "id": v["san_pham__id"],
            "ten": v["san_pham__ten_san_pham"],
            "anh": v["san_pham__anh_dai_dien"],
            "so_luot": v["so_luot"]
        }
        for v in views
    ]
    return JsonResponse(data, safe=False)



@api_view(['POST'])
def tang_luot_xem(request, pk):
    if request.method == "POST":
        sp = get_object_or_404(SanPham, pk=pk)
        SanPhamView.objects.create(san_pham=sp)
        return JsonResponse({
            "success": True,
            "message": f"Đã ghi nhận click cho sản phẩm {sp.ten_san_pham}"
        })
    return JsonResponse({"success": False}, status=400)



@api_view(['POST'])
def change_san_pham(request):
    """
    Thay đổi trạng thái của loại sản phẩm
    """
    try:
        loai = SanPham.objects.get(id=request.data.get('id'))
        loai.tinh_trang = not bool(loai.tinh_trang)
        loai.save()
        return Response({
            'status': True,
            'message': f"Đã đổi tình trạng {loai.ten_san_pham} thành công"
        }, status=status.HTTP_200_OK)
    except SanPham.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Không tìm thấy loại sản phẩm'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def create_san_pham(request):
    try:
        ten_san_pham = request.data.get('ten_san_pham')
        duong_dan_ngoai = request.data.get('duong_dan_ngoai')
        gia_mac_dinh = request.data.get('gia_mac_dinh')
        anh_dai_dien = request.FILES.get('anh_dai_dien')
        tinh_trang = request.data.get('tinh_trang', 0)

        # ================== XỬ LÝ LOẠI SẢN PHẨM ==================
        loai_san_pham_ids = []

        # Trường hợp frontend gửi dạng list (append nhiều lần)
        if hasattr(request.data, "getlist"):
            loai_san_pham_raw = request.data.getlist("loai_san_pham")
        else:
            loai_san_pham_raw = request.data.get("loai_san_pham", "")

        # Nếu là chuỗi "1,2,3" → tách thành list
        if isinstance(loai_san_pham_raw, str):
            loai_san_pham_raw = [x.strip() for x in loai_san_pham_raw.split(",") if x.strip()]

        # Convert sang int
        for item in loai_san_pham_raw:
            try:
                loai_san_pham_ids.append(int(item))
            except (ValueError, TypeError):
                return JsonResponse({
                    'status': False,
                    'error': f'ID loại sản phẩm không hợp lệ: {item}'
                }, status=400)

        # Validate tồn tại trong DB
        if loai_san_pham_ids:
            existing_ids = set(
                LoaiSanPham.objects.filter(id__in=loai_san_pham_ids).values_list('id', flat=True)
            )
            invalid_ids = set(loai_san_pham_ids) - existing_ids
            if invalid_ids:
                return JsonResponse({
                    'status': False,
                    'error': f'Không tìm thấy loại sản phẩm với ID: {list(invalid_ids)}'
                }, status=400)

        # ================== VALIDATE INPUT ==================
        if not ten_san_pham:
            return JsonResponse({'status': False, 'error': 'Tên sản phẩm là bắt buộc'}, status=400)

        if not gia_mac_dinh:
            return JsonResponse({'status': False, 'error': 'Giá mặc định là bắt buộc'}, status=400)

        # Validate file upload
        if anh_dai_dien:
            if anh_dai_dien.size > 5 * 1024 * 1024:
                return JsonResponse({'status': False, 'error': 'File quá lớn (>5MB)'}, status=400)

            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            file_extension = anh_dai_dien.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return JsonResponse({
                    'status': False,
                    'error': f'Định dạng file không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
                }, status=400)

        # ================== TẠO SẢN PHẨM ==================
        san_pham = SanPham.objects.create(
            ten_san_pham=ten_san_pham,
            duong_dan_ngoai=duong_dan_ngoai,
            gia_mac_dinh=gia_mac_dinh,
            anh_dai_dien=anh_dai_dien,
            tinh_trang=tinh_trang
        )

        # Gán nhiều loại sản phẩm
        if loai_san_pham_ids:
            for idx, loai_id in enumerate(loai_san_pham_ids):
                SanPhamLoai.objects.create(
                    san_pham=san_pham,
                    loai_id=loai_id,
                    order=idx  # đặt thứ tự hiển thị, bạn muốn mặc định sao cũng được
                )

        # ================== RESPONSE ==================
        response_data = {
            'status': True,
            'message': 'Thêm sản phẩm thành công.',
            'data': {
                'id': san_pham.id,
                'ten_san_pham': san_pham.ten_san_pham,
                'anh_dai_dien_url': san_pham.anh_dai_dien.url if san_pham.anh_dai_dien else None,
                'loai_san_pham': list(san_pham.loai_san_pham.values('id', 'ten_loai'))
            }
        }
        return JsonResponse(response_data)

    except Exception as e:
        import traceback

        return JsonResponse({
            'status': False,
            'error': f'Lỗi server: {str(e)}'
        }, status=500)

@api_view(['POST'])
def delete_san_pham(request, id):
    try:
        loai = SanPham.objects.get(id=id)
        loai.delete()
        return Response({'status': True,'message': 'Đã xóa thành công'})
    except SanPham.DoesNotExist:
        return Response({'status': False,'message': 'Không tìm thấy loại sản phẩm'}, status=status.HTTP_404_NOT_FOUND)
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status
import os

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def update_san_pham(request, id):
    try:
        data = SanPham.objects.get(id=id)
        
        # Chỉ cập nhật field khi có dữ liệu
        ten_san_pham = request.data.get('ten_san_pham')
        if ten_san_pham:
            data.ten_san_pham = ten_san_pham
            
        duong_dan_ngoai = request.data.get('duong_dan_ngoai')
        if duong_dan_ngoai is not None:  # Cho phép empty string
            data.duong_dan_ngoai = duong_dan_ngoai
            
        gia_mac_dinh = request.data.get('gia_mac_dinh')
        if gia_mac_dinh is not None:
            data.gia_mac_dinh = gia_mac_dinh  # Không ép kiểu float, cho phép text
        
        tinh_trang = request.data.get('tinh_trang')
        if tinh_trang is not None:
            data.tinh_trang = int(tinh_trang)
            
        # Xử lý loại sản phẩm (foreign key)
        # loai_san_pham_id = request.data.get('loai_san_pham')
        
        # Xử lý loại sản phẩm - tương thích với cả FormData và JSON
        loai_san_pham_raw = request.data.get("loai_san_pham", [])
        
        # Nếu là chuỗi "1,2,3" → tách thành list
        if isinstance(loai_san_pham_raw, str):
            loai_san_pham_raw = [x.strip() for x in loai_san_pham_raw.split(",") if x.strip()]
        
        # Convert sang int và validate
        loai_san_pham_id = []
        for item in loai_san_pham_raw:
            try:
                loai_san_pham_id.append(int(item))
            except (ValueError, TypeError):
                return Response({
                    'status': False,
                    'error': f'ID loại sản phẩm không hợp lệ: {item}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if loai_san_pham_id:
            # Xoá toàn bộ quan hệ cũ
            SanPhamLoai.objects.filter(san_pham=data).delete()

            # Thêm lại quan hệ mới + order
            for idx, loai_id in enumerate(loai_san_pham_id):
                # Kiểm tra loại sản phẩm có tồn tại không
                if not LoaiSanPham.objects.filter(id=loai_id).exists():
                    return Response({
                        'status': False,
                        'error': f'Không tìm thấy loại sản phẩm ID={loai_id}'
                    }, status=status.HTTP_400_BAD_REQUEST)

                SanPhamLoai.objects.create(
                    san_pham=data,
                    loai_id=loai_id,
                    order=idx
                )
        
        # Xử lý file upload - QUAN TRỌNG: Lấy từ request.FILES
        anh_dai_dien = request.FILES.get('anh_dai_dien')
        if anh_dai_dien:
            # Validate file
            if anh_dai_dien.size > 5 * 1024 * 1024:  # 5MB
                return Response({
                    'status': False,
                    'error': 'File quá lớn (>5MB)'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate file extension
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            file_extension = anh_dai_dien.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return Response({
                    'status': False, 
                    'error': f'Định dạng file không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Xóa file cũ nếu có
            if data.anh_dai_dien:
                try:
                    if os.path.exists(data.anh_dai_dien.path):
                        os.remove(data.anh_dai_dien.path)
                except Exception as e:
                    print(f"Error deleting old file: {e}")
            
            # Gán file mới
            data.anh_dai_dien = anh_dai_dien
        
        # Validate trước khi save
        if not data.ten_san_pham or data.ten_san_pham.strip() == "":
            return Response({
                'status': False,
                'error': 'Tên sản phẩm không được để trống'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data.save()
        
        return Response({
            'status': True,
            'message': 'Đã cập nhật sản phẩm thành công!',
            'data': {
                'id': data.id,
                'ten_san_pham': data.ten_san_pham,
                'anh_dai_dien_url': data.anh_dai_dien.url if data.anh_dai_dien else None
            }
        }, status=status.HTTP_200_OK)
        
    except SanPham.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Không tìm được sản phẩm để cập nhật!'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def change_loai_san_pham(request):
    """
    Thay đổi trạng thái của loại sản phẩm
    """
    try:
        loai = LoaiSanPham.objects.get(id=request.data.get('id'))
        loai.tinh_trang = not bool(loai.tinh_trang)
        loai.save()
        return Response({
            'status': True,
            'message': f"Đã đổi tình trạng {loai.ten_loai} thành công"
        }, status=status.HTTP_200_OK)
    except LoaiSanPham.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Không tìm thấy loại sản phẩm'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
       

@api_view(['POST'])
def create_loai_san_pham(request):
    try:
        ten_loai = request.data.get('ten_loai')
        link_danh_muc = request.data.get('link_danh_muc', '')  # Mặc định là rỗng nếu không có
        tinh_trang = request.data.get('tinh_trang')  # Mặc định là 0 nếu không có
        layout = request.data.get('layout', '0')  # Mặc định là 'default' nếu không có
        LoaiSanPham.objects.create(ten_loai=ten_loai,  tinh_trang=tinh_trang,link_danh_muc=link_danh_muc)
        return JsonResponse({'status': True, 'message': 'thêm loại sản phẩm thành công.'})
    except Exception as e:
            return JsonResponse({'status': False, 'error': str(e)}, status=400)
@api_view(['POST'])  
def update_loai_san_pham(request, id):
    try:
        data = LoaiSanPham.objects.get(id=id)
        data.ten_loai = request.data.get('ten_loai')
        data.link_danh_muc = request.data.get('link_danh_muc', '')  # Cập nhật link danh mục nếu có
        data.tinh_trang = request.data.get('tinh_trang')  # Cập nhật trạng thái nếu có
        data.layout = request.data.get('layout', data.layout)  # Cập nhật layout nếu có, giữ nguyên nếu không
        data.save()
        return Response({
            'status': True,
            'message': 'Đã cập nhật loại sản phẩm thành công!'
        }, status=status.HTTP_200_OK)
    except LoaiSanPham.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Không tìm được sản phẩm để cập nhật!'
        }, status=status.HTTP_404_NOT_FOUND)
@api_view(['POST'])
def delete_loai_san_pham(request, id):
    try:
        loai = LoaiSanPham.objects.get(id=id)
        loai.delete()
        return Response({'status': True,'message': 'Đã xóa thành công'})
    except LoaiSanPham.DoesNotExist:
        return Response({'status': False,'message': 'Không tìm thấy loại sản phẩm'}, status=status.HTTP_404_NOT_FOUND)
@api_view(['GET'])
def product_data(request):
    """
    Trả về dữ liệu sản phẩm cho trang chủ
    """
    try:
        # Giả sử bạn có một mô hình Sản Phẩm
        san_phams = SanPham.objects.all()  # Thay thế bằng mô hình thực tế của bạn

        # san_phams = SanPham.objects.filter(loai_san_pham_id=id, loai_san_pham__tinh_trang=1)
        serializer = SanPhamSerializer(san_phams, many=True)
        return Response({
            'status': True,
            'data': serializer.data
        })
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu sản phẩm: {str(e)}")
        return Response({
            'status': False,
            'message': "Lỗi khi lấy dữ liệu sản phẩm"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def product_type(request, id):
    """
    Trả về dữ liệu sản phẩm theo loại (ManyToMany) với thứ tự đúng
    """
    try:
        # Lấy sản phẩm theo thứ tự từ bảng SanPhamLoai
        san_pham_loai_relations = SanPhamLoai.objects.filter(
            loai_id=id,
            san_pham__tinh_trang=1
        ).select_related('san_pham').order_by('order')
        
        # Lấy danh sách sản phẩm theo thứ tự
        san_phams = [relation.san_pham for relation in san_pham_loai_relations]
        
        # Nếu không có sản phẩm nào, trả về danh sách rỗng
        if not san_phams:
            return Response({
                'status': True,
                'data': []
            })
        
        serializer = SanPhamSerializer(san_phams, many=True)
        return Response({
            'status': True,
            'data': serializer.data
        })
    except Exception as e:
        logger.error(f"Lỗi khi lấy dữ liệu sản phẩm theo loại: {str(e)}")
        return Response({
            'status': False,
            'message': "Lỗi khi lấy dữ liệu sản phẩm theo loại"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def product_data_type(request):
    """
    Trả về danh sách tất cả loại sản phẩm
    """
    loai_list = LoaiSanPham.objects.all()
    data = []
    for loai in loai_list:
        data.append({
            'id': loai.id,
            'ten_loai': loai.ten_loai,
            'link_danh_muc': loai.link_danh_muc,  # Thêm trường link_danh_muc
            'tinh_trang': loai.tinh_trang,
            'layout': loai.layout
        })
    return Response(data)