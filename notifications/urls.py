from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UserPreferenceViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet)
router.register(r'preferences', UserPreferenceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]