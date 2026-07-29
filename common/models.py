from django.conf import settings
from django.db import models
from django.utils import timezone

class ActiveManager(models.Manager):
    def get_queryset(self): return super().get_queryset().filter(deleted_at__isnull=True)
class DeletedManager(models.Manager):
    def get_queryset(self): return super().get_queryset().filter(deleted_at__isnull=False)
class TimestampedSoftDeleteModel(models.Model):
    created_at=models.DateTimeField(auto_now_add=True, db_index=True); updated_at=models.DateTimeField(auto_now=True)
    deleted_at=models.DateTimeField(null=True, blank=True, db_index=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_%(class)ss")
    updated_by=models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="updated_%(class)ss")
    objects=ActiveManager(); all_objects=models.Manager(); deleted_objects=DeletedManager()
    class Meta: abstract=True
    def soft_delete(self): self.deleted_at=timezone.now(); self.save(update_fields=["deleted_at", "updated_at"])
    def restore(self): self.deleted_at=None; self.save(update_fields=["deleted_at", "updated_at"])
    def permanent_delete(self): return super().delete()
