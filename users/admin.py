from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

User = get_user_model()

admin.site.unregister(Group)

class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Role', {'fields': ('role',)}),
        ('2FA Settings', {'fields': ('usr_2fa', 'usr_recovery_codes')}),
        ('Additional info', {'fields': ('usr_fecha_alta', 'usr_fecha_baja', 'usr_estado')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'usr_fecha_alta', 'usr_fecha_baja', 'usr_estado'),
        }),
    )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'role', 'usr_2fa', 'usr_estado')
    list_filter = ('is_superuser', 'is_staff', 'is_active', 'role', 'usr_2fa', 'usr_fecha_alta', 'usr_fecha_baja', 'usr_estado')
    readonly_fields = ('last_login', 'date_joined')

admin.site.register(User, UserAdmin)