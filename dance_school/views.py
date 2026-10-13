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
    from pathlib import Path
    from django.conf import settings

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

    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    def get_gallery_images(directory):
        directory = Path(directory)

        if not directory.exists():
            return []

        images = []

        for image_path in sorted(directory.rglob("*")):
            if image_path.is_file() and image_path.suffix.lower() in image_extensions:
                relative_path = image_path.relative_to(
                    settings.MEDIA_ROOT
                ).as_posix()

                images.append({
                    "url": (
                        f"{settings.MEDIA_URL.rstrip('/')}/"
                        f"{relative_path}"
                    ),
                    "name": image_path.stem,
                })

        return images

    media_directory = Path(settings.MEDIA_ROOT)

    all_studio_photos = get_gallery_images(
    media_directory / "studios"
)

    if all_studio_photos:
        teacher_index = teacher.pk % len(all_studio_photos)
        studio_photos = [
            all_studio_photos[teacher_index],
            all_studio_photos[
                (teacher_index + 1) % len(all_studio_photos)
            ],
    ]
    else:
        studio_photos = []
  
    teacher_style_slugs = {
        style.slug
        for style in teacher.unique_styles
    }

    class_photo_groups = []
    classes_directory = media_directory / "classes"

    if classes_directory.exists():
        for folder in sorted(classes_directory.iterdir()):
            if not folder.is_dir():
                continue

            # Название папки должно начинаться со slug стиля.
            matching_style = next(
                (
                    slug
                    for slug in teacher_style_slugs
                    if folder.name.lower().startswith(slug.lower())
                ),
                None,
            )

            if not matching_style:
                continue

            photos = get_gallery_images(folder)

            if photos:
                class_photo_groups.append({
                    "name": folder.name,
                    "photos": photos,
                })

    return render(
        request,
        "dance_school/teacher_detail.html",
        {
            "teacher": teacher,
            "studio_photos": studio_photos,
            "class_photo_groups": class_photo_groups,
        },
    )
def about(request):
    return render(
        request,
        "dance_school/about.html",
        {"title": "О танцевальной школе"},
    )

def studio(request):
    from pathlib import Path
    from django.conf import settings

    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".gif"}

    def get_images(folder):
        directory = Path(settings.MEDIA_ROOT) / folder

        if not directory.exists():
            return []

        images = []

        for path in sorted(directory.rglob("*")):
            if path.is_file() and path.suffix.lower() in image_extensions:
                relative_path = path.relative_to(settings.MEDIA_ROOT).as_posix()

                images.append({
                    "url": settings.MEDIA_URL + relative_path,
                    "name": path.stem.replace("_", " ").replace("-", " "),
                })

        return images

    studio_photos = get_images("studios")

    classes_directory = Path(settings.MEDIA_ROOT) / "classes"
    class_photo_groups = []

    if classes_directory.exists():
        for folder in sorted(classes_directory.iterdir()):
            if folder.is_dir():
                photos = get_images(folder.relative_to(settings.MEDIA_ROOT).as_posix())

                if photos:
                    class_photo_groups.append({
                        "name": folder.name.replace("-", " ").replace("_", " "),
                        "photos": photos,
                    })

    all_gallery_photos = [
        {**photo, "category": "Наши залы"}
        for photo in studio_photos
    ]

    for group in class_photo_groups:
        all_gallery_photos.extend(
            {**photo, "category": group["name"]}
            for photo in group["photos"]
        )

    return render(
        request,
        "dance_school/studio.html",
        {
            "title": "Залы и жизнь TEMPO",
            "studio_photos": studio_photos,
            "class_photo_groups": class_photo_groups,
            "all_gallery_photos": all_gallery_photos,
        },
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
