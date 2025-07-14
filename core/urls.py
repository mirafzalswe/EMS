# core/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Custom admin dashboard URL
    path('admin/dashboard/', include('users.urls')),
    
    # Django admin URLs
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API URLs для модулей системы
    path('api/users/', include('users.urls')),
    path('', include('users.urls')),
    path('api/schools/', include('schools.urls')),
    path('api/courses/', include('courses.urls')),
    path('scheduling/', include('scheduling.urls')),
    path('api/attendance/', include('attendance.urls')),
    path('assignment/', include('assignments.urls')),
    path('api/finance/', include('finance.urls')),
    path('', include('leads.urls')),
    path('api/communication/', include('communication.urls')),
    path('', include('motivation.urls')),
    path('analytics/', include('analytics.urls')),
]

# Добавляем URL для медиа файлов в режиме отладки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)