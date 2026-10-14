
from functools import wraps
import mimetypes
from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse,JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
from .models import Profile
from dance_school.models import (
    DanceClass,
    DanceStyle,
    Teacher,
    TrialRequest,
    DanceGroup,
    ClassSchedule,
    GroupVideo,
    StudioRoom,
    RoomBooking,
)

def role_required(required_role):
    def decorator(view_func):
        view_func
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            try:
                role = user.profile.role
            except Profile.DoesNotExist:
                role = None

            if required_role == Profile.Role.ADMIN:
                if (
                    role != Profile.Role.ADMIN
                    and not user.is_staff
                    and not user.is_superuser
                ):
                    raise PermissionDenied
            elif role != required_role:
                raise PermissionDenied

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator

def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            try:
                role = user.profile.role
            except Profile.DoesNotExist:
                role = None

            if role == Profile.Role.STUDENT:
                login(request, user)
                return redirect("student_dashboard")

            if role == Profile.Role.CHOREOGRAPHER:
                login(request, user)
                return redirect("choreographer_dashboard")

            if (
                role == Profile.Role.ADMIN
                or user.is_staff
                or user.is_superuser
            ):
                login(request, user)
                return redirect("admin_dashboard")

            error = "Для аккаунта не назначена роль."
        else:
            error = "Неверный логин или пароль."

    return render(
        request,
        "accounts/login.html",
        {"error": error},
    )

@role_required(Profile.Role.STUDENT)
def student_dashboard(request):
    profile = request.user.profile

    groups = list(
        profile.dance_groups
        .filter(is_active=True)
        .select_related("dance_class", "dance_class__teacher")
        .prefetch_related("schedule_entries")
    )

    videos = (
        GroupVideo.objects.filter(
            group__students=profile,
            group__is_active=True,
        )
        .select_related("group", "group__dance_class")
        .distinct()
    )

    now = timezone.localtime()
    today = now.date()

    weekday_names = {
        0: "Понедельник",
        1: "Вторник",
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
        6: "Воскресенье",
    }

    schedule_by_day = [
        {
            "name": weekday_names[day],
            "lessons": [],
        }
        for day in range(7)
    ]

    upcoming_lessons = []

    for group in groups:
        for entry in group.schedule_entries.all():
            lesson = {
                "group": group,
                "entry": entry,
                "teacher": group.dance_class.teacher,
            }

            schedule_by_day[entry.weekday]["lessons"].append(lesson)

            days_ahead = (entry.weekday - today.weekday()) % 7
            lesson_date = today + timedelta(days=days_ahead)

            lesson_start = timezone.make_aware(
                datetime.combine(lesson_date, entry.start_time),
                timezone.get_current_timezone(),
            )

            if lesson_start <= now:
                lesson_date += timedelta(days=7)
                lesson_start = timezone.make_aware(
                    datetime.combine(lesson_date, entry.start_time),
                    timezone.get_current_timezone(),
                )

            upcoming_lessons.append({
                **lesson,
                "date": lesson_date,
                "datetime": lesson_start,
            })

    for day in schedule_by_day:
        day["lessons"].sort(
            key=lambda item: item["entry"].start_time
        )

    schedule_by_day = [
        day for day in schedule_by_day
        if day["lessons"]
    ]

    upcoming_lessons.sort(key=lambda item: item["datetime"])

    next_lesson = (
        upcoming_lessons[0]
        if upcoming_lessons
        else None
    )

    return render(
        request,
        "accounts/student_dashboard.html",
        {
            "groups": groups,
            "videos": videos,
            "schedule_by_day": schedule_by_day,
            "next_lesson": next_lesson,
        },
    )


@login_required
def group_video_view(request, video_id):
    video = get_object_or_404(
        GroupVideo.objects.select_related(
            "group",
            "group__dance_class",
            "group__dance_class__teacher",
        ),
        pk=video_id,
    )

    user = request.user
    allowed = user.is_staff or user.is_superuser

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        profile = None

    if profile:
        if profile.role == Profile.Role.ADMIN:
            allowed = True

        elif (
            profile.role == Profile.Role.STUDENT
            and video.group.is_active
            and video.group.students.filter(pk=profile.pk).exists()
        ):
            allowed = True

        elif (
            profile.role == Profile.Role.CHOREOGRAPHER
            and video.group.dance_class.teacher.profile_id == profile.pk
        ):
            allowed = True

    if not allowed:
        raise PermissionDenied

    content_type, _ = mimetypes.guess_type(video.video.name)

    return FileResponse(
        video.video.open("rb"),
        content_type=content_type or "application/octet-stream",
        filename=video.video.name.split("/")[-1],
    )

@role_required(Profile.Role.CHOREOGRAPHER)
def choreographer_dashboard(request):
    profile = request.user.profile

    try:
        teacher = profile.teacher_record
    except Exception:
        teacher = None

    classes = (
        DanceClass.objects.filter(teacher=teacher)
        .prefetch_related(
            "dance_styles",
            "groups__schedule_entries",
        )
        if teacher
        else DanceClass.objects.none()
    )

    now = timezone.localtime()
    today = now.date()

    weekday_names = {
        0: "Понедельник",
        1: "Вторник",
        2: "Среда",
        3: "Четверг",
        4: "Пятница",
        5: "Суббота",
        6: "Воскресенье",
    }

    schedule_by_day = [
        {"name": weekday_names[day], "lessons": []}
        for day in range(7)
    ]
    upcoming_lessons = []

    for dance_class in classes:
        for group in dance_class.groups.filter(is_active=True):
            for entry in group.schedule_entries.all():
                lesson = {
                    "group": group,
                    "entry": entry,
                    "dance_class": dance_class,
                }

                schedule_by_day[entry.weekday]["lessons"].append(lesson)

                days_ahead = (entry.weekday - today.weekday()) % 7
                lesson_date = today + timedelta(days=days_ahead)

                lesson_start = timezone.make_aware(
                    datetime.combine(lesson_date, entry.start_time),
                    timezone.get_current_timezone(),
                )

                if lesson_start <= now:
                    lesson_date += timedelta(days=7)
                    lesson_start = timezone.make_aware(
                        datetime.combine(lesson_date, entry.start_time),
                        timezone.get_current_timezone(),
                    )

                upcoming_lessons.append({
                    **lesson,
                    "date": lesson_date,
                    "datetime": lesson_start,
                })

    for day in schedule_by_day:
        day["lessons"].sort(
            key=lambda item: item["entry"].start_time
        )

    schedule_by_day = [
        day for day in schedule_by_day
        if day["lessons"]
    ]

    upcoming_lessons.sort(key=lambda item: item["datetime"])
    next_lesson = upcoming_lessons[0] if upcoming_lessons else None

    worked_hours = ""
    salary = None
    salary_error = None

    if request.method == "POST" and "worked_hours" in request.POST:
        try:
            worked_hours = request.POST.get("worked_hours", "").strip()
            hours = Decimal(worked_hours.replace(",", "."))

            if not hours.is_finite() or hours < 0 or hours > Decimal("744"):
                raise InvalidOperation

            salary = hours * profile.hourly_rate

        except (InvalidOperation, ValueError):
            salary_error = "Введи корректное количество часов от 0 до 744."

    rooms = StudioRoom.objects.filter(
        is_available=True
    ).prefetch_related("bookings")

    room_bookings = (
        RoomBooking.objects.filter(teacher=teacher)
        .select_related("room")
        if teacher
        else RoomBooking.objects.none()
    )

    response = render(
        request,
        "accounts/choreographer_dashboard.html",
        {
            "teacher": teacher,
            "classes": classes,
            "schedule_by_day": schedule_by_day,
            "next_lesson": next_lesson,
            "hourly_rate": profile.hourly_rate,
            "worked_hours": worked_hours,
            "salary": salary,
            "salary_error": salary_error,
            "rooms": rooms,
            "room_bookings": room_bookings,
        },
    )

    if request.method == "POST" and "worked_hours" in request.POST:
        response["Content-Location"] = "#salary"

    return response
@role_required(Profile.Role.ADMIN)
def admin_dashboard(request):
    if request.method == "POST":
        action = request.POST.get("action")
        object_id = request.POST.get("object_id")
        new_status = request.POST.get("status")

        try:
            if action == "trial_request":
                trial_request = get_object_or_404(
                    TrialRequest,
                    pk=object_id,
                )

                if new_status not in (
                    TrialRequest.Status.CONFIRMED,
                    TrialRequest.Status.REJECTED,
                ):
                    return JsonResponse({
                        "success": False,
                        "message": "Недопустимый статус заявки.",
                    }, status=400)

                trial_request.status = new_status
                trial_request.save(update_fields=["status"])

                message = (
                    "Заявка подтверждена."
                    if new_status == TrialRequest.Status.CONFIRMED
                    else "Заявка отклонена."
                )

            elif action == "room_booking":
                booking = get_object_or_404(
                    RoomBooking,
                    pk=object_id,
                )

                if new_status not in (
                    RoomBooking.Status.CONFIRMED,
                    RoomBooking.Status.REJECTED,
                ):
                    return JsonResponse({
                        "success": False,
                        "message": "Недопустимый статус бронирования.",
                    }, status=400)

                booking.status = new_status
                booking.save(update_fields=["status"])

                message = (
                    "Бронирование подтверждено."
                    if new_status == RoomBooking.Status.CONFIRMED
                    else "Бронирование отклонено."
                )

            else:
                return JsonResponse({
                    "success": False,
                    "message": "Неизвестное действие.",
                }, status=400)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "message": message,
                    "status": new_status,
                    "status_label": (
                        trial_request.get_status_display()
                        if action == "trial_request"
                        else booking.get_status_display()
                    ),
                    "object_id": object_id,
                })

            return redirect("admin_dashboard")

        except (ValueError, TypeError):
            return JsonResponse({
                "success": False,
                "message": "Не удалось обработать запрос.",
            }, status=400)

    context = {
        "students_count": Profile.objects.filter(
            role=Profile.Role.STUDENT
        ).count(),
        "choreographers_count": Teacher.objects.count(),
        "classes_count": DanceClass.objects.count(),
        "styles_count": DanceStyle.objects.count(),
        "groups_count": DanceGroup.objects.count(),
        "active_groups_count": DanceGroup.objects.filter(
            is_active=True
        ).count(),
        "schedules_count": ClassSchedule.objects.count(),
        "trial_requests_count": TrialRequest.objects.count(),
        "pending_trial_requests_count": TrialRequest.objects.filter(
            status=TrialRequest.Status.PENDING
        ).count(),
        "rooms_count": StudioRoom.objects.count(),
        "pending_bookings_count": RoomBooking.objects.filter(
            status=RoomBooking.Status.PENDING
        ).count(),
        "confirmed_bookings_count": RoomBooking.objects.filter(
            status=RoomBooking.Status.CONFIRMED
        ).count(),
        "recent_trial_requests": TrialRequest.objects.select_related(
            "dance_class"
        ).order_by("-created_at")[:5],
        "recent_bookings": RoomBooking.objects.select_related(
            "room",
            "teacher",
        ).order_by("-created_at")[:5],
        "videos_count": GroupVideo.objects.count(),
    }

    return render(
        request,
        "accounts/admin_dashboard.html",
        context,
    )
def logout_view(request):
    logout(request)
    return redirect("login")

@role_required(Profile.Role.ADMIN)
def admin_accounts(request):
    search = request.GET.get("search", "").strip()
    error = None
    form_data = {}

    if request.method == "POST" and "toggle_active" in request.POST:
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)

        if user.is_superuser:
            error = "Нельзя заблокировать суперпользователя."
        elif user == request.user:
            error = "Нельзя заблокировать собственный аккаунт."
        else:
            user.is_active = not user.is_active
            user.save(update_fields=["is_active"])
            return redirect("admin_accounts")

    if request.method == "POST" and "edit_account" in request.POST:
        user_id = request.POST.get("user_id")
        user = get_object_or_404(User, id=user_id)

        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "")

        valid_roles = {
            choice[0] for choice in Profile.Role.choices
        }

        if user.is_superuser:
            error = "Нельзя редактировать суперпользователя."

        elif not username:
            error = "Логин не может быть пустым."

        elif User.objects.filter(
            username=username
        ).exclude(id=user.id).exists():
            error = "Пользователь с таким логином уже существует."

        elif role not in valid_roles:
            error = "Выбери корректную роль."

        elif password and len(password) < 8:
            error = "Новый пароль должен содержать минимум 8 символов."

        elif user == request.user and role != Profile.Role.ADMIN:
            error = "Нельзя изменить собственную роль администратора."

        else:
            try:
                with transaction.atomic():
                    user.username = username
                    user.first_name = first_name
                    user.last_name = last_name
                    user.email = email

                    if password:
                        user.set_password(password)

                    user.save()

                    profile, created = Profile.objects.get_or_create(
                        user=user,
                        defaults={"role": role},
                    )

                    if not created and profile.role != role:
                        profile.role = role
                        profile.save(update_fields=["role"])

                return redirect("admin_accounts")

            except Exception:
                error = "Не удалось сохранить изменения аккаунта."

    if request.method == "POST" and "create_account" in request.POST:
        username = request.POST.get("username", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        role = request.POST.get("role", "")

        form_data = {
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
        }

        valid_roles = {
            choice[0] for choice in Profile.Role.choices
        }

        if not username or not password:
            error = "Заполни логин и пароль."

        elif len(password) < 8:
            error = "Пароль должен содержать минимум 8 символов."

        elif User.objects.filter(username=username).exists():
            error = "Пользователь с таким логином уже существует."

        elif role not in valid_roles:
            error = "Выбери корректную роль."

        else:
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=username,
                        password=password,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                    )

                    profile, created = Profile.objects.get_or_create(
                        user=user,
                        defaults={"role": role},
                    )

                    if not created:
                        profile.role = role
                        profile.save(update_fields=["role"])

                return redirect("/accounts/admin/accounts/?created=1")

            except Exception:
                error = "Не удалось создать аккаунт. Проверь введённые данные."

    users = User.objects.select_related("profile").order_by("username")

    if search:
        users = users.filter(
            Q(username__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
            | Q(email__icontains=search)
        )

    return render(
        request,
        "accounts/admin_accounts.html",
        {
            "users": users,
            "search": search,
            "users_count": User.objects.count(),
            "error": error,
            "success": request.GET.get("created") == "1",
            "form_data": form_data,
        },
    )

@role_required(Profile.Role.ADMIN)
def admin_classes(request):
    error = None

    if request.method == "POST":
        action = (
            "edit_class" if "edit_class" in request.POST else
            "add_student" if "add_student" in request.POST else
            "remove_student" if "remove_student" in request.POST else
            "save_schedule" if "save_schedule" in request.POST else
            "add_video" if "add_video" in request.POST else
            None
        )

        try:
            if action == "edit_class":
                dance_class = get_object_or_404(
                    DanceClass,
                    id=request.POST.get("class_id"),
                )
                teacher = get_object_or_404(
                    Teacher,
                    id=request.POST.get("teacher"),
                )
                price = Decimal(request.POST.get("price", "").strip())

                if not price.is_finite() or price < 0:
                    raise ValueError

                dance_class.price = price
                dance_class.teacher = teacher
                dance_class.save(
                    update_fields=["price", "teacher", "updated_at"]
                )

                message = "Занятие обновлено."

            elif action in ("add_student", "remove_student"):
                group = get_object_or_404(
                    DanceGroup,
                    id=request.POST.get("group_id"),
                )
                student = get_object_or_404(
                    Profile,
                    id=request.POST.get("student_id"),
                )

                if action == "add_student":
                    group.students.add(student)
                    message = "Ученик добавлен в группу."
                else:
                    group.students.remove(student)
                    message = "Ученик удалён из группы."

                return JsonResponse({
                    "success": True,
                    "message": message,
                    "group_id": group.id,
                    "student_id": student.id,
                    "student_count": group.students.count(),
                })

            elif action == "save_schedule":
                group = get_object_or_404(
                    DanceGroup,
                    id=request.POST.get("group_id"),
                )

                schedule_id = request.POST.get("schedule_id")
                if schedule_id:
                    schedule = get_object_or_404(
                        ClassSchedule,
                        id=schedule_id,
                        group=group,
                    )
                else:
                    schedule = ClassSchedule(group=group)

                weekday = int(request.POST.get("weekday"))
                start_time = datetime.strptime(
                    request.POST.get("start_time", ""),
                    "%H:%M",
                ).time()
                end_time = datetime.strptime(
                    request.POST.get("end_time", ""),
                    "%H:%M",
                ).time()

                if weekday not in dict(ClassSchedule.Weekday.choices):
                    raise ValueError

                if end_time <= start_time:
                    return JsonResponse({
                        "success": False,
                        "message": "Время окончания должно быть позже начала.",
                    }, status=400)

                schedule.weekday = weekday
                schedule.start_time = start_time
                schedule.end_time = end_time
                schedule.save()

                return JsonResponse({
                    "success": True,
                    "message": "Расписание сохранено.",
                    "schedule_id": schedule.id,
                    "group_id": group.id,
                    "weekday": schedule.get_weekday_display(),
                    "start_time": schedule.start_time.strftime("%H:%M"),

                    "end_time": schedule.end_time.strftime("%H:%M"),
                })

            elif action == "add_video":
                group = get_object_or_404(
                    DanceGroup,
                    id=request.POST.get("group_id"),
                )
                title = request.POST.get("title", "").strip()
                video_file = request.FILES.get("video")

                if not title or not video_file:
                    return JsonResponse({
                        "success": False,
                        "message": "Укажи название и выбери видеофайл.",
                    }, status=400)

                video = GroupVideo.objects.create(
                    group=group,
                    title=title,
                    description=request.POST.get("description", "").strip(),
                    video=video_file,
                )

                return JsonResponse({
                    "success": True,
                    "message": "Видео добавлено.",
                    "video_id": video.id,
                    "title": video.title,
                    "group": group.name,
                    "description": video.description,
                })

            else:
                return JsonResponse({
                    "success": False,
                    "message": "Неизвестное действие.",
                }, status=400)

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "success": True,
                    "message": message,
                })

            return redirect("admin_classes")

        except (InvalidOperation, ValueError, TypeError):
            error = "Проверь введённые данные."
        except (DanceClass.DoesNotExist, Teacher.DoesNotExist):
            error = "Занятие или хореограф не найдены."

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({
                "success": False,
                "message": error,
            }, status=400)

    classes = (
        DanceClass.objects
        .select_related("teacher")
        .prefetch_related("dance_styles", "groups")
        .order_by("title")
    )

    groups = (
        DanceGroup.objects
        .select_related("dance_class")
        .prefetch_related("students", "schedule_entries")
        .order_by("name")
    )

    return render(
        request,
        "accounts/admin_classes.html",
        {
            "classes": classes,
            "groups": groups,
            "students": Profile.objects.select_related(
                "user"
            ).order_by("user__username"),
            "styles": DanceStyle.objects.order_by("name"),
            "teachers": Teacher.objects.order_by("last_name"),
            "schedules": ClassSchedule.objects.select_related(
                "group",
                "group__dance_class",
            ),
            "videos": GroupVideo.objects.select_related("group"),
            "error": error,
        },
    )
@role_required(Profile.Role.CHOREOGRAPHER)
def room_booking(request):
    profile = request.user.profile

    try:
        teacher = profile.teacher_record
    except Teacher.DoesNotExist:
        teacher = None

    rooms = StudioRoom.objects.filter(is_available=True)
    error = None
    success = False

    if request.method == "POST":
        room_id = request.POST.get("room")
        date = request.POST.get("date")
        start_time = request.POST.get("start_time")
        end_time = request.POST.get("end_time")
        purpose = request.POST.get("purpose", "").strip()

        if not teacher:
            error = "Твой аккаунт не связан с профилем хореографа."

        elif not all((room_id, date, start_time, end_time, purpose)):
            error = "Заполни все поля бронирования."

        else:
            try:
                room = rooms.get(pk=room_id)
                booking_date = datetime.strptime(date, "%Y-%m-%d").date()
                start = datetime.strptime(start_time, "%H:%M").time()
                end = datetime.strptime(end_time, "%H:%M").time()

                if booking_date < timezone.localdate():
                    error = "Нельзя бронировать зал на прошедшую дату."

                elif end <= start:
                    error = "Время окончания должно быть позже начала."

                else:
                    conflict = RoomBooking.objects.filter(
                        room=room,
                        date=booking_date,
                        status__in=[
                            RoomBooking.Status.PENDING,
                            RoomBooking.Status.CONFIRMED,
                        ],
                        start_time__lt=end,
                        end_time__gt=start,
                    ).exists()

                    if conflict:
                        error = "На это время уже есть заявка или подтверждённое бронирование."
                    else:
                        RoomBooking.objects.create(
                            room=room,
                            teacher=teacher,
                            date=booking_date,
                            start_time=start,
                            end_time=end,
                            purpose=purpose,
                        )
                        return redirect("room_booking")

            except (ValueError, StudioRoom.DoesNotExist):
                error = "Проверь выбранный зал, дату и время."

    bookings = (
        RoomBooking.objects.filter(teacher=teacher).select_related("room")
        if teacher
        else RoomBooking.objects.none()
    )
    return render(
        request,
        "accounts/room_booking.html",
        {
            "rooms": rooms,
            "bookings": bookings,
            "error": error,
            "success": success,
            "today": timezone.localdate(),
        },
    )








