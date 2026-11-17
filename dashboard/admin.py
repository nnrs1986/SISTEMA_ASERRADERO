from django.contrib import admin

from .models import ConfiguracionEmpresa, PerfilUsuario


@admin.register(ConfiguracionEmpresa)
class ConfiguracionEmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rif')
    fields = ('nombre', 'slogan', 'rif', 'logo_path')


@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cargo')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'cargo')
