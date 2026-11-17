from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aserrio', '0003_alter_paqueteaserrio_ch_estimado'),
    ]

    operations = [
        migrations.AddField(
            model_name='paqueteaserrio',
            name='fecha_edicion',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Fecha de edición'),
        ),
    ]
