# collect/admin.py
from django.contrib import admin
from .models import ThreatAlert  # ✅ Correct relative import

admin.site.register(ThreatAlert)