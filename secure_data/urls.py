from django.urls import path
from . import views

app_name = 'secure_data'

urlpatterns = [
    # Ruta ultra-secreta - Solo accesible conociendo la URL exacta
    path('', views.secure_access_view, name='access'),
    path('matrix-view/', views.matrix_view, name='matrix_view'),
    path('api/update-cell/', views.update_cell, name='update_cell'),
    path('api/save-matrix/', views.save_matrix, name='save_matrix'),
    path('api/load-cells/', views.load_cells, name='load_cells'),
    path('logout-secure/', views.logout_secure, name='logout_secure'),
    path('api/logout-beacon/', views.logout_secure, name='logout_beacon'),  # Para sendBeacon
    path('matrix/undo/', views.matrix_undo, name='matrix_undo'),
    path('matrix/redo/', views.matrix_redo, name='matrix_redo'),
    path('matrix/exit/', views.matrix_exit, name='matrix_exit'),
]
