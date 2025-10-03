from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model

from users.forms import PatientWithUserForm
from .models import Patient, Analysis, AnalysisType
from .serializers import PatientSerializer, AnalysisSerializer
from .forms import PatientForm, AnalysisForm, AnalysisResultForm

User = get_user_model()


# Кастомные классы permissions на основе групп
class IsAdministrator(permissions.BasePermission):
    """Только администратор"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_administrator


class IsModerator(permissions.BasePermission):
    """Модератор"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_moderator


class IsRegularUser(permissions.BasePermission):
    """Обычный пользователь"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_regular_user


class IsAdministratorOrModerator(permissions.BasePermission):
    """Администратор или модератор"""

    def has_permission(self, request, view):
        return request.user.is_authenticated and (
                request.user.is_administrator or request.user.is_moderator
        )


class IsOwnerOrAdministratorOrModerator(permissions.BasePermission):
    """Владелец, администратор или модератор"""

    def has_object_permission(self, request, view, obj):
        if request.user.is_administrator or request.user.is_moderator:
            return True
        # Для обычных пользователей - доступ только к своим данным
        if hasattr(obj, 'patient') and hasattr(obj.patient, 'created_by'):
            return obj.patient.created_by == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False


# ViewSet для пациентов
class PatientViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с пациентами
    """
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAdministratorOrModerator | IsRegularUser]
        elif self.action in ['create']:
            permission_classes = [IsModerator]  # Только модераторы могут создавать пациентов
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsOwnerOrAdministratorOrModerator]
        else:  # destroy
            permission_classes = [IsAdministrator]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Patient.objects.none()

        # Администратор видит всех пациентов
        if user.is_administrator:
            return Patient.objects.all()

        # Модератор видит всех пациентов
        if user.is_moderator:
            return Patient.objects.all()

        # Обычный пользователь видит только своих пациентов
        if user.is_regular_user:
            return Patient.objects.filter(created_by=user)

        return Patient.objects.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[IsAdministratorOrModerator | IsRegularUser])
    def analyses(self, request, pk=None):
        """
        Получить все анализы конкретного пациента
        GET /api/patients/{id}/analyses/
        """
        patient = self.get_object()

        # Проверяем права доступа для обычных пользователей
        if request.user.is_regular_user and patient.created_by != request.user:
            return Response(
                {'error': 'Доступ запрещен'},
                status=status.HTTP_403_FORBIDDEN
            )

        analyses = patient.analyses.all()
        serializer = AnalysisSerializer(analyses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdministratorOrModerator])
    def stats(self, request):
        """
        Статистика по пациентам
        GET /api/patients/stats/
        """
        user = request.user

        if user.is_administrator or user.is_moderator:
            total_patients = Patient.objects.count()
            recent_patients = Patient.objects.order_by('-created_at')[:5]
        else:
            return Response(
                {'error': 'Недостаточно прав'},
                status=status.HTTP_403_FORBIDDEN
            )

        stats_data = {
            'total_patients': total_patients,
            'recent_patients': PatientSerializer(recent_patients, many=True).data,
        }
        return Response(stats_data)


# ViewSet для анализов
class AnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с анализами
    """
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAdministratorOrModerator | IsRegularUser]
        elif self.action in ['create']:
            permission_classes = [IsModerator | IsRegularUser]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [IsOwnerOrAdministratorOrModerator]
        else:  # destroy
            permission_classes = [IsAdministrator]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if not user.is_authenticated:
            return Analysis.objects.none()

        # Администратор видит все анализы
        if user.is_administrator:
            return Analysis.objects.all()

        # Модератор видит все анализы
        if user.is_moderator:
            return Analysis.objects.all()

        # Обычный пользователь видит только анализы своих пациентов
        if user.is_regular_user:
            return Analysis.objects.filter(patient__created_by=user)

        return Analysis.objects.none()

    def perform_create(self, serializer):
        # Для обычных пользователей автоматически назначаем пациента
        if self.request.user.is_regular_user:
            # Находим или создаем пациента для текущего пользователя
            patient, created = Patient.objects.get_or_create(
                created_by=self.request.user,
                defaults={
                    'last_name': self.request.user.last_name or 'User',
                    'first_name': self.request.user.first_name or 'Unknown',
                    'birth_date': self.request.user.birth_date or '2000-01-01',
                    'gender': self.request.user.gender or 'O'
                }
            )
            serializer.save(patient=patient)
        else:
            serializer.save()

    @action(detail=True, methods=['post'], permission_classes=[IsModerator])
    def set_status(self, request, pk=None):
        """
        Изменить статус анализа
        POST /api/analyses/{id}/set_status/
        {
            "status": "completed"
        }
        """
        analysis = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(Analysis.STATUS_CHOICES):
            return Response(
                {'error': 'Неверный статус'},
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis.status = new_status
        analysis.save()

        serializer = self.get_serializer(analysis)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdministratorOrModerator])
    def by_status(self, request):
        """
        Получить анализы по статусу
        GET /api/analyses/by_status/?status=completed
        """
        status_filter = request.query_params.get('status')
        queryset = self.get_queryset()

        if status_filter:
            analyses = queryset.filter(status=status_filter)
        else:
            analyses = queryset

        serializer = self.get_serializer(analyses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAdministratorOrModerator | IsRegularUser])
    def dashboard_stats(self, request):
        """
        Статистика для дашборда
        GET /api/analyses/dashboard_stats/
        """
        user = request.user

        if user.is_administrator or user.is_moderator:
            queryset = Analysis.objects.all()
        elif user.is_regular_user:
            queryset = Analysis.objects.filter(patient__created_by=user)
        else:
            return Response(
                {'error': 'Недостаточно прав'},
                status=status.HTTP_403_FORBIDDEN
            )

        total_analyses = queryset.count()
        completed_analyses = queryset.filter(status='completed').count()
        in_progress_analyses = queryset.filter(status='in_progress').count()
        registered_analyses = queryset.filter(status='registered').count()

        stats = {
            'total_analyses': total_analyses,
            'completed_analyses': completed_analyses,
            'in_progress_analyses': in_progress_analyses,
            'registered_analyses': registered_analyses,
            'completion_rate': round((completed_analyses / total_analyses * 100), 2) if total_analyses > 0 else 0
        }

        return Response(stats)


# API views для публичной информации
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_overview(request):
    """
    Обзор доступных API endpoints (доступно всем)
    """
    overview = {
        'message': 'Добро пожаловать в API медицинской лаборатории',
        'endpoints': {
            'public_services': '/api/public/services/',
            'admin_login': '/admin/',
        },
        'user_groups': {
            'guests': 'Только публичная информация',
            'users': 'Просмотр своих анализов и запись на новые',
            'moderators': 'Просмотр и редактирование пациентов и анализов',
            'administrators': 'Полный доступ ко всем функциям'
        }
    }
    return Response(overview)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def public_services(request):
    """
    Публичная информация об услугах (доступно всем)
    """
    services = {
        'services': [
            {
                'name': 'Анализ крови',
                'description': 'Общий анализ крови, биохимия, гормоны',
                'price_range': 'от 500 руб.'
            },
            {
                'name': 'Анализ мочи',
                'description': 'Общий анализ мочи, биохимия',
                'price_range': 'от 300 руб.'
            },
        ],
        'contact_info': {
            'phone': '+7 (XXX) XXX-XX-XX',
            'email': 'info@medlab.ru',
            'address': 'г. Москва, ул. Медицинская, д. 1'
        }
    }
    return Response(services)


# HTML views
def home(request):
    """Главная страница"""
    return render(request, 'medical_lab/home.html')


def about(request):
    """Страница о лаборатории"""
    return render(request, 'medical_lab/about.html')


def services(request):
    """Страница услуг"""
    return render(request, 'medical_lab/services.html')


def contacts(request):
    """Страница контактов"""
    return render(request, 'medical_lab/contacts.html')


def patients_list(request):
    """Список пациентов"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для доступа к этой странице необходимо авторизоваться.')
        return redirect('users:login')

    # Фильтрация пациентов в зависимости от роли пользователя
    if request.user.is_administrator or request.user.is_moderator:
        patients = Patient.objects.all()
    elif request.user.is_regular_user:
        patients = Patient.objects.filter(created_by=request.user)
    else:
        patients = Patient.objects.none()

    # Поиск и фильтрация
    search_query = request.GET.get('search', '')
    gender_filter = request.GET.get('gender', '')
    birth_date_filter = request.GET.get('birth_date', '')

    if search_query:
        patients = patients.filter(
            Q(last_name__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(middle_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    if gender_filter:
        patients = patients.filter(gender=gender_filter)

    if birth_date_filter:
        patients = patients.filter(birth_date=birth_date_filter)

    # Пагинация
    paginator = Paginator(patients.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'patients': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'search_query': search_query,
        'gender_filter': gender_filter,
        'birth_date_filter': birth_date_filter,
    }

    return render(request, 'medical_lab/patients_list.html', context)


def create_patient(request):
    """Создание нового пациента"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для создания пациента необходимо авторизоваться.')
        return redirect('users:login')

    # Обычные пользователи не могут создавать пациентов
    if request.user.is_regular_user:
        messages.error(request, 'У вас нет прав для создания пациентов.')
        return redirect('medical_lab:patients_list')

    if not request.user.is_moderator:
        messages.error(request, 'Недостаточно прав для создания пациента.')
        return redirect('medical_lab:patients_list')

    if request.method == 'POST':
        # Используем разную форму в зависимости от роли пользователя
        if request.user.is_moderator:
            form = PatientWithUserForm(request.POST)
        else:
            form = PatientForm(request.POST)

        if form.is_valid():
            if request.user.is_moderator:
                # Для модераторов создаем пациента с пользователем
                patient = form.save(created_by=request.user)
                messages.success(request,
                                 f'Пациент {patient.get_full_name()} успешно создан! Пароль для входа отправлен на email.')
            else:
                # Для других ролей (если будут добавлены) используем старую логику
                patient = form.save(commit=False)
                patient.created_by = request.user
                patient.save()
                messages.success(request, f'Пациент {patient.get_full_name()} успешно создан!')

            return redirect('medical_lab:patients_list')
    else:
        # Используем разную форму в зависимости от роли пользователя
        if request.user.is_moderator:
            form = PatientWithUserForm()
        else:
            form = PatientForm()

    context = {
        'form': form,
        'page_title': 'Добавить пациента'
    }
    return render(request, 'medical_lab/create_patient.html', context)


def patient_detail(request, patient_id):
    """Детальная информация о пациенте"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для доступа к этой странице необходимо авторизоваться.')
        return redirect('users:login')

    patient = get_object_or_404(Patient, id=patient_id)

    # Проверка прав доступа
    if request.user.is_regular_user and patient.created_by != request.user:
        messages.error(request, 'Доступ запрещен.')
        return redirect('medical_lab:patients_list')

    # Получаем анализы пациента
    analyses = patient.analyses.all().order_by('-collection_date')

    # Статистика по анализам пациента
    total_analyses = analyses.count()
    completed_analyses = analyses.filter(status='completed').count()
    in_progress_analyses = analyses.filter(status='in_progress').count()
    registered_analyses = analyses.filter(status='registered').count()

    context = {
        'patient': patient,
        'analyses': analyses,
        'total_analyses': total_analyses,
        'completed_analyses': completed_analyses,
        'in_progress_analyses': in_progress_analyses,
        'registered_analyses': registered_analyses,
        'page_title': f'Пациент: {patient.get_full_name()}'
    }
    return render(request, 'medical_lab/patient_detail.html', context)


def edit_patient(request, patient_id):
    """Редактирование пациента"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для редактирования пациента необходимо авторизоваться.')
        return redirect('users:login')

    patient = get_object_or_404(Patient, id=patient_id)

    # Проверка прав доступа
    if not (request.user.is_administrator or request.user.is_moderator or
            (request.user.is_regular_user and patient.created_by == request.user)):
        messages.error(request, 'Недостаточно прав для редактирования этого пациента.')
        return redirect('medical_lab:patients_list')

    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, f'Данные пациента {patient.get_full_name()} успешно обновлены!')
            return redirect('medical_lab:patient_detail', patient_id=patient.id)
    else:
        form = PatientForm(instance=patient)

    context = {
        'form': form,
        'patient': patient,
        'page_title': f'Редактирование: {patient.get_full_name()}'
    }
    return render(request, 'medical_lab/edit_patient.html', context)


def analyses_list(request):
    """Список анализов"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для доступа к этой странице необходимо авторизоваться.')
        return redirect('users:login')

    # Фильтрация анализов в зависимости от роли пользователя
    if request.user.is_administrator or request.user.is_moderator:
        analyses = Analysis.objects.all()
    elif request.user.is_regular_user:
        analyses = Analysis.objects.filter(patient__created_by=request.user)
    else:
        analyses = Analysis.objects.none()

    # Фильтрация
    status_filter = request.GET.get('status', '')
    analysis_type_filter = request.GET.get('analysis_type', '')
    collection_date_filter = request.GET.get('collection_date', '')

    if status_filter:
        analyses = analyses.filter(status=status_filter)

    if analysis_type_filter:
        analyses = analyses.filter(analysis_type_id=analysis_type_filter)

    if collection_date_filter:
        analyses = analyses.filter(collection_date__date=collection_date_filter)

    # Статистика
    total_analyses = analyses.count()
    completed_analyses = analyses.filter(status='completed').count()

    # Пагинация
    paginator = Paginator(analyses.order_by('-collection_date'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'analyses': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'analysis_types': AnalysisType.objects.all(),
        'total_analyses': total_analyses,
        'completed_analyses': completed_analyses,
        'status_filter': status_filter,
        'analysis_type_filter': analysis_type_filter,
        'collection_date_filter': collection_date_filter,
    }

    return render(request, 'medical_lab/analyses_list.html', context)


def create_analysis(request):
    """Создание нового анализа"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для создания анализа необходимо авторизоваться.')
        return redirect('users:login')

    if not (request.user.is_moderator or request.user.is_regular_user):
        messages.error(request, 'Недостаточно прав для создания анализа.')
        return redirect('medical_lab:analyses_list')

    # Для обычных пользователей автоматически создаем/находим пациента
    if request.user.is_regular_user:
        try:
            patient = Patient.objects.get(created_by=request.user)
        except Patient.DoesNotExist:
            # Создаем пациента автоматически на основе данных пользователя
            patient = Patient.objects.create(
                last_name=request.user.last_name or 'User',
                first_name=request.user.first_name or 'Unknown',
                birth_date=request.user.birth_date or '2000-01-01',
                gender=request.user.gender or 'O',
                phone=request.user.phone,
                email=request.user.email,
                created_by=request.user
            )
        initial_data = {'patient': patient}
    else:
        initial_data = {}

    if request.method == 'POST':
        form = AnalysisForm(request.POST, user=request.user)
        if form.is_valid():
            analysis = form.save()
            messages.success(request, f'Анализ {analysis.analysis_type.name} успешно создан!')
            return redirect('medical_lab:analyses_list')
    else:
        form = AnalysisForm(user=request.user, initial=initial_data)

    context = {
        'form': form,
        'page_title': 'Новый анализ'
    }
    return render(request, 'medical_lab/create_analysis.html', context)


def analysis_detail(request, analysis_id):
    """Детальная информация об анализе"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для доступа к этой странице необходимо авторизоваться.')
        return redirect('users:login')

    analysis = get_object_or_404(Analysis, id=analysis_id)

    # Проверка прав доступа
    if request.user.is_regular_user and analysis.patient.created_by != request.user:
        messages.error(request, 'Доступ запрещен.')
        return redirect('medical_lab:analyses_list')

    context = {
        'analysis': analysis,
        'page_title': f'Анализ: {analysis.analysis_type.name}'
    }
    return render(request, 'medical_lab/analysis_detail.html', context)


def edit_analysis(request, analysis_id):
    """Редактирование анализа"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для редактирования анализа необходимо авторизоваться.')
        return redirect('users:login')

    analysis = get_object_or_404(Analysis, id=analysis_id)

    # Проверка прав доступа
    if not (request.user.is_administrator or request.user.is_moderator or
            (request.user.is_regular_user and analysis.patient.created_by == request.user)):
        messages.error(request, 'Недостаточно прав для редактирования этого анализа.')
        return redirect('medical_lab:analyses_list')

    if request.method == 'POST':
        form = AnalysisForm(request.POST, instance=analysis, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Анализ {analysis.analysis_type.name} успешно обновлен!')
            return redirect('medical_lab:analysis_detail', analysis_id=analysis.id)
    else:
        form = AnalysisForm(instance=analysis, user=request.user)

    context = {
        'form': form,
        'analysis': analysis,
        'page_title': f'Редактирование анализа: {analysis.analysis_type.name}'
    }
    return render(request, 'medical_lab/edit_analysis.html', context)


def add_analysis_result(request, analysis_id):
    """Добавление результата анализа"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для добавления результата необходимо авторизоваться.')
        return redirect('users:login')

    if not request.user.is_moderator:
        messages.error(request, 'Недостаточно прав для добавления результатов анализов.')
        return redirect('medical_lab:analyses_list')

    analysis = get_object_or_404(Analysis, id=analysis_id)

    if request.method == 'POST':
        form = AnalysisResultForm(request.POST, instance=analysis)
        if form.is_valid():
            analysis = form.save(commit=False)
            analysis.status = 'completed'
            analysis.lab_technician = request.user
            analysis.save()
            messages.success(request, f'Результат анализа {analysis.analysis_type.name} успешно добавлен!')
            return redirect('medical_lab:analysis_detail', analysis_id=analysis.id)
    else:
        form = AnalysisResultForm(instance=analysis)

    context = {
        'form': form,
        'analysis': analysis,
        'page_title': f'Результат анализа: {analysis.analysis_type.name}'
    }
    return render(request, 'medical_lab/add_analysis_result.html', context)


from django.db.models import Count


def reports(request):
    """Страница отчетов"""
    if not request.user.is_authenticated:
        messages.error(request, 'Для доступа к отчетам необходимо авторизоваться.')
        return redirect('users:login')

    if not (request.user.is_administrator or request.user.is_moderator):
        messages.error(request, 'Недостаточно прав для просмотра отчетов.')
        return redirect('medical_lab:home')

    # Базовые queryset
    analyses_queryset = Analysis.objects.all()
    patients_queryset = Patient.objects.all()

    # Применяем фильтры
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    analysis_type_id = request.GET.get('analysis_type')
    patient_id = request.GET.get('patient')

    if date_from:
        analyses_queryset = analyses_queryset.filter(created_at__date__gte=date_from)
    if date_to:
        analyses_queryset = analyses_queryset.filter(created_at__date__lte=date_to)
    if analysis_type_id:
        analyses_queryset = analyses_queryset.filter(analysis_type_id=analysis_type_id)
    if patient_id:
        analyses_queryset = analyses_queryset.filter(patient_id=patient_id)
        patients_queryset = patients_queryset.filter(id=patient_id)

    # Основная статистика
    total_analyses = analyses_queryset.count()
    completed_analyses = analyses_queryset.filter(status='completed').count()
    in_progress_analyses = analyses_queryset.filter(status='in_progress').count()
    registered_analyses = analyses_queryset.filter(status='registered').count()
    cancelled_analyses = analyses_queryset.filter(status='cancelled').count()

    total_patients = patients_queryset.count()

    # Статистика по типам анализов
    analysis_types_stats = analyses_queryset.values(
        'analysis_type__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')

    context = {
        # Основная статистика
        'total_analyses': total_analyses,
        'completed_analyses': completed_analyses,
        'in_progress_analyses': in_progress_analyses,
        'registered_analyses': registered_analyses,
        'cancelled_analyses': cancelled_analyses,
        'total_patients': total_patients,

        # Статистика по типам
        'analysis_types_stats': analysis_types_stats,

        # Данные для фильтров
        'analysis_types': AnalysisType.objects.all(),
        'patients': Patient.objects.all(),

        'page_title': 'Отчеты и статистика'
    }

    return render(request, 'medical_lab/reports.html', context)
