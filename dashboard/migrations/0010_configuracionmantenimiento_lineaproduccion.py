from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0009_trabajador_historial_ascensos_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionMantenimiento',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ciudad_parroquia', models.CharField(max_length=150, verbose_name='ciudad o parroquia')),
                ('nombre_aserradero', models.CharField(max_length=150, verbose_name='nombre del aserradero')),
                ('tiene_patios_rolas', models.BooleanField(default=False, verbose_name='¿Tiene patio de rolas?')),
                ('clasifica_rolas', models.BooleanField(default=False, verbose_name='¿Clasifica rolas?')),
                ('tipo_produccion', models.CharField(choices=[('seccionada', 'Seccionada'), ('completa', 'Completa')], max_length=20, verbose_name='tipo de producción')),
                ('cantidad_lineas', models.PositiveSmallIntegerField(blank=True, null=True, verbose_name='cantidad de líneas de producción')),
            ],
            options={
                'verbose_name': 'configuración general de mantenimiento',
                'verbose_name_plural': 'configuración general de mantenimiento',
            },
        ),
        migrations.CreateModel(
            name='LineaProduccion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=200, verbose_name='organización de la línea')),
                ('orden', models.PositiveSmallIntegerField(default=1)),
                ('configuracion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lineas_produccion', to='dashboard.configuracionmantenimiento')),
            ],
            options={
                'verbose_name': 'línea de producción',
                'verbose_name_plural': 'líneas de producción',
                'ordering': ['orden', 'pk'],
            },
        ),
    ]
