from rest_framework import serializers
from languages.models import Language
from languages.utils import localized_values
from .models import GoBagItem,GoBagItemTranslation
class CitizenGoBagSerializer(serializers.ModelSerializer):
    class Meta: model=GoBagItem; fields=["id","name","description","category","quantity","unit","priority_level","image","is_required","display_order"]
    def to_representation(self,obj):
        data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"name":("translated_name","name"),"description":("translated_description","description")}); data.update(values); return data
class ResponderGoBagSerializer(serializers.ModelSerializer):
    class Meta: model=GoBagItem; fields="__all__"; read_only_fields=["created_by","updated_by","deleted_at","created_at","updated_at"]
    def validate_name(self,v):
        qs=GoBagItem.all_objects.filter(name__iexact=v.strip());
        if self.instance: qs=qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError("An item with this name already exists.")
        return v.strip()
class GoBagTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=GoBagItemTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
