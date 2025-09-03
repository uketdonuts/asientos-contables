from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('empresas/', include('empresas.urls')),
    path('asientos/', include('asientos.urls')),
    path('asientos_detalle/', include('asientos_detalle.urls')),
    path('perfiles/', include('perfiles.urls')),
    path('plan_cuentas/', include('plan_cuentas.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('two_factor/', include('two_factor_auth.urls')),
    # Ruta que genera URL segura y envía email
    path('secure/', views.secure_access_handler, name='secure_access_handler'),
    # Rutas ultra-secretas con códigos dinámicos
    path('secure/<str:access_code>/', include('secure_data.urls')),
    # Endpoint de prueba de correos
    path('test-email/', views.test_email_endpoint, name='test_email'),
]

# Configuración para servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)