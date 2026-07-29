import hashlib
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from audit_logs.utils import audit
from common.permissions import PublicReadOnly,IsAdministratorResponder
from common.views import ResponderModelViewSet
from languages.utils import requested_language,completion,choose_translation
from languages.views import TranslationViewSet
from .models import Guideline,GuidelineTranslation,GuidelineMedia,GuidelineMediaTranslation
from .serializers import *
def file_metadata(request,field):
    if not field: return None
    try:
        size=field.size; sha=hashlib.sha256()
        with field.open("rb") as source:
            for chunk in iter(lambda:source.read(1024*1024),b""): sha.update(chunk)
        return {"url":request.build_absolute_uri(field.url),"file_size":size,"sha256":sha.hexdigest()}
    except (FileNotFoundError,OSError): return {"url":request.build_absolute_uri(field.url),"file_size":0,"sha256":None}
@extend_schema(tags=["Citizen – Guidelines"])
class CitizenGuidelineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=Guideline.objects.filter(status="Published",is_active=True); serializer_class=CitizenGuidelineSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; lookup_field="slug"; filterset_fields=["category","emergency_type","is_featured"]; search_fields=["title","summary","content"]; ordering_fields=["title","published_at"]
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
    @action(detail=True,methods=["get"],url_path="offline-manifest")
    def offline_manifest(self,r,slug=None):
        guideline=self.get_object(); code=requested_language(r); translation,returned,fallback=choose_translation(guideline,"translations",code); data=self.get_serializer(guideline).data; files=[]
        featured=file_metadata(r,guideline.featured_image) if guideline.featured_image else None
        if featured: files.append(featured)
        media=[]
        for item in guideline.media.filter(is_active=True):
            mt,media_language,media_fallback=choose_translation(item,"translations",code); selected=mt.alternative_media_file if mt and mt.alternative_media_file else item.media_file; entry={"id":str(item.id),"type":item.media_type,"returned_language":media_language,"used_fallback":media_fallback,"file":file_metadata(r,selected),"subtitle":file_metadata(r,mt.subtitle_file) if mt and mt.subtitle_file else None,"caption_text":mt.caption_text if mt else ""}; media.append(entry); files.extend(x for x in [entry["file"],entry["subtitle"]] if x)
        return Response({"guideline_id":str(guideline.id),"requested_language":code,"returned_language":returned,"used_fallback":fallback,"translation_version":translation.version if translation else 0,"guideline_version":guideline.version,"title":data["title"],"summary":data["summary"],"content":data["content"],"safety_instructions":data["safety_instructions"],"featured_image":featured,"media":media,"total_download_size":sum(x.get("file_size",0) for x in files),"last_updated":max(guideline.updated_at,translation.updated_at if translation else guideline.updated_at)})
@extend_schema(tags=["Responder – Guidelines"])
class ResponderGuidelineViewSet(ResponderModelViewSet):
    queryset=Guideline.objects.all(); serializer_class=ResponderGuidelineSerializer; module="guidelines"; filterset_fields=["category","emergency_type","status","is_featured","is_active"]; search_fields=["title","summary","content"]; ordering_fields=["title","published_at","created_at"]
    @action(detail=True,methods=["post"])
    def publish(self,r,pk=None): obj=self.get_object(); obj.status="Published"; obj.published_at=timezone.now(); obj.updated_by=r.user; obj.save(); audit(r,"publish",self.module,obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["post"])
    def archive(self,r,pk=None): obj=self.get_object(); obj.status="Archived"; obj.updated_by=r.user; obj.save(); audit(r,"archive",self.module,obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["get"],url_path="translation-status")
    def translation_status(self,r,pk=None): return Response(completion(self.get_object(),"translations"))
class GuidelineTranslationViewSet(TranslationViewSet): queryset=GuidelineTranslation.objects.all(); serializer_class=GuidelineTranslationSerializer; parent_field="guideline"; module="guideline_translations"
class GuidelineMediaViewSet(viewsets.ModelViewSet): queryset=GuidelineMedia.objects.all(); serializer_class=GuidelineMediaSerializer; permission_classes=[IsAdministratorResponder]; filterset_fields=["guideline","media_type","is_active"]
class GuidelineMediaTranslationViewSet(TranslationViewSet): queryset=GuidelineMediaTranslation.objects.all(); serializer_class=GuidelineMediaTranslationSerializer; parent_field="media"; module="guideline_media_translations"
