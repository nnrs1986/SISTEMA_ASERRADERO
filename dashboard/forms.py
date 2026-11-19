import json

from django import forms
from django.core.validators import MinValueValidator

from .condiciones import LogoEmpresa
from .models import (
    ConfiguracionEmpresa,
    ConfiguracionMantenimiento,
    ConfiguracionNomina,
    Consumible,
    Herramienta,
    NominaDetalle,
    NominaPeriodo,
    OrdenTrabajo,
    Trabajador,
)


def validar_imagen_logo(archivo):
    extensiones = {
        '.png': lambda contenido: contenido.startswith(b'\x89PNG\r\n\x1a\n'),
        '.jpg': lambda contenido: contenido.startswith(b'\xff\xd8\xff'),
        '.jpeg': lambda contenido: contenido.startswith(b'\xff\xd8\xff'),
        '.gif': lambda contenido: contenido.startswith((b'GIF87a', b'GIF89a')),
        '.webp': lambda contenido: contenido.startswith(b'RIFF') and contenido[8:12] == b'WEBP',
    }
    extension = '.' + archivo.name.rsplit('.', 1)[-1].lower() if '.' in archivo.name else ''
    validar_contenido = extensiones.get(extension)
    if not validar_contenido:
        raise forms.ValidationError('Usa una imagen PNG, JPG, JPEG, GIF o WEBP.')
    if archivo.size > 5 * 1024 * 1024:
        raise forms.ValidationError('La imagen no puede superar los 5 MB.')

    contenido = archivo.read(12)
    archivo.seek(0)
    if not validar_contenido(contenido):
        raise forms.ValidationError('El archivo no contiene una imagen válida para su formato.')


class NominaPeriodoForm(forms.ModelForm):
    class Meta:
        model = NominaPeriodo
        fields = ('periodo_desde', 'periodo_hasta', 'fecha_pago', 'metodo_pago')
        widgets = {
            'periodo_desde': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'periodo_hasta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_pago': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        desde = cleaned_data.get('periodo_desde')
        hasta = cleaned_data.get('periodo_hasta')
        if desde and hasta and desde > hasta:
            self.add_error('periodo_hasta', 'La fecha final debe ser igual o posterior a la inicial.')
        return cleaned_data


class NominaDetalleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in (
            'horas_extras',
            'bono_produccion',
            'bono_nocturno',
            'vacaciones',
            'anticipo_salarial',
            'prestamo_personal',
        ):
            self.fields[field_name].validators.append(MinValueValidator(0))

    class Meta:
        model = NominaDetalle
        fields = (
            'horas_extras',
            'bono_produccion',
            'bono_nocturno',
            'vacaciones',
            'anticipo_salarial',
            'prestamo_personal',
            'numero_cuenta',
        )
        widgets = {
            'horas_extras': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'bono_produccion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'bono_nocturno': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'vacaciones': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'anticipo_salarial': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'prestamo_personal': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'numero_cuenta': forms.PasswordInput(
                attrs={'class': 'form-control', 'autocomplete': 'new-password'},
                render_value=False,
            ),
        }


class ConfiguracionNominaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionNomina
        fields = (
            'ivss_patronal_porcentaje',
            'rpe_patronal_porcentaje',
            'faov_patronal_porcentaje',
            'inces_porcentaje',
            'pensiones_porcentaje',
        )
        widgets = {
            'ivss_patronal_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'rpe_patronal_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'faov_patronal_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'inces_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'pensiones_porcentaje': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
        }


class ConfiguracionEmpresaForm(forms.ModelForm):
    logo = forms.FileField(
        label='Logo de la empresa',
        required=False,
        validators=[validar_imagen_logo],
        help_text=f'La imagen se guardará en static/{LogoEmpresa} y esa ruta se registrará en la base de datos.',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
    )

    class Meta:
        model = ConfiguracionEmpresa
        fields = ('nombre', 'slogan', 'rif')
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'slogan': forms.TextInput(attrs={'class': 'form-control'}),
            'rif': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PersonalizacionSistemaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionEmpresa
        fields = ('color_fondo', 'color_sidebar', 'color_modulos')
        widgets = {
            'color_fondo': forms.Select(attrs={'class': 'form-control'}),
            'color_sidebar': forms.Select(attrs={'class': 'form-control'}),
            'color_modulos': forms.Select(attrs={'class': 'form-control'}),
        }


class MantenimientoGeneralForm(forms.ModelForm):
    lineas = forms.CharField(widget=forms.HiddenInput)
    tiene_patios_rolas = forms.TypedChoiceField(
        label='¿Tiene patio de rolas?',
        choices=(('true', 'Sí'), ('false', 'No')),
        coerce=lambda valor: valor == 'true',
        widget=forms.RadioSelect,
    )
    clasifica_rolas = forms.TypedChoiceField(
        label='¿Clasifica rolas?',
        choices=(('true', 'Sí'), ('false', 'No')),
        coerce=lambda valor: valor == 'true',
        widget=forms.RadioSelect,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial['tiene_patios_rolas'] = (
                'true' if self.instance.tiene_patios_rolas else 'false'
            )
            self.initial['clasifica_rolas'] = (
                'true' if self.instance.clasifica_rolas else 'false'
            )

    class Meta:
        model = ConfiguracionMantenimiento
        fields = (
            'ciudad_parroquia',
            'nombre_aserradero',
            'tiene_patios_rolas',
            'clasifica_rolas',
            'tipo_produccion',
            'cantidad_lineas',
        )
        widgets = {
            'ciudad_parroquia': forms.TextInput(attrs={'class': 'form-control'}),
            'nombre_aserradero': forms.TextInput(attrs={'class': 'form-control'}),
            'tiene_patios_rolas': forms.RadioSelect,
            'clasifica_rolas': forms.RadioSelect,
            'tipo_produccion': forms.RadioSelect,
            'cantidad_lineas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo_produccion = cleaned_data.get('tipo_produccion')
        cantidad_lineas = cleaned_data.get('cantidad_lineas')

        if tipo_produccion == 'seccionada' and not cantidad_lineas:
            self.add_error('cantidad_lineas', 'Indica cuántas líneas de producción tiene.')
        elif tipo_produccion == 'completa':
            cleaned_data['cantidad_lineas'] = None

        try:
            lineas = json.loads(cleaned_data.get('lineas', ''))
        except (TypeError, json.JSONDecodeError):
            self.add_error('lineas', 'Agrega la organización de al menos una línea.')
            return cleaned_data

        if not isinstance(lineas, list):
            self.add_error('lineas', 'La organización de las líneas no es válida.')
            return cleaned_data

        lineas_normalizadas = []
        for linea in lineas:
            if isinstance(linea, str):
                descripcion = linea.strip()
                maquinas = []
            elif isinstance(linea, dict):
                descripcion = linea.get('descripcion', '')
                maquinas = linea.get('maquinas', [])
                if not isinstance(descripcion, str) or not isinstance(maquinas, list):
                    self.add_error('lineas', 'Los datos de cada línea y sus máquinas no son válidos.')
                    return cleaned_data
                descripcion = descripcion.strip()
                if any(not isinstance(maquina, str) for maquina in maquinas):
                    self.add_error('lineas', 'Los nombres de las máquinas no son válidos.')
                    return cleaned_data
                maquinas = [maquina.strip() for maquina in maquinas if maquina.strip()]
                if maquinas and not descripcion:
                    self.add_error('lineas', 'Indica la descripción de cada línea que tenga máquinas.')
                    return cleaned_data
                if descripcion and not maquinas:
                    self.add_error('lineas', 'Agrega al menos una máquina para cada línea de producción.')
                    return cleaned_data
            else:
                self.add_error('lineas', 'Los datos de cada línea de producción no son válidos.')
                return cleaned_data

            if descripcion:
                lineas_normalizadas.append({
                    'descripcion': descripcion,
                    'maquinas': maquinas,
                })

        if not lineas_normalizadas:
            self.add_error('lineas', 'Agrega la organización de al menos una línea.')
        elif len(lineas_normalizadas) > 50:
            self.add_error('lineas', 'Puedes agregar un máximo de 50 líneas.')
        elif len({
            ' '.join(linea['descripcion'].split()).casefold()
            for linea in lineas_normalizadas
        }) != len(lineas_normalizadas):
            self.add_error('lineas', 'Los nombres de las líneas de producción no pueden repetirse.')
        elif any(len(linea['descripcion']) > 200 for linea in lineas_normalizadas):
            self.add_error('lineas', 'Cada descripción puede tener un máximo de 200 caracteres.')
        elif any(
            len(maquina) > 200
            for linea in lineas_normalizadas
            for maquina in linea['maquinas']
        ):
            self.add_error('lineas', 'Cada nombre de máquina puede tener un máximo de 200 caracteres.')
        elif any(len(linea['maquinas']) > 50 for linea in lineas_normalizadas):
            self.add_error('lineas', 'Puedes agregar un máximo de 50 máquinas por línea.')
        else:
            cleaned_data['lineas'] = lineas_normalizadas

        return cleaned_data


class OrdenTrabajoForm(forms.ModelForm):
    class Meta:
        model = OrdenTrabajo
        fields = (
            'titulo',
            'tipo_orden',
            'duracion_estimada',
            'actividades_programadas',
            'fecha_emision',
            'solicitante',
            'area_solicitante',
            'contacto_solicitante',
            'cliente_externo',
            'nombre_cliente',
            'contacto_cliente',
            'contacto_cliente_datos',
            'descripcion_trabajo',
            'detalle_trabajo',
            'ubicacion',
            'activo',
            'responsable',
            'fecha_programada',
            'prioridad',
            'materiales_estimados',
            'mano_obra_estimada',
            'materiales_utilizados',
            'tiempos_ejecucion',
            'observaciones',
            'hallazgos',
            'firma_responsable',
            'firma_supervisor',
        )
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo_orden': forms.Select(attrs={'class': 'form-control'}),
            'duracion_estimada': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej.: 4 horas'}),
            'actividades_programadas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_emision': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'solicitante': forms.TextInput(attrs={'class': 'form-control'}),
            'area_solicitante': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_solicitante': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente_externo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'nombre_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_cliente': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_cliente_datos': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion_trabajo': forms.TextInput(attrs={'class': 'form-control'}),
            'detalle_trabajo': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'ubicacion': forms.TextInput(attrs={'class': 'form-control'}),
            'activo': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_programada': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'prioridad': forms.Select(attrs={'class': 'form-control'}),
            'materiales_estimados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mano_obra_estimada': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'materiales_utilizados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tiempos_ejecucion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'hallazgos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'firma_responsable': forms.TextInput(attrs={'class': 'form-control'}),
            'firma_supervisor': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ActivoMaquinaForm(forms.Form):
    especificaciones = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )
    elementos = forms.CharField(
        required=False,
        widget=forms.HiddenInput,
    )

    def clean_especificaciones(self):
        try:
            especificaciones = json.loads(self.cleaned_data['especificaciones'] or '[]')
        except (TypeError, json.JSONDecodeError) as error:
            raise forms.ValidationError(
                'Las especificaciones no tienen un formato válido.'
            ) from error

        if not isinstance(especificaciones, list):
            raise forms.ValidationError('Agrega las especificaciones en formato de lista.')
        if len(especificaciones) > 30:
            raise forms.ValidationError('Puedes agregar un máximo de 30 especificaciones.')

        normalizadas = []
        nombres = set()
        for especificacion in especificaciones:
            if not isinstance(especificacion, dict):
                raise forms.ValidationError('Revisa el formato de las especificaciones.')

            nombre = especificacion.get('nombre', '')
            valor = especificacion.get('valor', '')
            if not isinstance(nombre, str) or not isinstance(valor, str):
                raise forms.ValidationError('Los nombres y valores deben ser texto.')
            nombre = nombre.strip()
            valor = valor.strip()

            if not nombre and not valor:
                continue
            if not nombre or not valor:
                raise forms.ValidationError(
                    'Completa el nombre y el valor de cada especificación.'
                )
            if len(nombre) > 80 or len(valor) > 250:
                raise forms.ValidationError(
                    'Cada nombre admite 80 caracteres y cada valor 250.'
                )

            nombre_normalizado = ' '.join(nombre.split()).casefold()
            if nombre_normalizado in nombres:
                raise forms.ValidationError(
                    'No repitas el nombre de una especificación en la misma máquina.'
                )
            nombres.add(nombre_normalizado)
            normalizadas.append({'nombre': nombre, 'valor': valor})

        if not normalizadas:
            raise forms.ValidationError(
                'Agrega al menos una especificación con su valor.'
            )
        return normalizadas


    def clean_elementos(self):
        try:
            elementos = json.loads(self.cleaned_data['elementos'] or '[]')
        except (TypeError, json.JSONDecodeError) as error:
            raise forms.ValidationError(
                'Los elementos de la máquina no tienen un formato válido.'
            ) from error

        if not isinstance(elementos, list):
            raise forms.ValidationError('Agrega los elementos en formato de lista.')
        if len(elementos) > 50:
            raise forms.ValidationError('Puedes agregar un máximo de 50 elementos.')

        tipos_permitidos = {'mecanico', 'electrico', 'manual', 'otro'}
        normalizados = []
        for elemento in elementos:
            if not isinstance(elemento, dict):
                raise forms.ValidationError('Revisa el formato de los elementos.')

            tipo_elemento = elemento.get('tipo_elemento', '')
            descripcion = elemento.get('descripcion', '')
            tipos = elemento.get('tipos', [])
            if (
                not isinstance(tipo_elemento, str)
                or not isinstance(descripcion, str)
                or not isinstance(tipos, list)
                or any(not isinstance(tipo, str) for tipo in tipos)
            ):
                raise forms.ValidationError('Revisa los datos de cada elemento.')

            tipo_elemento = tipo_elemento.strip()
            descripcion = descripcion.strip()
            tipos = list(dict.fromkeys(tipo.strip() for tipo in tipos))
            if not tipo_elemento and not descripcion and not tipos:
                continue
            if not tipo_elemento or not descripcion:
                raise forms.ValidationError(
                    'Completa el tipo y la descripción de cada elemento.'
                )
            if len(tipo_elemento) > 80 or len(descripcion) > 500:
                raise forms.ValidationError(
                    'El tipo admite 80 caracteres y la descripción 500.'
                )
            if not tipos or any(tipo not in tipos_permitidos for tipo in tipos):
                raise forms.ValidationError(
                    'Selecciona si el elemento es mecánico, eléctrico, manual u otro.'
                )

            normalizados.append({
                'tipo_elemento': tipo_elemento,
                'descripcion': descripcion,
                'tipos': tipos,
            })

        return normalizados


def validar_foto_consumible(archivo):
    if archivo.size > 5 * 1024 * 1024:
        raise forms.ValidationError('Cada foto no puede superar los 5 MB.')


def validar_ficha_pdf(archivo):
    if not archivo.name.lower().endswith('.pdf'):
        raise forms.ValidationError('La ficha técnica debe estar en formato PDF.')
    if archivo.size > 20 * 1024 * 1024:
        raise forms.ValidationError('La ficha técnica no puede superar los 20 MB.')
    encabezado = archivo.read(5)
    archivo.seek(0)
    if encabezado != b'%PDF-':
        raise forms.ValidationError('El archivo no contiene un documento PDF válido.')


class ConsumibleForm(forms.ModelForm):
    estado = forms.ChoiceField(
        label='Estado',
        required=False,
        choices=(('', 'Selecciona el estado'), *Consumible.ESTADO_CHOICES),
    )
    requiere_condiciones_especiales = forms.TypedChoiceField(
        label='¿Requiere condiciones especiales?',
        required=False,
        choices=(('', 'Selecciona una opción'), ('False', 'No'), ('True', 'Sí')),
        coerce=lambda value: {'False': False, 'True': True}.get(value),
        empty_value=None,
    )
    foto_frente = forms.ImageField(
        required=False,
        validators=[validar_foto_consumible],
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
    )
    foto_lado = forms.ImageField(
        required=False,
        validators=[validar_foto_consumible],
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
    )
    foto_perfil = forms.ImageField(
        required=False,
        validators=[validar_foto_consumible],
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
    )
    ficha_tecnica = forms.FileField(
        required=False,
        validators=[validar_ficha_pdf],
        widget=forms.ClearableFileInput(attrs={'accept': 'application/pdf,.pdf'}),
    )

    class Meta:
        model = Consumible
        exclude = ('fecha_registro',)
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'compatibilidad': forms.Textarea(attrs={'rows': 2}),
            'aplicacion': forms.Textarea(attrs={'rows': 2}),
            'condiciones_almacenamiento': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'consumable-input')
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'consumable-file'
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.setdefault('step', '0.01')
                field.widget.attrs.setdefault('min', '0')
            elif isinstance(field.widget, forms.Select) and name != 'estado':
                opciones = list(field.choices)
                if opciones and opciones[0][0] == '':
                    field.choices = [('', 'Selecciona una opción'), *opciones[1:]]


class HerramientaForm(forms.ModelForm):
    foto = forms.ImageField(
        required=False,
        validators=[validar_foto_consumible],
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*'}),
    )

    class Meta:
        model = Herramienta
        exclude = ('fecha_registro',)
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'consumable-input')
            if isinstance(field.widget, forms.FileInput):
                field.widget.attrs['class'] = 'consumable-file'
            elif isinstance(field.widget, forms.NumberInput):
                field.widget.attrs.setdefault('step', '0.01')
                field.widget.attrs.setdefault('min', '0')


class PrestamoHerramientaForm(forms.Form):
    sku = forms.CharField(
        label='SKU identificador',
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'consumable-input',
            'autocomplete': 'off',
            'placeholder': 'Ingresa el SKU de la herramienta',
        }),
    )
    fecha_prestamo = forms.DateField(
        label='Fecha de préstamo',
        widget=forms.DateInput(attrs={'class': 'consumable-input', 'type': 'date'}),
    )
    nombre_solicitante = forms.CharField(
        label='Nombre de quien pidió prestada',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'consumable-input'}),
    )
    fecha_devolucion = forms.DateField(
        label='Fecha de devolución',
        widget=forms.DateInput(attrs={'class': 'consumable-input', 'type': 'date'}),
    )
    nombre_responsable = forms.CharField(
        label='Nombre del responsable',
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'consumable-input'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        sku = cleaned_data.get('sku')
        if sku:
            try:
                cleaned_data['herramienta'] = Herramienta.objects.get(codigo_interno=sku)
            except Herramienta.DoesNotExist:
                self.sku_no_encontrado = True
                self.add_error(
                    'sku',
                    'La herramienta solicitada no existe o no está registrada en la base de datos.',
                )
        return cleaned_data


class TrabajadorForm(forms.ModelForm):
    foto = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
    )
    foto_cedula = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
    )
    tiene_rif = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    en_proceso_contratacion = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    trabajador_activo = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )
    en_proceso_egreso = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = Trabajador
        fields = (
            'nombres',
            'foto',
            'cedula_identidad',
            'foto_cedula',
            'tiene_rif',
            'rif',
            'fecha_nacimiento',
            'nacionalidad',
            'estado_civil',
            'direccion',
            'estado',
            'ciudad',
            'municipio',
            'parroquia',
            'calle',
            'numero',
            'punto_referencia',
            'telefono',
            'telefono_alternativo',
            'correo_personal',
            'correo_empresarial',
            'contacto_emergencia_nombre',
            'contacto_emergencia_apellido',
            'contacto_emergencia_telefono',
            'contacto_emergencia_parentesco',
            'contacto_emergencia_fecha_verificacion',
            'en_proceso_contratacion',
            'trabajador_activo',
            'ausencia_desde',
            'ausencia_hasta',
            'en_proceso_egreso',
            'fecha_egreso',
            'codigo_trabajador',
            'fecha_oferta_seleccion',
            'fecha_ingreso',
            'tipo_contrato',
            'fecha_fin_contrato',
            'area_trabajo',
            'departamento',
            'seccion',
            'cargo',
            'funciones',
            'responsabilidades',
            'nombre_supervisor_directo',
            'jornada_horario_trabajo',
            'turno',
            'salario_contratacion',
            'beneficios',
            'prestaciones',
            'deducciones',
            'responsable_contratacion_nombre',
            'responsable_contratacion_firma',
            'historial_ascensos',
            'historial_cambios_cargo',
            'historial_traslados',
            'historial_cambios_horario',
            'historial_cambio_turno',
            'historial_modificacion_salarial',
            'historial_cambio_supervisor',
            'historial_cambio_jornada',
        )
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ana María López'}),
            'cedula_identidad': forms.TextInput(attrs={'class': 'form-control'}),
            'rif': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nacionalidad': forms.TextInput(attrs={'class': 'form-control'}),
            'estado_civil': forms.Select(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'municipio': forms.TextInput(attrs={'class': 'form-control'}),
            'parroquia': forms.TextInput(attrs={'class': 'form-control'}),
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'punto_referencia': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono_alternativo': forms.TextInput(attrs={'class': 'form-control'}),
            'correo_personal': forms.EmailInput(attrs={'class': 'form-control'}),
            'correo_empresarial': forms.EmailInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_parentesco': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_fecha_verificacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ausencia_desde': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'ausencia_hasta': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_egreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'codigo_trabajador': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_oferta_seleccion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_ingreso': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'tipo_contrato': forms.Select(attrs={'class': 'form-control'}, choices=[('indeterminado', 'Indeterminado'), ('determinado', 'Determinado')]),
            'fecha_fin_contrato': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'area_trabajo': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.TextInput(attrs={'class': 'form-control'}),
            'seccion': forms.TextInput(attrs={'class': 'form-control'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'funciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsabilidades': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nombre_supervisor_directo': forms.TextInput(attrs={'class': 'form-control'}),
            'jornada_horario_trabajo': forms.TextInput(attrs={'class': 'form-control'}),
            'turno': forms.TextInput(attrs={'class': 'form-control'}),
            'salario_contratacion': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'beneficios': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prestaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'deducciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'responsable_contratacion_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'responsable_contratacion_firma': forms.TextInput(attrs={'class': 'form-control'}),
            'historial_ascensos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'historial_cambios_cargo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'historial_traslados': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'historial_cambios_horario': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'historial_cambio_turno': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'historial_modificacion_salarial': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'historial_cambio_supervisor': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'historial_cambio_jornada': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        telefono = cleaned_data.get('telefono')
        telefono_alternativo = cleaned_data.get('telefono_alternativo')

        if telefono and telefono_alternativo and telefono.strip() == telefono_alternativo.strip():
            self.add_error(
                'telefono_alternativo',
                'El teléfono alternativo debe ser diferente al principal.',
            )

        return cleaned_data
