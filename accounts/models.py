import uuid
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

ROLE = "administrator_responder"
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email: raise ValueError("Email is required")
        extra["role"] = ROLE
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password); user.save(using=self._db); return user
    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True, is_active=True, is_verified=True)
        return self.create_user(email, password, **extra)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, db_index=True)
    phone_number = models.CharField(max_length=30, blank=True)
    position = models.CharField(max_length=120, blank=True)
    office = models.CharField(max_length=160, blank=True)
    profile_image = models.ImageField(upload_to="responders/", null=True, blank=True)
    role = models.CharField(max_length=32, default=ROLE, editable=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"; REQUIRED_FIELDS = ["first_name", "last_name"]
    objects = UserManager()
    @property
    def display_name(self): return " ".join(x for x in [self.first_name, self.middle_name, self.last_name] if x)
    def save(self, *args, **kwargs): self.email=self.email.strip().lower(); self.role=ROLE; super().save(*args, **kwargs)
