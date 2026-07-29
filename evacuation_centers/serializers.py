from rest_framework import serializers
from .models import EvacuationCenter
from languages.models import Language
from languages.utils import localized_values,choose_translation
from .models import EvacuationCenterTranslation
PUBLIC=["id","name","description","region","province","city_municipality","barangay","street_address","latitude","longitude","available_slots","availability_status","contact_number","supported_emergency_types","facility_type","has_electricity","has_water_supply","has_restroom","has_medical_area","has_kitchen","has_parking","is_pwd_accessible","accepts_pets","image"]
class CitizenEvacuationSerializer(serializers.ModelSerializer):
    distance_km=serializers.FloatField(read_only=True)
    class Meta: model=EvacuationCenter; fields=PUBLIC+["distance_km"]
    def to_representation(self,obj):
        data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"description":("translated_description","description")}); translation,_,_=choose_translation(obj,"translations",self.context["language"]); values["facility_description"]=translation.translated_facility_description if translation else ""; data.update(values); return data
class ResponderEvacuationSerializer(serializers.ModelSerializer):
    class Meta: model=EvacuationCenter; fields="__all__"; read_only_fields=["available_slots","last_capacity_update","created_by","updated_by","deleted_at","created_at","updated_at"]
    def validate(self,d):
        total=d.get("total_capacity",getattr(self.instance,"total_capacity",0)); occupied=d.get("current_occupancy",getattr(self.instance,"current_occupancy",0))
        if occupied>total: raise serializers.ValidationError({"current_occupancy":"Occupancy cannot exceed total capacity."})
        return d
class EvacuationTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=EvacuationCenterTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
