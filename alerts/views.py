from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from audit_logs.utils import audit
from common.location import distance_km
from common.permissions import PublicReadOnly
from common.views import ResponderModelViewSet
from common.permissions import IsAdministratorResponder
from .models import EmergencyAlert
from languages.utils import requested_language,completion
from languages.views import TranslationViewSet
from .models import EmergencyAlertTranslation,CalamityType,CalamityTypeTranslation
from .serializers import *
def public_alerts(): return EmergencyAlert.objects.filter(is_public=True,is_active=True,status="Active",published_at__isnull=False,starts_at__lte=timezone.now(),expires_at__gt=timezone.now())
@extend_schema(tags=["Citizen – Alerts"])
class CitizenAlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class=CitizenAlertSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; filterset_fields=["alert_type","severity_level","region","province","city_municipality","barangay"]; search_fields=["title","message","instructions","affected_areas"]; ordering_fields=["severity_level","starts_at","expires_at","published_at"]
    def get_queryset(self): return public_alerts()
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
    @action(detail=False,methods=["get"])
    def active(self,r): return self.list(r)
    @action(detail=False,methods=["get"])
    def nearby(self,r):
        try: lat=float(r.query_params["latitude"]); lon=float(r.query_params["longitude"]); radius=float(r.query_params.get("radius",20))
        except (KeyError,ValueError): return Response({"detail":"Valid latitude, longitude, and radius are required."},status=400)
        found=[]
        for obj in self.filter_queryset(self.get_queryset().exclude(latitude=None).exclude(longitude=None)):
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
        obj=self.get_object(); now=timezone.now(); status_name="Scheduled" if obj.starts_at>now else "Active"; return self._transition(r,obj,status_name,"publish",published_at=now)
    @action(detail=True,methods=["post"])
    def resolve(self,r,pk=None): return self._transition(r,self.get_object(),"Resolved","resolve",resolved_at=timezone.now(),resolved_by=r.user)
    @action(detail=True,methods=["post"])
    def cancel(self,r,pk=None): return self._transition(r,self.get_object(),"Cancelled","cancel",cancelled_at=timezone.now(),cancelled_by=r.user)
    @action(detail=True,methods=["post"])
    def archive(self,r,pk=None): return self._transition(r,self.get_object(),"Archived","archive")
    @action(detail=True,methods=["get"],url_path="translation-status")
    def translation_status(self,r,pk=None): return Response(completion(self.get_object(),"translations"))
class AlertTranslationViewSet(TranslationViewSet): queryset=EmergencyAlertTranslation.objects.all(); serializer_class=AlertTranslationSerializer; parent_field="alert"; module="alert_translations"
class CitizenCalamityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=CalamityType.objects.filter(is_active=True); serializer_class=CitizenCalamitySerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; pagination_class=None
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
class ResponderCalamityViewSet(viewsets.ModelViewSet): queryset=CalamityType.objects.all(); serializer_class=ResponderCalamitySerializer; permission_classes=[IsAdministratorResponder]
    
class CalamityTranslationViewSet(TranslationViewSet): queryset=CalamityTypeTranslation.objects.all(); serializer_class=CalamityTranslationSerializer; parent_field="calamity"; module="calamity_translations"
