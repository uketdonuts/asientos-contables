from django.urls import path
from . import views

app_name = 'plan_cuentas'

urlpatterns = [
    path('', views.plan_cuenta_list, name='plan_cuenta_list'),
    path('crear/', views.plan_cuenta_create, name='plan_cuenta_create'),
    path('<int:id>/', views.plan_cuenta_detail, name='plan_cuenta_detail'), # New path for detail view
    path('editar/<int:id>/', views.plan_cuenta_edit, name='plan_cuenta_edit'),
    path('eliminar/<int:id>/', views.plan_cuenta_delete, name='plan_cuenta_delete'),
]