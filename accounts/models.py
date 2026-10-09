from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
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
        verbose_name="Дата регистрации",
    )

    class Meta:
        verbose_name = "профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return f"Профиль {self.user.username}"
# Create your models here.
