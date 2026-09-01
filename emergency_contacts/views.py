from drf_spectacular.utils import extend_schema
from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from audit_logs.utils import audit
from common.permissions import PublicReadOnly
from common.views import ResponderModelViewSet
from languages.utils import requested_language,completion
from languages.views import TranslationViewSet
from .models import EmergencyContact,EmergencyContactTranslation
from .serializers import *
@extend_schema(tags=["Citizen – Emergency Contacts"])
class CitizenContactViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=EmergencyContact.objects.filter(is_active=True,is_verified=True).prefetch_related(Prefetch("translations",queryset=EmergencyContactTranslation.objects.filter(status="Published").select_related("language"),to_attr="_published_translations")); serializer_class=CitizenContactSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; filterset_fields=["contact_type","availability","barangay","city_municipality","province"]; search_fields=["organization_name","description","contact_person"]; ordering_fields=["organization_name","priority_order"]
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
@extend_schema(tags=["Responder – Emergency Contacts"])
class ResponderContactViewSet(ResponderModelViewSet):
    queryset=EmergencyContact.objects.all(); serializer_class=ResponderContactSerializer; module="emergency_contacts"; filterset_fields=["contact_type","availability","region","province","city_municipality","barangay","is_verified","is_active"]; search_fields=["organization_name","description","contact_person"]; ordering_fields=["organization_name","priority_order","created_at"]
    @action(detail=True,methods=["post"])
    def verify(self,r,pk=None):
        obj=self.get_object()
        if obj.is_verified: raise ValidationError({"is_verified":["This contact is already verified."]})
        obj.is_verified=True; obj.updated_by=r.user; obj.save(); audit(r,"verify",self.module,obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["get"],url_path="translation-status")
    def translation_status(self,r,pk=None): return Response(completion(self.get_object(),"translations"))
class ContactTranslationViewSet(TranslationViewSet): queryset=EmergencyContactTranslation.objects.all(); serializer_class=ContactTranslationSerializer; parent_field="contact"; module="contact_translations"
