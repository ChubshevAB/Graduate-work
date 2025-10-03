from django.db import models
from django.conf import settings
from datetime import date
from django.contrib.auth import get_user_model

User = get_user_model()


class Patient(models.Model):
    # ФИО пациента (разделенные поля)
    last_name = models.CharField(
        max_length=100,
        verbose_name='Фамилия'
    )
    first_name = models.CharField(
        max_length=100,
        verbose_name='Имя'
    )
    middle_name = models.CharField(
        max_length=100,
        verbose_name='Отчество',
        blank=True,
        null=True
    )

    # Дата рождения
    birth_date = models.DateField(
        verbose_name='Дата рождения'
    )

    # Возраст (вычисляется автоматически)
    @property
    def age(self):
        """Автоматически вычисляет возраст на основе даты рождения"""
        if not self.birth_date:
            return None

        today = date.today()
        age = today.year - self.birth_date.year

        # Проверка, был ли уже день рождения в этом году
        if today < date(today.year, self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    # Пол пациента
    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
        ('O', 'Другой'),
    ]

    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name='Пол'
    )

    # Контактная информация
    phone = models.CharField(
        max_length=20,
        verbose_name='Телефон',
        blank=True,
        null=True
    )

    email = models.EmailField(
        verbose_name='Email',
        blank=True,
        null=True
    )

    address = models.TextField(
        verbose_name='Адрес',
        blank=True,
        null=True
    )

    medical_history = models.TextField(
        verbose_name='Медицинская история',
        blank=True,
        null=True
    )

    # Пользователь (который создал карточку)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Создатель карточки',
        related_name='created_patients'
    )

    # Дата создания карточки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания карточки'
    )

    # Дата обновления карточки
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Пациент'
        verbose_name_plural = 'Пациенты'
        ordering = ['-created_at']

    def __str__(self):
        return self.get_full_name()

    def get_full_name(self):
        """Возвращает полное ФИО пациента"""
        names = [self.last_name, self.first_name]
        if self.middle_name:
            names.append(self.middle_name)
        return ' '.join(names)

    def save(self, *args, **kwargs):
        # Валидация при сохранении
        if self.birth_date and self.birth_date > date.today():
            raise ValueError("Дата рождения не может быть в будущем")
        super().save(*args, **kwargs)


class AnalysisType(models.Model):
    """Типы анализов"""
    name = models.CharField(
        max_length=100,
        verbose_name='Название анализа'
    )
    description = models.TextField(
        verbose_name='Описание',
        blank=True
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Стоимость',
        default=0.00
    )
    preparation_instructions = models.TextField(
        verbose_name='Инструкции по подготовке',
        blank=True
    )
    turnaround_time = models.IntegerField(
        verbose_name='Срок выполнения (в днях)',
        default=1
    )

    is_active = models.BooleanField(
        verbose_name='Активен',
        default=True
    )

    class Meta:
        verbose_name = 'Тип анализа'
        verbose_name_plural = 'Типы анализов'
        ordering = ['name']

    def __str__(self):
        return self.name


class Analysis(models.Model):
    # Статусы анализа
    STATUS_CHOICES = [
        ('registered', 'Зарегистрирован'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнен'),
        ('cancelled', 'Отменен'),
    ]

    # Основные поля
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        verbose_name='Пациент',
        related_name='analyses'
    )

    analysis_type = models.ForeignKey(
        AnalysisType,
        on_delete=models.CASCADE,
        verbose_name='Тип анализа',
        related_name='analyses'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered',
        verbose_name='Статус'
    )

    # Даты
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    collection_date = models.DateTimeField(
        verbose_name='Дата забора',
        null=True,
        blank=True
    )

    completion_date = models.DateTimeField(
        verbose_name='Дата выполнения',
        null=True,
        blank=True
    )

    # Результаты
    result = models.TextField(
        verbose_name='Результат анализа',
        blank=True
    )

    result_values = models.JSONField(
        verbose_name='Значения результатов',
        blank=True,
        null=True,
        help_text='JSON с конкретными значениями анализов'
    )

    normal_range = models.TextField(
        verbose_name='Нормальные значения',
        blank=True
    )

    notes = models.TextField(
        verbose_name='Примечания',
        blank=True
    )

    # Лаборант, который выполнил анализ
    lab_technician = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        verbose_name='Лаборант',
        null=True,
        blank=True,
        related_name='performed_analyses'
    )

    # Метаданные
    class Meta:
        verbose_name = 'Анализ'
        verbose_name_plural = 'Анализы'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.analysis_type.name} - {self.patient.get_full_name()}"

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем дату выполнения при завершении анализа
        if self.status == 'completed' and not self.completion_date:
            from django.utils import timezone
            self.completion_date = timezone.now()
        super().save(*args, **kwargs)


class Report(models.Model):
    """Модель для отчетов"""
    title = models.CharField(
        max_length=200,
        verbose_name='Название отчета'
    )

    report_type = models.CharField(
        max_length=50,
        verbose_name='Тип отчета',
        choices=[
            ('patients', 'По пациентам'),
            ('analyses', 'По анализам'),
            ('financial', 'Финансовый'),
            ('custom', 'Пользовательский')
        ]
    )

    generated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Создатель отчета'
    )

    generated_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    date_from = models.DateField(
        verbose_name='Период с',
        null=True,
        blank=True
    )

    date_to = models.DateField(
        verbose_name='Период по',
        null=True,
        blank=True
    )

    data = models.JSONField(
        verbose_name='Данные отчета',
        blank=True,
        null=True
    )

    file = models.FileField(
        upload_to='reports/',
        verbose_name='Файл отчета',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'
        ordering = ['-generated_at']

    def __str__(self):
        return self.title
