from django.contrib import admin
from django.db.models import Count

from accounts.models import Profile
from .models import (
    Teacher,
    DanceStyle,
    DanceClass,
    TrialRequest,
    DanceGroup,
    ClassSchedule,
    GroupVideo
)

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "birth_date",
        "profile",
    )
    search_fields = (
        "first_name",
        "last_name",
        "profile__user__username",
        "profile__user__email",
    )
    list_filter = ("birth_date",)
    ordering = ("last_name",)
    autocomplete_fields = ("profile",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "profile":
            kwargs["queryset"] = Profile.objects.filter(
                role=Profile.Role.CHOREOGRAPHER
            ).select_related("user")

        return super().formfield_for_foreignkey(
            db_field, request, **kwargs
        )

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

    @admin.display(
        description="Количество занятий",
        ordering="dance_class_count",
    )
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
            "fields": ("title", "slug", "description", "image"),
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

@admin.register(DanceGroup)
class DanceGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "dance_class", "is_active")
    list_filter = ("is_active", "dance_class")
    search_fields = ("name", "dance_class__title")
    filter_horizontal = ("students",)

@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ("group", "weekday", "start_time", "end_time")
    list_filter = ("weekday", "group")
    ordering = ("weekday", "start_time")

@admin.register(TrialRequest)
class TrialRequestAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "dance_class", "created_at")
    search_fields = ("name", "phone")
    list_filter = ("dance_class", "created_at")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
@admin.register(GroupVideo)
class GroupVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "group", "created_at")
    list_filter = ("group", "created_at")
    search_fields = ("title", "description", "group__name")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)