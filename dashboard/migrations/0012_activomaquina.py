from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_lineaproduccion_maquinas'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivoMaquina',
            fields=[
                (
                    'id',
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID',
                    ),
                ),
                ('linea_descripcion', models.CharField(max_length=200, verbose_name='línea de producción')),
                ('maquina', models.CharField(max_length=200, verbose_name='máquina')),
                ('especificaciones', models.JSONField(blank=True, default=list, verbose_name='especificaciones')),
                (
                    'configuracion',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='activos_maquina',
                        to='dashboard.configuracionmantenimiento',
                    ),
                ),
            ],
            options={
                'verbose_name': 'activo de máquina',
                'verbose_name_plural': 'activos de máquinas',
                'ordering': ['linea_descripcion', 'maquina', 'pk'],
            },
        ),
    ]
