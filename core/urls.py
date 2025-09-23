from django.urls import path,re_path
from .views import view_count,view_sanpham,view_admin,view_link,view_location,view_styles,view_teams_report
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'

urlpatterns = [
path('', view_count.homepage, name='homepage'),
path('book/<int:book_id>/', view_count.coloring_book_detail, name='book_detail'),
path('api/visits/', view_count.get_visit_count_api, name='visit_api'),
path('api/visits/track/', view_count.track_visit, name='track_visit'),
path('api/frontend-page-visit/', view_count.frontend_page_visit, name='frontend_page_visit'),
path('location/', view_location.get_location, name='get_location'),




path('products/data/', view_sanpham.product_data, name='product_data'),
path('products/create/', view_sanpham.create_san_pham, name='create_san_pham'),
path('products/update/<int:id>/', view_sanpham.update_san_pham, name='update_san_pham'),
path('products/delete/<int:id>/', view_sanpham.delete_san_pham, name='delete_san_pham'),
path('products/change-status/', view_sanpham.change_san_pham, name='change_san_pham'),
path('products/update/order/', view_sanpham.update_product_order, name='update_product_order'),







path('products/type/<int:id>/', view_sanpham.product_type, name='product_list_by_type'),
path('products/type/list/', view_sanpham.product_data_type, name='product_list_all'),
path('products/type/create/', view_sanpham.create_loai_san_pham, name='create_loai_san_pham'),
path('products/type/update/<int:id>/', view_sanpham.update_loai_san_pham, name='update_loai_san_pham'),
path('products/type/delete/<int:id>/', view_sanpham.delete_loai_san_pham, name='delete_loai_san_pham'),
path('products/type/change-status/', view_sanpham.change_loai_san_pham, name='change_loai_san_pham'),
path("san-pham/<int:pk>/click/", view_sanpham.tang_luot_xem, name="tang_luot_xem"),
path("san-pham/top/", view_sanpham.top_san_pham, name="top_san_pham"),




    


path('api/admin/login/',view_admin.admin_login,name='admin_login'),
path('check_login/',view_admin.check_login),
path('logout/',view_admin.logout),
path('logout-all/',view_admin.logout_all),



path('api/links/', view_link.get_links_api, name='get_links'),
path('api/links/list/', view_link.get_list_links, name='get_list_links'),
path('api/links/list/data/', view_link.get_list_links_data, name='get_list_links_data'),
path('api/link/create/',view_link.create_link,name='create_link'),
path('api/link/delete/<int:id>/',view_link.delete_link,name='delete_link'),
path('api/link/update/<int:id>/',view_link.update_link,name='update_link'),
path('api/link/change-status/', view_link.change_link, name='change_link'),
path('api/links/<int:pk>/click/', view_link.tang_luot_click, name='tang_luot_click'),
path('api/links/top/', view_link.top_link, name='top_link'),
path('api/links/click-stats/', view_link.thong_ke_luot_click, name='thong_ke_luot_click'),



path('api/styles/list/', view_styles.get_list_styles, name='get_list_styles'),
path('api/styles/list/data/', view_styles.get_data_styles, name='get_list_styles'),
path('api/styles/create/',view_styles.create_styles,name='create_styles'),
path('api/styles/delete/<int:id>/',view_styles.delete_styles,name='delete_styles'),
path('api/styles/update/<int:id>/',view_styles.update_styles,name='update_styles'),
path('api/styles/background/',view_styles.site_background,name='update_styles'),

# Teams Report URLs
path('api/teams/send-report/', view_teams_report.send_daily_report, name='send_daily_report'),
path('api/teams/preview-report/', view_teams_report.get_report_preview, name='preview_report'),
path('api/teams/send-custom-report/', view_teams_report.send_custom_report, name='send_custom_report'),


    



]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



