from rest_framework import serializers
from .models import Notification, UserPreference


class NotificationSerializer(serializers.ModelSerializer):
    """Converts Notification model to/from JSON"""

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = [
            'id',
            'status',
            'retry_count',
            'created_at',
            'updated_at'
        ]


class CreateNotificationSerializer(serializers.Serializer):
    """Validates incoming notification requests"""

    user_id = serializers.CharField(max_length=100)
    channel = serializers.ChoiceField(choices=['email', 'sms', 'push'])
    priority = serializers.ChoiceField(
        choices=['critical', 'high', 'normal', 'low'],
        default='normal'
    )

    message = serializers.CharField(required=False, allow_blank=True)
    template_name = serializers.CharField(max_length=100, required=False)
    template_vars = serializers.JSONField(required=False, default=dict)

    idempotency_key = serializers.CharField(
        max_length=100,
        required=False
    )

    def validate(self, data):
        """Custom validation"""

        # Must have either message or template
        if not data.get('message') and not data.get('template_name'):
            raise serializers.ValidationError(
                "Either 'message' or 'template_name' is required"
            )

        return data


class UserPreferenceSerializer(serializers.ModelSerializer):
    """Converts UserPreference model to/from JSON"""

    class Meta:
        model = UserPreference
        fields = [
            'user_id',
            'email_enabled',
            'sms_enabled',
            'push_enabled'
        ]