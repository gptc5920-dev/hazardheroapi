import uuid
from django.conf import settings
from django.db import models
class AuditLog(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); user=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)
    action=models.CharField(max_length=40,db_index=True); module=models.CharField(max_length=60,db_index=True); record_id=models.CharField(max_length=64,blank=True); record_description=models.CharField(max_length=255,blank=True)
    previous_values=models.JSONField(default=dict,blank=True); new_values=models.JSONField(default=dict,blank=True); ip_address=models.GenericIPAddressField(null=True,blank=True); user_agent=models.TextField(blank=True); created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    class Meta: ordering=["-created_at"]
