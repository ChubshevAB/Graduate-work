from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class User(AbstractUser):
    """
    Кастомная модель пользователя (пациента)
    """
    # Делаем email уникальным и используем его для авторизации
    email = models.EmailField(
        unique=True,
        verbose_name='Email'
    )

    # Добавляем поле отчества
    middle_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отчество'
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='Телефон'
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name='Дата рождения'
    )

    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        default='O',
        verbose_name='Пол'
    )

    address = models.TextField(
        blank=True,
        verbose_name='Адрес'
    )

    medical_history = models.TextField(
        blank=True,
        verbose_name='Медицинская история'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    # Убираем username, используем email вместо него
    username = None

    # Указываем, что email будет использоваться как поле для авторизации
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']  # Добавляем обязательные поля

    # Используем кастомный менеджер
    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def get_full_name(self):
        """Возвращает полное ФИО пользователя"""
        names = [self.last_name, self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        return ' '.join(names)

    @property
    def is_administrator(self):
        return self.groups.filter(name='administrators').exists() or self.is_superuser

    @property
    def is_moderator(self):
        return self.groups.filter(name='moderators').exists()

    @property
    def is_regular_user(self):
        """Обычный пользователь - это тот, кто не админ и не модератор"""
        return not (self.is_administrator or self.is_moderator)

    @property
    def is_guest(self):
        return not self.is_authenticated

    @property
    def role_display(self):
        """Отображаемая роль пользователя"""
        if self.is_administrator:
            return "Администратор"
        elif self.is_moderator:
            return "Модератор"
        else:
            return "Пациент"

    def save(self, *args, **kwargs):
        """
        Сохраняет пользователя, обеспечивая правильные права доступа
        """
        # Сохраняем флаг, создается ли новый пользователь
        is_new = self._state.adding

        # Сначала сохраняем пользователя, чтобы получить id
        super().save(*args, **kwargs)

        # Теперь, когда у пользователя есть id, можем работать с группами
        # Для новых обычных пользователей снимаем права staff/superuser
        if is_new:
            if not (self.is_administrator or self.is_moderator):
                # Если это не админ и не модератор, обновляем права
                User.objects.filter(id=self.id).update(
                    is_staff=False,
                    is_superuser=False
                )
                # Обновляем объект в памяти
                self.is_staff = False
                self.is_superuser = False
