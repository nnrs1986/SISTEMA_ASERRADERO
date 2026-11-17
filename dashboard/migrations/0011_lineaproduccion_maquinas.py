from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0010_configuracionmantenimiento_lineaproduccion'),
    ]

    operations = [
        migrations.AddField(
            model_name='lineaproduccion',
            name='maquinas',
            field=models.JSONField(blank=True, default=list, verbose_name='máquinas de la línea'),
        ),
    ]
