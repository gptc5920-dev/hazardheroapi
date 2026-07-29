from rest_framework import serializers
from .models import Language,SUPPORTED_CODES
class PublicLanguageSerializer(serializers.ModelSerializer):
    class Meta: model=Language; fields=["name","native_name","language_code","is_default"]
class ResponderLanguageSerializer(serializers.ModelSerializer):
    class Meta: model=Language; fields=["id","name","native_name","language_code","is_default","is_active","created_at","updated_at"]; read_only_fields=["id","name","native_name","language_code","is_default","created_at","updated_at"]
    def validate_is_active(self,v):
        if self.instance and self.instance.language_code=="en" and not v: raise serializers.ValidationError("English must remain active.")
        return v
