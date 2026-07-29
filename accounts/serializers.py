from django.contrib.auth import authenticate, password_validation
from rest_framework import serializers
from .models import User
class UserSerializer(serializers.ModelSerializer):
    password=serializers.CharField(write_only=True,required=False,validators=[password_validation.validate_password]); full_name=serializers.CharField(source="display_name",read_only=True)
    class Meta: model=User; fields=["id","first_name","middle_name","last_name","full_name","email","phone_number","position","office","profile_image","role","is_active","is_verified","last_login","created_at","updated_at","password"]; read_only_fields=["id","role","last_login","created_at","updated_at"]
    def create(self,data):
        password=data.pop("password",None)
        if not password: raise serializers.ValidationError({"password":"This field is required."})
        return User.objects.create_user(password=password,**data)
    def update(self,obj,data):
        password=data.pop("password",None); obj=super().update(obj,data)
        if password: obj.set_password(password); obj.save(update_fields=["password","updated_at"])
        return obj
class LoginSerializer(serializers.Serializer):
    email=serializers.EmailField(); password=serializers.CharField()
    def validate(self,data):
        user=authenticate(email=data["email"].lower(),password=data["password"])
        if not user: raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active: raise serializers.ValidationError("Account is inactive.")
        if not user.is_verified: raise serializers.ValidationError("Account is not verified.")
        data["user"]=user; return data
class ChangePasswordSerializer(serializers.Serializer):
    old_password=serializers.CharField(); new_password=serializers.CharField(validators=[password_validation.validate_password])
class ForgotPasswordSerializer(serializers.Serializer): email=serializers.EmailField()
class ResetPasswordSerializer(serializers.Serializer):
    uid=serializers.CharField(); token=serializers.CharField(); new_password=serializers.CharField(validators=[password_validation.validate_password])
class LogoutSerializer(serializers.Serializer): refresh=serializers.CharField()
class EmptySerializer(serializers.Serializer): pass
