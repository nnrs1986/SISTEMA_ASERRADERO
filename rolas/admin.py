from django.contrib import admin
from .models import Rola


@admin.register(Rola)
class RolaAdmin(admin.ModelAdmin):
    """Admin personalizado para el modelo Rola"""
    
    list_display = (
        'numero_guia',
        'fecha',
        'empresa_vendedora',
        'tipo_madera_especie',
        'tipo_madera',
        'metros_estereos',
        'metros_cubicos_rola',
        'nombre_chofer',
        'activo',
    )
    
    list_filter = (
        'fecha',
        'tipo_madera',
        'activo',
        'empresa_vendedora',
    )
    
    search_fields = (
        'numero_guia',
        'empresa_vendedora',
        'nombre_chofer',
        'tipo_madera_especie',
        'nombre_supervisor',
        'placa_carro',
    )
    
    readonly_fields = (
        'fecha_registro',
        'fecha_actualizado',
        'volumen_total',
    )
    
    fieldsets = (
        ('Información General', {
            'fields': ('fecha', 'numero_guia', 'empresa_vendedora')
        }),
        ('Medidas', {
            'fields': ('metros_estereos', 'metros_cubicos_rola', 'volumen_total')
        }),
        ('Tipo de Madera', {
            'fields': ('tipo_madera_especie', 'tipo_madera')
        }),
        ('Transporte', {
            'fields': ('placa_carro', 'nombre_chofer')
        }),
        ('Medición Interna', {
            'fields': ('nombre_supervisor', 'largo_camion', 'ancho_camion', 'altura_camion')
        }),
        ('Control', {
            'fields': ('activo', 'fecha_registro', 'fecha_actualizado'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-fecha_registro',)
    
    def get_queryset(self, request):
        """Mostrar todas las rolas (incluyendo las inactivas) en admin"""
        return super().get_queryset(request)
