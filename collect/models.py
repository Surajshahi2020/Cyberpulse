from django.db import models
from django.utils import timezone
import datetime

class ThreatAlert(models.Model):
    # 🔹 Define choices inside the model
    CATEGORY_CHOICES = [
        ('Genz', 'Genz'),
        ('Chapagau', 'Chapagau'),
        ('UML', 'UML'),
        ('Bhrikuti Mandav', 'Bhrikuti Mandav'),
        ('Samakoshi', 'Samakoshi'),
        ('PM', 'PM'),
        ('People', 'People'),
        ('Protest', 'Protest'),
        ('Disinformation', 'Disinformation / Fake News'),
        ('Army', 'Army'),
        ('Police', 'Police'),
        ('APF', 'APF'),
        ('NationalCyberCrime', 'National CyberCrime'),
        ('InternationalCyberCrime', 'International CyberCrime'),
        ('ElectionManipulation', 'Election Manipulation'),
        ('SocialEngineering', 'Social Engineering'),
        ('DataLeak', 'Data Leak'),
        ('Scam', 'Financial Scam'),
        ('Impersonation', 'Impersonation'),
        ('Malware', 'Malware / Infected Links'),
        ('Other', 'Other'),
    ]

    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
         ('critical', 'Critical'), 
    ]

    title = models.CharField(max_length=300)
    image = models.ImageField(upload_to='threat_alerts/', blank=True, null=True)
    video = models.FileField(upload_to='threat_alerts/videos/', blank=True, null=True, 
                           help_text="Upload video files")
    content = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='Other'
    )
    source = models.CharField(max_length=50, default='unknown')
    url = models.URLField(unique=True)
    severity = models.CharField(
        max_length=10,
        choices=SEVERITY_CHOICES,
        default='low'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.id}: {self.title}"
    
    @property
    def has_media(self):
        return bool(self.image or self.video)

    @property
    def media_type(self):
        if self.video:
            return 'video'
        elif self.image:
            return 'image'
        return 'none'
    