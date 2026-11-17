from django.db import models

from aserrio.models import PaqueteAserrio


class SecadoRegistro(models.Model):
    fecha_inicio = models.DateField(verbose_name='Fecha inicial')
    fecha_fin = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha final del proceso',
    )
    turno = models.CharField(
        max_length=10,
        choices=PaqueteAserrio.TURNO_CHOICES,
        verbose_name='Turno de secado',
    )
    nombre_supervisor = models.CharField(max_length=150, verbose_name='Nombre del supervisor')
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        ordering = ['-fecha_inicio', '-fecha_registro']
        verbose_name = 'Registro de secado'
        verbose_name_plural = 'Registros de secado'

    def __str__(self):
        return f'Secado {self.fecha_inicio:%d/%m/%Y} - {self.get_turno_display()}'


class SecadoPaquete(models.Model):
    registro = models.ForeignKey(
        SecadoRegistro,
        on_delete=models.CASCADE,
        related_name='paquetes',
    )
    paquete = models.ForeignKey(
        PaqueteAserrio,
        on_delete=models.PROTECT,
        related_name='registros_secado',
    )
    ch_final = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='CH final (%)',
    )

    class Meta:
        ordering = ['paquete__codigo_paquete']
        constraints = [
            models.UniqueConstraint(
                fields=['registro', 'paquete'],
                name='secado_registro_paquete_unico',
            ),
        ]
        verbose_name = 'Paquete secado'
        verbose_name_plural = 'Paquetes secados'

    def __str__(self):
        return f'{self.paquete.codigo_paquete} - {self.registro}'
