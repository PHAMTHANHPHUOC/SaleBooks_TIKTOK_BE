from itertools import count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from core.models.LinkMangXaHoi import LinkProfile,LinkClickHistory
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
import json
from django.utils.timezone import make_aware, get_current_timezone
from django.utils.timezone import now
from rest_framework.decorators import api_view
from datetime import datetime, time, timedelta
@api_view(['POST'])
def tang_luot_click(request, pk):
    """
    Tăng lượt click cho link mạng xã hội (giống sản phẩm)
    """
    try:
        link = LinkProfile.objects.get(pk=pk)
        LinkClickHistory.objects.create(link=link)
        return Response({'status': True, 'message': 'Đã ghi nhận lượt click'})
    except LinkProfile.DoesNotExist:
        return Response({'status': False, 'message': 'Không tìm thấy link'}, status=404)

@api_view(['GET'])
def top_link(request):
    loai = request.GET.get("loai", "ngay")
    tz = get_current_timezone()
    today = now().date()

    if loai == "ngay":
        start = make_aware(datetime.combine(today, time.min), tz)
        end = make_aware(datetime.combine(today + timedelta(days=1), time.min), tz)
    elif loai == "tuan":
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=7)
        start = make_aware(datetime.combine(start_date, time.min), tz)
        end = make_aware(datetime.combine(end_date, time.min), tz)
    elif loai == "thang":
        start_date = today.replace(day=1)
        if today.month == 12:
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:
            end_date = today.replace(month=today.month + 1, day=1)
        start = make_aware(datetime.combine(start_date, time.min), tz)
        end = make_aware(datetime.combine(end_date, time.min), tz)
    elif loai == "nam":
        start_date = today.replace(month=1, day=1)
        end_date = today.replace(year=today.year + 1, month=1, day=1)
        start = make_aware(datetime.combine(start_date, time.min), tz)
        end = make_aware(datetime.combine(end_date, time.min), tz)
    else:
        return JsonResponse({"error": "Tham số 'loai' không hợp lệ"}, status=400)
    views = (
        LinkClickHistory.objects.filter(
            created_at__gte=start,
            created_at__lt=end
        )
        .values('link__id', 'link__name', 'link__links')
        .annotate(so_luot=count("id"))
        .order_by("-so_luot")[:10]
    )
    data = [
        {
            "id": v["link__id"],
            "name": v["link__name"],
            "links": v["link__links"],
            "so_luot": v["so_luot"]
        }
        for v in views
    ]
    return JsonResponse(data, safe=False)
    
    
#     from django.db.models import Count
#     stats = LinkClickHistory.objects.values('link__id', 'link__name', 'link__links').annotate(luot_click=Count('id')).order_by('-luot_click')[:10]
#     return Response({'status': True, 'data': list(stats)})
# from datetime import datetime

@api_view(['GET'])
def thong_ke_luot_click(request):
    from django.db.models import Count
    loai = request.GET.get('loai', 'ngay')
    today = datetime.now().date()
    current_year = today.year
    current_month = today.month
    current_week = today.isocalendar()[1]
    queryset = LinkClickHistory.objects.all()
    if loai == 'ngay':
        queryset = queryset.filter(created_at__date=today)
    if loai == 'tuan':
        queryset = queryset.filter(
        created_at__week=current_week,
        created_at__year=current_year
    )

    if loai == 'thang':
        queryset = queryset.filter(
        created_at__month=current_month,
        created_at__year=current_year
        )

    if loai == 'nam':
        queryset = queryset.filter(
        created_at__year=current_year
        )
    # Có thể bổ sung lọc tuần/tháng/năm ở đây
    stats = queryset.values('link__id', 'link__name', 'link__links') \
        .annotate(luot_click=Count('id')) \
        .order_by('-luot_click')
    return Response({'status': True, 'data': list(stats)})
@api_view(['POST'])
def change_link(request):
    """
    Thay đổi trạng thái của link
    """
    try:
        loai = LinkProfile.objects.get(id=request.data.get('id'))
        loai.tinh_trang = not bool(loai.tinh_trang)
        loai.save()
        return Response({
            'status': True,
            'message': f"Đã đổi tình trạng {loai.name} thành công"
        }, status=status.HTTP_200_OK)
    except LinkProfile.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Không tìm thấy link'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': False,
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
def get_list_links_data(request):
    """
    Trả về danh sách tất cả link
    """
    loai_list = LinkProfile.objects.all()
    data = []
    for loai in loai_list:
        # Lấy URL tuyệt đối cho ảnh đại diện nếu có
        if loai.anh_dai_dien:
            try:
                anh_url = request.build_absolute_uri(loai.anh_dai_dien.url)
            except Exception:
                anh_url = ""
        else:
            anh_url = ""
        data.append({
            'id': loai.id,
            'name': loai.name,
            'subtitle': loai.subtitle,
            'anh_dai_dien': anh_url,
            'loai': loai.loai,
            'tinh_trang': loai.tinh_trang,
            'links': loai.links,
        })
    return Response({'data': data, 'status': 1})
@api_view(['GET'])
def get_list_links(request):
    """
    Trả về danh sách link đang hoạt động (tinh_trang = 1)

    - Giữ nguyên các khóa cũ: "link", "avatar"
    - Bổ sung khóa tiếng Việt: "duong_dan", "anh_dai_dien"

    Cấu trúc:
    {
      "Facebook": {"link": "...", "duong_dan": "...", "avatar": "...", "anh_dai_dien": "...", "loai": ..., "tinh_trang": ...},
      ...
    }
    """
    profiles = LinkProfile.objects.filter(tinh_trang=1)
    data = {}

    for profile in profiles:
        # Lấy link (parse JSON nếu cần)
        link_value = ""
        try:
            if profile.links:
                if isinstance(profile.links, str):
                    try:
                        parsed = json.loads(profile.links)
                        if isinstance(parsed, dict) and "link" in parsed:
                            link_value = parsed["link"]
                        else:
                            link_value = profile.links
                    except json.JSONDecodeError:
                        link_value = profile.links
                else:
                    link_value = profile.links
        except Exception:
            link_value = ""

        # Lấy URL avatar tuyệt đối
        avatar_url = ""
        try:
            if getattr(profile, 'anh_dai_dien', None):
                avatar_url = request.build_absolute_uri(profile.anh_dai_dien.url)
        except Exception:
            avatar_url = ""

        # Gán vào dict, bổ sung khóa Việt hóa và giữ tương thích ngược
        data[profile.name] = {
            "link": link_value,
            "subtitle": profile.subtitle,
            "duong_dan": link_value,
            "avatar": avatar_url,
            "anh_dai_dien": avatar_url,
            "loai": profile.loai,
            "tinh_trang": profile.tinh_trang,
        }

    # Giữ nguyên hành vi cũ: trả trực tiếp dict
    # Đồng thời bổ sung trường Việt hóa ở mức bao gói để dễ mở rộng sau này
    return Response({
        "trang_thai": True,
        "du_lieu": data,
        "data": data,
    })

from django.conf import settings
@require_http_methods(["GET"])
def get_links_api(request):
    try:
        profiles = LinkProfile.objects.all()
        data = {}

        for profile in profiles:
            # Xử lý link
            link_value = ""
            if profile.links:
                if isinstance(profile.links, str):
                    try:
                        parsed_links = json.loads(profile.links)
                        # Nếu links là JSON {"link": "..."} thì lấy key "link"
                        if isinstance(parsed_links, dict) and "link" in parsed_links:
                            link_value = parsed_links["link"]
                        else:
                            link_value = profile.links
                    except json.JSONDecodeError:
                        link_value = profile.links
                else:
                    link_value = profile.links

            # Xử lý avatar
            avatar_url = ""
            if profile.anh_dai_dien:
                try:
                    avatar_url = request.build_absolute_uri(profile.anh_dai_dien.url)
                except Exception:
                    avatar_url = ""

            # Đưa về dict, bổ sung loai và tinh_trang
            data[profile.name] = {
                "link": link_value,
                "subtitle": profile.subtitle,
                "avatar": avatar_url,
                "loai": profile.loai,
                "tinh_trang": profile.tinh_trang
            }

        return JsonResponse({
            'success': True,
            'data': data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@api_view(['POST'])
def create_link(request):
    try:
        name = request.data.get('name')
        subtitle = request.data.get('subtitle', '')  # Mặc định là chuỗi rỗng nếu không có
        links = request.data.get('links', '')  # Mặc định là rỗng nếu không có
        loai = request.data.get('loai', 0)  # Mặc định là 0 nếu không có
        tinh_trang = request.data.get('tinh_trang', 0)  #
        anh_dai_dien = request.FILES.get('anh_dai_dien')  # Lấy file ảnh từ request
        if anh_dai_dien:
            # Kiểm tra kích thước file
            if anh_dai_dien.size > 5 * 1024 * 1024:  # 5MB
                return JsonResponse({'status': False, 'error': 'File quá lớn (>5MB)'}, status=400)
            
            # Kiểm tra định dạng file
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            file_extension = anh_dai_dien.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return JsonResponse({
                    'status': False, 
                    'error': f'Định dạng file không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
                }, status=400)

        LinkProfile.objects.create(name=name,subtitle=subtitle,links=links,anh_dai_dien=anh_dai_dien, loai=loai, tinh_trang=tinh_trang)
        return JsonResponse({'status': True, 'message': 'thêm link thành công.'})
    except Exception as e:
            return JsonResponse({'status': False, 'error': str(e)}, status=400)
        
@api_view(['POST'])
def delete_link(request, id):
    try:
        LinkProfile.objects.get(id=id).delete()
        return Response({'status': True, 'message': 'Đã xóa thành công'})
    except LinkProfile.DoesNotExist:
        return Response({'status': False, 'message': 'Không tìm thấy link'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['POST'])  
def update_link(request, id):
    try:
        data = LinkProfile.objects.get(id=id)
        data.links = request.data.get('links')
        data.subtitle = request.data.get('subtitle', data.subtitle)  # Nếu có cập nhật subtitle
        data.name = request.data.get('name', data.name)  # Nếu có cập nhật tên
        data.loai = request.data.get('loai', data.loai)  # Nếu có cập nhật loại
        data.tinh_trang = request.data.get('tinh_trang', data.tinh_trang)  # Nếu có cập nhật tình trạng

        # Xử lý cập nhật ảnh đại diện nếu có file mới
        anh_dai_dien = request.FILES.get('anh_dai_dien')
        if anh_dai_dien:
            # Kiểm tra kích thước file
            if anh_dai_dien.size > 5 * 1024 * 1024:  # 5MB
                return Response({'status': False, 'message': 'File quá lớn (>5MB)'}, status=status.HTTP_400_BAD_REQUEST)
            # Kiểm tra định dạng file
            allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
            file_extension = anh_dai_dien.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return Response({
                    'status': False,
                    'message': f'Định dạng file không được hỗ trợ. Chỉ chấp nhận: {", ".join(allowed_extensions)}'
                }, status=status.HTTP_400_BAD_REQUEST)
            data.anh_dai_dien = anh_dai_dien

        data.save()
        return Response({
            'status': True,
            'message': 'Đã cập nhật link thành công!'
        }, status=status.HTTP_200_OK)
    except LinkProfile.DoesNotExist:
        return Response({
            'status': False,
            'message': 'Không tìm được link để cập nhật!'
        }, status=status.HTTP_404_NOT_FOUND)