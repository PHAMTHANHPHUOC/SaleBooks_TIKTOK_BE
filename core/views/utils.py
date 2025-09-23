from django.utils import timezone
from django.http import HttpRequest
from ..models import VisitCounter, VisitLog
from datetime import date
from datetime import datetime, timedelta
from django.db.models import Count
import geoip2
import ipaddress
import os
from django.conf import settings
def _is_public_ip(ip_str: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_str)
        return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local)
    except Exception:
        return False

def get_client_ip(request):
    """Lấy IP thật của user, ưu tiên IP công khai từ các header phổ biến."""
    # 1) Cloudflare / Proxy headers
    for header in ['HTTP_CF_CONNECTING_IP', 'HTTP_X_REAL_IP']:
        candidate = request.META.get(header)
        if candidate and _is_public_ip(candidate.strip()):
            return candidate.strip()
    # 2) X-Forwarded-For (chuỗi danh sách)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        for part in [p.strip() for p in x_forwarded_for.split(',')]:
            if _is_public_ip(part):
                return part
    # 3) REMOTE_ADDR
    remote_ip = request.META.get('REMOTE_ADDR')
    return remote_ip

def update_visit_counter(request: HttpRequest, page_name='homepage'):
    """Cập nhật counter và log visit"""
    
    # Lấy hoặc tạo counter record
    counter, created = VisitCounter.objects.get_or_create(
        page_name=page_name,
        defaults={
            'total_visits': 0,
            'today_visits': 0,
            'last_visit_date': timezone.now().date()
        }
    )
    
    # Kiểm tra ngày mới
    today = timezone.now().date()
    if counter.last_visit_date < today:
        counter.today_visits = 0
        counter.last_visit_date = today
    
    # Tăng counter
    counter.total_visits += 1
    counter.today_visits += 1
    counter.save()
    
    # Log visit (ghi kèm thông tin quốc gia để thống kê đồng bộ với total)
    ip_address = get_client_ip(request)
    country_code = None
    country_name = None
    city_name = None
    region_name = None

    # Chỉ tra cứu GeoIP khi IP là công khai. Nếu không, gán UN để tránh sai lệch.
    if ip_address and _is_public_ip(ip_address):
        try:
            mmdb_path_primary = os.path.join(settings.BASE_DIR, 'GeoLite2-City.mmdb')
            mmdb_path_alt = os.path.join(settings.BASE_DIR, 'backend', 'GeoLite2-City.mmdb')
            mmdb_path = mmdb_path_primary if os.path.exists(mmdb_path_primary) else mmdb_path_alt
            reader = geoip2.database.Reader(mmdb_path)
            response = reader.city(ip_address)
            iso = response.country.iso_code or 'UN'
            country_code = iso[:2]
            country_name = response.country.name or 'Unknown'
            city_name = response.city.name
            region_name = response.subdivisions.most_specific.name
        except Exception:
            country_code = 'UN'
            country_name = 'Unknown'
    else:
        country_code = 'UN'
        country_name = 'Unknown'
    VisitLog.objects.create(
        ip_address=ip_address,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        page_visited=page_name,
        country_code=country_code,
        country_name=country_name,
        city=city_name,
        region=region_name,
    )
    return 


def calculate_growth_rate(page_name, period):
    """Tính tỷ lệ tăng trưởng"""
    from datetime import datetime, timedelta
    now = datetime.now()
    
    if period == 'day':
        current_start = now.date()
        previous_start = current_start - timedelta(days=1)
        current_count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date=current_start
        ).count()
        previous_count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date=previous_start
        ).count()
        
    elif period == 'week':
        current_start = now.date() - timedelta(days=now.weekday())
        previous_start = current_start - timedelta(days=7)
        current_count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date__gte=current_start
        ).count()
        previous_count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date__gte=previous_start,
            visit_time__date__lt=current_start
        ).count()
        
    elif period == 'month':
        current_start = now.replace(day=1).date()
        if current_start.month == 1:
            previous_start = current_start.replace(year=current_start.year-1, month=12)
        else:
            previous_start = current_start.replace(month=current_start.month-1)
        
        current_count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date__gte=current_start
        ).count()
        previous_count = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date__gte=previous_start,
            visit_time__date__lt=current_start
        ).count()
    
    if previous_count == 0:
        return 100 if current_count > 0 else 0
    
    growth = ((current_count - previous_count) / previous_count) * 100
    return round(growth, 1)
def get_visit_stats(page_name='homepage'):
    """Lấy thống kê visit"""
    try:
        counter = VisitCounter.objects.get(page_name=page_name)
        
        
        # Force refresh từ DB
        counter.refresh_from_db()
        
        # Thống kê tuần này
        from datetime import datetime, timedelta
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        week_visits = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date__gte=week_start
        ).count()
        
        # Thống kê tháng này
        month_start = timezone.now().replace(day=1).date()
        month_visits = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date__gte=month_start
        ).count()
        
        # Unique visitors hôm nay (theo IP)
        today = timezone.now().date()
        unique_today = VisitLog.objects.filter(
            page_visited=page_name,
            visit_time__date=today
        ).values('ip_address').distinct().count()
        
        return {
            'total_visits': counter.total_visits,
            'today_visits': counter.today_visits,
            'week_visits': week_visits,
            'month_visits': month_visits,
            'unique_today': unique_today,
            'last_update': counter.updated_at,
        }
    except VisitCounter.DoesNotExist:
        return {
            'total_visits': 0,
            'today_visits': 0,
            'week_visits': 0,
            'month_visits': 0,
            'unique_today': 0,
            'last_update': None,
        }
## DO NOT redefine get_client_ip below; we use the robust version above.

def update_visit_counter_from_data(page_name):
    """Cập nhật counter không cần request object"""
    from django.utils import timezone
    
    # Lấy hoặc tạo counter record
    counter, created = VisitCounter.objects.get_or_create(
        page_name=page_name,
        defaults={
            'total_visits': 0,
            'today_visits': 0,
            'last_visit_date': timezone.now().date()
        }
    )
    
    # Kiểm tra ngày mới
    today = timezone.now().date()
    if counter.last_visit_date < today:
        counter.today_visits = 0
        counter.last_visit_date = today
    
    # Tăng counter
    counter.total_visits += 1
    counter.today_visits += 1
    counter.save()
    
    return counter

def get_country_stats(page_name):
    """Lấy thống kê theo quốc gia cho các khoảng thời gian"""
    from django.utils import timezone
    now = timezone.now()
    
    def get_period_stats(period):
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = VisitLog.objects.filter(
                page_visited=page_name,
                visit_time__gte=start_date
            )
        elif period == 'week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            queryset = VisitLog.objects.filter(
                page_visited=page_name,
                visit_time__gte=start_date
            )
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            queryset = VisitLog.objects.filter(
                page_visited=page_name,
                visit_time__gte=start_date
            )
        else:  # all
            queryset = VisitLog.objects.filter(page_visited=page_name)
        
        # Group by country và đếm
        stats = queryset.values('country_code', 'country_name').annotate(
            visits=Count('id')
        ).exclude(
            country_code__isnull=True
        ).order_by('-visits')
        
        return list(stats)
    
    return {
        'today': get_period_stats('today'),
        'week': get_period_stats('week'),
        'month': get_period_stats('month'),
        'all': get_period_stats('all')
    }