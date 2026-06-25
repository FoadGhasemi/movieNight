from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .forms import UserCreationForm, UserUpdateForm
from .models import User


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):

    add_form = UserCreationForm
    form = UserUpdateForm

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Profile Info', {'fields': ('bio', 'avatar', 'is_premium')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Profile Info', {'fields': ('bio', 'avatar', 'is_premium')}),
    )

    list_display = ('username', 'email', 'is_premium', 'is_staff')
    list_filter = ('is_premium',)
    search_fields = ('username', 'email')
    filter_horizontal = []

