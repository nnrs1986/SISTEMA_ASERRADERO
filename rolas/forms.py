from django import forms
from .models import Rola


class RolaForm(forms.ModelForm):
    """Formulario para registrar nuevas rolas"""

    ESPECIE_CHOICES = [
        ('pino', 'Pino'),
        ('cedro', 'Cedro'),
        ('caoba', 'Caoba'),
        ('mureillo', 'Mureillo'),
        ('pardillo', 'Pardillo'),
        ('saman', 'Samán'),
        ('saqui-saqui', 'Saqui-saqui'),
        ('teca', 'Teca'),
        ('otro', 'Otro'),
    ]
    tipo_madera_especie = forms.ChoiceField(
        choices=[('', 'Seleccione una especie'), *ESPECIE_CHOICES],
        label='Especie',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    otra_especie = forms.CharField(
        required=False,
        label='Especifique la especie',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escriba la especie',
            'disabled': True,
        }),
    )
    
    class Meta:
        model = Rola
        fields = [
            'fecha',
            'numero_guia',
            'metros_estereos',
            'metros_cubicos_rola',
            'tipo_madera_especie',
            'otra_especie',
            'tipo_madera',
            'empresa_vendedora',
            'empresa_comercializadora',
            'cantidad_rolas_estimacion',
            'placa_carro',
            'color_carro',
            'nombre_chofer',
            'nombre_supervisor',
            'largo_camion',
            'ancho_camion',
            'altura_camion',
            'cantidad_cargas',
            'metros_estereos_verificacion',
            'cantidad_rolas_verificacion',
            'clasificacion_visual',
            'metros_cubicos_verificacion',
        ]
        widgets = {
            'fecha': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
            'numero_guia': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: G-001234',
            }),
            'metros_estereos': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'metros_cubicos_rola': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'tipo_madera': forms.Select(attrs={
                'class': 'form-control',
            }),
            'empresa_vendedora': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa',
            }),
            'empresa_comercializadora': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la empresa',
            }),
            'cantidad_rolas_estimacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
            }),
            'placa_carro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: ABC-123',
            }),
            'color_carro': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Color del carro',
            }),
            'nombre_chofer': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del chofer',
            }),
            'nombre_supervisor': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre completo del supervisor',
            }),
            'largo_camion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'ancho_camion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'altura_camion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'cantidad_cargas': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
            }),
            'metros_estereos_verificacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01',
                'readonly': 'readonly',
            }),
            'cantidad_rolas_verificacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1',
            }),
            'clasificacion_visual': forms.Select(attrs={
                'class': 'form-control',
            }),
            'metros_cubicos_verificacion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'min': '0',
                'step': '0.01',
                'readonly': 'readonly',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        especies_guardadas = Rola.objects.values_list('tipo_madera_especie', flat=True).distinct()
        valores_conocidos = {value for value, _label in self.ESPECIE_CHOICES}
        opciones_especies = list(self.ESPECIE_CHOICES)
        for especie in especies_guardadas:
            if especie and especie not in valores_conocidos:
                opciones_especies.insert(-1, (especie, especie.title()))
                valores_conocidos.add(especie)
        self.fields['tipo_madera_especie'].choices = [('', 'Seleccione una especie'), *opciones_especies]

        especie_actual = self.instance.tipo_madera_especie if self.instance.pk else ''
        if especie_actual and especie_actual not in {value for value, _label in self.ESPECIE_CHOICES}:
            self.initial['tipo_madera_especie'] = especie_actual
        elif especie_actual:
            self.initial['tipo_madera_especie'] = especie_actual

        if self.instance.pk and self.instance.tipo_madera not in dict(self.fields['tipo_madera'].choices):
            self.fields['tipo_madera'].choices = [
                *self.fields['tipo_madera'].choices,
                ('mixta', 'Mixta (registro anterior)'),
            ]

        clasificaciones_visuales = dict(Rola.CLASIFICACION_VISUAL_CHOICES)
        clasificacion_actual = self.instance.clasificacion_visual if self.instance.pk else ''
        if clasificacion_actual and clasificacion_actual not in clasificaciones_visuales:
            self.fields['clasificacion_visual'].choices = [
                *self.fields['clasificacion_visual'].choices,
                (clasificacion_actual, f'{clasificacion_actual.title()} (registro anterior)'),
            ]
    
    def clean_numero_guia(self):
        """Validar que el número de guía sea único"""
        numero_guia = self.cleaned_data.get('numero_guia')
        if numero_guia:
            # Si es una edición, excluir el registro actual
            if self.instance.pk:
                if Rola.objects.filter(numero_guia=numero_guia).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError("Este número de guía ya está registrado.")
            else:
                if Rola.objects.filter(numero_guia=numero_guia).exists():
                    raise forms.ValidationError("Este número de guía ya está registrado.")
        return numero_guia

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['metros_estereos_verificacion'], cleaned_data[
            'metros_cubicos_verificacion'
        ] = Rola.calcular_verificacion_interna(
            cleaned_data.get('largo_camion'),
            cleaned_data.get('ancho_camion'),
            cleaned_data.get('altura_camion'),
            cleaned_data.get('cantidad_cargas'),
            cleaned_data.get('tipo_madera'),
        )

        especie = cleaned_data.get('tipo_madera_especie')
        if especie == 'otro':
            otra_especie = cleaned_data.get('otra_especie', '').strip()
            if otra_especie:
                cleaned_data['tipo_madera_especie'] = otra_especie
            else:
                self.add_error('otra_especie', 'Escriba el nombre de la especie.')

        metros_estereos = cleaned_data.get('metros_estereos')
        metros_cubicos = cleaned_data.get('metros_cubicos_rola')
        cantidad_campos = (
            'cantidad_rolas_estimacion',
            'cantidad_cargas',
            'cantidad_rolas_verificacion',
        )
        
        if metros_estereos and metros_estereos < 0:
            self.add_error('metros_estereos', 'Este valor no puede ser negativo.')
        
        if metros_cubicos and metros_cubicos < 0:
            self.add_error('metros_cubicos_rola', 'Este valor no puede ser negativo.')

        for field_name in ('metros_estereos_verificacion', 'metros_cubicos_verificacion'):
            value = cleaned_data.get(field_name)
            if value is not None and value < 0:
                self.add_error(field_name, 'Este valor no puede ser negativo.')

        for field_name in cantidad_campos:
            value = cleaned_data.get(field_name)
            if value is not None and value < 0:
                self.add_error(field_name, 'Este valor no puede ser negativo.')
        
        return cleaned_data
