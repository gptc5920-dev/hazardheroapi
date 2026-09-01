from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from common.validators import clean_string_list,clean_text,validate_latitude as validate_latitude_value,validate_longitude as validate_longitude_value,validate_phone_number
from .models import EvacuationCenter
from languages.models import Language
from languages.serializers import CleanTranslationFieldsMixin
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
    def validate_center_code(self,v):
        v=clean_text(v,field_name="Center code"); qs=EvacuationCenter.all_objects.filter(center_code__iexact=v)
        if self.instance: qs=qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError("An evacuation center with this code already exists.")
        return v
    def validate_latitude(self,v): validate_latitude_value(v); return v
    def validate_longitude(self,v): validate_longitude_value(v); return v
    def validate_contact_number(self,v): validate_phone_number(v); return v.strip()
    def validate_alternative_contact_number(self,v): validate_phone_number(v); return v.strip()
    def validate_supported_emergency_types(self,v): return clean_string_list(v,field_name="Supported emergency types")
    def validate(self,d):
        total=d.get("total_capacity",getattr(self.instance,"total_capacity",0)); occupied=d.get("current_occupancy",getattr(self.instance,"current_occupancy",0))
        errors={}
        for field,label,allow_blank in (("name","Name",False),("description","Description",True),("region","Region",False),("province","Province",False),("city_municipality","Municipality",False),("barangay","Barangay",False),("street_address","Street address",False),("contact_person","Contact person",False),("remarks","Remarks",True)):
            if field in d:
                try: d[field]=clean_text(d[field],field_name=label,allow_blank=allow_blank)
                except DjangoValidationError as error: errors[field]=error.messages
        if total is not None and total<0: errors["total_capacity"]="Total capacity cannot be negative."
        if occupied is not None and occupied<0: errors["current_occupancy"]="Current occupancy cannot be negative."
        if total is not None and occupied is not None and occupied>total: errors["current_occupancy"]="Occupancy cannot exceed total capacity."
        if errors: raise serializers.ValidationError(errors)
        return d
class EvacuationTranslationSerializer(CleanTranslationFieldsMixin,serializers.ModelSerializer):
    translated_text_fields={"translated_description":("Translated description",False),"translated_facility_description":("Translated facility description",True)}
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=EvacuationCenterTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
