# collect/models.py
from django.db import models

class ThreatAlert(models.Model):
    title = models.CharField(max_length=300)
    content = models.TextField()
    source = models.CharField(max_length=50, default='unknown')
    url = models.URLField(unique=True)
    severity = models.CharField(max_length=10, default='low', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
         return f"{self.id}: {self.title}"