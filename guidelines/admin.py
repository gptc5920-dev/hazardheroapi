from django.contrib import admin
from .models import Guideline,GuidelineTranslation,GuidelineMedia,GuidelineMediaTranslation
admin.site.register(Guideline)
admin.site.register(GuidelineTranslation)
admin.site.register(GuidelineMedia)
admin.site.register(GuidelineMediaTranslation)
