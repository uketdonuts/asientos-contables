from django.urls import path
from . import views

app_name = 'asientos'

urlpatterns = [
    path('', views.asiento_list, name='asiento_list'),
    path('detalle/<str:id>/', views.asiento_detail, name='asiento_detail'),
    path('crear/', views.asiento_create_new, name='asiento_create'),
    path('crear-old/', views.asiento_create, name='asiento_create_old'),
    path('editar/<str:id>/', views.asiento_edit, name='asiento_edit'),
    path('eliminar/<str:id>/', views.asiento_delete, name='asiento_delete'),
    path('<str:asiento_id>/detalle/agregar/', views.add_detalle, name='add_detalle'),
    path('<str:asiento_id>/detalle/<int:detalle_id>/editar/', views.edit_detalle, name='edit_detalle'),
    path('<str:asiento_id>/detalle/<int:detalle_id>/eliminar/', views.delete_detalle, name='delete_detalle'),
    path('agregar-bulk-detalles/', views.add_detalles_bulk, name='add_detalles_bulk'),
    path('perfil/<str:perfil_id>/cuentas/', views.get_cuentas_for_perfil, name='get_cuentas_for_perfil'),
    path('secure/', views.secure_data_view, name='secure_data'),
    path('secure/dashboard/', views.secure_dashboard_view, name='secure_dashboard'),
]

# API endpoints
urlpatterns += [
    path('api/perfil/<str:perfil_id>/cuentas/', views.api_perfil_cuentas, name='api_perfil_cuentas'),
    path('api/asiento/<str:asiento_id>/detalles/', views.get_asiento_detalles, name='get_asiento_detalles'),
]