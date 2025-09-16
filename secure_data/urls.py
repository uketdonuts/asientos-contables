from django.urls import path
from . import views

app_name = 'secure_data'

urlpatterns = [
    path('', views.secure_access_view, name='access'),
    path('matrix/', views.matrix_view, name='matrix'),
    path('matrix/edit/', views.matrix_edit_view, name='matrix_edit'),
    path('matrix/load-cells/', views.load_cells, name='load_cells'),
    path('matrix/download/', views.matrix_download_view, name='matrix_download'),
    path('matrix/upload/', views.matrix_upload_view, name='matrix_upload'),
    path('logout/', views.logout_secure, name='logout_secure'),
    # URLs adicionales que usa matrix.html
    path('api/update-cell/', views.matrix_edit_view, name='update_cell'),
    path('api/load-cells/', views.load_cells, name='api_load_cells'),
    path('api/save-matrix/', views.matrix_edit_view, name='save_matrix'),
    path('api/logout-beacon/', views.logout_secure, name='logout_beacon'),
]
