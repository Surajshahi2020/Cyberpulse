# collect/admin.py
from django.contrib import admin
from .models import ThreatAlert, CurrentInformation, NewsSource # ✅ Correct relative import

admin.site.register(ThreatAlert)
admin.site.register(CurrentInformation)
admin.site.register(NewsSource)



