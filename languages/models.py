import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

SUPPORTED_CODES=("en","fil","ceb")
LANGUAGE_CHOICES=[("en","English"),("fil","Filipino"),("ceb","Bisaya")]
TRANSLATION_STATUSES=[(x,x) for x in ["Draft","Published","Needs Review","Archived"]]

class Language(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    name=models.CharField(max_length=30); native_name=models.CharField(max_length=30)
    language_code=models.CharField(max_length=3,unique=True,choices=LANGUAGE_CHOICES)
    is_default=models.BooleanField(default=False); is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: ordering=["-is_default","name"]; constraints=[models.CheckConstraint(check=models.Q(language_code__in=SUPPORTED_CODES),name="supported_language_code")]
    def clean(self):
        if self.language_code not in SUPPORTED_CODES: raise ValidationError({"language_code":"Only en, fil, and ceb are supported."})
        if self.language_code=="en" and (not self.is_active or not self.is_default): raise ValidationError("English must remain active and default.")
        if self.language_code!="en" and self.is_default: raise ValidationError({"is_default":"English is the only default language."})
    def save(self,*a,**k): self.full_clean(); super().save(*a,**k)
    def delete(self,*a,**k): raise ValidationError("Supported languages cannot be deleted.")
    def __str__(self): return self.name

class TranslationBase(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    language=models.ForeignKey(Language,on_delete=models.PROTECT)
    status=models.CharField(max_length=20,choices=TRANSLATION_STATUSES,default="Draft",db_index=True)
    version=models.PositiveIntegerField(default=1); published_at=models.DateTimeField(null=True,blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="created_%(class)ss")
    updated_by=models.ForeignKey(settings.AUTH_USER_MODEL,null=True,blank=True,on_delete=models.SET_NULL,related_name="updated_%(class)ss")
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    translated_fields=()
    class Meta: abstract=True
    def save(self,*a,**k):
        if self.language_id:
            code=Language.objects.only("language_code").get(pk=self.language_id).language_code
            if code not in SUPPORTED_CODES: raise ValidationError("Unsupported translation language.")
        if self.pk:
            old=type(self).objects.filter(pk=self.pk).first()
            if old and any(getattr(old,f)!=getattr(self,f) for f in self.translated_fields): self.version=old.version+1
        if self.status=="Published" and not self.published_at: self.published_at=timezone.now()
        super().save(*a,**k)
