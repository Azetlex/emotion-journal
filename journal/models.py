# journal/models.py

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Topic(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='topics', null=True, blank=True)
    title = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return self.title

class Entry(models.Model):
    topic = models.ForeignKey(Topic, related_name='entries', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField()
    emotion = models.CharField(max_length=50)  
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
