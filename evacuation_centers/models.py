import uuid
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F,Q
from django.utils import timezone
from common.models import TimestampedSoftDeleteModel
from common.validators import validate_upload
from languages.models import TranslationBase
class EvacuationCenter(TimestampedSoftDeleteModel):
    OPERATING=[(x,x) for x in ["Operational","Temporarily Closed","Under Maintenance","Full","Inactive"]]; AVAILABILITY=[(x,x) for x in ["Available","Limited","Full","Closed"]]; FACILITIES=[(x,x) for x in ["School","Gymnasium","Barangay Hall","Covered Court","Community Center","Government Building","Religious Facility","Temporary Shelter","Other"]]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); name=models.CharField(max_length=200,db_index=True); description=models.TextField(blank=True); center_code=models.CharField(max_length=40,unique=True); region=models.CharField(max_length=100,db_index=True); province=models.CharField(max_length=100,db_index=True); city_municipality=models.CharField(max_length=100,db_index=True); barangay=models.CharField(max_length=100,db_index=True); street_address=models.CharField(max_length=255); latitude=models.DecimalField(max_digits=10,decimal_places=7,db_index=True); longitude=models.DecimalField(max_digits=10,decimal_places=7,db_index=True); total_capacity=models.PositiveIntegerField(); current_occupancy=models.PositiveIntegerField(default=0); available_slots=models.PositiveIntegerField(default=0,editable=False); contact_person=models.CharField(max_length=150); contact_number=models.CharField(max_length=30); alternative_contact_number=models.CharField(max_length=30,blank=True); email=models.EmailField(blank=True); operating_status=models.CharField(max_length=30,choices=OPERATING,default="Operational",db_index=True); availability_status=models.CharField(max_length=20,choices=AVAILABILITY,default="Available",db_index=True); facility_type=models.CharField(max_length=40,choices=FACILITIES,db_index=True); supported_emergency_types=models.JSONField(default=list); has_electricity=models.BooleanField(default=False); has_water_supply=models.BooleanField(default=False); has_restroom=models.BooleanField(default=False); has_medical_area=models.BooleanField(default=False); has_kitchen=models.BooleanField(default=False); has_parking=models.BooleanField(default=False); is_pwd_accessible=models.BooleanField(default=False); accepts_pets=models.BooleanField(default=False); image=models.ImageField(upload_to="evacuation_centers/",null=True,blank=True,validators=[validate_upload]); remarks=models.TextField(blank=True); last_capacity_update=models.DateTimeField(default=timezone.now); is_active=models.BooleanField(default=True,db_index=True)
    class Meta:
        ordering=["name"]; constraints=[models.CheckConstraint(check=Q(total_capacity__gte=0),name="evac_capacity_nonnegative"),models.CheckConstraint(check=Q(current_occupancy__gte=0),name="evac_occupancy_nonnegative"),models.CheckConstraint(check=Q(current_occupancy__lte=F("total_capacity")),name="evac_occupancy_lte_capacity")]
    def clean(self):
        if self.current_occupancy>self.total_capacity: raise ValidationError({"current_occupancy":"Occupancy cannot exceed total capacity."})
    def save(self,*a,**k):
        self.full_clean(); self.available_slots=self.total_capacity-self.current_occupancy
        if self.available_slots==0: self.availability_status="Full"; self.operating_status="Full"
        elif self.operating_status in ["Temporarily Closed","Inactive","Under Maintenance"]: self.availability_status="Closed"
        self.last_capacity_update=timezone.now(); super().save(*a,**k)
    def __str__(self): return self.name
class EvacuationCenterTranslation(TranslationBase):
    center=models.ForeignKey(EvacuationCenter,on_delete=models.CASCADE,related_name="translations")
    translated_description=models.TextField(); translated_facility_description=models.TextField(blank=True)
    translated_fields=("translated_description","translated_facility_description")
    class Meta: constraints=[models.UniqueConstraint(fields=["center","language"],name="unique_center_language")]
