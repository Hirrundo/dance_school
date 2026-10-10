from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import DanceClass, DanceStyle, Teacher


def dance_class_list(request):
    dance_classes = DanceClass.objects.filter(
        is_available=True
    ).select_related("teacher").prefetch_related("dance_styles")

    context = {
        "dance_classes": dance_classes,
        "title": "Расписание занятий",
        "total_count": dance_classes.count(),
        "has_classes": dance_classes.exists(),
    }

    return render(
        request,
        "dance_school/dance_class_list.html",
        context,
    )

def dance_class_detail(request, slug):
    dance_class = get_object_or_404(
        DanceClass.objects.filter(is_available=True)
        .select_related("teacher")
        .prefetch_related("dance_styles"),
        slug=slug,
    )

    return render(
        request,
        "dance_school/dance_class_detail.html",
        {"dance_class": dance_class},
    )

def teacher_list(request):
    teachers = Teacher.objects.all().prefetch_related("dance_classes")
    context = {
        "teachers": teachers,
        "title": "Наши хореографы",
        "total_count": teachers.count(),
        "has_teachers": teachers.exists(),
    }
    return render(
        request,
        "dance_school/teacher_list.html",context
    )

def teacher_detail(request, pk):
    teacher = get_object_or_404(
        Teacher.objects.prefetch_related(
            Prefetch(
                "dance_classes",
                queryset=DanceClass.objects.filter(
                    is_available=True
                ).prefetch_related("dance_styles"),
            )
        ),
        pk=pk,
    )

    return render(
        request,
        "dance_school/teacher_detail.html",
        {"teacher": teacher},
    )
def about(request):
    return render(
        request,
        "dance_school/about.html",
        {"title": "О танцевальной школе"},
    )

def dance_style_list(request):
    dance_styles = DanceStyle.objects.prefetch_related("dance_classes")

    return render(
        request,
        "dance_school/dance_style_list.html",
        {"dance_styles": dance_styles},
    )
# Create your views here.
