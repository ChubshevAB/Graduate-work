from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Analysis
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Analysis)
def handle_analysis_status_change(sender, instance, **kwargs):
    """Отправляет email при изменении статуса анализа на 'completed'"""
    if not instance.pk:
        return  # Новый объект

    try:
        old_instance = Analysis.objects.get(pk=instance.pk)

        # Проверяем изменение статуса на 'completed'
        if old_instance.status != "completed" and instance.status == "completed":
            logger.info(f"Статус анализа {instance.id} изменен на 'completed'")

            # Устанавливаем дату выполнения
            if not instance.completion_date:
                instance.completion_date = timezone.now()

            # Отправляем email
            instance.send_completion_email()

    except Analysis.DoesNotExist:
        pass  # Игнорируем ошибку
