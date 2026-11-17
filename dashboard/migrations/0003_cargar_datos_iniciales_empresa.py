from django.db import migrations


def cargar_datos_iniciales_empresa(apps, schema_editor):
    ConfiguracionEmpresa = apps.get_model('dashboard', 'ConfiguracionEmpresa')
    configuracion = ConfiguracionEmpresa.objects.using(
        schema_editor.connection.alias,
    ).filter(pk=1)

    configuracion.filter(nombre='Nombre de la Empresa').update(nombre='Wisdom Tech')
    configuracion.filter(rif='J-12345678-9').update(rif='J-1783881-6')
    configuracion.filter(slogan='Slogan de la Empresa').update(
        slogan='Innovando el Futuro, Transformando el Presente',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0002_actualizar_ruta_logo_empresa'),
    ]

    operations = [
        migrations.RunPython(
            cargar_datos_iniciales_empresa,
            migrations.RunPython.noop,
        ),
    ]
