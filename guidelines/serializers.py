import os
from rest_framework import serializers
from languages.models import Language
from languages.utils import localized_values
from .models import Guideline,GuidelineTranslation,GuidelineMedia,GuidelineMediaTranslation
class CitizenMediaSerializer(serializers.ModelSerializer):
    requested_language=serializers.SerializerMethodField(); returned_language=serializers.SerializerMethodField(); used_fallback=serializers.SerializerMethodField(); media_url=serializers.SerializerMethodField(); title=serializers.SerializerMethodField(); description=serializers.SerializerMethodField(); caption_text=serializers.SerializerMethodField(); subtitle_url=serializers.SerializerMethodField()
    class Meta: model=GuidelineMedia; fields=["id","media_type","requested_language","returned_language","used_fallback","title","description","caption_text","media_url","subtitle_url","updated_at"]
    def _selected(self,o):
        code=self.context["language"]; published=list(o.translations.filter(status="Published").select_related("language")); requested=next((x for x in published if x.language.language_code==code),None); english=next((x for x in published if x.language.language_code=="en"),None); t=requested or english; return t,(t.language.language_code if t else "en"),bool(code!="en" and not requested)
    def get_requested_language(self,o): return self.context["language"]
    def get_returned_language(self,o): return self._selected(o)[1]
    def get_used_fallback(self,o): return self._selected(o)[2]
    def get_title(self,o): t,_,_=self._selected(o); return t.translated_title if t else o.title
    def get_description(self,o): t,_,_=self._selected(o); return t.translated_description if t else o.description
    def get_caption_text(self,o): t,_,_=self._selected(o); return t.caption_text if t else ""
    def _url(self,f): return self.context["request"].build_absolute_uri(f.url) if f else None
    def get_media_url(self,o): t,_,_=self._selected(o); return self._url(t.alternative_media_file if t and t.alternative_media_file else o.media_file)
    def get_subtitle_url(self,o): t,_,_=self._selected(o); return self._url(t.subtitle_file) if t and t.subtitle_file else None
class CitizenGuidelineSerializer(serializers.ModelSerializer):
    media=serializers.SerializerMethodField()
    class Meta: model=Guideline; fields=["id","title","slug","summary","content","safety_instructions","category","emergency_type","featured_image","is_featured","published_at","version","media"]
    def to_representation(self,obj):
        data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"title":("translated_title","title"),"summary":("translated_summary","summary"),"content":("translated_content","content"),"safety_instructions":("translated_safety_instructions","safety_instructions")}); data.update(values); return data
    def get_media(self,o) -> list: return CitizenMediaSerializer(o.media.filter(is_active=True),many=True,context=self.context).data
class ResponderGuidelineSerializer(serializers.ModelSerializer):
    class Meta: model=Guideline; fields="__all__"; read_only_fields=["slug","version","created_by","updated_by","deleted_at","created_at","updated_at","published_at"]
class GuidelineTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=GuidelineTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
class GuidelineMediaSerializer(serializers.ModelSerializer):
    class Meta: model=GuidelineMedia; fields="__all__"; read_only_fields=["id","created_at","updated_at"]
    def validate(self,d):
        media_type=d.get("media_type",getattr(self.instance,"media_type",None)); f=d.get("media_file")
        if f:
            ext=os.path.splitext(f.name)[1].lower()
            if media_type=="image" and ext not in {".jpg",".jpeg",".png",".webp"}: raise serializers.ValidationError({"media_file":"Image media requires JPEG, PNG, or WebP."})
            if media_type=="video" and ext not in {".mp4",".webm",".mov"}: raise serializers.ValidationError({"media_file":"Video media requires MP4, WebM, or MOV."})
        return d
class GuidelineMediaTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=GuidelineMediaTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
