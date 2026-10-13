from django.shortcuts import render, get_object_or_404
from django.db.models import Prefetch
from .models import DanceClass, DanceStyle, Teacher,Student,TrialRequest


def dance_class_list(request):
    dance_classes = DanceClass.objects.filter(
        is_available=True
    ).select_related("teacher").prefetch_related("dance_styles")

    context = {
        "dance_classes": dance_classes,
        "title": "Расписание занятий",
        "total_count": dance_classes.count(),
        "styles_count": DanceStyle.objects.count(),
        "has_classes": dance_classes.exists(),
    }

    return render(
        request,
        "dance_school/dance_class_list.html",
        context,
    )

def home(request):
    teachers = Teacher.objects.all()[:3]
    dance_styles = DanceStyle.objects.all()[:3]

    return render(
        request,
        "dance_school/home.html",
        {
            "teachers": teachers,
            "dance_styles": dance_styles,
            "title": "TEMPO — найди свой ритм",
        },
    )

def dance_class_detail(request, slug):
    dance_class = get_object_or_404(
        DanceClass.objects.filter(is_available=True)
        .select_related("teacher")
        .prefetch_related("dance_styles"),
        slug=slug,
    )

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        phone = request.POST.get("phone", "").strip()
        comment = request.POST.get("comment", "").strip()

        if name and phone:
            TrialRequest.objects.create(
                dance_class=dance_class,
                name=name,
                phone=phone,
                comment=comment,
            )
            return render(
                request,
                "dance_school/dance_class_detail.html",
                {
                    "dance_class": dance_class,
                    "trial_request_success": True,
                },
            )

        return render(
            request,
            "dance_school/dance_class_detail.html",
            {
                "dance_class": dance_class,
                "trial_request_error": True,
            },
        )

    return render(
        request,
        "dance_school/dance_class_detail.html",
        {"dance_class": dance_class},
    )




def teacher_list(request):
    teachers = Teacher.objects.prefetch_related(
        Prefetch(
            "dance_classes",
            queryset=DanceClass.objects.filter(
                is_available=True
            ).prefetch_related("dance_styles"),
        )
    )

    for teacher in teachers:
        styles = {}

        for dance_class in teacher.dance_classes.all():
            for style in dance_class.dance_styles.all():
                styles[style.pk] = style

        teacher.unique_styles = list(styles.values())

    context = {
        "teachers": teachers,
        "title": "Наши хореографы",
        "total_count": teachers.count(),
        "has_teachers": teachers.exists(),
    }

    return render(
        request,
        "dance_school/teacher_list.html",
        context,
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

    teacher.unique_styles = {
        style.id: style
        for dance_class in teacher.dance_classes.all()
        for style in dance_class.dance_styles.all()
    }.values()

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

def studio(request):
    return render(
        request,
        "dance_school/studio.html",
        {"title": "Залы и жизнь TEMPO"},
    )

def dance_style_list(request):
    dance_styles = DanceStyle.objects.prefetch_related("dance_classes")

    return render(
        request,
        "dance_school/dance_style_list.html",
        {"dance_styles": dance_styles},
    )

def dance_style_detail(request, slug):
    dance_style = get_object_or_404(
        DanceStyle.objects.prefetch_related("dance_classes"),
        slug=slug,
    )

    return render(
        request,
        "dance_school/dance_style_detail.html",
        {"dance_style": dance_style},
    )

def student_list(request):
    students = Student.objects.order_by("last_name", "first_name")

    context = {
        "students": students,
        "title": "Наши ученики",
        "total_count": students.count(),
        "has_students": students.exists(),
    }

    return render(
        request,
        "dance_school/student_list.html",
        context,
    )

def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)

    return render(
        request,
        "dance_school/student_detail.html",
        {
            "student": student,
            "title": f"{student.first_name} {student.last_name}",
        },
    )
# Create your views here.
