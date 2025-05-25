from django.urls import path
from . import views

app_name = 'entries'  # Add namespace for consistency

urlpatterns = [
    path('', views.entry_list, name='entry_list'),
    path('create/', views.entry_create, name='entry_create'),
    path('edit/<int:asc_id>/', views.entry_edit, name='entry_edit'),
    path('delete/<int:asc_id>/', views.entry_delete, name='entry_delete'),
]