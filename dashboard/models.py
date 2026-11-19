from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .condiciones import NombreEmpresa, NumeroRif, LogoEmpresa, SloganEmpresa


class ConfiguracionEmpresa(models.Model):
    PALETAS_FONDO = [
        ('claro', 'Gris claro'),
        ('azulado', 'Azul muy claro'),
        ('calido', 'Arena suave'),
        ('marron', 'Marrón suave'),
        ('salvia', 'Verde salvia'),
        ('petroleo', 'Azul petróleo'),
    ]
    PALETAS_BARRA_LATERAL = [
        ('verde', 'Verde'),
        ('azul', 'Azul'),
        ('vino', 'Vino'),
        ('marron', 'Marrón'),
        ('salvia', 'Verde salvia'),
        ('petroleo', 'Azul petróleo'),
    ]
    PALETAS_MODULOS = [
        ('azul', 'Azul'),
        ('verde', 'Verde'),
        ('grafito', 'Grafito'),
        ('marron', 'Marrón'),
        ('salvia', 'Verde salvia'),
        ('petroleo', 'Azul petróleo'),
    ]

    nombre = models.CharField('nombre de la empresa', max_length=150, default=NombreEmpresa)
    rif = models.CharField('RIF', max_length=30, default=NumeroRif)
    logo_path = models.CharField(
        'ruta del logo',
        max_length=255,
        blank=True,
        default=LogoEmpresa,
        help_text='Ruta relativa a la carpeta static del proyecto, por ejemplo: images/logo.png.',
    )
    slogan = models.CharField('slogan', max_length=255, default=SloganEmpresa)
    color_fondo = models.CharField(
        'fondo del dashboard',
        max_length=20,
        choices=PALETAS_FONDO,
        default='claro',
    )
    color_sidebar = models.CharField(
        'color de la barra lateral',
        max_length=20,
        choices=PALETAS_BARRA_LATERAL,
        default='verde',
    )
    color_modulos = models.CharField(
        'color de las barras de módulos',
        max_length=20,
        choices=PALETAS_MODULOS,
        default='azul',
    )

    class Meta:
        verbose_name = 'configuración de la empresa'
        verbose_name_plural = 'configuración de la empresa'

    def __str__(self):
        return self.nombre


class ConfiguracionMantenimiento(models.Model):
    TIPO_PRODUCCION_CHOICES = [
        ('seccionada', 'Seccionada'),
        ('completa', 'Completa'),
    ]

    ciudad_parroquia = models.CharField('ciudad o parroquia', max_length=150)
    nombre_aserradero = models.CharField('nombre del aserradero', max_length=150)
    tiene_patios_rolas = models.BooleanField('¿Tiene patio de rolas?', default=False)
    clasifica_rolas = models.BooleanField('¿Clasifica rolas?', default=False)
    tipo_produccion = models.CharField(
        'tipo de producción',
        max_length=20,
        choices=TIPO_PRODUCCION_CHOICES,
    )
    cantidad_lineas = models.PositiveSmallIntegerField(
        'cantidad de líneas de producción',
        blank=True,
        null=True,
    )

    @property
    def tag_identificacion(self):
        ciudad = ''.join(
            caracter for caracter in self.ciudad_parroquia if caracter.isalpha()
        )[:3].upper()
        palabras_nombre = [
            ''.join(caracter for caracter in palabra if caracter.isalpha())[:3].upper()
            for palabra in self.nombre_aserradero.split()
        ]
        partes = [ciudad, *[palabra for palabra in palabras_nombre[:2] if palabra]]
        return '-'.join(parte for parte in partes if parte)

    class Meta:
        verbose_name = 'configuración general de mantenimiento'
        verbose_name_plural = 'configuración general de mantenimiento'

    def __str__(self):
        return self.nombre_aserradero


class LineaProduccion(models.Model):
    configuracion = models.ForeignKey(
        ConfiguracionMantenimiento,
        on_delete=models.CASCADE,
        related_name='lineas_produccion',
    )
    descripcion = models.CharField('organización de la línea', max_length=200)
    maquinas = models.JSONField('máquinas de la línea', default=list, blank=True)
    orden = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ['orden', 'pk']
        verbose_name = 'línea de producción'
        verbose_name_plural = 'líneas de producción'

    def __str__(self):
        return self.descripcion


class ActivoMaquina(models.Model):
    configuracion = models.ForeignKey(
        ConfiguracionMantenimiento,
        on_delete=models.CASCADE,
        related_name='activos_maquina',
    )
    linea_descripcion = models.CharField('línea de producción', max_length=200)
    maquina = models.CharField('máquina', max_length=200)
    especificaciones = models.JSONField('especificaciones', default=list, blank=True)
    elementos = models.JSONField('elementos de la máquina', default=list, blank=True)

    class Meta:
        ordering = ['linea_descripcion', 'maquina', 'pk']
        verbose_name = 'activo de máquina'
        verbose_name_plural = 'activos de máquinas'

    def __str__(self):
        return f'{self.maquina} - {self.linea_descripcion}'


class Consumible(models.Model):
    CRITICIDAD_CHOICES = [
        ('alta', 'Alta'),
        ('media', 'Media'),
        ('baja', 'Baja'),
    ]
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]
    TIPO_CONSUMIBLE_CHOICES = [
        ('directo', 'Directo'),
        ('indirecto', 'Indirecto'),
    ]
    CRITICIDAD_ADMINISTRATIVA_CHOICES = [
        ('critico', 'Crítico'),
        ('no_critico', 'No crítico'),
    ]

    codigo_interno = models.CharField(
        'Código interno SK',
        max_length=50,
        unique=True,
    )
    nombre = models.CharField('Nombre', max_length=150)
    categoria = models.CharField('Categoría', max_length=100, blank=True)
    descripcion = models.TextField('Descripción', blank=True)
    subcategoria = models.CharField('Subcategoría', max_length=100, blank=True)
    marca = models.CharField('Marca', max_length=100, blank=True)
    fabricante = models.CharField('Fabricante', max_length=150, blank=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    codigo_fabricante = models.CharField('Código de fabricante', max_length=100, blank=True)
    codigo_barras = models.CharField('Código de barras', max_length=100, blank=True)
    foto_frente = models.ImageField(
        'Foto de frente',
        upload_to='mantenimiento/consumibles/',
        blank=True,
    )
    foto_lado = models.ImageField(
        'Foto de lado',
        upload_to='mantenimiento/consumibles/',
        blank=True,
    )
    foto_perfil = models.ImageField(
        'Foto de perfil',
        upload_to='mantenimiento/consumibles/',
        blank=True,
    )

    material = models.CharField('Material', max_length=120, blank=True)
    diametro = models.DecimalField('Diámetro', max_digits=10, decimal_places=2, blank=True, null=True)
    espesor = models.DecimalField('Espesor', max_digits=10, decimal_places=2, blank=True, null=True)
    numero_dientes = models.PositiveSmallIntegerField('Número de dientes', blank=True, null=True)
    compatibilidad = models.TextField('Compatibilidad', blank=True)
    vida_util_estimada = models.CharField('Vida útil estimada', max_length=100, blank=True)
    aplicacion = models.TextField('Aplicación', blank=True)
    ficha_tecnica = models.FileField(
        'Ficha técnica (PDF)',
        upload_to='mantenimiento/consumibles/fichas/',
        blank=True,
    )

    proveedor_habitual = models.CharField('Proveedor habitual', max_length=150, blank=True)
    precio_compra = models.DecimalField('Precio de compra', max_digits=12, decimal_places=2, blank=True, null=True)
    ultimo_precio_compra = models.DecimalField(
        'Último precio de compra',
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    moneda = models.CharField('Moneda', max_length=20, blank=True)
    fecha_ultima_entrega = models.DateField('Fecha de entrega de última compra', blank=True, null=True)
    tiempo_entrega = models.PositiveSmallIntegerField('Tiempo de entrega (días)', blank=True, null=True)
    cantidad_minima_compra = models.DecimalField(
        'Cantidad mínima de compra',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )

    unidad_medida = models.CharField('Unidad de medida', max_length=50, blank=True)
    presentacion = models.CharField('Presentación', max_length=100, blank=True)
    cantidad_por_presentacion = models.DecimalField(
        'Cantidad por presentación',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    stock_disponible = models.DecimalField(
        'Stock disponible',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
    )
    ubicacion = models.CharField('Ubicación', max_length=150, blank=True)
    stock_minimo = models.DecimalField('Stock mínimo', max_digits=10, decimal_places=2, blank=True, null=True)
    stock_maximo = models.DecimalField('Stock máximo', max_digits=10, decimal_places=2, blank=True, null=True)
    stock_seguridad = models.DecimalField(
        'Stock de seguridad',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    requiere_condiciones_especiales = models.BooleanField(
        '¿Requiere condiciones especiales?',
        blank=True,
        null=True,
    )
    condiciones_almacenamiento = models.TextField('Condiciones de almacenamiento', blank=True)

    departamento_consumo = models.CharField('Departamento de consumo', max_length=120, blank=True)
    maquina_asociada = models.CharField('Máquina asociada', max_length=150, blank=True)
    proceso_productivo = models.CharField('Proceso productivo', max_length=150, blank=True)
    consumo_promedio_mensual = models.DecimalField(
        'Consumo promedio mensual',
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    frecuencia_reposicion = models.CharField('Frecuencia de reposición', max_length=100, blank=True)
    responsable_consumo = models.CharField('Responsable del consumo', max_length=150, blank=True)
    criticidad_consumo = models.CharField(
        'Criticidad del consumo',
        max_length=10,
        choices=CRITICIDAD_CHOICES,
        blank=True,
    )

    estado = models.CharField('Estado', max_length=10, choices=ESTADO_CHOICES, blank=True)
    tipo_consumible = models.CharField(
        'Tipo de consumible',
        max_length=10,
        choices=TIPO_CONSUMIBLE_CHOICES,
        blank=True,
    )
    criticidad_administrativa = models.CharField(
        'Criticidad administrativa',
        max_length=12,
        choices=CRITICIDAD_ADMINISTRATIVA_CHOICES,
        blank=True,
    )
    centro_costo_asociado = models.CharField('Centro de costo asociado', max_length=120, blank=True)
    cuenta_contable_asociada = models.CharField('Cuenta contable asociada', max_length=120, blank=True)
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        ordering = ['nombre', 'codigo_interno']
        verbose_name = 'consumible'
        verbose_name_plural = 'consumibles'

    def __str__(self):
        return f'{self.codigo_interno} - {self.nombre}'


class Herramienta(models.Model):
    codigo_interno = models.CharField('Código interno', max_length=50, unique=True)
    nombre = models.CharField('Nombre', max_length=150)
    descripcion = models.TextField('Descripción', blank=True)
    categoria = models.CharField('Categoría', max_length=100, blank=True)
    subcategoria = models.CharField('Subcategoría', max_length=100, blank=True)
    marca = models.CharField('Marca', max_length=100, blank=True)
    modelo = models.CharField('Modelo', max_length=100, blank=True)
    numero_serie = models.CharField('Número de serie', max_length=100, blank=True)
    foto = models.ImageField('Foto', upload_to='mantenimiento/herramientas/', blank=True)
    codigo_barras = models.CharField('Código QR o de barras', max_length=100, blank=True)

    tipo_herramienta = models.CharField('Tipo de herramienta', max_length=100, blank=True)
    material = models.CharField('Material', max_length=120, blank=True)
    potencia = models.CharField('Potencia', max_length=80, blank=True)
    voltaje = models.CharField('Voltaje', max_length=80, blank=True)
    frecuencia = models.CharField('Frecuencia', max_length=80, blank=True)
    peso = models.CharField('Peso', max_length=80, blank=True)
    dimensiones = models.CharField('Dimensiones', max_length=120, blank=True)
    capacidad_trabajo = models.CharField('Capacidad de trabajo', max_length=150, blank=True)
    capacidad_especifica = models.CharField('Capacidad específica', max_length=150, blank=True)
    area_trabajo = models.CharField('Área de trabajo', max_length=150, blank=True)

    tipo_adquisicion = models.CharField('Tipo de adquisición', max_length=100, blank=True)
    fecha_adquisicion = models.DateField('Fecha de adquisición', blank=True, null=True)
    proveedor = models.CharField('Proveedor', max_length=150, blank=True)
    fabricante = models.CharField('Fabricante', max_length=150, blank=True)
    numero_factura = models.CharField('Número de factura', max_length=100, blank=True)
    orden_factura = models.CharField('Orden de factura', max_length=100, blank=True)
    precio_adquisicion = models.DecimalField(
        'Precio de adquisición', max_digits=12, decimal_places=2, blank=True, null=True,
    )
    moneda = models.CharField('Moneda', max_length=20, blank=True)
    tiempo_garantia = models.CharField('Tiempo de garantía', max_length=100, blank=True)
    fecha_vencimiento_garantia = models.DateField(
        'Fecha de vencimiento de garantía', blank=True, null=True,
    )
    vida_util_estimada = models.CharField('Vida útil estimada', max_length=100, blank=True)

    empresa = models.CharField('Empresa', max_length=150, blank=True)
    planta = models.CharField('Planta', max_length=120, blank=True)
    edificio = models.CharField('Edificio', max_length=120, blank=True)
    departamento = models.CharField('Departamento', max_length=120, blank=True)
    area = models.CharField('Área', max_length=120, blank=True)
    sector = models.CharField('Sector', max_length=120, blank=True)
    almacen = models.CharField('Almacén', max_length=120, blank=True)
    estanteria = models.CharField('Estantería', max_length=120, blank=True)
    ubicacion_especifica = models.CharField('Ubicación específica', max_length=150, blank=True)

    tipo_asignacion = models.CharField('Tipo de asignación', max_length=100, blank=True)
    trabajador_responsable = models.CharField('Trabajador responsable', max_length=150, blank=True)
    departamento_responsable = models.CharField('Departamento responsable', max_length=120, blank=True)
    area_cargo = models.CharField('Área o cargo', max_length=120, blank=True)
    fecha_entrega = models.DateField('Fecha de entrega', blank=True, null=True)
    responsable_entrega = models.CharField('Responsable de entrega', max_length=150, blank=True)
    fecha_prevista_devolucion = models.DateField(
        'Fecha prevista de devolución', blank=True, null=True,
    )
    condicion_entrega = models.CharField('Condición de entrega', max_length=150, blank=True)

    estado_operativo = models.CharField('Estado operativo', max_length=100, blank=True)
    condicion_fisica = models.CharField('Condición física', max_length=100, blank=True)
    disponibilidad = models.CharField('Disponibilidad', max_length=100, blank=True)
    estado_conservacion = models.CharField('Estado de conservación', max_length=100, blank=True)
    fecha_ultima_evaluacion = models.DateField(
        'Fecha de última evaluación', blank=True, null=True,
    )
    responsable_evaluacion = models.CharField('Responsable de evaluación', max_length=150, blank=True)
    observaciones = models.TextField('Observaciones', blank=True)

    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        ordering = ['nombre', 'codigo_interno']
        verbose_name = 'herramienta'
        verbose_name_plural = 'herramientas'

    def __str__(self):
        return f'{self.codigo_interno} - {self.nombre}'


class PrestamoHerramienta(models.Model):
    herramienta = models.ForeignKey(
        Herramienta,
        on_delete=models.PROTECT,
        related_name='prestamos',
        verbose_name='Herramienta',
    )
    fecha_prestamo = models.DateField('Fecha de préstamo')
    nombre_solicitante = models.CharField('Nombre de quien solicita', max_length=150)
    fecha_devolucion = models.DateField('Fecha de devolución')
    nombre_responsable = models.CharField('Nombre del responsable', max_length=150)
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        ordering = ['-fecha_prestamo', '-fecha_registro']
        verbose_name = 'préstamo de herramienta'
        verbose_name_plural = 'préstamos de herramientas'

    def __str__(self):
        return f'{self.herramienta.codigo_interno} - {self.nombre_solicitante}'


class OrdenTrabajo(models.Model):
    TIPO_ORDEN_CHOICES = [
        ('correctivo', 'Correctivo'),
        ('preventivo', 'Preventivo'),
        ('inspeccion', 'Inspección'),
        ('emergencia', 'Emergencia'),
        ('servicio_cliente', 'Servicio al cliente'),
        ('produccion', 'Producción'),
        ('construccion', 'Construcción'),
    ]
    PRIORIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    numero_orden = models.BigAutoField('Número de orden', primary_key=True)
    titulo = models.CharField('Título de la orden', max_length=180)
    tipo_orden = models.CharField('Tipo de orden', max_length=30, choices=TIPO_ORDEN_CHOICES)
    duracion_estimada = models.CharField('Duración estimada', max_length=80, blank=True)
    actividades_programadas = models.TextField('Actividades programadas', blank=True)
    fecha_emision = models.DateField('Fecha de emisión', default=timezone.localdate)
    solicitante = models.CharField('Nombre del solicitante', max_length=150)
    area_solicitante = models.CharField('Área o departamento del solicitante', max_length=120, blank=True)
    contacto_solicitante = models.CharField('Teléfono o correo del solicitante', max_length=150, blank=True)
    cliente_externo = models.BooleanField('¿Es un cliente externo?', default=False)
    nombre_cliente = models.CharField('Nombre del cliente', max_length=150, blank=True)
    contacto_cliente = models.CharField('Contacto del cliente', max_length=150, blank=True)
    contacto_cliente_datos = models.CharField('Teléfono o correo del cliente', max_length=150, blank=True)
    descripcion_trabajo = models.CharField('Título del trabajo', max_length=180)
    detalle_trabajo = models.TextField('Detalle del trabajo')
    ubicacion = models.CharField('Ubicación', max_length=180, blank=True)
    activo = models.CharField('Activo o equipo', max_length=180, blank=True)
    responsable = models.CharField('Responsable del trabajo', max_length=150, blank=True)
    fecha_programada = models.DateField('Fecha programada', blank=True, null=True)
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=PRIORIDAD_CHOICES,
        blank=True,
    )
    materiales_estimados = models.TextField('Materiales estimados', blank=True)
    mano_obra_estimada = models.DecimalField(
        'Costo estimado de mano de obra',
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )
    materiales_utilizados = models.TextField('Materiales utilizados', blank=True)
    tiempos_ejecucion = models.TextField('Registro de tiempos de ejecución', blank=True)
    observaciones = models.TextField('Observaciones', blank=True)
    hallazgos = models.TextField('Hallazgos', blank=True)
    firma_responsable = models.CharField('Firma o nombre del responsable/mecánico', max_length=150, blank=True)
    firma_supervisor = models.CharField('Firma o nombre del supervisor', max_length=150, blank=True)
    fecha_registro = models.DateTimeField('Fecha de registro', auto_now_add=True)

    class Meta:
        ordering = ['-numero_orden']
        verbose_name = 'orden de trabajo'
        verbose_name_plural = 'órdenes de trabajo'

    def __str__(self):
        return f'OT-{self.numero_orden:05d} - {self.titulo}'


class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    cargo = models.CharField('cargo', max_length=100)

    class Meta:
        verbose_name = 'perfil de usuario'
        verbose_name_plural = 'perfiles de usuario'

    def __str__(self):
        return f'{self.usuario} - {self.cargo}'


class Trabajador(models.Model):
    ESTADO_CIVIL_CHOICES = [
        ('soltero', 'Soltero(a)'),
        ('casado', 'Casado(a)'),
        ('divorciado', 'Divorciado(a)'),
        ('union_estable', 'Unión estable'),
        ('viudo', 'Viudo(a)'),
        ('separado', 'Separado(a)'),
    ]

    nombres = models.CharField(max_length=120, verbose_name='Nombre y apellidos')
    foto = models.ImageField(
        upload_to='personal/fotos/',
        blank=True,
        null=True,
        verbose_name='Foto del trabajador',
    )
    cedula_identidad = models.CharField(max_length=20, verbose_name='Cédula de identidad')
    foto_cedula = models.ImageField(
        upload_to='personal/cedulas/',
        blank=True,
        null=True,
        verbose_name='Foto de la cédula',
    )
    tiene_rif = models.BooleanField(default=False, verbose_name='¿Tiene RIF?')
    rif = models.CharField(max_length=20, blank=True, null=True, verbose_name='RIF')
    fecha_nacimiento = models.DateField(verbose_name='Fecha de nacimiento')
    nacionalidad = models.CharField(max_length=80, default='Venezolana', verbose_name='Nacionalidad')
    estado_civil = models.CharField(
        max_length=30,
        choices=ESTADO_CIVIL_CHOICES,
        default='soltero',
        verbose_name='Estado civil',
    )
    direccion = models.CharField(max_length=255, blank=True, verbose_name='Dirección completa')
    estado = models.CharField(max_length=80, blank=True, verbose_name='Estado')
    ciudad = models.CharField(max_length=100, blank=True, verbose_name='Ciudad')
    municipio = models.CharField(max_length=100, blank=True, verbose_name='Municipio')
    parroquia = models.CharField(max_length=100, blank=True, verbose_name='Parroquia')
    calle = models.CharField(max_length=150, blank=True, verbose_name='Calle')
    numero = models.CharField(max_length=20, blank=True, verbose_name='Número')
    punto_referencia = models.CharField(max_length=255, blank=True, verbose_name='Punto de referencia')

    telefono = models.CharField(max_length=30, blank=True, verbose_name='Teléfono principal')
    telefono_alternativo = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Teléfono alternativo',
    )
    correo_personal = models.EmailField(blank=True, verbose_name='Correo personal')
    correo_empresarial = models.EmailField(blank=True, verbose_name='Correo empresarial')
    contacto_emergencia_nombre = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Nombre del contacto de emergencia',
    )
    contacto_emergencia_apellido = models.CharField(
        max_length=80,
        blank=True,
        verbose_name='Apellido del contacto de emergencia',
    )
    contacto_emergencia_telefono = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Teléfono del contacto de emergencia',
    )
    contacto_emergencia_parentesco = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Parentesco',
    )
    contacto_emergencia_fecha_verificacion = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de verificación de la información',
    )

    en_proceso_contratacion = models.BooleanField(
        default=False,
        verbose_name='En proceso de contratación',
    )
    trabajador_activo = models.BooleanField(default=True, verbose_name='Trabajador activo')
    ausencia_desde = models.DateField(
        blank=True,
        null=True,
        verbose_name='Periodo de ausencia o suspensión - desde',
    )
    ausencia_hasta = models.DateField(
        blank=True,
        null=True,
        verbose_name='Periodo de ausencia o suspensión - hasta',
    )
    en_proceso_egreso = models.BooleanField(default=False, verbose_name='En proceso de egreso')
    fecha_egreso = models.DateField(blank=True, null=True, verbose_name='Fecha de egreso')

    codigo_trabajador = models.CharField(
        max_length=30,
        blank=True,
        unique=True,
        verbose_name='Código de trabajador',
    )
    fecha_oferta_seleccion = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha de oferta o selección',
    )
    fecha_ingreso = models.DateField(blank=True, null=True, verbose_name='Fecha de ingreso')
    tipo_contrato = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='Tipo de contrato',
    )
    fecha_fin_contrato = models.DateField(
        blank=True,
        null=True,
        verbose_name='Fecha final del contrato',
    )
    area_trabajo = models.CharField(max_length=100, blank=True, verbose_name='Área de trabajo')
    departamento = models.CharField(max_length=100, blank=True, verbose_name='Departamento')
    seccion = models.CharField(max_length=100, blank=True, verbose_name='Sección')
    cargo = models.CharField(max_length=120, blank=True, verbose_name='Cargo')
    funciones = models.TextField(blank=True, verbose_name='Funciones')
    responsabilidades = models.TextField(blank=True, verbose_name='Responsabilidades')
    nombre_supervisor_directo = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Nombre del supervisor directo',
    )
    jornada_horario_trabajo = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Jornada y horario de trabajo',
    )
    turno = models.CharField(max_length=50, blank=True, verbose_name='Turno')
    salario_contratacion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name='Salario de contratación',
    )
    beneficios = models.TextField(blank=True, verbose_name='Beneficios')
    prestaciones = models.TextField(blank=True, verbose_name='Prestaciones')
    deducciones = models.TextField(blank=True, verbose_name='Deducciones')
    responsable_contratacion_nombre = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Persona responsable de la contratación',
    )
    responsable_contratacion_firma = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Firma de la persona responsable',
    )

    historial_ascensos = models.TextField(blank=True, verbose_name='Historial de ascensos')
    historial_cambios_cargo = models.TextField(
        blank=True,
        verbose_name='Historial de cambios de cargo',
    )
    historial_traslados = models.TextField(blank=True, verbose_name='Historial de traslados')
    historial_cambios_horario = models.TextField(
        blank=True,
        verbose_name='Historial de cambios de horario',
    )
    historial_cambio_turno = models.TextField(
        blank=True,
        verbose_name='Historial de cambio de turno',
    )
    historial_modificacion_salarial = models.TextField(
        blank=True,
        verbose_name='Historial de modificación salarial',
    )
    historial_cambio_supervisor = models.TextField(
        blank=True,
        verbose_name='Historial de cambio de supervisor',
    )
    historial_cambio_jornada = models.TextField(
        blank=True,
        verbose_name='Historial de cambio de jornada',
    )

    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')

    class Meta:
        ordering = ['nombres']
        verbose_name = 'Trabajador'
        verbose_name_plural = 'Trabajadores'

    def __str__(self):
        return self.nombres


class ConfiguracionNomina(models.Model):
    ivss_patronal_porcentaje = models.DecimalField(
        'IVSS patronal (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    rpe_patronal_porcentaje = models.DecimalField(
        'RPE patronal (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    faov_patronal_porcentaje = models.DecimalField(
        'FAOV patronal (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    inces_porcentaje = models.DecimalField(
        'INCES (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    pensiones_porcentaje = models.DecimalField(
        'Pensiones (%)',
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    class Meta:
        verbose_name = 'configuración de nómina'
        verbose_name_plural = 'configuración de nómina'


class NominaPeriodo(models.Model):
    METODOS_PAGO = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('otro', 'Otro'),
    ]

    codigo = models.CharField('Código de nómina', max_length=24, unique=True)
    periodo_desde = models.DateField('Período desde')
    periodo_hasta = models.DateField('Período hasta')
    fecha_pago = models.DateField('Fecha de pago')
    metodo_pago = models.CharField(
        'Método de pago',
        max_length=20,
        choices=METODOS_PAGO,
        default='transferencia',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_pago', '-pk']
        verbose_name = 'período de nómina'
        verbose_name_plural = 'períodos de nómina'

    def __str__(self):
        return self.codigo


class NominaDetalle(models.Model):
    periodo = models.ForeignKey(
        NominaPeriodo,
        on_delete=models.PROTECT,
        related_name='detalles',
    )
    trabajador = models.ForeignKey(
        Trabajador,
        on_delete=models.PROTECT,
        related_name='nominas',
    )
    trabajador_nombre = models.CharField('Nombre del trabajador', max_length=120)
    cedula_identidad = models.CharField('Cédula', max_length=20)
    cargo = models.CharField('Cargo', max_length=120, blank=True)
    area_trabajo = models.CharField('Área de trabajo', max_length=100, blank=True)
    departamento = models.CharField('Departamento', max_length=100, blank=True)
    seccion = models.CharField('Sección', max_length=100, blank=True)
    tipo_contrato = models.CharField('Contrato', max_length=30, blank=True)
    salario_base = models.DecimalField('Salario base', max_digits=12, decimal_places=2, default=0)
    horas_extras = models.DecimalField('Horas extras', max_digits=12, decimal_places=2, default=0)
    bono_produccion = models.DecimalField('Bono de producción', max_digits=12, decimal_places=2, default=0)
    bono_nocturno = models.DecimalField('Bono nocturno', max_digits=12, decimal_places=2, default=0)
    vacaciones = models.DecimalField('Vacaciones', max_digits=12, decimal_places=2, default=0)
    total_asignaciones = models.DecimalField('Total asignaciones', max_digits=12, decimal_places=2, default=0)
    ivss_deduccion = models.DecimalField('IVSS trabajador', max_digits=12, decimal_places=2, default=0)
    rpe_deduccion = models.DecimalField('RPE trabajador', max_digits=12, decimal_places=2, default=0)
    faov_deduccion = models.DecimalField('FAOV trabajador', max_digits=12, decimal_places=2, default=0)
    anticipo_salarial = models.DecimalField('Anticipo salarial', max_digits=12, decimal_places=2, default=0)
    prestamo_personal = models.DecimalField('Préstamo personal', max_digits=12, decimal_places=2, default=0)
    total_deducciones = models.DecimalField('Total deducciones', max_digits=12, decimal_places=2, default=0)
    neto_pagar = models.DecimalField('Neto a pagar', max_digits=12, decimal_places=2, default=0)
    numero_cuenta = models.CharField('Número de cuenta', max_length=40, blank=True)
    ivss_patronal = models.DecimalField('IVSS patronal', max_digits=12, decimal_places=2, default=0)
    rpe_patronal = models.DecimalField('RPE patronal', max_digits=12, decimal_places=2, default=0)
    faov_patronal = models.DecimalField('FAOV patronal', max_digits=12, decimal_places=2, default=0)
    inces = models.DecimalField('INCES', max_digits=12, decimal_places=2, default=0)
    pensiones = models.DecimalField('Pensiones', max_digits=12, decimal_places=2, default=0)
    ivss_patronal_porcentaje = models.DecimalField('Tasa IVSS patronal (%)', max_digits=5, decimal_places=2, default=0)
    rpe_patronal_porcentaje = models.DecimalField('Tasa RPE patronal (%)', max_digits=5, decimal_places=2, default=0)
    faov_patronal_porcentaje = models.DecimalField('Tasa FAOV patronal (%)', max_digits=5, decimal_places=2, default=0)
    inces_porcentaje = models.DecimalField('Tasa INCES (%)', max_digits=5, decimal_places=2, default=0)
    pensiones_porcentaje = models.DecimalField('Tasa pensiones (%)', max_digits=5, decimal_places=2, default=0)
    total_aportes = models.DecimalField('Total aportes patronales', max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['trabajador_nombre']
        constraints = [
            models.UniqueConstraint(
                fields=['periodo', 'trabajador'],
                name='nomina_periodo_trabajador_unico',
            ),
        ]
        verbose_name = 'detalle de nómina'
        verbose_name_plural = 'detalles de nómina'

    @property
    def numero_cuenta_enmascarado(self):
        digitos = ''.join(caracter for caracter in self.numero_cuenta if caracter.isdigit())
        if not digitos:
            return 'Sin registrar'
        return f'{"*" * max(len(digitos) - 4, 0)}{digitos[-4:]}'
