import logging
import time
import random

from celery import shared_task, Task
from django.utils import timezone

from .models import Notification

logger = logging.getLogger(__name__)


# -------------------------------
# Mock Notification Providers
# -------------------------------
class NotificationProviders:
    """Mock external services (Email, SMS, Push)"""

    @staticmethod
    def send_email(user_id, message):
        logger.info(f"Sending email to {user_id}: {message}")
        time.sleep(0.1)

        if random.random() < 0.1:
            raise Exception("Email service temporarily unavailable")

        return True

    @staticmethod
    def send_sms(user_id, message):
        logger.info(f"Sending SMS to {user_id}: {message}")
        time.sleep(0.1)

        if random.random() < 0.1:
            raise Exception("SMS service temporarily unavailable")

        return True

    @staticmethod
    def send_push(user_id, message):
        logger.info(f"Sending push to {user_id}: {message}")
        time.sleep(0.1)

        if random.random() < 0.1:
            raise Exception("Push service temporarily unavailable")

        return True


# -------------------------------
# Custom Priority Task
# -------------------------------
class PriorityTask(Task):
    """Custom task class with priority routing"""

    def apply_async(self, *args, **kwargs):
        # Extract notification_id
        notification_id = args[0] if args else kwargs.get('notification_id')
        
        # Handle case where notification_id can be a tuple
        if isinstance(notification_id, tuple):
            notification_id = notification_id[0]

        # notification = Notification.objects.get(id=notification_id)

        if notification_id:
            try:
                notification = Notification.objects.get(id=notification_id)

                priority_map = {
                    'critical': 9,
                    'high': 7,
                    'normal': 5,
                    'low': 3,
                }

                kwargs['priority'] = priority_map.get(notification.priority, 5)

            except Notification.DoesNotExist:
                logger.warning(f"Notification {notification_id} not found for priority assignment")

        return super().apply_async(*args, **kwargs)


# -------------------------------
# Celery Task
# -------------------------------
@shared_task(bind=True, max_retries=3, base=PriorityTask)
def send_notification_task(self, notification_id):
    """
    Background task to send notification
    - Runs asynchronously
    - Retries on failure with exponential backoff
    """
    try:
        notification = Notification.objects.get(id=notification_id)
        logger.info(f"Processing notification {notification_id}")

        # Select provider based on channel
        if notification.channel == 'email':
            NotificationProviders.send_email(
                notification.user_id,
                notification.message
            )
        elif notification.channel == 'sms':
            NotificationProviders.send_sms(
                notification.user_id,
                notification.message
            )
        elif notification.channel == 'push':
            NotificationProviders.send_push(
                notification.user_id,
                notification.message
            )

        # Update status to sent
        notification.status = 'sent'
        notification.updated_at = timezone.now()
        notification.save()
        
        logger.info(f"Notification {notification_id} sent successfully")

    except Exception as exc:
        logger.error(f"Failed to send notification {notification_id}: {exc}")

        try:
            notification = Notification.objects.get(id=notification_id)

            notification.retry_count += 1
            notification.error_message = str(exc)

            # Mark as failed if max retries reached
            if notification.retry_count >= 3:
                notification.status = 'failed'
                logger.error(f"Max retries reached for notification {notification_id}")
            else:
                notification.status = 'pending'

            notification.save()

            # Retry with exponential backoff
            if notification.retry_count < 3:
                retry_delay = 2 ** notification.retry_count
                logger.info(f"Retrying in {retry_delay} seconds...")

                raise self.retry(exc=exc, countdown=retry_delay)

        except Notification.DoesNotExist:
            logger.error(f"Notification {notification_id} no longer exists")