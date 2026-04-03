import logging
from django.core.cache import cache
from .models import Notification, UserPreference

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles notification business logic"""

    # Template storage (in-memory for simplicity)
    TEMPLATES = {
        'welcome': 'Hello {{name}}, welcome to our platform!',
        'order_shipped': 'Hi {{name}}, your order {{order_id}} has shipped!',
        'password_reset': 'Your password reset code is {{code}}',
    }

    @staticmethod
    def render_template(template_name, variables):
        """Replace {{variable}} with actual values"""

        template = NotificationService.TEMPLATES.get(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        # Simple variable substitution
        message = template
        for key, value in variables.items():
            message = message.replace(f"{{{{{key}}}}}", str(value))

        return message

    @staticmethod
    def check_rate_limit(user_id):
        """Check if user exceeded rate limit (100 notifications/hour)"""

        cache_key = f"rate_limit:{user_id}"
        count = cache.get(cache_key, 0)

        if count >= 100:
            return False  # Rate limit exceeded

        # Increment counter (expires in 1 hour)
        cache.set(cache_key, count + 1, timeout=3600)
        return True

    @staticmethod
    def check_user_preference(user_id, channel):
        """Check if user opted-in for this channel"""

        try:
            prefs = UserPreference.objects.get(user_id=user_id)

            if channel == 'email':
                return prefs.email_enabled
            elif channel == 'sms':
                return prefs.sms_enabled
            elif channel == 'push':
                return prefs.push_enabled

        except UserPreference.DoesNotExist:
            # Default: all channels enabled
            return True

        return False