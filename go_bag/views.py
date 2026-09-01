from drf_spectacular.utils import extend_schema
from django.db.models import Prefetch
from rest_framework import viewsets
from common.permissions import PublicReadOnly
from common.views import ResponderModelViewSet
from languages.utils import requested_language,completion
from languages.views import TranslationViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import GoBagItem,GoBagItemTranslation
from .serializers import *
@extend_schema(tags=["Citizen – Go Bag"])
class CitizenGoBagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset=GoBagItem.objects.filter(is_active=True).prefetch_related(Prefetch("translations",queryset=GoBagItemTranslation.objects.filter(status="Published").select_related("language"),to_attr="_published_translations")); serializer_class=CitizenGoBagSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; filterset_fields=["category","priority_level","is_required"]; search_fields=["name","description"]; ordering_fields=["name","display_order"]
    def get_serializer_context(self): context=super().get_serializer_context(); context["language"]=requested_language(self.request); return context
@extend_schema(tags=["Responder – Go Bag"])
class ResponderGoBagViewSet(ResponderModelViewSet):
    queryset=GoBagItem.objects.all(); serializer_class=ResponderGoBagSerializer; module="go_bag"; filterset_fields=["category","priority_level","is_required","is_active"]; search_fields=["name","description"]; ordering_fields=["name","display_order","created_at"]
    @action(detail=True,methods=["get"],url_path="translation-status")
    def translation_status(self,r,pk=None): return Response(completion(self.get_object(),"translations"))
class GoBagTranslationViewSet(TranslationViewSet):
    queryset=GoBagItemTranslation.objects.all(); serializer_class=GoBagTranslationSerializer; parent_field="item"; module="go_bag_translations"
