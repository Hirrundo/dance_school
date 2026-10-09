from django.contrib import admin
from django.db.models import Count

from .models import Teacher, DanceStyle, DanceClass

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "birth_date")
    search_fields = ("first_name", "last_name")
    list_filter = ("birth_date",)
    ordering = ("last_name",)

@admin.register(DanceStyle)
class DanceStyleAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "classes_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(
            dance_class_count=Count("dance_classes")
        )

    @admin.display(description="Количество занятий", ordering="dance_class_count")
    def classes_count(self, obj):
        return obj.dance_class_count

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

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("teacher").prefetch_related(
            "dance_styles"
        )

    fieldsets = (
        ("Основное", {
            "fields": ("title", "slug", "description"),
        }),
        ("Хореограф и стили", {
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