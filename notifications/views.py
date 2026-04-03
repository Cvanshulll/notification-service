from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Notification, UserPreference
from .serializers import (
    NotificationSerializer,
    CreateNotificationSerializer,
    UserPreferenceSerializer
)
from .services import NotificationService
from .tasks import send_notification_task


class NotificationViewSet(viewsets.ModelViewSet):
    """API endpoints for notifications"""

    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def create(self, request):
        """POST /notifications - Send a new notification"""

        serializer = CreateNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Check idempotency
        idempotency_key = data.get('idempotency_key')
        if idempotency_key:
            existing = Notification.objects.filter(
                idempotency_key=idempotency_key
            ).first()

            if existing:
                return Response(
                    NotificationSerializer(existing).data,
                    status=status.HTTP_200_OK
                )

        # Check rate limit
        if not NotificationService.check_rate_limit(data['user_id']):
            return Response(
                {'error': 'Rate limit exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        # Check user preference
        if not NotificationService.check_user_preference(
            data['user_id'],
            data['channel']
        ):
            return Response(
                {'error': f"User opted out of {data['channel']} notifications"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Render template if provided
        if data.get('template_name'):
            data['message'] = NotificationService.render_template(
                data['template_name'],
                data.get('template_vars', {})
            )

        # Create notification
        notification = Notification.objects.create(**data)
        print(notification)

        # Queue for async processing
        send_notification_task.delay(notification.id)

        return Response(
            NotificationSerializer(notification).data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, pk=None):
        """GET /notifications/:id - Get notification status"""

        notification = get_object_or_404(Notification, pk=pk)
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def user_notifications(self, request, user_id=None):
        """GET /notifications/user/:userId - Get user's notification history"""

        notifications = Notification.objects.filter(user_id=user_id)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class UserPreferenceViewSet(viewsets.ModelViewSet):
    """API endpoints for user preferences"""

    queryset = UserPreference.objects.all()
    serializer_class = UserPreferenceSerializer
    lookup_field = 'user_id'

    def create(self, request):
        """POST /preferences - Set user preferences"""

        serializer = UserPreferenceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = serializer.validated_data['user_id']

        # Update or create
        prefs, created = UserPreference.objects.update_or_create(
            user_id=user_id,
            defaults=serializer.validated_data
        )

        return Response(
            UserPreferenceSerializer(prefs).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )