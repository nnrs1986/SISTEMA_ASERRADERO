import json

from django import forms
from django.core.exceptions import ValidationError

from aserrio.models import PaqueteAserrio


class SecadoRegistroForm(forms.Form):
    fecha_inicio = forms.DateField(
        label='Fecha inicial',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    fecha_fin = forms.DateField(
        label='Fecha final del proceso',
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
    )
    turno = forms.ChoiceField(
        label='Turno de secado',
        choices=PaqueteAserrio.TURNO_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    nombre_supervisor = forms.CharField(
        label='Nombre del supervisor',
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'name',
        }),
    )
    paquetes_json = forms.CharField(widget=forms.HiddenInput)

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            self.add_error(
                'fecha_fin',
                'La fecha final no puede ser anterior a la fecha inicial.',
            )
        if fecha_inicio:
            for item in cleaned_data.get('paquetes_json', []):
                paquete = item['paquete']
                if fecha_inicio < paquete.fecha:
                    self.add_error(
                        'paquetes_json',
                        (
                            f'El paquete {paquete.codigo_paquete} fue creado el '
                            f'{paquete.fecha:%d/%m/%Y} y no existía en la fecha '
                            f'indicada para el secado.'
                        ),
                    )
        return cleaned_data

    def clean_paquetes_json(self):
        raw_items = self.cleaned_data['paquetes_json']
        try:
            items = json.loads(raw_items)
        except json.JSONDecodeError as error:
            raise ValidationError('La lista de paquetes no es válida.') from error

        if not isinstance(items, list) or not items:
            raise ValidationError('Agregue al menos un paquete de aserrío.')

        package_ids = []
        cleaned_items = []
        moisture_field = forms.DecimalField(
            required=False,
            max_digits=6,
            decimal_places=2,
            min_value=0,
        )
        for item in items:
            if not isinstance(item, dict):
                raise ValidationError('La lista de paquetes contiene datos no válidos.')
            raw_package_id = item.get('id')
            if isinstance(raw_package_id, bool) or not (
                isinstance(raw_package_id, int)
                or (
                    isinstance(raw_package_id, str)
                    and raw_package_id.isdigit()
                )
            ):
                raise ValidationError('Uno de los paquetes no es válido.')
            try:
                package_id = int(raw_package_id)
            except (TypeError, ValueError) as error:
                raise ValidationError('Uno de los paquetes no es válido.') from error
            if package_id < 1 or package_id in package_ids:
                raise ValidationError('Los paquetes deben ser válidos y no repetirse.')

            try:
                ch_final = moisture_field.clean(item.get('ch_final', ''))
            except ValidationError as error:
                raise ValidationError(
                    'El CH final debe ser un número mayor o igual a cero y tener hasta dos decimales.'
                ) from error

            package_ids.append(package_id)
            cleaned_items.append({'id': package_id, 'ch_final': ch_final})

        packages = PaqueteAserrio.objects.in_bulk(package_ids)
        if len(packages) != len(package_ids):
            raise ValidationError('Uno o más códigos ya no existen en el registro de aserrío.')

        return [
            {'paquete': packages[item['id']], 'ch_final': item['ch_final']}
            for item in cleaned_items
        ]
