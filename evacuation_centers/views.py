from drf_spectacular.utils import extend_schema
from django.db.models import Prefetch
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from audit_logs.utils import audit
from common.location import distance_km,nearby_parameters,within_bounding_box
from common.permissions import PublicReadOnly
from common.views import ResponderModelViewSet
from languages.utils import requested_language,completion
from languages.views import TranslationViewSet
from .models import EvacuationCenter,EvacuationCenterTranslation
from .serializers import *
@extend_schema(tags=["Citizen – Evacuation Centers"])
class CitizenEvacuationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=EvacuationCenter.objects.filter(is_active=True,operating_status="Operational").prefetch_related(Prefetch("translations",queryset=EvacuationCenterTranslation.objects.filter(status="Published").select_related("language"),to_attr="_published_translations")); serializer_class=CitizenEvacuationSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; filterset_fields=["barangay","city_municipality","province","availability_status","facility_type","is_pwd_accessible","accepts_pets"]; search_fields=["name","barangay","city_municipality"]; ordering_fields=["name","available_slots"]
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
    @action(detail=False,methods=["get"])
    def nearby(self,r):
        lat,lon,radius=nearby_parameters(r,default_radius=10)
        found=[]
        queryset=within_bounding_box(self.filter_queryset(self.get_queryset()),lat,lon,radius)
        for obj in queryset:
            obj.distance_km=round(distance_km(lat,lon,obj.latitude,obj.longitude),2)
            if obj.distance_km<=radius: found.append(obj)
        found.sort(key=lambda x:x.distance_km); return Response(self.get_serializer(found,many=True).data)
@extend_schema(tags=["Responder – Evacuation Centers"])
class ResponderEvacuationViewSet(ResponderModelViewSet):
    queryset=EvacuationCenter.objects.all(); serializer_class=ResponderEvacuationSerializer; module="evacuation_centers"; filterset_fields=["region","province","city_municipality","barangay","availability_status","operating_status","facility_type","is_pwd_accessible","accepts_pets","is_active"]; search_fields=["name","center_code","street_address"]; ordering_fields=["name","available_slots","total_capacity","created_at"]
    def _action_data(self,r,allowed):
        supplied=set(r.data); unknown=supplied-set(allowed)
        if unknown: raise ValidationError({field:["This field is not accepted by this action."] for field in sorted(unknown)})
        if not supplied: raise ValidationError({"non_field_errors":["Provide at least one field to update."]})
        return {key:r.data[key] for key in supplied}
    def _locked_object(self,pk):
        queryset=self.filter_queryset(self.get_queryset()).select_for_update()
        obj=get_object_or_404(queryset,pk=pk); self.check_object_permissions(self.request,obj); return obj
    @action(detail=True,methods=["patch"])
    def capacity(self,r,pk=None):
        data=self._action_data(r,{"total_capacity","current_occupancy"})
        with transaction.atomic():
            obj=self._locked_object(pk); s=self.get_serializer(obj,data=data,partial=True); s.is_valid(raise_exception=True); s.save(updated_by=r.user); audit(r,"capacity_update",self.module,obj,new=s.data)
        return Response(s.data)
    @action(detail=True,methods=["patch"])
    def status(self,r,pk=None):
        data=self._action_data(r,{"operating_status","availability_status","is_active"})
        with transaction.atomic():
            obj=self._locked_object(pk); s=self.get_serializer(obj,data=data,partial=True); s.is_valid(raise_exception=True); s.save(updated_by=r.user); audit(r,"status_update",self.module,obj,new=s.data)
        return Response(s.data)
    @action(detail=True,methods=["get"],url_path="translation-status")
    def translation_status(self,r,pk=None): return Response(completion(self.get_object(),"translations"))
class EvacuationTranslationViewSet(TranslationViewSet): queryset=EvacuationCenterTranslation.objects.all(); serializer_class=EvacuationTranslationSerializer; parent_field="center"; module="evacuation_translations"
