from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Patient, Analysis, AnalysisType


class PatientForm(forms.ModelForm):
    """Форма для создания и редактирования пациентов"""

    class Meta:
        model = Patient
        fields = [
            "last_name",
            "first_name",
            "middle_name",
            "birth_date",
            "gender",
            "phone",
            "email",
            "address",
            "medical_history",
        ]
        widgets = {
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Введите фамилию"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Введите имя"}
            ),
            "middle_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Введите отчество (необязательно)",
                }
            ),
            "birth_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+7 (XXX) XXX-XX-XX"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "example@mail.ru"}
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Введите адрес пациента",
                }
            ),
            "medical_history": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Медицинская история, аллергии, хронические заболевания...",
                }
            ),
        }
        labels = {
            "last_name": "Фамилия *",
            "first_name": "Имя *",
            "middle_name": "Отчество",
            "birth_date": "Дата рождения *",
            "gender": "Пол *",
            "phone": "Телефон",
            "email": "Email",
            "address": "Адрес",
            "medical_history": "Медицинская история",
        }

    def clean_birth_date(self):
        """Валидация даты рождения"""
        birth_date = self.cleaned_data.get("birth_date")
        if birth_date:
            if birth_date > date.today():
                raise ValidationError("Дата рождения не может быть в будущем")
            # Проверяем, что пациенту не больше 150 лет
            age = (date.today() - birth_date).days / 365.25
            if age > 150:
                raise ValidationError("Проверьте правильность даты рождения")
        return birth_date

    def clean_phone(self):
        """Базовая валидация телефона"""
        phone = self.cleaned_data.get("phone")
        if phone:
            # Убираем все нецифровые символы, кроме +
            cleaned_phone = "".join(c for c in phone if c.isdigit() or c == "+")
            if len(cleaned_phone) < 10:
                raise ValidationError("Некорректный номер телефона")
        return phone


class AnalysisForm(forms.ModelForm):
    """Форма для создания и редактирования анализов"""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Ограничиваем выбор пациентов в зависимости от роли пользователя
        if self.user:
            if self.user.is_administrator or self.user.is_moderator:
                # Администраторы и модераторы видят всех пациентов
                patients = Patient.objects.all()
            else:
                # Обычные пользователи видят только СЕБЯ как пациента
                patients = Patient.objects.filter(created_by=self.user)

            self.fields["patient"].queryset = patients

            # Для обычных пользователей скрываем поле выбора пациента
            if self.user.is_regular_user:
                # Автоматически назначаем текущего пользователя как пациента
                try:
                    patient = Patient.objects.get(created_by=self.user)
                    self.fields["patient"].initial = patient
                    self.fields["patient"].widget = forms.HiddenInput()  # Скрываем поле
                except Patient.DoesNotExist:
                    # Если пациента нет, создаем его автоматически
                    patient = Patient.objects.create(
                        last_name=self.user.last_name or "User",
                        first_name=self.user.first_name or "Unknown",
                        birth_date=self.user.birth_date or "2000-01-01",
                        gender=self.user.gender or "O",
                        phone=self.user.phone,
                        email=self.user.email,
                        created_by=self.user,
                    )
                    self.fields["patient"].initial = patient
                    self.fields["patient"].widget = forms.HiddenInput()

        # Только активные типы анализов
        self.fields["analysis_type"].queryset = AnalysisType.objects.filter(
            is_active=True
        )

        # Настройка виджетов
        self.fields["patient"].widget.attrs.update({"class": "form-select"})
        self.fields["analysis_type"].widget.attrs.update({"class": "form-select"})
        self.fields["collection_date"].widget = forms.DateTimeInput(
            attrs={"class": "form-control", "type": "datetime-local"}
        )
        self.fields["notes"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 3,
                "placeholder": "Дополнительные примечания к анализу...",
            }
        )

    class Meta:
        model = Analysis
        fields = ["patient", "analysis_type", "collection_date", "notes"]
        labels = {
            "patient": "Пациент *",
            "analysis_type": "Тип анализа *",
            "collection_date": "Дата и время забора",
            "notes": "Примечания",
        }


class AnalysisResultForm(forms.ModelForm):
    """Форма для добавления результатов анализа"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Настройка виджетов
        self.fields["result"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 6,
                "placeholder": "Введите результаты анализа...",
            }
        )
        self.fields["result_values"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 4,
                "placeholder": '{"параметр": "значение", "параметр2": "значение2"}',
            }
        )
        self.fields["normal_range"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 3,
                "placeholder": "Нормальные значения для данного анализа...",
            }
        )
        self.fields["notes"].widget.attrs.update(
            {
                "class": "form-control",
                "rows": 3,
                "placeholder": "Комментарии лаборанта...",
            }
        )

    class Meta:
        model = Analysis
        fields = ["result", "result_values", "normal_range", "notes"]
        labels = {
            "result": "Результат анализа *",
            "result_values": "Значения параметров (JSON)",
            "normal_range": "Нормальные значения",
            "notes": "Комментарии лаборанта",
        }

    def clean_result_values(self):
        """Валидация JSON поля"""
        result_values = self.cleaned_data.get("result_values")
        if result_values:
            try:
                # Пытаемся распарсить JSON для проверки валидности
                import json

                if isinstance(result_values, str):
                    json.loads(result_values)
            except json.JSONDecodeError:
                raise ValidationError("Некорректный JSON формат")
        return result_values


class AnalysisTypeForm(forms.ModelForm):
    """Форма для типов анализов"""

    class Meta:
        model = AnalysisType
        fields = [
            "name",
            "description",
            "price",
            "preparation_instructions",
            "turnaround_time",
            "is_active",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "preparation_instructions": forms.Textarea(
                attrs={"class": "form-control", "rows": 4}
            ),
            "turnaround_time": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "name": "Название анализа *",
            "description": "Описание",
            "price": "Стоимость (руб)",
            "preparation_instructions": "Инструкции по подготовке",
            "turnaround_time": "Срок выполнения (дни)",
            "is_active": "Активен",
        }


class ReportForm(forms.Form):
    """Форма для генерации отчетов"""

    REPORT_TYPES = [
        ("patients", "Отчет по пациентам"),
        ("analyses", "Отчет по анализам"),
        ("financial", "Финансовый отчет"),
    ]

    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Тип отчета *",
    )

    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Период с",
    )

    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Период по",
    )

    include_details = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label="Включить детализацию",
    )

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")

        if date_from and date_to:
            if date_from > date_to:
                raise ValidationError("Дата 'с' не может быть позже даты 'по'")

        return cleaned_data


class SearchForm(forms.Form):
    """Форма поиска пациентов"""

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "ФИО, телефон или email..."}
        ),
        label="Поиск",
    )

    gender = forms.ChoiceField(
        required=False,
        choices=[("", "Все полы")] + Patient.GENDER_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Пол",
    )

    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Дата рождения",
    )
