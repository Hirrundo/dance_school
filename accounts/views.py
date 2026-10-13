from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from .models import Profile
from dance_school.models import DanceClass



def role_required(required_role):
    def decorator(view_func):
        view_func
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user

            if required_role == Profile.Role.ADMIN:
                try:
                    role = user.profile.role
                except Profile.DoesNotExist:
                    role = None

                if (
                    role != Profile.Role.ADMIN
                    and not user.is_staff
                    and not user.is_superuser
                ):
                    raise PermissionDenied

            else:
                try:
                    role = user.profile.role
                except Profile.DoesNotExist:
                    role = None

                if role != required_role:
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
    return render(request, "accounts/student_dashboard.html")

@role_required(Profile.Role.CHOREOGRAPHER)
def choreographer_dashboard(request):
    profile = request.user.profile

    try:
        teacher = profile.teacher_record
    except Exception:
        teacher = None

    classes = (
        DanceClass.objects.filter(teacher=teacher)
        .prefetch_related("dance_styles")
        if teacher
        else DanceClass.objects.none()
    )

    return render(
        request,
        "accounts/choreographer_dashboard.html",
        {
            "teacher": teacher,
            "classes": classes,
        },
    )

@role_required(Profile.Role.ADMIN)
def admin_dashboard(request):
    return render(request, "accounts/admin_dashboard.html")

def logout_view(request):
    logout(request)
    return redirect("login")