import uuid
from django.db import models
from django.utils.text import slugify
from common.models import TimestampedSoftDeleteModel
from common.validators import validate_upload,validate_media_upload,validate_subtitle
from languages.models import TranslationBase
class Guideline(TimestampedSoftDeleteModel):
    CATEGORIES=[(x,x) for x in ["Before an Emergency","During an Emergency","After an Emergency","First Aid","Evacuation","Disaster Preparedness","Safety Procedures","Emergency Communication"]]
    EMERGENCIES=[(x,x) for x in ["Earthquake","Flood","Typhoon","Fire","Landslide","Tsunami","Volcanic Eruption","Medical Emergency","Armed Conflict","General Emergency"]]
    STATUSES=[(x,x) for x in ["Draft","Published","Archived"]]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); title=models.CharField(max_length=255,unique=True,db_index=True); slug=models.SlugField(max_length=255,unique=True,blank=True,db_index=True); summary=models.TextField(); content=models.TextField(); safety_instructions=models.TextField(blank=True); category=models.CharField(max_length=40,choices=CATEGORIES,db_index=True); emergency_type=models.CharField(max_length=40,choices=EMERGENCIES,db_index=True); featured_image=models.ImageField(upload_to="guidelines/images/",null=True,blank=True,validators=[validate_upload]); status=models.CharField(max_length=12,choices=STATUSES,default="Draft",db_index=True); is_featured=models.BooleanField(default=False); is_active=models.BooleanField(default=True,db_index=True); version=models.PositiveIntegerField(default=1); published_at=models.DateTimeField(null=True,blank=True,db_index=True)
    class Meta: ordering=["title"]
    def save(self,*a,**k):
        if self.pk:
            old=Guideline.all_objects.filter(pk=self.pk).first()
            if old and any(getattr(old,f)!=getattr(self,f) for f in ("title","summary","content","safety_instructions")): self.version=old.version+1
        if not self.slug:
            base=slugify(self.title); slug=base; n=2
            while Guideline.all_objects.filter(slug=slug).exclude(pk=self.pk).exists(): slug=f"{base}-{n}"; n+=1
            self.slug=slug
        super().save(*a,**k)
    def __str__(self): return self.title
class GuidelineTranslation(TranslationBase):
    guideline=models.ForeignKey(Guideline,on_delete=models.CASCADE,related_name="translations")
    translated_title=models.CharField(max_length=255); translated_summary=models.TextField(); translated_content=models.TextField(); translated_safety_instructions=models.TextField(blank=True)
    translated_fields=("translated_title","translated_summary","translated_content","translated_safety_instructions")
    class Meta: constraints=[models.UniqueConstraint(fields=["guideline","language"],name="unique_guideline_language")]
class GuidelineMedia(models.Model):
    TYPES=[("image","Image"),("video","Video"),("svg","SVG"),("icon","Icon")]
    SOURCES=[("upload","Uploaded file"),("link","Embedded link")]
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False); guideline=models.ForeignKey(Guideline,on_delete=models.CASCADE,related_name="media")
    source_type=models.CharField(max_length=10,choices=SOURCES,default="upload"); media_type=models.CharField(max_length=5,choices=TYPES); title=models.CharField(max_length=255); description=models.TextField(blank=True); media_file=models.FileField(upload_to="guidelines/media/",null=True,blank=True,validators=[validate_media_upload]); external_url=models.URLField(max_length=500,blank=True); display_order=models.PositiveIntegerField(default=0); is_active=models.BooleanField(default=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        ordering=["display_order","created_at"]
        constraints=[models.CheckConstraint(condition=(models.Q(source_type="upload")&~models.Q(media_file="")&models.Q(external_url=""))|(models.Q(source_type="link")&models.Q(media_file="")&~models.Q(external_url="")),name="guideline_media_has_one_source")]
class GuidelineMediaTranslation(TranslationBase):
    media=models.ForeignKey(GuidelineMedia,on_delete=models.CASCADE,related_name="translations")
    translated_title=models.CharField(max_length=255); translated_description=models.TextField(blank=True); caption_text=models.TextField(blank=True); subtitle_file=models.FileField(upload_to="guidelines/subtitles/",null=True,blank=True,validators=[validate_subtitle]); alternative_media_file=models.FileField(upload_to="guidelines/media/language/",null=True,blank=True,validators=[validate_media_upload])
    translated_fields=("translated_title","translated_description","caption_text","subtitle_file","alternative_media_file")
    class Meta: constraints=[models.UniqueConstraint(fields=["media","language"],name="unique_media_language")]
