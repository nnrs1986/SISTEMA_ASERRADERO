from django.db import models
from django.db.models import UniqueConstraint


class PaqueteAserrio(models.Model):
	TURNO_CHOICES = [
		('turno_1', 'Turno 1'),
		('turno_2', 'Turno 2'),
		('turno_3', 'Turno 3'),
	]
	ESPECIE_CHOICES = [
		('pino', 'Pino'),
		('cedro', 'Cedro'),
		('caoba', 'Caoba'),
		('mureillo', 'Mureillo'),
		('pardillo', 'Pardillo'),
		('saman', 'Samán'),
		('saqui_saqui', 'Saqui-saqui'),
		('teca', 'Teca'),
		('otro', 'Otro'),
	]
	TIPO_ROLA_CHOICES = [
		('gruesa', 'Gruesa'),
		('mediana_fina', 'Mediana fina'),
		('lena', 'Leña'),
	]
	MAQUINAS_CHOICES = [
		('sierra_principal', 'Sierra principal'),
		('sierra_doble', 'Sierra doble'),
		('sierra_de_disco', 'Sierra de disco'),
		('multiple_de_disco', 'Múltiple de disco'),
		('multiple_horizontal_3_ejes', 'Múltiple de sierras horizontales (3 o más ejes)'),
		('sierra_horizontal_2_ejes', 'Sierra horizontal (2 ejes)'),
		('sierra_horizontal_1_eje', 'Sierra horizontal (1 eje)'),
	]
	MAQUINAS_EXCLUSIVAS = {
		'sierra_principal', 'sierra_doble', 'sierra_de_disco',
	}
	RECUPERACION_CHOICES = [
		('sierra_1_disco', 'Sierra de 1 disco'),
		('sierra_2_discos', 'Sierra de 2 discos'),
		('sierra_horizontal', 'Sierra horizontal'),
	]
	ELEMENTO_CHOICES = [
		('tablilla', 'Tablilla'),
		('forro', 'Forro'),
		('tabla', 'Tabla'),
		('alfajilla', 'Alfajilla'),
		('tablon', 'Tablón'),
		('liston', 'Listón'),
		('cuarton', 'Cuartón'),
		('viga', 'Viga'),
		('columna', 'Columna'),
	]
	CALIDAD_CHOICES = [
		('primera', 'Madera de 1era'),
		('segunda', 'Madera de 2da'),
		('tercera', 'Madera de 3era'),
		('cuarta', 'Madera de 4ta'),
	]

	fecha = models.DateField(verbose_name='Fecha')
	turno = models.CharField(max_length=10, choices=TURNO_CHOICES, verbose_name='Turno de trabajo')
	nombre_supervisor = models.CharField(max_length=150, verbose_name='Nombre del supervisor')
	nombre_operador = models.CharField(max_length=150, verbose_name='Nombre del operador')
	especie_madera = models.CharField(max_length=20, choices=ESPECIE_CHOICES, verbose_name='Especie de madera')
	tipo_rola = models.CharField(max_length=20, choices=TIPO_ROLA_CHOICES, verbose_name='Tipo de rola')
	maquinas_proceso = models.JSONField(default=list, verbose_name='Máquinas en el proceso')
	incluye_recuperacion = models.BooleanField(default=False, verbose_name='Incluye recuperación de madera')
	maquina_recuperacion = models.CharField(
		max_length=30,
		choices=RECUPERACION_CHOICES,
		blank=True,
		verbose_name='Máquina de recuperación',
	)
	codigo_paquete = models.CharField(max_length=32, unique=True, verbose_name='Código del paquete')
	consecutivo_diario = models.PositiveIntegerField(verbose_name='Producción del día')

	largo = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Largo (m)')
	ancho = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Ancho (m)')
	espesor = models.DecimalField(max_digits=10, decimal_places=3, verbose_name='Espesor (m)')
	m3_pieza = models.DecimalField(max_digits=30, decimal_places=9, editable=False, verbose_name='m³ por pieza')
	cantidad_piezas = models.PositiveIntegerField(verbose_name='Cantidad de piezas')
	volumen_total = models.DecimalField(max_digits=40, decimal_places=9, editable=False, verbose_name='Volumen total (m³)')
	ch_estimado = models.PositiveIntegerField(verbose_name='CH% estimado')
	tipo_elemento = models.CharField(max_length=20, choices=ELEMENTO_CHOICES, verbose_name='Tipo de elemento')
	calidad_visual = models.CharField(max_length=10, choices=CALIDAD_CHOICES, verbose_name='Calidad visual')
	fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')
	fecha_edicion = models.DateTimeField(null=True, blank=True, verbose_name='Fecha de edición')

	class Meta:
		ordering = ['fecha', 'consecutivo_diario']
		constraints = [
			UniqueConstraint(fields=['fecha', 'consecutivo_diario'], name='aserrio_fecha_consecutivo_unico'),
		]
		verbose_name = 'Paquete de aserrío'
		verbose_name_plural = 'Paquetes de aserrío'

	def save(self, *args, **kwargs):
		self.m3_pieza = self.largo * self.ancho * self.espesor
		self.volumen_total = self.m3_pieza * self.cantidad_piezas
		super().save(*args, **kwargs)

	def __str__(self):
		return f'{self.codigo_paquete} - {self.fecha:%d/%m/%Y}'
