from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.utils import timezone


class Rola(models.Model):
    """Modelo para registrar las rolas (troncos) que ingresan a la aserradería"""

    FACTORES_MADERA_VERIFICACION = {
        'leña': Decimal('0.50'),
        'fina': Decimal('0.55'),
        'mediana': Decimal('0.60'),
        'gruesa': Decimal('0.65'),
    }
    PRECISION_VERIFICACION = Decimal('0.01')
    
    TIPO_MADERA_CHOICES = [
        ('leña', 'Leña'),
        ('fina', 'Fina'),
        ('mediana', 'Mediana'),
        ('gruesa', 'Gruesa'),
    ]
    CLASIFICACION_VISUAL_CHOICES = [
        ('mala', 'Mala'),
        ('regular', 'Regular'),
        ('buena', 'Buena'),
        ('excelente', 'Excelente'),
    ]
    
    # Información General
    fecha = models.DateField(default=timezone.now, verbose_name="Fecha de Ingreso")
    numero_guia = models.CharField(max_length=50, unique=True, verbose_name="Número de Guía")
    
    # Medidas Externas
    metros_estereos = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Metros Estéreos"
    )
    metros_cubicos_rola = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Metros Cúbicos Rola"
    )
    
    # Tipo de Madera
    tipo_madera_especie = models.CharField(
        max_length=100, 
        verbose_name="Especie de Madera"
    )
    tipo_madera = models.CharField(
        max_length=20,
        choices=TIPO_MADERA_CHOICES,
        verbose_name="Diámetro (clasificación)",
        help_text="Clasificación general del tipo de madera"
    )
    
    # Vendedor
    empresa_vendedora = models.CharField(
        max_length=200, 
        verbose_name="Empresa Vendedora"
    )
    empresa_comercializadora = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Empresa Comercializadora"
    )
    cantidad_rolas_estimacion = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Cantidad de Rolas (estimación)"
    )
    
    # Transporte - Carro
    placa_carro = models.CharField(
        max_length=20, 
        verbose_name="Placa del Carro"
    )
    color_carro = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Color del Carro"
    )
    nombre_chofer = models.CharField(
        max_length=100, 
        verbose_name="Nombre del Chofer"
    )
    
    # Medición Interna - Supervisor
    nombre_supervisor = models.CharField(
        max_length=100, 
        verbose_name="Nombre del Supervisor"
    )
    
    # Medición Interna - Dimensiones
    largo_camion = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Largo del Camión (m)"
    )
    ancho_camion = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Ancho del Camión (m)"
    )
    altura_camion = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Altura del Camión (m)"
    )
    cantidad_cargas = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Cantidad de Cargas"
    )
    cantidad_rolas_verificacion = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Cantidad de Rolas (estimación interna)"
    )
    clasificacion_visual = models.CharField(
        max_length=20,
        choices=CLASIFICACION_VISUAL_CHOICES,
        blank=True,
        verbose_name="Clasificación Visual"
    )
    metros_estereos_verificacion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="mE de Verificación Interna"
    )
    metros_cubicos_verificacion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="m³ de Verificación Interna"
    )
    
    # Control
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    fecha_actualizado = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    
    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = "Rola"
        verbose_name_plural = "Rolas"
        indexes = [
            models.Index(fields=['-fecha_registro']),
            models.Index(fields=['numero_guia']),
        ]
    
    def __str__(self):
        return f"Rola {self.numero_guia} - {self.fecha.strftime('%d/%m/%Y')}"
    
    def volumen_total(self):
        """Calcula el volumen total en metros cúbicos"""
        return self.metros_estereos + self.metros_cubicos_rola

    volumen_total.short_description = "Volumen Total (m³)"

    @classmethod
    def calcular_verificacion_interna(
        cls,
        largo,
        ancho,
        altura,
        cantidad_cargas,
        tipo_madera,
    ):
        if (
            largo is None
            or ancho is None
            or altura is None
            or not cantidad_cargas
        ):
            return None, None

        largo_por_carga = largo / cantidad_cargas
        metros_estereos = (
            largo_por_carga
            * ancho
            * altura
            * cantidad_cargas
        ).quantize(cls.PRECISION_VERIFICACION, rounding=ROUND_HALF_UP)

        factor_madera = cls.FACTORES_MADERA_VERIFICACION.get(tipo_madera)
        if factor_madera is None:
            return metros_estereos, None

        metros_cubicos = (metros_estereos * factor_madera).quantize(
            cls.PRECISION_VERIFICACION,
            rounding=ROUND_HALF_UP,
        )
        return metros_estereos, metros_cubicos
