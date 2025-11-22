# collect/admin.py
from django.contrib import admin
from .models import ThreatAlert, CurrentInformation  # ✅ Correct relative import

admin.site.register(ThreatAlert)
admin.site.register(CurrentInformation)