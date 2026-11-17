from django.db import migrations, models


def actualizar_ruta_logo(apps, schema_editor):
    ConfiguracionEmpresa = apps.get_model('dashboard', 'ConfiguracionEmpresa')
    ConfiguracionEmpresa.objects.using(schema_editor.connection.alias).filter(
        pk=1,
        logo_path='images/logo_empresa.png',
    ).update(logo_path='images/logo.png')


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0001_configuracion_empresa_y_perfil'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuracionempresa',
            name='logo_path',
            field=models.CharField(
                blank=True,
                default='images/logo.png',
                help_text='Ruta relativa a la carpeta static del proyecto, por ejemplo: images/logo.png.',
                max_length=255,
                verbose_name='ruta del logo',
            ),
        ),
        migrations.RunPython(actualizar_ruta_logo, migrations.RunPython.noop),
    ]
