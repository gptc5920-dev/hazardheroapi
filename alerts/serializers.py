from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from common.validators import clean_string_list,clean_text,validate_latitude as validate_latitude_value,validate_longitude as validate_longitude_value
from languages.models import Language
from languages.serializers import CleanTranslationFieldsMixin
from languages.utils import localized_values,choose_translation
from .models import EmergencyAlert,EmergencyAlertTranslation,CalamityType,CalamityTypeTranslation
class CitizenAlertSerializer(serializers.ModelSerializer):
    distance_km=serializers.FloatField(read_only=True); recommended_evacuation_center_name=serializers.CharField(source="recommended_evacuation_center.name",read_only=True)
    class Meta: model=EmergencyAlert; fields=["id","alert_code","title","message","instructions","alert_type","severity_level","source","region","province","city_municipality","barangay","latitude","longitude","radius_km","affected_areas","evacuation_required","recommended_evacuation_center","recommended_evacuation_center_name","attachment","image","starts_at","expires_at","published_at","distance_km"]
    def to_representation(self,obj):
        data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"title":("translated_title","title"),"message":("translated_message","message"),"instructions":("translated_instructions","instructions")}); translation,_,_=choose_translation(obj,"translations",self.context["language"]); values["affected_area_description"]=translation.translated_affected_area_description if translation else ""; data.update(values); return data
class ResponderAlertSerializer(serializers.ModelSerializer):
    class Meta: model=EmergencyAlert; fields="__all__"; read_only_fields=["alert_code","status","published_at","resolved_at","resolved_by","cancelled_at","cancelled_by","created_by","updated_by","deleted_at","created_at","updated_at"]
    def validate_latitude(self,v): validate_latitude_value(v); return v
    def validate_longitude(self,v): validate_longitude_value(v); return v
    def validate_affected_areas(self,v): return clean_string_list(v,field_name="Affected areas")
    def validate_radius_km(self,v):
        if v is not None and v<=0: raise serializers.ValidationError("Radius must be greater than zero.")
        return v
    def validate(self,d):
        start=d.get("starts_at",getattr(self.instance,"starts_at",None)); end=d.get("expires_at",getattr(self.instance,"expires_at",None)); severity=d.get("severity_level",getattr(self.instance,"severity_level",None)); instructions=d.get("instructions",getattr(self.instance,"instructions","")); evac=d.get("evacuation_required",getattr(self.instance,"evacuation_required",False)); areas=d.get("affected_areas",getattr(self.instance,"affected_areas",[]))
        errors={}
        for field,label,allow_blank in (("title","Title",False),("message","Message",False),("instructions","Instructions",True),("source","Source",False),("region","Region",True),("province","Province",True),("city_municipality","Municipality",True),("barangay","Barangay",True)):
            if field in d:
                try: d[field]=clean_text(d[field],field_name=label,allow_blank=allow_blank)
                except DjangoValidationError as error: errors[field]=error.messages
        latitude=d.get("latitude",getattr(self.instance,"latitude",None)); longitude=d.get("longitude",getattr(self.instance,"longitude",None))
        if (latitude is None)!=(longitude is None):
            errors["location"]="Latitude and longitude must be provided together."
        if start and end and end<=start: errors["expires_at"]="Expiration must be later than start."
        if severity=="Critical" and not instructions.strip(): errors["instructions"]="Critical alerts require safety instructions."
        if evac and not areas: errors["affected_areas"]="Evacuation alerts require an affected area."
        if errors: raise serializers.ValidationError(errors)
        return d
class AlertTranslationSerializer(CleanTranslationFieldsMixin,serializers.ModelSerializer):
    translated_text_fields={"translated_title":("Translated title",False),"translated_message":("Translated message",False),"translated_instructions":("Translated instructions",True),"translated_affected_area_description":("Translated affected area description",True)}
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=EmergencyAlertTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
class CitizenCalamitySerializer(serializers.ModelSerializer):
    class Meta: model=CalamityType; fields=["id","name","description"]
    def to_representation(self,obj): data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"name":("translated_name","name"),"description":("translated_description","description")}); data.update(values); return data
class ResponderCalamitySerializer(serializers.ModelSerializer):
    class Meta: model=CalamityType; fields="__all__"
    def validate_name(self,v):
        v=clean_text(v,field_name="Name"); qs=CalamityType.objects.filter(name__iexact=v)
        if self.instance: qs=qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError("A calamity with this name already exists.")
        return v
    def validate_description(self,v): return clean_text(v,field_name="Description")
class CalamityTranslationSerializer(CleanTranslationFieldsMixin,serializers.ModelSerializer):
    translated_text_fields={"translated_name":("Translated name",False),"translated_description":("Translated description",False)}
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=CalamityTypeTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
