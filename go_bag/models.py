import uuid
from django.db import models
from common.models import TimestampedSoftDeleteModel
from common.validators import validate_upload
from languages.models import TranslationBase
class GoBagItem(TimestampedSoftDeleteModel):
    CATEGORIES=[(x,x) for x in ["Food and Water","Medical Supplies","Communication","Clothing","Important Documents","Tools and Equipment","Hygiene","Emergency Supplies","Baby Supplies","Senior Citizen Supplies","Pet Supplies","Other"]]
    PRIORITIES=[(x,x) for x in ["Low","Medium","High","Critical"]]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); name=models.CharField(max_length=180,unique=True,db_index=True); description=models.TextField(); category=models.CharField(max_length=40,choices=CATEGORIES,db_index=True); quantity=models.PositiveIntegerField(default=1); unit=models.CharField(max_length=40); priority_level=models.CharField(max_length=10,choices=PRIORITIES,db_index=True); image=models.ImageField(upload_to="go_bag/",null=True,blank=True,validators=[validate_upload]); is_required=models.BooleanField(default=False); is_active=models.BooleanField(default=True,db_index=True); display_order=models.PositiveIntegerField(default=0)
    class Meta: ordering=["display_order","name"]
    def __str__(self): return self.name
class GoBagItemTranslation(TranslationBase):
    item=models.ForeignKey(GoBagItem,on_delete=models.CASCADE,related_name="translations")
    translated_name=models.CharField(max_length=180); translated_description=models.TextField()
    translated_fields=("translated_name","translated_description")
    class Meta: constraints=[models.UniqueConstraint(fields=["item","language"],name="unique_go_bag_language")]
    def __str__(self): return f"{self.item} ({self.language.language_code})"
