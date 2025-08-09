from django.urls import path
from . import views

app_name = 'empresas'

urlpatterns = [
    # URLs principales para empresas
    path('', views.empresa_list, name='empresa_list'),
    path('crear/', views.empresa_create, name='empresa_create'),
    path('detalle/<int:empresa_id>/', views.empresa_detail, name='empresa_detail'),
    path('editar/<int:empresa_id>/', views.empresa_edit, name='empresa_edit'),
    path('eliminar/<int:empresa_id>/', views.empresa_delete, name='empresa_delete'),
    path('toggle-active/<int:empresa_id>/', views.empresa_toggle_active, name='empresa_toggle_active'),
    
    # URLs para AJAX
    path('ajax/list/', views.empresa_ajax_list, name='empresa_ajax_list'),
]
