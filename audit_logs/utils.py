import json
from django.core.serializers.json import DjangoJSONEncoder
from .models import AuditLog
def _json_safe(value): return json.loads(json.dumps(value or {},cls=DjangoJSONEncoder))
def audit(request,action,module,obj=None,previous=None,new=None):
    forwarded=request.META.get("HTTP_X_FORWARDED_FOR","").split(",")[0].strip()
    AuditLog.objects.create(user=request.user if request.user.is_authenticated else None,action=action,module=module,record_id=str(getattr(obj,"pk","")),record_description=str(obj)[:255] if obj else "",previous_values=_json_safe(previous),new_values=_json_safe(new),ip_address=forwarded or request.META.get("REMOTE_ADDR"),user_agent=request.META.get("HTTP_USER_AGENT","")[:1000])
