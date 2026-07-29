from django.contrib import admin
from .models import EmergencyAlert,EmergencyAlertTranslation,CalamityType,CalamityTypeTranslation
admin.site.register(EmergencyAlert)
admin.site.register(EmergencyAlertTranslation)
admin.site.register(CalamityType)
admin.site.register(CalamityTypeTranslation)
