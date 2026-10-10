from django.urls import path

from . import views

app_name = "dance_school"

urlpatterns = [
    path("classes/", views.dance_class_list, name="class_list"),
    path("classes/<slug:slug>/", views.dance_class_detail, name="class_detail"),
    path("teachers/", views.teacher_list, name="teacher_list"),
    path("teachers/<int:pk>/", views.teacher_detail, name="teacher_detail"),
    path("styles/", views.dance_style_list, name="style_list"),
    path("about/", views.about, name="about"),
]