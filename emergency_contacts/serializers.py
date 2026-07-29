from rest_framework import serializers
from languages.models import Language
from languages.utils import localized_values
from .models import EmergencyContact,EmergencyContactTranslation
class CitizenContactSerializer(serializers.ModelSerializer):
    primary_phone_uri=serializers.SerializerMethodField(); hotline_uri=serializers.SerializerMethodField()
    def get_primary_phone_uri(self,o) -> str: return "tel:"+"".join(c for c in o.primary_phone_number if c.isdigit() or c=="+")
    def get_hotline_uri(self,o) -> str|None: return "tel:"+"".join(c for c in o.hotline_number if c.isdigit() or c=="+") if o.hotline_number else None
    class Meta: model=EmergencyContact; fields=["id","organization_name","contact_person","contact_type","description","primary_phone_number","primary_phone_uri","secondary_phone_number","hotline_number","hotline_uri","email","region","province","city_municipality","barangay","street_address","availability","office_hours","emergency_types","priority_order","logo"]
    def to_representation(self,obj): data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"description":("translated_description","description")}); data.update(values); return data
class ResponderContactSerializer(serializers.ModelSerializer):
    class Meta: model=EmergencyContact; fields="__all__"; read_only_fields=["created_by","updated_by","deleted_at","created_at","updated_at"]
class ContactTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=EmergencyContactTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
