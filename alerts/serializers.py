from rest_framework import serializers
from languages.models import Language
from languages.utils import localized_values,choose_translation
from .models import EmergencyAlert,EmergencyAlertTranslation,CalamityType,CalamityTypeTranslation
class CitizenAlertSerializer(serializers.ModelSerializer):
    distance_km=serializers.FloatField(read_only=True); recommended_evacuation_center_name=serializers.CharField(source="recommended_evacuation_center.name",read_only=True)
    class Meta: model=EmergencyAlert; fields=["id","alert_code","title","message","instructions","alert_type","severity_level","source","region","province","city_municipality","barangay","latitude","longitude","radius_km","affected_areas","evacuation_required","recommended_evacuation_center","recommended_evacuation_center_name","attachment","image","starts_at","expires_at","published_at","distance_km"]
    def to_representation(self,obj):
        data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"title":("translated_title","title"),"message":("translated_message","message"),"instructions":("translated_instructions","instructions")}); translation,_,_=choose_translation(obj,"translations",self.context["language"]); values["affected_area_description"]=translation.translated_affected_area_description if translation else ""; data.update(values); return data
class ResponderAlertSerializer(serializers.ModelSerializer):
    class Meta: model=EmergencyAlert; fields="__all__"; read_only_fields=["alert_code","published_at","resolved_at","resolved_by","cancelled_at","cancelled_by","created_by","updated_by","deleted_at","created_at","updated_at"]
    def validate(self,d):
        start=d.get("starts_at",getattr(self.instance,"starts_at",None)); end=d.get("expires_at",getattr(self.instance,"expires_at",None)); severity=d.get("severity_level",getattr(self.instance,"severity_level",None)); instructions=d.get("instructions",getattr(self.instance,"instructions","")); evac=d.get("evacuation_required",getattr(self.instance,"evacuation_required",False)); areas=d.get("affected_areas",getattr(self.instance,"affected_areas",[]))
        errors={}
        if start and end and end<=start: errors["expires_at"]="Expiration must be later than start."
        if severity=="Critical" and not instructions.strip(): errors["instructions"]="Critical alerts require safety instructions."
        if evac and not areas: errors["affected_areas"]="Evacuation alerts require an affected area."
        if errors: raise serializers.ValidationError(errors)
        return d
class AlertTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=EmergencyAlertTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
class CitizenCalamitySerializer(serializers.ModelSerializer):
    class Meta: model=CalamityType; fields=["id","name","description"]
    def to_representation(self,obj): data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"name":("translated_name","name"),"description":("translated_description","description")}); data.update(values); return data
class ResponderCalamitySerializer(serializers.ModelSerializer):
    class Meta: model=CalamityType; fields="__all__"
class CalamityTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=CalamityTypeTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
