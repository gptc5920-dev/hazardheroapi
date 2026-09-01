from django.utils import timezone
from django.db.models import Prefetch
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from audit_logs.utils import audit
from common.location import distance_km,nearby_parameters,within_bounding_box
from common.permissions import PublicReadOnly
from common.views import ResponderModelViewSet
from common.permissions import IsAdministratorResponder
from .models import EmergencyAlert
from languages.utils import requested_language,completion
from languages.views import TranslationViewSet
from .models import EmergencyAlertTranslation,CalamityType,CalamityTypeTranslation
from .serializers import *
def public_alerts(): return EmergencyAlert.objects.filter(is_public=True,is_active=True,status__in=["Active","Scheduled"],published_at__isnull=False,starts_at__lte=timezone.now(),expires_at__gt=timezone.now()).select_related("recommended_evacuation_center").prefetch_related(Prefetch("translations",queryset=EmergencyAlertTranslation.objects.filter(status="Published").select_related("language"),to_attr="_published_translations"))
@extend_schema(tags=["Citizen – Alerts"])
class CitizenAlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=CitizenAlertSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; filterset_fields=["alert_type","severity_level","region","province","city_municipality","barangay"]; search_fields=["title","message","instructions","affected_areas"]; ordering_fields=["severity_level","starts_at","expires_at","published_at"]
    def get_queryset(self): return public_alerts()
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
    @action(detail=False,methods=["get"])
    def active(self,r): return self.list(r)
    @action(detail=False,methods=["get"])
    def nearby(self,r):
        lat,lon,radius=nearby_parameters(r,default_radius=20)
        found=[]
        queryset=self.filter_queryset(self.get_queryset().exclude(latitude=None).exclude(longitude=None))
        for obj in within_bounding_box(queryset,lat,lon,radius):
            obj.distance_km=round(distance_km(lat,lon,obj.latitude,obj.longitude),2)
            if obj.distance_km<=radius: found.append(obj)
        found.sort(key=lambda x:x.distance_km); return Response(self.get_serializer(found,many=True).data)
@extend_schema(tags=["Responder – Alerts"])
class ResponderAlertViewSet(ResponderModelViewSet):
    queryset=EmergencyAlert.objects.all(); serializer_class=ResponderAlertSerializer; module="alerts"; filterset_fields=["alert_type","severity_level","status","region","province","city_municipality","barangay","is_public","is_active"]; search_fields=["alert_code","title","message","affected_areas"]; ordering_fields=["title","severity_level","starts_at","expires_at","published_at","created_at"]
    def _transition(self,r,obj,status_name,action_name,**fields):
        obj.status=status_name; obj.updated_by=r.user
        for k,v in fields.items(): setattr(obj,k,v)
        obj.save(); audit(r,action_name,self.module,obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["post"])
    def publish(self,r,pk=None):
        obj=self.get_object(); now=timezone.now()
        if obj.status not in {"Draft","Scheduled"}: raise ValidationError({"status":["Only draft or scheduled alerts can be published."]})
        if obj.expires_at<=now: raise ValidationError({"expires_at":["Expired alerts cannot be published."]})
        status_name="Scheduled" if obj.starts_at>now else "Active"; return self._transition(r,obj,status_name,"publish",published_at=now)
    @action(detail=True,methods=["post"])
    def resolve(self,r,pk=None):
        obj=self.get_object()
        if obj.status not in {"Active","Scheduled"}: raise ValidationError({"status":["Only active or scheduled alerts can be resolved."]})
        return self._transition(r,obj,"Resolved","resolve",resolved_at=timezone.now(),resolved_by=r.user)
    @action(detail=True,methods=["post"])
    def cancel(self,r,pk=None):
        obj=self.get_object()
        if obj.status not in {"Active","Scheduled"}: raise ValidationError({"status":["Only active or scheduled alerts can be cancelled."]})
        return self._transition(r,obj,"Cancelled","cancel",cancelled_at=timezone.now(),cancelled_by=r.user)
    @action(detail=True,methods=["post"])
    def archive(self,r,pk=None):
        obj=self.get_object()
        if obj.status=="Archived": raise ValidationError({"status":["This alert is already archived."]})
        return self._transition(r,obj,"Archived","archive")
    @action(detail=True,methods=["get"],url_path="translation-status")
    def translation_status(self,r,pk=None): return Response(completion(self.get_object(),"translations"))
class AlertTranslationViewSet(TranslationViewSet): queryset=EmergencyAlertTranslation.objects.all(); serializer_class=AlertTranslationSerializer; parent_field="alert"; module="alert_translations"
class CitizenCalamityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=CalamityType.objects.filter(is_active=True).prefetch_related(Prefetch("translations",queryset=CalamityTypeTranslation.objects.filter(status="Published").select_related("language"),to_attr="_published_translations")); serializer_class=CitizenCalamitySerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; pagination_class=None
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
class ResponderCalamityViewSet(viewsets.ModelViewSet): queryset=CalamityType.objects.all(); serializer_class=ResponderCalamitySerializer; permission_classes=[IsAdministratorResponder]
    
class CalamityTranslationViewSet(TranslationViewSet): queryset=CalamityTypeTranslation.objects.all(); serializer_class=CalamityTranslationSerializer; parent_field="calamity"; module="calamity_translations"
