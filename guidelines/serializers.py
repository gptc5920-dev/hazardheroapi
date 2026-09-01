import os
import re
from urllib.parse import parse_qs, urlparse
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from common.validators import IMAGE, VECTOR, VIDEO, clean_text
from languages.models import Language
from languages.utils import localized_values
from .models import Guideline,GuidelineTranslation,GuidelineMedia,GuidelineMediaTranslation

YOUTUBE_HOSTS={"youtube.com","m.youtube.com","youtu.be","youtube-nocookie.com"}
VIMEO_HOSTS={"vimeo.com","player.vimeo.com"}
def external_media_provider(url):
    parsed=urlparse(url); host=(parsed.hostname or "").lower().removeprefix("www.")
    if parsed.scheme!="https" or not host: return None
    segments=[segment for segment in parsed.path.split("/") if segment]
    if host in YOUTUBE_HOSTS:
        video_id=segments[0] if host=="youtu.be" and segments else parse_qs(parsed.query).get("v",[None])[0]
        if not video_id and len(segments)>=2 and segments[0] in {"embed","shorts","live"}: video_id=segments[1]
        return "youtube" if video_id and re.fullmatch(r"[A-Za-z0-9_-]{6,}",video_id) else None
    if host in VIMEO_HOSTS: return "vimeo" if any(segment.isdigit() for segment in segments) else None
    return "direct"

class CitizenMediaSerializer(serializers.ModelSerializer):
    requested_language=serializers.SerializerMethodField(); returned_language=serializers.SerializerMethodField(); used_fallback=serializers.SerializerMethodField(); media_url=serializers.SerializerMethodField(); provider=serializers.SerializerMethodField(); title=serializers.SerializerMethodField(); description=serializers.SerializerMethodField(); caption_text=serializers.SerializerMethodField(); subtitle_url=serializers.SerializerMethodField()
    class Meta: model=GuidelineMedia; fields=["id","source_type","media_type","provider","requested_language","returned_language","used_fallback","title","description","caption_text","media_url","subtitle_url","updated_at"]
    def _selected(self,o):
        code=self.context["language"]; published=list(o.translations.filter(status="Published").select_related("language")); requested=next((x for x in published if x.language.language_code==code),None); english=next((x for x in published if x.language.language_code=="en"),None); t=requested or english; return t,(t.language.language_code if t else "en"),bool(code!="en" and not requested)
    def get_requested_language(self,o): return self.context["language"]
    def get_returned_language(self,o): return self._selected(o)[1]
    def get_used_fallback(self,o): return self._selected(o)[2]
    def get_title(self,o): t,_,_=self._selected(o); return t.translated_title if t else o.title
    def get_description(self,o): t,_,_=self._selected(o); return t.translated_description if t else o.description
    def get_caption_text(self,o): t,_,_=self._selected(o); return t.caption_text if t else ""
    def _url(self,f): return self.context["request"].build_absolute_uri(f.url) if f else None
    def get_media_url(self,o):
        t,_,_=self._selected(o)
        if t and t.alternative_media_file: return self._url(t.alternative_media_file)
        if o.source_type=="link": return o.external_url
        return self._url(o.media_file)
    def get_provider(self,o):
        t,_,_=self._selected(o)
        if t and t.alternative_media_file: return "upload"
        return external_media_provider(o.external_url) if o.source_type=="link" else "upload"
    def get_subtitle_url(self,o): t,_,_=self._selected(o); return self._url(t.subtitle_file) if t and t.subtitle_file else None
class CitizenGuidelineSerializer(serializers.ModelSerializer):
    media=serializers.SerializerMethodField()
    class Meta: model=Guideline; fields=["id","title","slug","summary","content","safety_instructions","category","emergency_type","featured_image","is_featured","published_at","version","media"]
    def to_representation(self,obj):
        data=super().to_representation(obj); values,_=localized_values(obj,"translations",self.context["language"],{"title":("translated_title","title"),"summary":("translated_summary","summary"),"content":("translated_content","content"),"safety_instructions":("translated_safety_instructions","safety_instructions")}); data.update(values); return data
    def get_media(self,o) -> list: return CitizenMediaSerializer(getattr(o,"_active_media",o.media.filter(is_active=True)),many=True,context=self.context).data
class ResponderGuidelineSerializer(serializers.ModelSerializer):
    class Meta: model=Guideline; fields="__all__"; read_only_fields=["slug","status","version","created_by","updated_by","deleted_at","created_at","updated_at","published_at"]
    def validate_title(self,v):
        v=clean_text(v,field_name="Title"); qs=Guideline.all_objects.filter(title__iexact=v)
        if self.instance: qs=qs.exclude(pk=self.instance.pk)
        if qs.exists(): raise serializers.ValidationError("A guideline with this title already exists.")
        return v
    def validate(self,d):
        errors={}
        for field,label,allow_blank in (("summary","Summary",False),("content","Content",False),("safety_instructions","Safety instructions",True)):
            if field in d:
                try: d[field]=clean_text(d[field],field_name=label,allow_blank=allow_blank)
                except DjangoValidationError as error: errors[field]=error.messages
        if errors: raise serializers.ValidationError(errors)
        return d
class GuidelineTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=GuidelineTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
    def validate(self,d):
        errors={}
        for field,label,allow_blank in (("translated_title","Translated title",False),("translated_summary","Translated summary",False),("translated_content","Translated content",False),("translated_safety_instructions","Translated safety instructions",True)):
            if field in d:
                try: d[field]=clean_text(d[field],field_name=label,allow_blank=allow_blank)
                except DjangoValidationError as error: errors[field]=error.messages
        if errors: raise serializers.ValidationError(errors)
        return d
class GuidelineMediaSerializer(serializers.ModelSerializer):
    class Meta: model=GuidelineMedia; fields="__all__"; read_only_fields=["id","created_at","updated_at"]
    def validate(self,d):
        source_type=d.get("source_type",getattr(self.instance,"source_type","upload")); media_type=d.get("media_type",getattr(self.instance,"media_type",None)); f=d.get("media_file",getattr(self.instance,"media_file",None)); external_url=d.get("external_url",getattr(self.instance,"external_url","")).strip()
        if "title" in d: d["title"]=clean_text(d["title"],field_name="Title")
        if "description" in d: d["description"]=clean_text(d["description"],field_name="Description",allow_blank=True)
        errors={}
        if source_type=="upload":
            if not f: errors["media_file"]="Choose a media file to upload."
            if d.get("external_url"): errors["external_url"]="Uploaded media cannot also use an external link."
        elif source_type=="link":
            provider=external_media_provider(external_url)
            if not external_url: errors["external_url"]="Enter an HTTPS media link."
            elif provider is None: errors["external_url"]="Only secure HTTPS media links are allowed."
            elif provider in {"youtube","vimeo"} and media_type!="video": errors["media_type"]="YouTube and Vimeo links must use the Video type."
            elif provider=="direct":
                ext=os.path.splitext(urlparse(external_url).path)[1].lower()
                allowed={"image":IMAGE,"video":VIDEO,"svg":VECTOR,"icon":IMAGE|VECTOR}.get(media_type,set())
                if ext not in allowed: errors["external_url"]="The direct link file type does not match the selected media type."
            d["external_url"]=external_url
        else: errors["source_type"]="Select an uploaded file or embedded link."
        if source_type=="upload" and f:
            ext=os.path.splitext(f.name)[1].lower()
            allowed={"image":IMAGE,"video":VIDEO,"svg":VECTOR,"icon":IMAGE|VECTOR}.get(media_type,set())
            if ext not in allowed: errors["media_file"]="The uploaded file type does not match the selected media type."
        if errors: raise serializers.ValidationError(errors)
        return d
    def create(self,d):
        if d.get("source_type","upload")=="link": d["media_file"]=None
        else: d["external_url"]=""
        return super().create(d)
    def update(self,obj,d):
        source_type=d.get("source_type",obj.source_type)
        if source_type=="link": d["media_file"]=None
        else: d["external_url"]=""
        return super().update(obj,d)
class GuidelineMediaTranslationSerializer(serializers.ModelSerializer):
    language=serializers.SlugRelatedField(slug_field="language_code",queryset=Language.objects.all())
    class Meta: model=GuidelineMediaTranslation; fields="__all__"; read_only_fields=["id","version","published_at","created_by","updated_by","created_at","updated_at"]
    def validate(self,d):
        media=d.get("media",getattr(self.instance,"media",None)); alternative=d.get("alternative_media_file")
        errors={}
        for field,label,allow_blank in (("translated_title","Translated title",False),("translated_description","Translated description",True),("caption_text","Caption text",True)):
            if field in d:
                try: d[field]=clean_text(d[field],field_name=label,allow_blank=allow_blank)
                except DjangoValidationError as error: errors[field]=error.messages
        if alternative and media:
            extension=os.path.splitext(alternative.name)[1].lower(); allowed={"image":IMAGE,"video":VIDEO,"svg":VECTOR,"icon":IMAGE|VECTOR}.get(media.media_type,set())
            if extension not in allowed: errors["alternative_media_file"]="The translated media file type must match the original media type."
        if errors: raise serializers.ValidationError(errors)
        return d
