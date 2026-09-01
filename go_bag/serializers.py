from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from common.validators import clean_text
from languages.models import Language
from languages.serializers import CleanTranslationFieldsMixin
from languages.utils import localized_values
from .models import GoBagItem,GoBagItemTranslation
class CitizenGoBagSerializer(serializers.ModelSerializer):
    class Meta: model=GoBagItem; fields=["id","name","description","category","quantity","unit","priority_level","image","is_required","display_order"]
    def to_representation(self,obj):
        data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"name":("translated_name","name"),"description":("translated_description","description")}); data.update(values); return data
class ResponderGoBagSerializer(serializers.ModelSerializer):
    class Meta: model=GoBagItem; fields="__all__"; read_only_fields=["created_by","updated_by","deleted_at","created_at","updated_at"]
    def validate_name(self,v):
        v=clean_text(v,field_name="Name"); qs=GoBagItem.all_objects.filter(name__iexact=v);
        if self.instance: qs=qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError("An item with this name already exists.")
        return v
    def validate(self,d):
        errors={}
        for field,label in (("description","Description"),("unit","Unit")):
            if field in d:
                try: d[field]=clean_text(d[field],field_name=label)
                except DjangoValidationError as error: errors[field]=error.messages
        quantity=d.get("quantity",getattr(self.instance,"quantity",1))
        if quantity is not None and quantity<1: errors["quantity"]="Quantity must be at least 1."
        if errors: raise serializers.ValidationError(errors)
        return d
class GoBagTranslationSerializer(CleanTranslationFieldsMixin,serializers.ModelSerializer):
    translated_text_fields={"translated_name":("Translated name",False),"translated_description":("Translated description",False)}
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=GoBagItemTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
