from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    extra = 0

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "phone",
        "birth_date",
        "membership_number",
        "registration_date",
    )
    search_fields = (
        "user__username",
        "user__email",
        "phone",
        "membership_number",
    )
    readonly_fields = ("registration_date",)
# Register your models here.
