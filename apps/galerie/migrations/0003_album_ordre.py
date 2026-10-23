# Migration rendue « idempotente » : si la colonne `ordre` existe déjà dans la base (cas d'une base où elle a été ajoutée
# par une ancienne version de cette migration), on ne la recrée pas. Sur une base neuve, elle est créée normalement.
from django.db import migrations, models


def ajouter_colonne_si_absente(apps, schema_editor):
    Album = apps.get_model('galerie', 'Album')
    table = Album._meta.db_table
    with schema_editor.connection.cursor() as cur:
        colonnes = [c.name for c in schema_editor.connection.introspection.get_table_description(cur, table)]
    if 'ordre' not in colonnes:
        champ = models.PositiveSmallIntegerField(default=0)
        champ.set_attributes_from_name('ordre')
        schema_editor.add_field(Album, champ)


class Migration(migrations.Migration):

    dependencies = [
        ("galerie", "0002_photo_image_statique_alter_photo_image"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="album",
            options={"ordering": ["ordre", "-date", "-id"], "verbose_name": "Album photo"},
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="album",
                    name="ordre",
                    field=models.PositiveSmallIntegerField(default=0, help_text="Position dans la galerie (0 = en premier)."),
                ),
            ],
            database_operations=[
                migrations.RunPython(ajouter_colonne_si_absente, migrations.RunPython.noop),
            ],
        ),
    ]