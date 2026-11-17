from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_configuracionempresa_colores'),
    ]

    operations = [
        migrations.AlterField(
            model_name='configuracionempresa',
            name='color_fondo',
            field=models.CharField(
                choices=[
                    ('claro', 'Gris claro'),
                    ('azulado', 'Azul muy claro'),
                    ('calido', 'Arena suave'),
                    ('marron', 'Marrón suave'),
                    ('salvia', 'Verde salvia'),
                    ('petroleo', 'Azul petróleo'),
                ],
                default='claro',
                max_length=20,
                verbose_name='fondo del dashboard',
            ),
        ),
        migrations.AlterField(
            model_name='configuracionempresa',
            name='color_sidebar',
            field=models.CharField(
                choices=[
                    ('verde', 'Verde'),
                    ('azul', 'Azul'),
                    ('vino', 'Vino'),
                    ('marron', 'Marrón'),
                    ('salvia', 'Verde salvia'),
                    ('petroleo', 'Azul petróleo'),
                ],
                default='verde',
                max_length=20,
                verbose_name='color de la barra lateral',
            ),
        ),
        migrations.AlterField(
            model_name='configuracionempresa',
            name='color_modulos',
            field=models.CharField(
                choices=[
                    ('azul', 'Azul'),
                    ('verde', 'Verde'),
                    ('grafito', 'Grafito'),
                    ('marron', 'Marrón'),
                    ('salvia', 'Verde salvia'),
                    ('petroleo', 'Azul petróleo'),
                ],
                default='azul',
                max_length=20,
                verbose_name='color de las barras de módulos',
            ),
        ),
    ]
