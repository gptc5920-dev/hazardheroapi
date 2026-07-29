from rest_framework import mixins, serializers, viewsets
from common.permissions import IsAdministratorResponder
from .models import AuditLog
class AuditSerializer(serializers.ModelSerializer):
    user_email=serializers.EmailField(source="user.email",read_only=True)
    class Meta: model=AuditLog; fields="__all__"
class AuditViewSet(mixins.ListModelMixin,mixins.RetrieveModelMixin,viewsets.GenericViewSet):
    queryset=AuditLog.objects.select_related("user"); serializer_class=AuditSerializer; permission_classes=[IsAdministratorResponder]; filterset_fields=["action","module","user"]; search_fields=["record_description","record_id","user__email"]; ordering_fields=["created_at","action","module"]
