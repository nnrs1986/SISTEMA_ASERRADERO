from django.contrib.staticfiles import finders

from .condiciones import LogoEmpresa, NombreEmpresa, NumeroRif, SloganEmpresa
from .models import ConfiguracionEmpresa, PerfilUsuario


PALETAS_COLORES = {
    'fondo': {
        'claro': '#f5f5f5',
        'azulado': '#eef4f9',
        'calido': '#f7f2e9',
        'marron': '#dcc4ac',
        'salvia': '#eef2ed',
        'petroleo': '#edf2f2',
    },
    'sidebar': {
        'verde': ('#3b3535', '#17f14d'),
        'azul': ('#17365d', '#2878b8'),
        'vino': ('#4a1f35', '#9c3d5b'),
        'marron': ('#594236', '#8b6b52'),
        'salvia': ('#34483f', '#6b8a75'),
        'petroleo': ('#164e5a', '#2a7883'),
    },
    'modulos': {
        'azul': ('#667eea', '#764ba2'),
        'verde': ('#16794b', '#45a36d'),
        'grafito': ('#344054', '#667085'),
        'marron': ('#8b5e3c', '#c08a5a'),
        'salvia': ('#5d7867', '#8fa98d'),
        'petroleo': ('#28717a', '#4f9a9b'),
    },
}


def dashboard_context(request):
    empresa, _ = ConfiguracionEmpresa.objects.get_or_create(
        pk=1,
        defaults={
            'nombre': NombreEmpresa,
            'rif': NumeroRif,
            'logo_path': LogoEmpresa,
            'slogan': SloganEmpresa,
        },
    )
    cargo_usuario = ''
    is_admin = False
    if request.user.is_authenticated:
        is_admin = request.user.is_staff or request.user.is_superuser
        perfil, _ = PerfilUsuario.objects.get_or_create(
            usuario=request.user,
            defaults={'cargo': 'Gerente' if is_admin else 'Empleado'},
        )
        cargo_usuario = perfil.cargo

    sidebar_inicio, sidebar_fin = PALETAS_COLORES['sidebar'].get(
        empresa.color_sidebar,
        PALETAS_COLORES['sidebar']['verde'],
    )
    modulo_inicio, modulo_fin = PALETAS_COLORES['modulos'].get(
        empresa.color_modulos,
        PALETAS_COLORES['modulos']['azul'],
    )

    return {
        'empresa': empresa,
        'logo_empresa_disponible': bool(empresa.logo_path and finders.find(empresa.logo_path)),
        'cargo_usuario': cargo_usuario,
        'is_admin': is_admin,
        'tema_colores': {
            'fondo': PALETAS_COLORES['fondo'].get(empresa.color_fondo, '#f5f5f5'),
            'sidebar_inicio': sidebar_inicio,
            'sidebar_fin': sidebar_fin,
            'modulo_inicio': modulo_inicio,
            'modulo_fin': modulo_fin,
        },
    }
