import uuid
from django.db import models
from common.models import TimestampedSoftDeleteModel
from common.validators import validate_upload
from languages.models import TranslationBase
class EmergencyContact(TimestampedSoftDeleteModel):
    TYPES=[(x,x) for x in ["Police","Fire Department","Ambulance","Hospital","Disaster Risk Reduction Office","Rescue Team","Coast Guard","Barangay Emergency Response Team","Social Welfare Office","Electric Utility","Water Utility","Other"]]; AVAIL=[(x,x) for x in ["24/7","Office Hours","On Call","Temporarily Unavailable"]]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); organization_name=models.CharField(max_length=200,db_index=True); contact_person=models.CharField(max_length=150,blank=True); contact_type=models.CharField(max_length=50,choices=TYPES,db_index=True); description=models.TextField(blank=True); primary_phone_number=models.CharField(max_length=30); secondary_phone_number=models.CharField(max_length=30,blank=True); hotline_number=models.CharField(max_length=30,blank=True); email=models.EmailField(blank=True); region=models.CharField(max_length=100,db_index=True); province=models.CharField(max_length=100,db_index=True); city_municipality=models.CharField(max_length=100,db_index=True); barangay=models.CharField(max_length=100,db_index=True); street_address=models.CharField(max_length=255,blank=True); availability=models.CharField(max_length=30,choices=AVAIL,db_index=True); office_hours=models.CharField(max_length=120,blank=True); emergency_types=models.JSONField(default=list); priority_order=models.PositiveIntegerField(default=0); logo=models.ImageField(upload_to="contacts/",null=True,blank=True,validators=[validate_upload]); is_verified=models.BooleanField(default=False); is_active=models.BooleanField(default=True,db_index=True)
    class Meta: ordering=["priority_order","organization_name"]
    def __str__(self): return self.organization_name
class EmergencyContactTranslation(TranslationBase):
    contact=models.ForeignKey(EmergencyContact,on_delete=models.CASCADE,related_name="translations")
    translated_description=models.TextField()
    translated_fields=("translated_description",)
    class Meta: constraints=[models.UniqueConstraint(fields=["contact","language"],name="unique_contact_language")]
