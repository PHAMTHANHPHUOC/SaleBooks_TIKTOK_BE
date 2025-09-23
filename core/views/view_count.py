from django.shortcuts import render
from django.http import JsonResponse
from .utils import update_visit_counter, get_visit_stats,calculate_growth_rate,get_client_ip,update_visit_counter_from_data,get_country_stats
 # Lấy thêm dữ liệu khác
from datetime import datetime, timedelta
from django.db.models import Count
from core.models.VisitCounter import VisitLog, VisitCounter
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import traceback
def homepage(request):
    """API tính lượt truy cập cho trang frontend http://localhost:5173/"""
    counter = update_visit_counter(request, 'frontend_home')
    stats = get_visit_stats('frontend_home')
    return JsonResponse(stats)
def get_visit_count_api(request):
    """
    API GET /api/visits/ - Trả về đầy đủ dữ liệu cho frontend Vue.js
    Cần include_countries=true để có dữ liệu country_stats
    """
    page_name = request.GET.get('page', 'home')
    include_countries = request.GET.get('include_countries', 'false').lower() == 'true'
    
    stats = get_visit_stats(page_name)
    
    # Thống kê theo giờ (24h qua) 
    hourly_stats = []
    now = datetime.now()
    for i in range(24):
        hour_start = now - timedelta(hours=i+1)
        hour_end = now - timedelta(hours=i)
        count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__range=[hour_start, hour_end]
        ).count()
        hourly_stats.append({
            'hour': hour_start.strftime('%H:00'),
            'visits': count
        })
    
    # Thống kê theo ngày (7 ngày qua)
    daily_stats = []
    for i in range(7):
        date_check = now.date() - timedelta(days=i)
        count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date=date_check
        ).count()
        daily_stats.append({
            'date': date_check.strftime('%d/%m'),
            'visits': count
        })
    
    # Unique visitors (theo IP) hôm nay
    unique_today = VisitLog.objects.filter(
        page_visited=page_name,
        visit_time__date=now.date()
    ).values('ip_address').distinct().count()
    
    # Kết quả cơ bản
    result = {
        # Dữ liệu cơ bản mà frontend cần
        'total_visits': int(stats.get('total_visits', 0)),
        'today_visits': int(stats.get('today_visits', 0)),
        'week_visits': int(stats.get('week_visits', 0)),
        'month_visits': int(stats.get('month_visits', 0)),
        'unique_today': unique_today,
        'last_update': stats.get('last_update').isoformat() if stats.get('last_update') else now.isoformat(),
        
        # Dữ liệu charts
        'hourly_stats': list(reversed(hourly_stats[:24])),  # 24h, mới nhất sau
        'daily_stats': list(reversed(daily_stats)),  # 7 ngày, mới nhất trước
        
        # Metadata
        'page_name': page_name,
        'server_time': now.isoformat(),
        'timezone': 'UTC+7',
        
        # Growth rates
        'growth': {
            'today_vs_yesterday': calculate_growth_rate(page_name, 'day'),
            'this_week_vs_last_week': calculate_growth_rate(page_name, 'week'),
            'this_month_vs_last_month': calculate_growth_rate(page_name, 'month'),
        }
    }
    
    # Thêm country_stats nếu được yêu cầu
    if include_countries:
        result['country_stats'] = get_country_stats(page_name)
    
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
def coloring_book_detail(request, book_id):
    """Chi tiết sách - có counter riêng"""
    page_name = f'book_{book_id}'
    counter = update_visit_counter(request, page_name)
    stats = get_visit_stats(page_name)
    
    context = {
        'book_id': book_id,
        'visit_stats': stats,
    }
    return render(request, 'book_detail.html', context)

def frontend_page_visit(request):
    """API tính và trả về lượt truy cập cho bất kỳ trang frontend nào (dùng query param 'page')"""
    # Đồng bộ với dashboard (index.vue) đang đọc thống kê mặc định cho 'home'
    page_name = request.GET.get('page', 'home')
    counter = update_visit_counter(request, page_name)
    stats = get_visit_stats(page_name)
    return JsonResponse(stats)


@csrf_exempt
@require_http_methods(["POST"])
def track_visit(request):
    """
    API POST /api/visits/track - Nhận thông tin tracking từ frontend
    Đây là endpoint mà frontend Vue.js đang cố gửi request tới
    """
    try:
        # Parse JSON data từ frontend
        data = json.loads(request.body)
        
        # Lấy thông tin cơ bản
        page_name = data.get('page', 'home')
        # Ưu tiên IP từ payload (được client xác định qua dịch vụ geo) nếu có
        ip_address = data.get('ip') or get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Tạo VisitLog mới với thông tin từ frontend
        visit_log = VisitLog.objects.create(
            ip_address=ip_address,
            user_agent=user_agent,
            page_visited=page_name,
            # Thêm các trường mới từ frontend
            country_code=(data.get('country_code') or 'UN')[:2],
            country_name=data.get('country_name'),
            city=data.get('city'),
            region=data.get('region'),
            referrer=data.get('referrer'),
            screen_resolution=data.get('screen_resolution'),
            language=data.get('language'),
            # session_id nếu có
        )
        
        # Cập nhật counter
        update_visit_counter_from_data(page_name)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Visit tracked successfully',
            'visit_id': visit_log.id,
            'timestamp': visit_log.visit_time.isoformat()
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        }, status=400)
    except Exception as e:
        print("Error in track_visit:", str(e))
        traceback.print_exc()
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)