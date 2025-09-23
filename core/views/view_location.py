from django.http import JsonResponse
from django.contrib.gis.geoip2 import GeoIP2
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
    """Lấy IP thật từ request, ưu tiên IP công khai từ các header phổ biến."""
    for header in ['HTTP_CF_CONNECTING_IP', 'HTTP_X_REAL_IP']:
        candidate = request.META.get(header)
        if candidate and _is_public_ip(candidate.strip()):
            return candidate.strip()
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        for part in [p.strip() for p in x_forwarded_for.split(',')]:
            if _is_public_ip(part):
                return part
    return request.META.get('REMOTE_ADDR')

def get_location(request):
    # Cho phép override qua query nhưng mặc định dùng IP thật từ request
    ip = request.GET.get("ip") or get_client_ip(request)

    try:
        if not ip or not _is_public_ip(ip):
            # Không tra cứu GeoIP cho IP nội bộ; trả về Unknown
            return JsonResponse({
                "ip": ip,
                "country_code": "UN",
                "country": "Unknown",
                "region": None,
                "city": None,
            })

        mmdb_path_primary = os.path.join(settings.BASE_DIR, 'GeoLite2-City.mmdb')
        mmdb_path_alt = os.path.join(settings.BASE_DIR, 'backend', 'GeoLite2-City.mmdb')
        mmdb_path = mmdb_path_primary if os.path.exists(mmdb_path_primary) else mmdb_path_alt
        reader = geoip2.database.Reader(mmdb_path)
        response = reader.city(ip)
        country_code = (response.country.iso_code or 'UN')[:2]
        country_name = response.country.name or 'Unknown'
        region_name = response.subdivisions.most_specific.name
        city_name = response.city.name
        return JsonResponse({
            "ip": ip,
            "country_code": country_code,
            "country": country_name,
            "region": region_name,
            "city": city_name,
        })
    except Exception as e:
        return JsonResponse({"error": str(e), "ip": ip})
