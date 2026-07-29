import os
from django.core.exceptions import ValidationError
from PIL import Image
ALLOWED={".jpg",".jpeg",".png",".webp",".pdf",".doc",".docx"}; IMAGE={".jpg",".jpeg",".png",".webp"}
MEDIA=IMAGE|{".mp4",".webm",".mov"}; SUBTITLES={".vtt",".srt"}
def validate_upload(f):
    ext=os.path.splitext(f.name)[1].lower()
    if ext not in ALLOWED: raise ValidationError("Unsupported file type.")
    if not f.size: raise ValidationError("Empty files are not allowed.")
    if f.size>10*1024*1024: raise ValidationError("File exceeds 10 MB.")
    if ext in IMAGE:
        try:
            im=Image.open(f); im.verify(); f.seek(0)
            if im.width>8000 or im.height>8000: raise ValidationError("Image dimensions exceed 8000x8000.")
        except ValidationError: raise
        except Exception: raise ValidationError("Corrupted image.")
def validate_media_upload(f):
    ext=os.path.splitext(f.name)[1].lower()
    if ext not in MEDIA: raise ValidationError("Only JPEG, PNG, WebP, MP4, WebM, and MOV media are allowed.")
    if not f.size or f.size>100*1024*1024: raise ValidationError("Media must be non-empty and no larger than 100 MB.")
    if ext in IMAGE: validate_upload(f)
def validate_subtitle(f):
    if os.path.splitext(f.name)[1].lower() not in SUBTITLES: raise ValidationError("Only VTT or SRT subtitles are allowed.")
    if not f.size or f.size>2*1024*1024: raise ValidationError("Subtitle must be non-empty and no larger than 2 MB.")
