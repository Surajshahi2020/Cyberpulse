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
    

class CurrentInformation(models.Model):
    timing = models.CharField(
        max_length=255,
        help_text="When the activity took place"
    )

    location = models.CharField(
        max_length=255,
        help_text="Where the activity took place"
    )
    leader = models.CharField(
        max_length=255,
        help_text="Name of the person in charge"
    )
    number = models.CharField(
        max_length=50,
        help_text="Contact number, ID, or team number",
        blank=True,
        null=True
    )
    vehicle = models.CharField(
        max_length=100,
        help_text="Type of vehicle used (e.g., Toyota Hilux, Motorcycle)",
        blank=True,
        null=True
    )
    description = models.TextField(
        help_text="Details of the activity or event",
        blank=True,
        null=True
    )

    # Optional: Add timestamp for when record was created
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    # Optional: Add status field
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-created_at']  # Show newest first

    def __str__(self):
        return f"{self.leader} at {self.location} on {self.timing}"
