import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_prestamoherramienta'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrdenTrabajo',
            fields=[
                ('numero_orden', models.BigAutoField(primary_key=True, serialize=False, verbose_name='Número de orden')),
                ('titulo', models.CharField(max_length=180, verbose_name='Título de la orden')),
                ('tipo_orden', models.CharField(choices=[('correctivo', 'Correctivo'), ('preventivo', 'Preventivo'), ('inspeccion', 'Inspección'), ('emergencia', 'Emergencia'), ('servicio_cliente', 'Servicio al cliente'), ('produccion', 'Producción'), ('construccion', 'Construcción')], max_length=30, verbose_name='Tipo de orden')),
                ('duracion_estimada', models.CharField(blank=True, max_length=80, verbose_name='Duración estimada')),
                ('actividades_programadas', models.TextField(blank=True, verbose_name='Actividades programadas')),
                ('fecha_emision', models.DateField(default=django.utils.timezone.localdate, verbose_name='Fecha de emisión')),
                ('solicitante', models.CharField(max_length=150, verbose_name='Nombre del solicitante')),
                ('area_solicitante', models.CharField(blank=True, max_length=120, verbose_name='Área o departamento del solicitante')),
                ('contacto_solicitante', models.CharField(blank=True, max_length=150, verbose_name='Teléfono o correo del solicitante')),
                ('cliente_externo', models.BooleanField(default=False, verbose_name='¿Es un cliente externo?')),
                ('nombre_cliente', models.CharField(blank=True, max_length=150, verbose_name='Nombre del cliente')),
                ('contacto_cliente', models.CharField(blank=True, max_length=150, verbose_name='Contacto del cliente')),
                ('contacto_cliente_datos', models.CharField(blank=True, max_length=150, verbose_name='Teléfono o correo del cliente')),
                ('descripcion_trabajo', models.CharField(max_length=180, verbose_name='Título del trabajo')),
                ('detalle_trabajo', models.TextField(verbose_name='Detalle del trabajo')),
                ('ubicacion', models.CharField(blank=True, max_length=180, verbose_name='Ubicación')),
                ('activo', models.CharField(blank=True, max_length=180, verbose_name='Activo o equipo')),
                ('responsable', models.CharField(blank=True, max_length=150, verbose_name='Responsable del trabajo')),
                ('fecha_programada', models.DateField(blank=True, null=True, verbose_name='Fecha programada')),
                ('prioridad', models.CharField(blank=True, choices=[('baja', 'Baja'), ('media', 'Media'), ('alta', 'Alta'), ('urgente', 'Urgente')], max_length=10, verbose_name='Prioridad')),
                ('materiales_estimados', models.TextField(blank=True, verbose_name='Materiales estimados')),
                ('mano_obra_estimada', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name='Costo estimado de mano de obra')),
                ('materiales_utilizados', models.TextField(blank=True, verbose_name='Materiales utilizados')),
                ('tiempos_ejecucion', models.TextField(blank=True, verbose_name='Registro de tiempos de ejecución')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('hallazgos', models.TextField(blank=True, verbose_name='Hallazgos')),
                ('firma_responsable', models.CharField(blank=True, max_length=150, verbose_name='Firma o nombre del responsable/mecánico')),
                ('firma_supervisor', models.CharField(blank=True, max_length=150, verbose_name='Firma o nombre del supervisor')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')),
            ],
            options={
                'verbose_name': 'orden de trabajo',
                'verbose_name_plural': 'órdenes de trabajo',
                'ordering': ['-numero_orden'],
            },
        ),
    ]
