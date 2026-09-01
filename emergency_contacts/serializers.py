from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from common.validators import clean_string_list,clean_text,validate_phone_number
from languages.models import Language
from languages.serializers import CleanTranslationFieldsMixin
from languages.utils import localized_values
from .models import EmergencyContact,EmergencyContactTranslation
class CitizenContactSerializer(serializers.ModelSerializer):
    primary_phone_uri=serializers.SerializerMethodField(); hotline_uri=serializers.SerializerMethodField()
    def get_primary_phone_uri(self,o) -> str: return "tel:"+"".join(c for c in o.primary_phone_number if c.isdigit() or c=="+")
    def get_hotline_uri(self,o) -> str|None: return "tel:"+"".join(c for c in o.hotline_number if c.isdigit() or c=="+") if o.hotline_number else None
    class Meta: model=EmergencyContact; fields=["id","organization_name","contact_person","contact_type","description","primary_phone_number","primary_phone_uri","secondary_phone_number","hotline_number","hotline_uri","email","region","province","city_municipality","barangay","street_address","availability","office_hours","emergency_types","priority_order","logo"]
    def to_representation(self,obj): data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"description":("translated_description","description")}); data.update(values); return data
class ResponderContactSerializer(serializers.ModelSerializer):
    class Meta: model=EmergencyContact; fields="__all__"; read_only_fields=["is_verified","created_by","updated_by","deleted_at","created_at","updated_at"]
    def validate_primary_phone_number(self,v): validate_phone_number(v); return v.strip()
    def validate_secondary_phone_number(self,v): validate_phone_number(v); return v.strip()
    def validate_hotline_number(self,v): validate_phone_number(v); return v.strip()
    def validate_emergency_types(self,v): return clean_string_list(v,field_name="Emergency types")
    def validate(self,d):
        errors={}
        for field,label,allow_blank in (("organization_name","Organization name",False),("contact_person","Contact person",True),("description","Description",True),("region","Region",False),("province","Province",False),("city_municipality","Municipality",False),("barangay","Barangay",False),("street_address","Street address",True),("office_hours","Office hours",True)):
            if field in d:
                try: d[field]=clean_text(d[field],field_name=label,allow_blank=allow_blank)
                except DjangoValidationError as error: errors[field]=error.messages
        priority=d.get("priority_order",getattr(self.instance,"priority_order",0))
        if priority is not None and priority<0: errors["priority_order"]="Priority order cannot be negative."
        if errors: raise serializers.ValidationError(errors)
        return d
class ContactTranslationSerializer(CleanTranslationFieldsMixin,serializers.ModelSerializer):
    translated_text_fields={"translated_description":("Translated description",False)}
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=EmergencyContactTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
