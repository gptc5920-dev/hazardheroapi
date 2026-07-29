from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
@admin.register(User)
class ResponderAdmin(UserAdmin):
    ordering=("email",); list_display=("email","first_name","last_name","office","is_active","is_verified"); search_fields=("email","first_name","last_name")
    fieldsets=((None,{"fields":("email","password")}), ("Profile",{"fields":("first_name","middle_name","last_name","phone_number","position","office","profile_image","role")}), ("Access",{"fields":("is_active","is_verified","is_staff","is_superuser","groups","user_permissions")}), ("Dates",{"fields":("last_login","date_joined","created_at","updated_at")})); readonly_fields=("role","created_at","updated_at")
    add_fieldsets=((None,{"classes":("wide",),"fields":("email","first_name","last_name","password1","password2","is_active","is_verified")}),)
