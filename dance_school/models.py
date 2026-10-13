from django.db import models

class Teacher(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile = models.OneToOneField(
        "accounts.Profile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_record",
        verbose_name="Аккаунт хореографа",
    )
    birth_date = models.DateField(null=True, blank=True)
    biography = models.TextField(blank=True)
    photo=models.ImageField(upload_to="teachers/",
        blank=True,
        null=True,
        verbose_name="Фото хореографа",)
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
    image = models.ImageField(
        upload_to="styles/",
        blank=True,
        null=True,
        verbose_name="Изображение направления",
        )

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
    image = models.ImageField(
        upload_to="classes/",
        blank=True,
        null=True,
        verbose_name="Изображение занятия",
)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "танцевальное занятие"
        verbose_name_plural = "Танцевальные занятия"

    def __str__(self):
        return self.title
class TrialRequest(models.Model):
    dance_class = models.ForeignKey(
        DanceClass,
        on_delete=models.CASCADE,
        related_name="trial_requests",
        verbose_name="Занятие",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Имя",
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
    )
    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата заявки",
    )

    class Meta:
        verbose_name = "заявка на пробное занятие"
        verbose_name_plural = "Заявки на пробное занятие"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} — {self.dance_class.title}"


# Create your models here.
