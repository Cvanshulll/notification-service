from django.test import TestCase
from django.core.cache import cache

from rest_framework.test import APITestCase
from rest_framework import status

from .models import Notification, UserPreference
from .services import NotificationService


# -------------------------------
# Unit Tests (Business Logic)
# -------------------------------
class NotificationServiceTest(TestCase):
    """Test business logic"""

    def setUp(self):
        cache.clear()

    def test_render_template(self):
        """Test template rendering"""
        message = NotificationService.render_template(
            'welcome',
            {'name': 'John'}
        )
        self.assertEqual(
            message,
            'Hello John, welcome to our platform!'
        )

    def test_rate_limit(self):
        """Test rate limiting"""
        user_id = 'test_user'

        # First 100 should pass
        for _ in range(100):
            self.assertTrue(
                NotificationService.check_rate_limit(user_id)
            )

        # 101st should fail
        self.assertFalse(
            NotificationService.check_rate_limit(user_id)
        )

    def test_user_preference_default(self):
        """Test default preferences (all enabled)"""
        self.assertTrue(
            NotificationService.check_user_preference('new_user', 'email')
        )

    def test_user_preference_opt_out(self):
        """Test user opt-out"""
        UserPreference.objects.create(
            user_id='test_user',
            email_enabled=False
        )

        self.assertFalse(
            NotificationService.check_user_preference('test_user', 'email')
        )


# -------------------------------
# API Integration Tests
# -------------------------------
class NotificationAPITest(APITestCase):
    """Test API endpoints"""
    
    def setUp(self):
        from django.core.cache import cache
        cache.clear()

    def test_create_notification(self):
        """Test POST /notifications"""
        data = {
            'user_id': 'user123',
            'channel': 'email',
            'priority': 'high',
            'message': 'Test notification'
        }

        response = self.client.post('/api/notifications/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_id'], 'user123')
        self.assertEqual(response.data['status'], 'pending')

    def test_idempotency(self):
        """Test duplicate requests with same idempotency key"""
        data = {
            'user_id': 'user123',
            'channel': 'email',
            'message': 'Test',
            'idempotency_key': 'unique-key-123'
        }

        # First request
        response1 = self.client.post('/api/notifications/', data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Duplicate request
        response2 = self.client.post('/api/notifications/', data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertEqual(response1.data['id'], response2.data['id'])

    def test_rate_limit(self):
        """Test rate limiting"""
        data = {
            'user_id': 'user123',
            'channel': 'email',
            'message': 'Test'
        }

        # First 100 should succeed
        for _ in range(100):
            response = self.client.post('/api/notifications/', data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 101st should fail
        response = self.client.post('/api/notifications/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_template_rendering(self):
        """Test template-based notifications"""
        data = {
            'user_id': 'user123',
            'channel': 'email',
            'template_name': 'welcome',
            'template_vars': {'name': 'Alice'}
        }

        response = self.client.post('/api/notifications/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('Alice', response.data['message'])


class UserPreferenceAPITest(APITestCase):
    """Test user preference endpoints"""

    def test_set_preferences(self):
        """Test POST /preferences"""
        data = {
            'user_id': 'user123',
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True
        }

        response = self.client.post('/api/preferences/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['sms_enabled'], False)

    def test_get_preferences(self):
        """Test GET /preferences/:userId"""
        UserPreference.objects.create(
            user_id='user123',
            email_enabled=False
        )

        response = self.client.get('/api/preferences/user123/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email_enabled'], False)