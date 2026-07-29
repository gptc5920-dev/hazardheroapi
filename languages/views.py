from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.db.models import Case,When,Value,IntegerField
from rest_framework import mixins,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from audit_logs.utils import audit
from common.permissions import PublicReadOnly,IsAdministratorResponder
from .models import Language
from .serializers import PublicLanguageSerializer,ResponderLanguageSerializer
@extend_schema(tags=["Citizen – Languages"])
class PublicLanguageViewSet(mixins.ListModelMixin,viewsets.GenericViewSet):
    queryset=Language.objects.filter(is_active=True); serializer_class=PublicLanguageSerializer; permission_classes=[PublicReadOnly]; authentication_classes=[]; pagination_class=None
    def get_queryset(self): return super().get_queryset().order_by(Case(When(language_code="en",then=Value(0)),When(language_code="fil",then=Value(1)),When(language_code="ceb",then=Value(2)),default=Value(3),output_field=IntegerField()))
@extend_schema(tags=["Responder – Languages"])
class ResponderLanguageViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,viewsets.GenericViewSet):
    queryset=Language.objects.all(); serializer_class=ResponderLanguageSerializer; permission_classes=[IsAdministratorResponder]; http_method_names=["get","patch","head","options"]
class TranslationViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAdministratorResponder]; parent_field=""; module="translations"; filterset_fields=["language__language_code","status"]; ordering_fields=["updated_at","version","status"]
    def get_queryset(self):
        qs=self.queryset.select_related("language")
        parent=self.request.query_params.get(self.parent_field)
        return qs.filter(**{self.parent_field:parent}) if parent else qs
    def perform_create(self,s): obj=s.save(created_by=self.request.user,updated_by=self.request.user); audit(self.request,"create_translation",self.module,obj)
    def perform_update(self,s): obj=s.save(updated_by=self.request.user); audit(self.request,"update_translation",self.module,obj)
    def perform_destroy(self,obj): audit(self.request,"delete_translation",self.module,obj); obj.delete()
    def _status(self,r,obj,value,action_name): obj.status=value; obj.updated_by=r.user; obj.published_at=timezone.now() if value=="Published" else obj.published_at; obj.save(); audit(r,action_name,self.module,obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["post"])
    def publish(self,r,pk=None): return self._status(r,self.get_object(),"Published","publish_translation")
    @action(detail=True,methods=["post"])
    def archive(self,r,pk=None): return self._status(r,self.get_object(),"Archived","archive_translation")
    @action(detail=True,methods=["post"],url_path="needs-review")
    def needs_review(self,r,pk=None): return self._status(r,self.get_object(),"Needs Review","review_translation")
    @action(detail=False,methods=["post"],url_path="copy-english")
    def copy_english(self,r):
        parent_id=r.data.get(self.parent_field); code=r.data.get("language")
        if not parent_id or code not in {"fil","ceb"}: return Response({"detail":f"{self.parent_field} and target language fil or ceb are required."},status=400)
        english=self.queryset.filter(**{self.parent_field:parent_id,"language__language_code":"en"}).first()
        if not english: return Response({"detail":"English translation is missing."},status=404)
        target_language=Language.objects.get(language_code=code); defaults={field:getattr(english,field) for field in english.translated_fields}; defaults.update(status="Draft",updated_by=r.user)
        obj,created=self.queryset.get_or_create(**{self.parent_field+"_id":parent_id,"language":target_language},defaults={**defaults,"created_by":r.user})
        if not created:
            for field,value in defaults.items(): setattr(obj,field,value)
            obj.save()
        audit(r,"copy_english",self.module,obj); return Response(self.get_serializer(obj).data,status=201 if created else 200)
