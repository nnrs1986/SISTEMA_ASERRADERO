from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0004_alter_configuracionempresa_nombre_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='configuracionempresa',
            name='color_fondo',
            field=models.CharField(
                choices=[('claro', 'Gris claro'), ('azulado', 'Azul muy claro'), ('calido', 'Arena suave')],
                default='claro',
                max_length=20,
                verbose_name='fondo del dashboard',
            ),
        ),
        migrations.AddField(
            model_name='configuracionempresa',
            name='color_sidebar',
            field=models.CharField(
                choices=[('verde', 'Verde'), ('azul', 'Azul'), ('vino', 'Vino')],
                default='verde',
                max_length=20,
                verbose_name='color de la barra lateral',
            ),
        ),
        migrations.AddField(
            model_name='configuracionempresa',
            name='color_modulos',
            field=models.CharField(
                choices=[('azul', 'Azul'), ('verde', 'Verde'), ('grafito', 'Grafito')],
                default='azul',
                max_length=20,
                verbose_name='color de las barras de módulos',
            ),
        ),
    ]
