from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    class Role(models.TextChoices):
        STUDENT = "student", "Ученик"
        CHOREOGRAPHER = "choreographer", "Хореограф"
        ADMIN = "admin", "Администратор"

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name="Роль",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Телефон",
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Адрес",
    )
    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дата рождения",
    )
    membership_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Номер карты ученика",
    )
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания профиля",
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Почасовая ставка хореографа",
    )
    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"
# Create your models here.
