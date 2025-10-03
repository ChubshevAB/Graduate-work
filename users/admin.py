from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Кастомная админка для пользователей"""

    # Поля для отображения в списке
    list_display = ('email', 'get_full_name', 'phone', 'birth_date', 'gender', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'gender', 'groups')
    search_fields = ('email', 'first_name', 'last_name', 'phone')
    ordering = ('-created_at',)

    # Поля для формы редактирования
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 'last_name', 'birth_date', 'gender',
                'phone', 'address', 'medical_history'
            )
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    # Поля для формы добавления
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name', 'birth_date', 'gender',
                'phone', 'password1', 'password2'
            ),
        }),
    )

    # Только для чтения
    readonly_fields = ('created_at', 'updated_at', 'last_login')

    def get_full_name(self, obj):
        return obj.get_full_name()

    get_full_name.short_description = _('Full name')
    get_full_name.admin_order_field = 'last_name'
