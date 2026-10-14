
from functools import wraps
import mimetypes
from decimal import Decimal, InvalidOperation
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Profile
from dance_school.models import (
    DanceClass,
    GroupVideo,
    ClassSchedule,
    StudioRoom,
    RoomBooking,
    Teacher,
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
    return render(request, "accounts/admin_dashboard.html")

def logout_view(request):
    logout(request)
    return redirect("login")

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








