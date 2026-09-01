from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from common.validators import clean_text
from .models import Language,SUPPORTED_CODES


class CleanTranslationFieldsMixin:
    translated_text_fields = {}

    def validate(self, data):
        data = super().validate(data)
        errors = {}
        for field, options in self.translated_text_fields.items():
            if field not in data:
                continue
            label, allow_blank = options
            try:
                data[field] = clean_text(
                    data[field], field_name=label, allow_blank=allow_blank
                )
            except DjangoValidationError as error:
                errors[field] = error.messages
        if errors:
            raise serializers.ValidationError(errors)
        return data


class PublicLanguageSerializer(serializers.ModelSerializer):
    class Meta: model=Language; fields=["name","native_name","language_code","is_default"]
class ResponderLanguageSerializer(serializers.ModelSerializer):
    class Meta: model=Language; fields=["id","name","native_name","language_code","is_default","is_active","created_at","updated_at"]; read_only_fields=["id","name","native_name","language_code","is_default","created_at","updated_at"]
    def validate_is_active(self,v):
        if self.instance and self.instance.language_code=="en" and not v: raise serializers.ValidationError("English must remain active.")
        return v
