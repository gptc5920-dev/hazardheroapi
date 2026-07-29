from drf_spectacular.utils import extend_schema
from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from audit_logs.utils import audit
from common.location import distance_km
from common.permissions import PublicReadOnly
from common.views import ResponderModelViewSet
from languages.utils import requested_language,completion
from languages.views import TranslationViewSet
from .models import EvacuationCenter,EvacuationCenterTranslation
from .serializers import *
@extend_schema(tags=["Citizen – Evacuation Centers"])
class CitizenEvacuationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=EvacuationCenter.objects.filter(is_active=True,operating_status="Operational"); serializer_class=CitizenEvacuationSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; filterset_fields=["barangay","city_municipality","province","availability_status","facility_type","is_pwd_accessible","accepts_pets"]; search_fields=["name","barangay","city_municipality"]; ordering_fields=["name","available_slots"]
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
    @action(detail=False,methods=["get"])
    def nearby(self,r):
        try: lat=float(r.query_params["latitude"]); lon=float(r.query_params["longitude"]); radius=float(r.query_params.get("radius",10))
        except (KeyError,ValueError): return Response({"detail":"Valid latitude, longitude, and radius are required."},status=400)
        found=[]
        for obj in self.filter_queryset(self.get_queryset()):
            obj.distance_km=round(distance_km(lat,lon,obj.latitude,obj.longitude),2)
            if obj.distance_km<=radius: found.append(obj)
        found.sort(key=lambda x:x.distance_km); return Response(self.get_serializer(found,many=True).data)
@extend_schema(tags=["Responder – Evacuation Centers"])
class ResponderEvacuationViewSet(ResponderModelViewSet):
    queryset=EvacuationCenter.objects.all(); serializer_class=ResponderEvacuationSerializer; module="evacuation_centers"; filterset_fields=["region","province","city_municipality","barangay","availability_status","operating_status","facility_type","is_pwd_accessible","accepts_pets","is_active"]; search_fields=["name","center_code","street_address"]; ordering_fields=["name","available_slots","total_capacity","created_at"]
    @action(detail=True,methods=["patch"])
    def capacity(self,r,pk=None):
        obj=self.get_object(); s=self.get_serializer(obj,data={k:v for k,v in r.data.items() if k in ["total_capacity","current_occupancy"]},partial=True); s.is_valid(raise_exception=True); s.save(updated_by=r.user); audit(r,"capacity_update",self.module,obj,new=s.data); return Response(s.data)
    @action(detail=True,methods=["patch"])
    def status(self,r,pk=None):
        obj=self.get_object(); s=self.get_serializer(obj,data={k:v for k,v in r.data.items() if k in ["operating_status","availability_status","is_active"]},partial=True); s.is_valid(raise_exception=True); s.save(updated_by=r.user); audit(r,"status_update",self.module,obj,new=s.data); return Response(s.data)
    @action(detail=True,methods=["get"],url_path="translation-status")
    def translation_status(self,r,pk=None): return Response(completion(self.get_object(),"translations"))
class EvacuationTranslationViewSet(TranslationViewSet): queryset=EvacuationCenterTranslation.objects.all(); serializer_class=EvacuationTranslationSerializer; parent_field="center"; module="evacuation_translations"
