from django.contrib import admin
from .models import PaqueteAserrio


@admin.register(PaqueteAserrio)
class PaqueteAserrioAdmin(admin.ModelAdmin):
	list_display = ('codigo_paquete', 'fecha', 'consecutivo_diario', 'turno', 'especie_madera', 'volumen_total_formateado')
	list_filter = ('fecha', 'turno', 'especie_madera', 'tipo_elemento', 'calidad_visual')
	search_fields = ('codigo_paquete', 'nombre_supervisor', 'nombre_operador')

	@admin.display(description='Volumen total (m³)', ordering='volumen_total')
	def volumen_total_formateado(self, paquete):
		return f'{paquete.volumen_total:.3f}'
