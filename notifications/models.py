from enum import auto

from django.db import models

# Create your models here.
class UserPreference(models.Model): 
    """Stores user's notification channel preferences""" 
    
    user_id = models.CharField(max_length=100, unique=True) 
    email_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True) 
    push_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Preferences for {self.user_id}"
    

class Notification(models.Model): 
    """Stores each notification""" 
    
    CHANNEL_CHOICES = [ 
        ('email', 'Email'), 
        ('sms', 'SMS'), 
        ('push', 'Push Notification'), 
    ]
    
    PRIORITY_CHOICES = [ 
        ('critical', 'Critical'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    user_id = models.CharField(max_length=100)
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    message = models.TextField()

    template_name = models.CharField(max_length=100, blank=True)
    template_vars = models.JSONField(default=dict, blank=True)

    idempotency_key = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['idempotency_key']),
        ]

    def __str__(self):
        return f"{self.channel} to {self.user_id} - {self.status}"