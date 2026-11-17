from django import forms

from .models import PaqueteAserrio


class PaqueteAserrioForm(forms.ModelForm):
    maquinas_proceso = forms.MultipleChoiceField(
        choices=PaqueteAserrio.MAQUINAS_CHOICES,
        label='Máquinas en el proceso',
        help_text='Seleccione exactamente una de las tres primeras opciones. También puede agregar otras máquinas.',
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'checkbox-select'}),
    )
    incluye_recuperacion = forms.TypedChoiceField(
        choices=((True, 'Sí'), (False, 'No')),
        coerce=lambda value: value == 'True',
        label='¿Incluye recuperación de madera?',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
    )
    m3_pieza = forms.CharField(
        label='m³ por pieza',
        required=False,
        disabled=True,
        initial='0',
        widget=forms.TextInput(attrs={'class': 'form-control calculated-field', 'data-calculation': 'piece'}),
    )
    volumen_total = forms.CharField(
        label='Volumen total (m³)',
        required=False,
        disabled=True,
        initial='0',
        widget=forms.TextInput(attrs={'class': 'form-control calculated-field', 'data-calculation': 'total'}),
    )

    class Meta:
        model = PaqueteAserrio
        fields = [
            'fecha', 'turno', 'nombre_supervisor', 'nombre_operador',
            'especie_madera', 'tipo_rola', 'maquinas_proceso',
            'incluye_recuperacion', 'maquina_recuperacion', 'largo', 'ancho',
            'espesor', 'cantidad_piezas', 'ch_estimado', 'tipo_elemento',
            'calidad_visual',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'turno': forms.Select(attrs={'class': 'form-control'}),
            'nombre_supervisor': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'name'}),
            'nombre_operador': forms.TextInput(attrs={'class': 'form-control', 'autocomplete': 'name'}),
            'especie_madera': forms.Select(attrs={'class': 'form-control'}),
            'tipo_rola': forms.Select(attrs={'class': 'form-control'}),
            'maquina_recuperacion': forms.Select(attrs={'class': 'form-control'}),
            'largo': forms.NumberInput(attrs={'class': 'form-control dimension-input', 'min': '0.001', 'step': '0.001', 'placeholder': '0'}),
            'ancho': forms.NumberInput(attrs={'class': 'form-control dimension-input', 'min': '0.001', 'step': '0.001', 'placeholder': '0'}),
            'espesor': forms.NumberInput(attrs={'class': 'form-control dimension-input', 'min': '0.001', 'step': '0.001', 'placeholder': '0'}),
            'cantidad_piezas': forms.NumberInput(attrs={'class': 'form-control dimension-input', 'min': '1', 'step': '1', 'placeholder': '0'}),
            'ch_estimado': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '1', 'placeholder': '0'}),
            'tipo_elemento': forms.Select(attrs={'class': 'form-control'}),
            'calidad_visual': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial.setdefault('incluye_recuperacion', False)
        self.fields['maquina_recuperacion'].required = False
        self.fields['maquina_recuperacion'].choices = [
            ('', 'Seleccione una máquina'),
            *PaqueteAserrio.RECUPERACION_CHOICES,
        ]

    def clean_maquinas_proceso(self):
        maquinas = self.cleaned_data['maquinas_proceso']
        exclusivas = PaqueteAserrio.MAQUINAS_EXCLUSIVAS.intersection(maquinas)
        if len(exclusivas) != 1:
            raise forms.ValidationError('Seleccione exactamente una entre sierra principal, sierra doble y sierra de disco.')
        return maquinas

    def clean(self):
        cleaned_data = super().clean()
        incluye_recuperacion = cleaned_data.get('incluye_recuperacion')
        maquina_recuperacion = cleaned_data.get('maquina_recuperacion')

        if incluye_recuperacion and not maquina_recuperacion:
            self.add_error('maquina_recuperacion', 'Seleccione la máquina de recuperación.')
        elif incluye_recuperacion is False:
            cleaned_data['maquina_recuperacion'] = ''

        for field_name in ('largo', 'ancho', 'espesor'):
            value = cleaned_data.get(field_name)
            if value is not None and value <= 0:
                self.add_error(field_name, 'La dimensión debe ser mayor que cero.')

        cantidad_piezas = cleaned_data.get('cantidad_piezas')
        if cantidad_piezas is not None and cantidad_piezas < 1:
            self.add_error('cantidad_piezas', 'Debe ingresar al menos una pieza.')

        return cleaned_data