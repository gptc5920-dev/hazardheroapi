from rest_framework import status,viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from audit_logs.utils import audit
from .permissions import IsAdministratorResponder
class ResponderModelViewSet(viewsets.ModelViewSet):
    permission_classes=[IsAdministratorResponder]
    module="content"
    def get_queryset(self):
        qs=self.queryset.model.all_objects.all()
        return qs.filter(deleted_at__isnull=False) if self.action=="deleted" else qs.filter(deleted_at__isnull=True)
    def perform_create(self,s): obj=s.save(created_by=self.request.user,updated_by=self.request.user); audit(self.request,"create",self.module,obj,new=s.data)
    def perform_update(self,s): obj=s.save(updated_by=self.request.user); audit(self.request,"update",self.module,obj,new=s.data)
    def perform_destroy(self,obj): obj.soft_delete(); audit(self.request,"delete",self.module,obj)
    @action(detail=False,methods=["get"])
    def deleted(self,r):
        page=self.paginate_queryset(self.filter_queryset(self.get_queryset())); s=self.get_serializer(page if page is not None else self.get_queryset(),many=True); return self.get_paginated_response(s.data) if page is not None else Response(s.data)
    @action(detail=True,methods=["post"],url_path="restore")
    def restore(self,r,pk=None):
        obj=self.queryset.model.all_objects.filter(pk=pk,deleted_at__isnull=False).first()
        if not obj: return Response(status=404)
        obj.restore(); audit(r,"restore",self.module,obj); return Response(self.get_serializer(obj).data)
    @action(detail=True,methods=["delete"],url_path="permanent-delete")
    def permanent_delete(self,r,pk=None):
        obj=self.queryset.model.all_objects.filter(pk=pk).first()
        if not obj: return Response(status=404)
        audit(r,"permanent_delete",self.module,obj); obj.permanent_delete(); return Response(status=204)
