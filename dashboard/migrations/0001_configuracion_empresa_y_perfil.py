from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def crear_configuracion_empresa(apps, schema_editor):
    ConfiguracionEmpresa = apps.get_model('dashboard', 'ConfiguracionEmpresa')
    ConfiguracionEmpresa.objects.using(schema_editor.connection.alias).get_or_create(
        pk=1,
        defaults={
            'nombre': 'Nombre de la Empresa',
            'rif': 'J-12345678-9',
            'logo_path': 'images/logo_empresa.png',
            'slogan': 'Slogan de la Empresa',
        },
    )


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionEmpresa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(default='Nombre de la Empresa', max_length=150, verbose_name='nombre de la empresa')),
                ('rif', models.CharField(default='J-12345678-9', max_length=30, verbose_name='RIF')),
                ('logo_path', models.CharField(blank=True, default='images/logo_empresa.png', help_text='Ruta relativa a la carpeta static del proyecto, por ejemplo: images/logo_empresa.png.', max_length=255, verbose_name='ruta del logo')),
                ('slogan', models.CharField(default='Slogan de la Empresa', max_length=255, verbose_name='slogan')),
            ],
            options={
                'verbose_name': 'configuración de la empresa',
                'verbose_name_plural': 'configuración de la empresa',
            },
        ),
        migrations.CreateModel(
            name='PerfilUsuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cargo', models.CharField(max_length=100, verbose_name='cargo')),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='perfil', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'perfil de usuario',
                'verbose_name_plural': 'perfiles de usuario',
            },
        ),
        migrations.RunPython(crear_configuracion_empresa, migrations.RunPython.noop),
    ]
