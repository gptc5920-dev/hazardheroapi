from django.db import migrations

class Migration(migrations.Migration):
    initial=True
    dependencies=[]
    operations=[migrations.RunSQL(
        sql=["DROP TABLE IF EXISTS resources_syncchange", "DROP TABLE IF EXISTS resources_clientmutation", "DROP TABLE IF EXISTS resources_resource"],
        reverse_sql=migrations.RunSQL.noop,
    )]
