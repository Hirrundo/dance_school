from django.contrib import admin
from .models import Teacher, DanceStyle, DanceClass

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "birth_date")
    search_fields = ("first_name", "last_name")
    list_filter = ("birth_date",)
    ordering = ("last_name",)

@admin.register(DanceStyle)
class DanceStyleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

@admin.register(DanceClass)
class DanceClassAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "teacher",
        "duration_minutes",
        "price",
        "is_available",
    )
    list_editable = ("price", "is_available")
    search_fields = ("title", "description")
    list_filter = ("is_available", "teacher", "dance_styles")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("teacher",)
    date_hierarchy = "created_at"

    fieldsets = (
        ("Основное", {
            "fields": ("title", "slug", "description"),
        }),
        ("Преподаватель и стили", {
            "fields": ("teacher", "dance_styles"),
        }),
        ("Параметры занятия", {
            "fields": ("duration_minutes", "capacity"),
        }),
        ("Цена и наличие", {
            "fields": ("price", "is_available"),
        }),
        ("Служебное", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
# Register your models here.
