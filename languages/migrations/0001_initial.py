import uuid
from django.db import migrations,models

def seed_languages(apps,schema_editor):
    Language=apps.get_model("languages","Language")
    for code,name,native,default in [("en","English","English",True),("fil","Filipino","Filipino",False),("ceb","Bisaya","Bisaya",False)]:
        Language.objects.update_or_create(language_code=code,defaults={"name":name,"native_name":native,"is_default":default,"is_active":True})

class Migration(migrations.Migration):
    initial=True; dependencies=[]
    operations=[migrations.CreateModel(name="Language",fields=[("id",models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),("name",models.CharField(max_length=30)),("native_name",models.CharField(max_length=30)),("language_code",models.CharField(choices=[("en","en"),("fil","fil"),("ceb","ceb")],max_length=3,unique=True)),("is_default",models.BooleanField(default=False)),("is_active",models.BooleanField(default=True)),("created_at",models.DateTimeField(auto_now_add=True)),("updated_at",models.DateTimeField(auto_now=True))],options={"ordering":["-is_default","name"]}),migrations.AddConstraint(model_name="language",constraint=models.CheckConstraint(check=models.Q(("language_code__in",("en","fil","ceb"))),name="supported_language_code")),migrations.RunPython(seed_languages,migrations.RunPython.noop)]
