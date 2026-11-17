from django.db import models

from aserrio.models import PaqueteAserrio


class ReprocesoRegistro(models.Model):
    fecha = models.DateField(verbose_name='Fecha')
    nombre_supervisor = models.CharField(max_length=150, verbose_name='Nombre del supervisor')
    paquete_origen = models.ForeignKey(
        PaqueteAserrio,
        on_delete=models.PROTECT,
        related_name='registros_reproceso',
        verbose_name='Paquete de origen',
    )
    maquinas_proceso = models.JSONField(default=list, verbose_name='Máquinas utilizadas')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        ordering = ['-fecha', '-fecha_registro']
        verbose_name = 'Registro de reproceso'
        verbose_name_plural = 'Registros de reproceso'

    def __str__(self):
        return f'Reproceso {self.pk} - {self.paquete_origen.codigo_paquete}'


class ReprocesoPaquete(models.Model):
    PRODUCTO_CHOICES = [
        ('mill', 'Mill'),
        ('s2s', 'S2S'),
        ('s4s', 'S4S'),
        ('deck', 'Deck'),
        ('machihembrado', 'Machihembrado'),
        ('pallets', 'Pallets'),
    ]

    registro = models.ForeignKey(
        ReprocesoRegistro,
        on_delete=models.CASCADE,
        related_name='paquetes_generados',
    )
    fecha = models.DateField(verbose_name='Fecha')
    codigo_paquete = models.CharField(max_length=32, unique=True, verbose_name='Código del paquete')
    consecutivo_diario = models.PositiveIntegerField(verbose_name='Producción del día')
    tipo_producto = models.CharField(max_length=20, choices=PRODUCTO_CHOICES, verbose_name='Tipo de producto')
    largo = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Largo (m)')
    ancho = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Ancho (m)')
    espesor = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Espesor (m)')
    cantidad_piezas = models.PositiveIntegerField(verbose_name='Cantidad de piezas')
    calidad_visual = models.CharField(
        max_length=10,
        choices=PaqueteAserrio.CALIDAD_CHOICES,
        verbose_name='Calidad visual',
    )
    m3_pieza = models.DecimalField(
        max_digits=30,
        decimal_places=9,
        editable=False,
        verbose_name='m³ por pieza',
    )
    volumen_total = models.DecimalField(
        max_digits=40,
        decimal_places=9,
        editable=False,
        verbose_name='Volumen total (m³)',
    )

    class Meta:
        ordering = ['fecha', 'consecutivo_diario']
        constraints = [
            models.UniqueConstraint(
                fields=['fecha', 'consecutivo_diario'],
                name='reproceso_fecha_consecutivo_unico',
            ),
        ]
        verbose_name = 'Paquete de reproceso'
        verbose_name_plural = 'Paquetes de reproceso'

    def save(self, *args, **kwargs):
        self.m3_pieza = self.largo * self.ancho * self.espesor
        self.volumen_total = self.m3_pieza * self.cantidad_piezas
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.codigo_paquete} - {self.get_tipo_producto_display()}'
