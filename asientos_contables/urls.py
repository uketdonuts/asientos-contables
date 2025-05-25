from django.contrib import admin
from django.urls import path, include
from entries import views as entries_views
from django.contrib.auth import views as auth_views
from asientos import views as asientos_views

urlpatterns = [
    path('', asientos_views.asiento_list, name='home'),  # Change home page to asientos list
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('entries/', include('entries.urls')),
    path('asientos/', include('asientos.urls')),
    path('perfiles/', include('perfiles.urls')),
    path('plan_cuentas/', include('plan_cuentas.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('two_factor/', include('two_factor_auth.urls')),
]