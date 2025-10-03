from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Подключи URLs из приложения medical_lab
    path('', include('medical_lab.urls')),

    # Подключи URLs из приложения users (если создал)
    path('users/', include('users.urls')),

    # URLs для REST Framework аутентификации
    path('api-auth/', include('rest_framework.urls')),
]

# Добавь обработку статических файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
