from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models.StyleConfig import StyleConfig, SiteConfig
from django.http import JsonResponse
@api_view(['GET'])
def get_list_styles(request):
    list_data = StyleConfig.objects.all()
    data = []
    for style in list_data:
        data.append({
            'id': style.id,
            'tag': style.tag,
            'font_family': style.font_family,
            'font_weight': style.font_weight,
            'background': style.background,
            'color': style.color,
        })
    return Response(data)
def get_data_styles(request):
    styles = StyleConfig.objects.all()
    data = {}
    for style in styles:
        data[style.tag] = {
            "font_family": style.font_family,
            "font_weight": style.font_weight,
            "color": style.color,
            "background": style.background,
            # Không lấy background ở đây!
        }
    # Nếu muốn trả về background, lấy từ SiteConfig
    site_config = SiteConfig.objects.first()
    background = site_config.background if site_config else "#fffef3"
    return JsonResponse({"data": data, "background": background})
@api_view(['POST'])
def create_styles(request):
    try:
        tag = request.data.get('tag')
        font_family = request.data.get('font_family', '')  
        font_weight = request.data.get('font_weight', '')  
        color = request.data.get('color', '')
        background = request.data.get('background', '')
        StyleConfig.objects.create(
            tag=tag,
            font_family=font_family,
            font_weight=font_weight,
            color=color,
            background = background,
        )
        return Response({'status': True, 'message': 'Thêm style thành công.'})
    except Exception as e:
        return Response({'status': False, 'error': str(e)}, status=400)

@api_view(['POST'])
def update_styles(request, id):
    try:
        data = StyleConfig.objects.get(id=id)
        data.tag = request.data.get('tag', data.tag)
        data.font_family = request.data.get('font_family', data.font_family)
        data.font_weight = request.data.get('font_weight', data.font_weight)
        data.background = request.data.get('background', data.background)
        data.color = request.data.get('color', data.color)
        data.save()
        return Response({'status': True, 'message': 'Đã cập nhật style thành công!'})
    except StyleConfig.DoesNotExist:
        return Response({'status': False, 'message': 'Không tìm được style để cập nhật!'}, status=404)

@api_view(['POST'])
def delete_styles(request, id):
    try:
        StyleConfig.objects.get(id=id).delete()
        return Response({'status': True, 'message': 'Đã xóa thành công'})
    except StyleConfig.DoesNotExist:
        return Response({'status': False, 'message': 'Không tìm thấy tag'}, status=404)

# API lấy màu nền chung
@api_view(['GET', 'POST'])
def site_background(request):
    if request.method == 'GET':
        config = SiteConfig.objects.first()
        return Response({'background': config.background if config else '#fffef3'})
    elif request.method == 'POST':
        color = request.data.get('background', '#fffef3')
        config, _ = SiteConfig.objects.get_or_create(id=1)
        config.background = color
        config.save()
        return Response({'status': True, 'background': config.background})