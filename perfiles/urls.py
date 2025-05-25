from django.urls import path
from . import views

app_name = 'perfiles'

urlpatterns = [
    path('', views.perfil_list, name='perfil_list'),
    path('crear/', views.perfil_create, name='perfil_create'),
    path('editar/<str:id>/', views.perfil_edit, name='perfil_edit'),
    path('eliminar/<str:id>/', views.perfil_delete, name='perfil_delete'),
]