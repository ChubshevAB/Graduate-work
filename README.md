# Медицинская Лаборатория - Система Управления
## 📋 О проекте  
Система управления медицинской лабораторией - это веб-приложение на Django для автоматизации процессов медицинской лаборатории. Проект включает управление пациентами, анализами, пользователями и предоставляет REST API для интеграции.

## 🏗️ Архитектура проекта  
Проект использует микросервисную архитектуру с Docker контейнеризацией:

Основные компоненты:
Django приложение - основное веб-приложение

PostgreSQL - основная база данных

Redis - кэширование и брокер сообщений

Nginx - веб-сервер и прокси

Gunicorn - WSGI сервер для Django

## 🚀 Быстрый старт  

Предварительные требования  

Docker и Docker Compose

Python 3.11+

Git

Установка и запуск  
Клонирование репозитория

```bash
git clone https://github.com/ChubshevAB/Graduate-work.git
cd medical-lab
Настройка переменных окружения
Создайте файл .env в корневой директории:
nano .env
```
### Django Settings
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,your-server-ip

### Database
POSTGRES_DB=medical_lab_db
POSTGRES_USER=medical_lab_user
POSTGRES_PASSWORD=secure-password-here

### Email Settings (для уведомлений)
EMAIL_HOST=smtp.yandex.ru
EMAIL_PORT=465
EMAIL_HOST_USER=your-email@yandex.ru
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@yandex.ru

### Application Database Configuration
DB_NAME=medical_lab_db  
DB_USER=medical_lab_user  
DB_PASSWORD=secure-password-here  
DB_HOST=postgres  
DB_PORT=5432  

### Redis
CELERY_BROKER_URL=redis://redis:6379/0  
CELERY_RESULT_BACKEND=redis://redis:6379/0 

### Запуск приложения

```bash
docker-compose up -d --build

Выполнение миграций
docker-compose exec web python manage.py migrate

Создание суперпользователя
docker-compose exec web python manage.py createsuperuser

Сбор статических файлов
docker-compose exec web python manage.py collectstatic --noinput

Приложение будет доступно по адресу: http://внешний_ip_адрес
```
## 👥 Система ролей пользователей  
Группы пользователей:  

 - Администраторы (administrators)

    Полный доступ ко всем функциям системы

    Управление пользователями

    Просмотр всех отчетов и статистики

- Модераторы (moderators)

    Создание и редактирование пациентов

    Управление анализами

    Добавление результатов анализов

    Просмотр отчетов

- Пациенты (regular users)

    Просмотр своих данных и анализов

    Запись на новые анализы

    Получение уведомлений о готовности анализов

## 📊 Основные модули системы
1. Управление пациентами  
Создание и редактирование карточек пациентов  
Поиск и фильтрация пациентов  
Медицинская история  
Автоматический расчет возраста  
2. Управление анализами  
Регистрация новых анализов  
Отслеживание статусов (зарегистрирован, в работе, выполнен, отменен)  
Ввод результатов анализов  
Автоматические email-уведомления
3. Типы анализов  
Настройка различных типов медицинских анализов  
Стоимость анализов  
Сроки выполнения  
Инструкции по подготовке  
4. Отчетность и статистика  
Статистика по анализам  
Отчеты по пациентам  
Пользовательские отчеты

## 🔧 API Endpoints  
Публичные endpoints (доступны без авторизации):  
GET /api/ - обзор API  
GET /api/public/services/ - информация об услугах  

Защищенные endpoints (требуют авторизации):  

Пациенты:  
GET /api/patients/ - список пациентов  
POST /api/patients/ - создание пациента (только модераторы)  
GET /api/patients/{id}/ - детальная информация  
PUT /api/patients/{id}/ - обновление  
GET /api/patients/{id}/analyses/ - анализы пациента  
GET /api/patients/stats/ - статистика (администраторы/модераторы)  

Анализы:  
GET /api/analyses/ - список анализов  
POST /api/analyses/ - создание анализа  
GET /api/analyses/{id}/ - детальная информация  
POST /api/analyses/{id}/set_status/ - изменение статуса  
GET /api/analyses/by_status/ - фильтрация по статусу  
GET /api/analyses/dashboard_stats/ - статистика для дашборда

Пользователи:  
GET /api/users/ - список пользователей (администраторы/модераторы)  
GET /api/users/profile/ - профиль текущего пользователя  
GET /api/users/stats/ - статистика пользователей (администраторы)  

## 🗄️ Модели данных
Основные модели:  
Patient (Пациент):  
ФИО  
Дата рождения  
Пол  
Контактная информация  
Медицинская история  
Связь с пользователем-создателем  

AnalysisType (Тип анализа):  
Название  
Описание  
Стоимость  
Срок выполнения  
Инструкции по подготовке

Analysis (Анализ):  
Связь с пациентом и типом анализа  
Статус выполнения  
Результаты и нормальные значения  
Даты забора и выполнения  
Лаборант, выполнивший анализ

User (Пользователь):  
Кастомная модель на основе AbstractUser

Аутентификация по email

Дополнительные поля: отчество, телефон, дата рождения

## 🛠️ Разработка
Локальная разработка  
Установка зависимостей

```bash
pip install -r requirements.txt
Настройка базы данных
```
```bash
python manage.py migrate
python manage.py createsuperuser
Запуск сервера разработки
```
```bash
python manage.py runserver
```
Тестирование
```bash
python manage.py test medical_lab users
flake8 . --count --max-line-length=127 --statistics --exclude=migrations
```
CI/CD Pipeline  
Проект использует GitHub Actions для автоматизации:

Тестирование и линтинг - при каждом push

Сборка Docker образа - при push в main

Security scanning - проверка безопасности

Автоматический деплой - на сервер при успешных тестах

## 🔒 Безопасность
Аутентификация по email

Ролевая модель доступа

Валидация паролей

Защита от CSRF атак

Безопасные настройки Django

Health checks для мониторинга

@@ 🐳 Docker контейнеры  
Сервисы:
web - Django приложение (Gunicorn)

postgres - База данных PostgreSQL

redis - Кэш и брокер сообщений

nginx - Веб-сервер

Health checks: Все сервисы включают health checks для мониторинга:

PostgreSQL: проверка готовности БД

Redis: ping команда

Web: проверка эндпоинта /health/

## 📈 Мониторинг и логи
Логи приложения в контейнерах

Health checks эндпоинты

Статусы сервисов через Docker Compose

Логи Nginx в отдельных файлах

## 🔄 Миграции базы данных
```bash
# Создание миграций
docker-compose exec web python manage.py makemigrations

# Применение миграций
docker-compose exec web python manage.py migrate

# Откат миграций
docker-compose exec web python manage.py migrate app_name migration_name
🚨 Аварийное восстановление
Резервное копирование базы данных:
bash
docker-compose exec postgres pg_dump -U medical_lab_user medical_lab_db > backup.sql
Восстановление из бэкапа:
bash
docker-compose exec -T postgres psql -U medical_lab_user medical_lab_db < backup.sql
```