from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from core.models.KhachHang import KhachHang
from django.contrib.auth import authenticate
from rest_framework.decorators import authentication_classes,permission_classes
from rest_framework.authentication import SessionAuthentication,TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from rest_framework.authtoken.models import Token
# python manage.py shell
# from core.models.KhachHang import KhachHang
# u = KhachHang.objects.get(email='Admin@gmail.com')
# u.set_password('Newmoon123')
# u.save()
@csrf_exempt
@api_view(['POST'])
def admin_login(request):
    email = request.data.get('email','').lower()  # chuyển về chữ thường
    password = request.data.get('password')
    try:
        user = KhachHang.objects.get(email=email)
        if user.check_password(password):
            if not user.is_active:
                return Response({
                    'message': 'Tài khoản của bạn chưa được kích hoạt!',
                    'status': 2
                })
            elif getattr(user, 'is_block', False):
                return Response({
                    'message': 'Tài khoản của bạn đã bị khóa!',
                    'status': 0
                })
            else:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Đã đăng nhập thành công!',
                    'status': 1,
                    'chia_khoa': token.key,
                    'ten_kh': user.ho_va_ten
                })
        else:
            return Response({
                'message': 'Tài khoản hoặc mật khẩu không đúng!',
                'status': 0
            }, status=status.HTTP_401_UNAUTHORIZED)
    except KhachHang.DoesNotExist:
        return Response({
            'message': 'Tài khoản hoặc mật khẩu không đúng!',
            'status': 0
        }, status=status.HTTP_401_UNAUTHORIZED)
        

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
def check_login(request):
    user = request.user
    if user and user.is_authenticated:
        return Response({
            'status': True,
            'message': 'Đã được đăng nhập',
            'user': getattr(user, 'ho_va_ten', )
        })
    else:
        return Response({
            'status': False,
            'message': 'Mời bạn đăng nhập'
        })
@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        # Xóa token hiện tại
        if hasattr(request.user, 'auth_token'):
            request.user.auth_token.delete()
            return JsonResponse({'status': True, 'message': 'Bạn đã đăng xuất thành công!'}, status=200)
        else:
            return JsonResponse({'status': False, 'message': 'Không tìm thấy token!'}, status=400)
    except Exception as e:
        return JsonResponse({'status': False, 'message': f'Đăng xuất thất bại: {str(e)}'}, status=400)

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def logout_all(request):
    try:
        # Xóa tất cả token của user
        Token.objects.filter(user=request.user).delete()
        return JsonResponse({'status': True, 'message': 'Bạn đã đăng xuất tất cả thành công!'}, status=200)
    except Exception as e:
        return JsonResponse({'status': False, 'message': f'Đăng xuất tất cả thất bại: {str(e)}'}, status=400)
           


