from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from datetime import date
from .models import Patient, AnalysisType, Analysis

User = get_user_model()


class BasicModelTests(TestCase):
    """Базовые тесты моделей"""

    def setUp(self):
        # Создаем пользователя только с email
        self.user = User.objects.create_user(
            email='test@test.ru',
            password='testpass123'
        )

        # Создаем пациента
        self.patient = Patient.objects.create(
            last_name='Иванов',
            first_name='Петр',
            birth_date=date(1990, 1, 1),
            gender='M',
            created_by=self.user
        )

        # Создаем тип анализа
        self.analysis_type = AnalysisType.objects.create(
            name='Общий анализ крови',
            price=1000.00
        )

    def test_patient_creation(self):
        """Тест создания пациента"""
        self.assertEqual(str(self.patient), 'Иванов Петр')
        self.assertEqual(self.patient.get_full_name(), 'Иванов Петр')
        self.assertEqual(self.patient.age, date.today().year - 1990)

    def test_analysis_type_creation(self):
        """Тест создания типа анализа"""
        self.assertEqual(str(self.analysis_type), 'Общий анализ крови')

    def test_analysis_creation(self):
        """Тест создания анализа"""
        analysis = Analysis.objects.create(
            patient=self.patient,
            analysis_type=self.analysis_type,
            status='registered'
        )
        self.assertEqual(
            str(analysis),
            'Общий анализ крови - Иванов Петр'
        )
        self.assertEqual(analysis.status, 'registered')


class ViewTests(TestCase):
    """Базовые тесты представлений"""

    def test_home_page(self):
        """Тест главной страницы"""
        response = self.client.get(reverse('medical_lab:home'))
        self.assertEqual(response.status_code, 200)

    def test_about_page(self):
        """Тест страницы о лаборатории"""
        response = self.client.get(reverse('medical_lab:about'))
        self.assertEqual(response.status_code, 200)

    def test_services_page(self):
        """Тест страницы услуг"""
        response = self.client.get(reverse('medical_lab:services'))
        self.assertEqual(response.status_code, 200)

    def test_contacts_page(self):
        """Тест страницы контактов"""
        response = self.client.get(reverse('medical_lab:contacts'))
        self.assertEqual(response.status_code, 200)


class EmailTests(TestCase):
    """Базовые тесты отправки email"""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.ru',
            password='testpass123'
        )

        self.patient = Patient.objects.create(
            last_name='Иванов',
            first_name='Петр',
            birth_date=date(1990, 1, 1),
            gender='M',
            email='patient@test.ru',
            created_by=self.user
        )

        self.analysis_type = AnalysisType.objects.create(
            name='Общий анализ крови'
        )

        self.analysis = Analysis.objects.create(
            patient=self.patient,
            analysis_type=self.analysis_type,
            status='completed'
        )

    def test_send_completion_email(self):
        """Тест отправки email о готовности анализа"""
        from django.core import mail

        # Очищаем почтовый ящик
        mail.outbox = []

        # Отправляем email
        self.analysis.send_completion_email()

        # Проверяем, что email был отправлен
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, f'Готовность анализа #{self.analysis.id}')
        self.assertEqual(mail.outbox[0].to, [self.patient.email])


class APITests(TestCase):
    """Базовые тесты API"""

    def test_api_overview(self):
        """Тест обзора API"""
        response = self.client.get(reverse('medical_lab:api_overview'))
        self.assertEqual(response.status_code, 200)

    def test_public_services(self):
        """Тест публичных услуг API"""
        response = self.client.get(reverse('medical_lab:public_services'))
        self.assertEqual(response.status_code, 200)
