from django.db import migrations


def add_initial_categories(apps, schema_editor):
    category = apps.get_model("studio", "Category")
    for name in ("3D-дизайн", "2D-дизайн", "Эскиз"):
        category.objects.using(schema_editor.connection.alias).get_or_create(name=name)


class Migration(migrations.Migration):
    dependencies = [("studio", "0001_initial")]
    operations = [migrations.RunPython(add_initial_categories, migrations.RunPython.noop)]
