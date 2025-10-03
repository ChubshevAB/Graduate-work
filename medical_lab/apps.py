from django.apps import AppConfig


class MedicalLabConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "medical_lab"

    # def ready(self):
    # Импортируем и регистрируем сигналы
    # import medical_lab.signals
