from django.urls import path
from . import views

app_name = 'plan_cuentas'

urlpatterns = [
    # URLs para Planes de Cuentas
    path('', views.plan_cuenta_list, name='plan_cuenta_list'),
    path('crear/', views.plan_cuenta_create, name='plan_cuenta_create'),
    path('editar/<int:id>/', views.plan_cuenta_edit, name='plan_cuenta_edit'),
    path('detalle/<int:id>/', views.plan_cuenta_detail, name='plan_cuenta_detail'),
    path('eliminar/<int:id>/', views.plan_cuenta_delete, name='plan_cuenta_delete'),
    
    # URLs para Cuentas Contables
    path('cuentas/', views.cuenta_list, name='cuenta_list'),
    path('cuentas/crear/', views.cuenta_create, name='cuenta_create'),
    path('cuentas/editar/<int:id>/', views.cuenta_edit, name='cuenta_edit'),
    path('cuentas/detalle/<int:id>/', views.cuenta_detail, name='cuenta_detail'),
    path('cuentas/eliminar/<int:id>/', views.cuenta_delete, name='cuenta_delete'),
    
    # URLs para AJAX
    path('ajax/cuentas-por-empresa/', views.get_cuentas_by_empresa, name='get_cuentas_by_empresa'),
    path('ajax/cuentas-por-plan/<int:plan_id>/', views.cuentas_por_plan_ajax, name='cuentas_por_plan_ajax'),
    path('ajax/cuentas-madre/', views.get_cuentas_madre_ajax, name='get_cuentas_madre_ajax'),
]