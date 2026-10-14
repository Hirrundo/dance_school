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
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает обработки"
        CONFIRMED = "confirmed", "Подтверждена"
        REJECTED = "rejected", "Отклонена"

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    class Meta:
        verbose_name = "заявка на пробное занятие"
        verbose_name_plural = "Заявки на пробное занятие"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} — {self.dance_class.title}"

class DanceGroup(models.Model):
    name = models.CharField(
        max_length=150,
        verbose_name="Название группы",
    )
    dance_class = models.ForeignKey(
        DanceClass,
        on_delete=models.PROTECT,
        related_name="groups",
        verbose_name="Занятие",
    )
    students = models.ManyToManyField(
        "accounts.Profile",
        blank=True,
        related_name="dance_groups",
        verbose_name="Ученики",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
    )

    class Meta:
        verbose_name = "танцевальная группа"
        verbose_name_plural = "Танцевальные группы"
        ordering = ("name",)

    def __str__(self):
        return self.name

class ClassSchedule(models.Model):
    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Понедельник"
        TUESDAY = 1, "Вторник"
        WEDNESDAY = 2, "Среда"
        THURSDAY = 3, "Четверг"
        FRIDAY = 4, "Пятница"
        SATURDAY = 5, "Суббота"
        SUNDAY = 6, "Воскресенье"

    group = models.ForeignKey(
        DanceGroup,
        on_delete=models.CASCADE,
        related_name="schedule_entries",
        verbose_name="Группа",
    )
    weekday = models.IntegerField(
        choices=Weekday.choices,
        verbose_name="День недели",
    )
    start_time = models.TimeField(
        verbose_name="Время начала",
    )
    end_time = models.TimeField(
        verbose_name="Время окончания",
    )

    class Meta:
        verbose_name = "занятие в расписании"
        verbose_name_plural = "Расписание занятий"
        ordering = ("weekday", "start_time")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="schedule_end_after_start",
            ),
        ]

    def __str__(self):
        return (
            f"{self.group.name} — "
            f"{self.get_weekday_display()}, "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )
class GroupVideo(models.Model):
    group = models.ForeignKey(
        DanceGroup,
        on_delete=models.CASCADE,
        related_name="videos",
        verbose_name="Группа",
    )
    title = models.CharField(
        max_length=200,
        verbose_name="Название видео",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    video = models.FileField(
        upload_to="group_videos/",
        verbose_name="Файл видео",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления",
    )

    class Meta:
        verbose_name = "видео занятия"
        verbose_name_plural = "Видео занятий"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.title} — {self.group.name}"
class StudioRoom(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название зала",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    capacity = models.PositiveIntegerField(
        verbose_name="Вместимость",
    )
    image = models.ImageField(
        upload_to="rooms/",
        blank=True,
        null=True,
        verbose_name="Фото зала",
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name="Доступен для бронирования",
    )

    class Meta:
        verbose_name = "танцевальный зал"
        verbose_name_plural = "Танцевальные залы"
        ordering = ("name",)

    def __str__(self):
        return self.name

class RoomBooking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает подтверждения"
        CONFIRMED = "confirmed", "Подтверждено"
        CANCELLED = "cancelled", "Отменено"
        REJECTED = "rejected", "Отклонено"

    room = models.ForeignKey(
        StudioRoom,
        on_delete=models.PROTECT,
        related_name="bookings",
        verbose_name="Зал",
    )
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="room_bookings",
        verbose_name="Хореограф",
    )
    date = models.DateField(
        verbose_name="Дата бронирования",
    )
    start_time = models.TimeField(
        verbose_name="Время начала",
    )
    end_time = models.TimeField(
        verbose_name="Время окончания",
    )
    purpose = models.CharField(
        max_length=255,
        verbose_name="Цель бронирования",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Статус",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания заявки",
    )

    class Meta:
        verbose_name = "бронирование зала"
        verbose_name_plural = "Бронирования залов"
        ordering = ("date", "start_time")
        constraints = [
            models.CheckConstraint(
                condition=models.Q(end_time__gt=models.F("start_time")),
                name="booking_end_after_start",
            ),
        ]

    def __str__(self):
        return (
            f"{self.room.name} — {self.date:%d.%m.%Y}, "
            f"{self.start_time:%H:%M}–{self.end_time:%H:%M}"
        )






# Create your models here.
