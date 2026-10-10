from django.db import models

class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    birth_date = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "хореограф"
        verbose_name_plural = "Хореографы"
        ordering = ("last_name",)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class DanceStyle(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "танцевальный стиль"
        verbose_name_plural = "Танцевальные стили"

    def __str__(self):
        return self.name

class DanceClass(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="dance_classes",
        verbose_name="Хореограф"
    )
    dance_styles = models.ManyToManyField(
        DanceStyle,
        blank=True,
        related_name="dance_classes"
    )
    duration_minutes = models.PositiveIntegerField()
    capacity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "танцевальное занятие"
        verbose_name_plural = "Танцевальные занятия"

    def __str__(self):
        return self.title

class Student(models.Model):
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя",
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия",
    )
    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почта",
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
    registered_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации",
    )

    class Meta:
        verbose_name = "ученик"
        verbose_name_plural = "Ученики"
        ordering = ("last_name", "first_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
# Create your models here.
