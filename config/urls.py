from django.contrib import admin
from django.urls import path, include 
from core.views import view_count




urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    # path('api/frontend-page-visit/', view_count.frontend_page_visit, name='frontend_page_visit'),

]
