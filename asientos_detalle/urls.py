from django.urls import path
from . import views

app_name = 'asientos_detalle'

urlpatterns = [
    # URLs para Detalles de Asientos
    path('', views.detalle_list, name='detalle_list'),
    path('crear/', views.detalle_create, name='detalle_create'),
    path('editar/<int:id>/', views.detalle_edit, name='detalle_edit'),
    path('eliminar/<int:id>/', views.detalle_delete, name='detalle_delete'),
    path('detalle/<int:id>/', views.detalle_detail, name='detalle_detail'),
] 