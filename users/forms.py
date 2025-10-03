from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from datetime import date

from medical_lab.models import Patient

User = get_user_model()


class PatientRegistrationForm(UserCreationForm):
    """Форма регистрации пациента (пользователя)"""

    # Основные поля пациента - делаем все обязательными
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        }),
        label='Фамилия *'
    )

    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        }),
        label='Имя *'
    )

    middle_name = forms.CharField(  # Добавляем отчество как обязательное поле
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите отчество'
        }),
        label='Отчество *'
    )

    birth_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Дата рождения *'
    )

    gender = forms.ChoiceField(
        choices=User.GENDER_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label='Пол *'
    )

    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (XXX) XXX-XX-XX'
        }),
        label='Телефон'
    )

    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru'
        }),
        label='Email *'
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Введите ваш адрес'
        }),
        label='Адрес'
    )

    medical_history = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Медицинская история, аллергии, хронические заболевания...'
        }),
        label='Медицинская история'
    )

    class Meta:
        model = User
        fields = (
            'last_name', 'first_name', 'middle_name', 'birth_date', 'gender',
            'phone', 'email', 'address', 'medical_history', 'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Кастомизация виджетов для полей паролей
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })

        # Убираем автоматические метки паролей
        self.fields['password1'].label = 'Пароль *'
        self.fields['password2'].label = 'Подтверждение пароля *'

    def clean_birth_date(self):
        """Валидация даты рождения"""
        birth_date = self.cleaned_data.get('birth_date')
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
        phone = self.cleaned_data.get('phone')
        if phone:
            # Убираем все нецифровые символы, кроме +
            cleaned_phone = ''.join(c for c in phone if c.isdigit() or c == '+')
            if len(cleaned_phone) < 10:
                raise ValidationError("Некорректный номер телефона")
        return phone

    def save(self, commit=True):
        """Создает пользователя с данными пациента"""
        user = super().save(commit=False)

        # Заполняем данные пользователя из формы
        user.last_name = self.cleaned_data['last_name']
        user.first_name = self.cleaned_data['first_name']
        user.middle_name = self.cleaned_data['middle_name']  # Добавляем отчество
        user.birth_date = self.cleaned_data['birth_date']
        user.gender = self.cleaned_data['gender']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.medical_history = self.cleaned_data['medical_history']

        # Явно указываем, что это обычный пользователь
        user.is_staff = False
        user.is_superuser = False

        if commit:
            user.save()
            # Добавляем в группу обычных пользователей
            from django.contrib.auth.models import Group
            try:
                users_group = Group.objects.get(name='users')
                user.groups.add(users_group)
            except Group.DoesNotExist:
                # Если группы нет, просто сохраняем без группы
                pass

        return user


class PatientWithUserForm(forms.ModelForm):
    """Форма для создания пациента с пользователем (для модераторов)"""

    # Поля для создания пользователя
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.ru'
        }),
        label='Email *',
        help_text='Email будет использоваться для входа в систему'
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        }),
        label='Пароль *',
        help_text='Пароль должен содержать минимум 8 символов'
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        }),
        label='Подтверждение пароля *'
    )

    class Meta:
        model = Patient
        fields = [
            'last_name', 'first_name', 'middle_name',
            'birth_date', 'gender', 'phone', 'email',
            'address', 'medical_history', 'password1', 'password2'
        ]
        widgets = {
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите фамилию'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите имя'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите отчество'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+7 (XXX) XXX-XX-XX'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите адрес пациента'
            }),
            'medical_history': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Медицинская история, аллергии, хронические заболевания...'
            }),
        }
        labels = {
            'last_name': 'Фамилия *',
            'first_name': 'Имя *',
            'middle_name': 'Отчество *',
            'birth_date': 'Дата рождения *',
            'gender': 'Пол *',
            'phone': 'Телефон',
            'address': 'Адрес',
            'medical_history': 'Медицинская история',
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        email = cleaned_data.get('email')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")

        if email:
            # Проверяем, что email не занят
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if User.objects.filter(email=email).exists():
                raise ValidationError("Пользователь с таким email уже существует")

        return cleaned_data

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1 and len(password1) < 8:
            raise ValidationError("Пароль должен содержать минимум 8 символов")
        return password1

    def save(self, commit=True, created_by=None):
        # Создаем пользователя
        from django.contrib.auth import get_user_model
        User = get_user_model()

        user = User.objects.create_user(
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            birth_date=self.cleaned_data['birth_date'],
            gender=self.cleaned_data['gender'],
            phone=self.cleaned_data['phone'],
            address=self.cleaned_data['address'],
            medical_history=self.cleaned_data['medical_history'],
        )

        # Добавляем пользователя в группу patients
        from django.contrib.auth.models import Group
        try:
            users_group = Group.objects.get(name='users')
            user.groups.add(users_group)
        except Group.DoesNotExist:
            pass

        # Создаем пациента
        patient = super().save(commit=False)
        patient.created_by = created_by or user

        if commit:
            patient.save()

        return patient
