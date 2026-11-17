import json

from django import forms
from django.core.exceptions import ValidationError

from aserrio.models import PaqueteAserrio
from secado.models import SecadoPaquete
from .models import ReprocesoPaquete, ReprocesoRegistro


MAQUINAS_CHOICES = [
    ('tronzadora', 'Tronzadora'),
    ('cepilladora', 'Cepilladora'),
    ('regruesadora', 'Regruesadora'),
    ('trompo', 'Trompo'),
    ('lijadora_banda', 'Lijadora de banda'),
    ('moldurera', 'Moldurera'),
    ('sierra_circular', 'Sierra circular'),
]


class ReprocesoRegistroForm(forms.Form):
    fecha = forms.DateField(
        label='Fecha',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    nombre_supervisor = forms.CharField(
        label='Nombre del supervisor',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'name',
        }),
    )
    paquete_origen_id = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    maquinas_proceso = forms.MultipleChoiceField(
        choices=MAQUINAS_CHOICES,
        label='Máquinas utilizadas',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-select'}),
    )
    productos_json = forms.CharField(widget=forms.HiddenInput)

    def clean_paquete_origen_id(self):
        paquete_id = self.cleaned_data['paquete_origen_id']
        if not PaqueteAserrio.objects.filter(pk=paquete_id).exists():
            raise ValidationError('No existe un paquete con ese ID.')

        if ReprocesoRegistro.objects.filter(paquete_origen_id=paquete_id).exists():
            raise ValidationError('Este paquete ya fue usado en un reproceso.')

        if not SecadoPaquete.objects.filter(
            paquete_id=paquete_id,
            registro__fecha_fin__isnull=False,
        ).exists():
            raise ValidationError('El paquete todavía no ha pasado por el proceso de secado.')
        return paquete_id

    def clean_productos_json(self):
        try:
            items = json.loads(self.cleaned_data['productos_json'])
        except json.JSONDecodeError as error:
            raise ValidationError('La lista de productos no es válida.') from error

        if not isinstance(items, list) or not items:
            raise ValidationError('Agregue al menos un producto de reproceso.')

        dimension_field = forms.DecimalField(max_digits=10, decimal_places=3, min_value=0.001)
        quantity_field = forms.IntegerField(min_value=1, max_value=2147483647)
        product_types = dict(ReprocesoPaquete.PRODUCTO_CHOICES)
        qualities = dict(PaqueteAserrio.CALIDAD_CHOICES)
        cleaned_items = []

        for item in items:
            if not isinstance(item, dict):
                raise ValidationError('La lista de productos contiene datos no válidos.')

            tipo_producto = item.get('tipo_producto')
            calidad_visual = item.get('calidad_visual')
            if tipo_producto not in product_types or calidad_visual not in qualities:
                raise ValidationError('Seleccione un tipo de producto y una calidad visual válidos.')

            try:
                dimensions = {
                    field: dimension_field.clean(item.get(field))
                    for field in ('largo', 'ancho', 'espesor')
                }
                cantidad_piezas = quantity_field.clean(item.get('cantidad_piezas'))
            except ValidationError as error:
                raise ValidationError(
                    'Las dimensiones deben ser mayores que cero y la cantidad debe estar entre 1 y 2147483647 piezas.'
                ) from error

            cleaned_items.append({
                **dimensions,
                'tipo_producto': tipo_producto,
                'cantidad_piezas': cantidad_piezas,
                'calidad_visual': calidad_visual,
            })

        return cleaned_items

    def clean(self):
        cleaned_data = super().clean()
        paquete_id = cleaned_data.get('paquete_origen_id')
        fecha = cleaned_data.get('fecha')
        productos = cleaned_data.get('productos_json')
        if not paquete_id:
            return cleaned_data

        paquete_origen = PaqueteAserrio.objects.get(pk=paquete_id)
        if fecha and fecha < paquete_origen.fecha:
            self.add_error(
                'paquete_origen_id',
                (
                    f'El paquete {paquete_origen.codigo_paquete} fue creado el '
                    f'{paquete_origen.fecha:%d/%m/%Y}; no se puede reprocesar '
                    f'antes de esa fecha.'
                ),
            )
        else:
            secado = (
                SecadoPaquete.objects
                .filter(paquete_id=paquete_id, registro__fecha_fin__isnull=False)
                .select_related('registro')
                .order_by('-registro__fecha_fin')
                .first()
            )
            if fecha and secado and fecha < secado.registro.fecha_fin:
                self.add_error(
                    'paquete_origen_id',
                    (
                        f'El paquete {paquete_origen.codigo_paquete} terminó el '
                        f'secado el {secado.registro.fecha_fin:%d/%m/%Y}; no se '
                        f'puede reprocesar antes de esa fecha.'
                    ),
                )

        if productos is None:
            return cleaned_data
        cantidad_generada = sum(producto['cantidad_piezas'] for producto in productos)
        if cantidad_generada != paquete_origen.cantidad_piezas:
            self.add_error(
                'productos_json',
                (
                    f'La suma de piezas de los paquetes resultantes debe ser '
                    f'{paquete_origen.cantidad_piezas}. Actualmente suma {cantidad_generada}.'
                ),
            )
        return cleaned_data


class ReprocesoPaqueteForm(forms.ModelForm):
    class Meta:
        model = ReprocesoPaquete
        fields = [
            'tipo_producto',
            'largo',
            'ancho',
            'espesor',
            'cantidad_piezas',
            'calidad_visual',
        ]
        widgets = {
            'tipo_producto': forms.Select(attrs={'class': 'form-control'}),
            'largo': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.001', 'step': '0.001'}),
            'ancho': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.001', 'step': '0.001'}),
            'espesor': forms.NumberInput(attrs={'class': 'form-control', 'min': '0.001', 'step': '0.001'}),
            'cantidad_piezas': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'step': '1'}),
            'calidad_visual': forms.Select(attrs={'class': 'form-control'}),
        }
