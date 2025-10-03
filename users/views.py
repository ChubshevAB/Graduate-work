from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.contrib import messages
from .models import User
from .serializers import UserSerializer, UserCreateSerializer
from .forms import PatientRegistrationForm


class CustomLoginView(LoginView):
    template_name = 'users/login.html'

    # Используем email вместо username для аутентификации
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['username'].label = 'Email'
        form.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Введите ваш email'
        })
        return form

    def get_success_url(self):
        return reverse_lazy('medical_lab:home')

    def form_valid(self, form):
        messages.success(self.request, f'Добро пожаловать, {form.get_user().get_full_name()}!')
        return super().form_valid(form)


# Кастомные permissions для пользователей на основе групп
class IsAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_administrator


class IsModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_moderator


class IsRegularUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_regular_user


class IsAdministratorOrModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
                request.user.is_administrator or request.user.is_moderator
        )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления пользователями
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_permissions(self):
        """
        Только администраторы могут управлять пользователями
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [IsAdministratorOrModerator]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdministrator]
        else:
            permission_classes = [IsAdministrator]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Администраторы видят всех пользователей
        Модераторы видят только модераторов и users (не видят администраторов)
        """
        user = self.request.user

        if not user.is_authenticated:
            return User.objects.none()

        if user.is_administrator:
            return User.objects.all()

        if user.is_moderator:
            return User.objects.filter(
                Q(groups__name='moderators') | Q(groups__name='users')
            ).distinct()

        return User.objects.none()

    @action(detail=False, methods=['get'], permission_classes=[IsAdministrator])
    def stats(self, request):
        """
        Статистика по пользователям
        GET /api/users/stats/
        """
        from django.contrib.auth.models import Group

        total_users = User.objects.count()
        admins_count = User.objects.filter(groups__name='administrators').count()
        moderators_count = User.objects.filter(groups__name='moderators').count()
        users_count = User.objects.filter(groups__name='users').count()

        stats = {
            'total_users': total_users,
            'by_group': {
                'administrators': admins_count,
                'moderators': moderators_count,
                'users': users_count,
            }
        }
        return Response(stats)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        """
        Получить профиль текущего пользователя
        GET /api/users/profile/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


def register(request):
    """
    View для регистрации новых пациентов (пользователей)
    """
    if request.method == 'POST':
        form = PatientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически входим после регистрации
            login(request, user)
            messages.success(request, f'Регистрация прошла успешно! Добро пожаловать, {user.get_full_name()}!')
            return redirect('medical_lab:home')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = PatientRegistrationForm()

    context = {
        'form': form,
        'page_title': 'Регистрация пациента'
    }
    return render(request, 'users/register.html', context)


def custom_login(request):
    """
    Кастомная view для входа по email
    """
    if request.method == 'POST':
        email = request.POST.get('username')  # Django использует 'username' для поля логина
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name()}!')
            return redirect('medical_lab:home')
        else:
            messages.error(request, 'Неверный email или пароль.')

    return render(request, 'users/login.html')
