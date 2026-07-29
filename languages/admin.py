from django.contrib import admin
from .models import Language
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display=("name","language_code","is_default","is_active"); readonly_fields=("name","native_name","language_code","is_default")
    def has_add_permission(self,r): return False
    def has_delete_permission(self,r,obj=None): return False
