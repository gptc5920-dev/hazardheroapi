import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F,Q
from django.utils import timezone
from common.models import TimestampedSoftDeleteModel
from common.validators import validate_upload
from languages.models import TranslationBase
class EmergencyAlert(TimestampedSoftDeleteModel):
    TYPES=[(x,x) for x in ["Earthquake","Flood","Typhoon","Fire","Landslide","Tsunami","Volcanic Eruption","Medical Emergency","Road Closure","Missing Person","Evacuation Notice","Weather Advisory","Public Safety","General Emergency"]]; SEVERITIES=[(x,x) for x in ["Information","Advisory","Warning","Severe","Critical"]]; STATUSES=[(x,x) for x in ["Draft","Scheduled","Active","Expired","Resolved","Cancelled","Archived"]]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); alert_code=models.CharField(max_length=40,unique=True,editable=False); title=models.CharField(max_length=255,db_index=True); message=models.TextField(); instructions=models.TextField(blank=True); alert_type=models.CharField(max_length=40,choices=TYPES,db_index=True); severity_level=models.CharField(max_length=20,choices=SEVERITIES,db_index=True); status=models.CharField(max_length=15,choices=STATUSES,default="Draft",db_index=True); source=models.CharField(max_length=180); region=models.CharField(max_length=100,blank=True,db_index=True); province=models.CharField(max_length=100,blank=True,db_index=True); city_municipality=models.CharField(max_length=100,blank=True,db_index=True); barangay=models.CharField(max_length=100,blank=True,db_index=True); latitude=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True,db_index=True); longitude=models.DecimalField(max_digits=10,decimal_places=7,null=True,blank=True,db_index=True); radius_km=models.DecimalField(max_digits=8,decimal_places=2,null=True,blank=True); affected_areas=models.JSONField(default=list); evacuation_required=models.BooleanField(default=False); recommended_evacuation_center=models.ForeignKey("evacuation_centers.EvacuationCenter",null=True,blank=True,on_delete=models.SET_NULL); attachment=models.FileField(upload_to="alerts/attachments/",null=True,blank=True,validators=[validate_upload]); image=models.ImageField(upload_to="alerts/images/",null=True,blank=True,validators=[validate_upload]); starts_at=models.DateTimeField(); expires_at=models.DateTimeField(); published_at=models.DateTimeField(null=True,blank=True,db_index=True); resolved_at=models.DateTimeField(null=True,blank=True); resolved_by=models.ForeignKey("accounts.User",null=True,blank=True,on_delete=models.SET_NULL,related_name="resolved_alerts"); cancelled_at=models.DateTimeField(null=True,blank=True); cancelled_by=models.ForeignKey("accounts.User",null=True,blank=True,on_delete=models.SET_NULL,related_name="cancelled_alerts"); is_public=models.BooleanField(default=True); is_active=models.BooleanField(default=True,db_index=True)
    class Meta:
        ordering=["-published_at","-created_at"]; constraints=[models.CheckConstraint(check=Q(expires_at__gt=F("starts_at")),name="alert_expiry_after_start")]
    def clean(self):
        errors={}
        if self.expires_at<=self.starts_at: errors["expires_at"]="Expiration must be later than start."
        if self.severity_level=="Critical" and not self.instructions.strip(): errors["instructions"]="Critical alerts require safety instructions."
        if self.evacuation_required and not self.affected_areas: errors["affected_areas"]="Evacuation alerts require an affected area."
        if errors: raise ValidationError(errors)
    def save(self,*a,**k):
        if not self.alert_code: self.alert_code=f"ALERT-{timezone.now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"
        self.full_clean(); super().save(*a,**k)
    def __str__(self): return f"{self.alert_code}: {self.title}"
class EmergencyAlertTranslation(TranslationBase):
    alert=models.ForeignKey(EmergencyAlert,on_delete=models.CASCADE,related_name="translations")
    translated_title=models.CharField(max_length=255); translated_message=models.TextField(); translated_instructions=models.TextField(blank=True); translated_affected_area_description=models.TextField(blank=True)
    translated_fields=("translated_title","translated_message","translated_instructions","translated_affected_area_description")
    class Meta: constraints=[models.UniqueConstraint(fields=["alert","language"],name="unique_alert_language")]
class CalamityType(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); name=models.CharField(max_length=100,unique=True); description=models.TextField(); is_active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    def __str__(self): return self.name
class CalamityTypeTranslation(TranslationBase):
    calamity=models.ForeignKey(CalamityType,on_delete=models.CASCADE,related_name="translations"); translated_name=models.CharField(max_length=100); translated_description=models.TextField(); translated_fields=("translated_name","translated_description")
    class Meta: constraints=[models.UniqueConstraint(fields=["calamity","language"],name="unique_calamity_language")]
