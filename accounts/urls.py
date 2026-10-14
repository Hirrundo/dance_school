from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path(
        "student/",
        views.student_dashboard,
        name="student_dashboard",
    ),
   path(
    "videos/<int:video_id>/",
    views.group_video_view,
    name="group_video",
),
    path(
        "choreographer/",
        views.choreographer_dashboard,
        name="choreographer_dashboard",
    ),

    path(
        "admin/",
        views.admin_dashboard,
        name="admin_dashboard",
    ),
 
]