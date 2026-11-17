from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Sum
from .models import Rola
from .forms import RolaForm


def _form_sections(form):
    return [
        ('Información de ingreso', [
            form['fecha'], form['numero_guia'], form['metros_estereos'],
            form['metros_cubicos_rola'], form['cantidad_rolas_estimacion'],
        ]),
        ('Madera', [
            form['tipo_madera_especie'], form['otra_especie'], form['tipo_madera'],
        ]),
        ('Empresas', [form['empresa_vendedora'], form['empresa_comercializadora']]),
        ('Transporte', [
            form['nombre_chofer'], form['color_carro'], form['placa_carro'],
        ]),
        ('Verificación interna', [
            form['nombre_supervisor'], form['largo_camion'], form['ancho_camion'],
            form['altura_camion'], form['cantidad_cargas'],
            form['metros_estereos_verificacion'], form['cantidad_rolas_verificacion'],
            form['clasificacion_visual'], form['metros_cubicos_verificacion'],
        ]),
    ]


@login_required(login_url='login')
def rolas_list(request):
    """Vista para listar todas las rolas registradas"""
    
    # Búsqueda y filtrado
    query = request.GET.get('q', '')
    tipo_madera_filter = request.GET.get('tipo_madera', '')
    
    rolas = Rola.objects.filter(activo=True)
    
    if query:
        rolas = rolas.filter(
            Q(numero_guia__icontains=query) |
            Q(empresa_vendedora__icontains=query) |
            Q(nombre_chofer__icontains=query) |
            Q(tipo_madera_especie__icontains=query)
        )
    
    if tipo_madera_filter:
        rolas = rolas.filter(tipo_madera=tipo_madera_filter)
    
    # Estadísticas
    total_rolas = rolas.count()
    total_estereos = rolas.aggregate(Sum('metros_estereos'))['metros_estereos__sum'] or 0
    total_cubicos = rolas.aggregate(Sum('metros_cubicos_rola'))['metros_cubicos_rola__sum'] or 0
    
    context = {
        'rolas': rolas,
        'total_rolas': total_rolas,
        'total_estereos': total_estereos,
        'total_cubicos': total_cubicos,
        'query': query,
        'tipo_madera_filter': tipo_madera_filter,
        'tipo_madera_choices': Rola.TIPO_MADERA_CHOICES,
    }
    
    return render(request, 'modules/rolas_list.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def rola_crear(request):
    """Vista para crear una nueva rola"""
    
    if request.method == 'POST':
        form = RolaForm(request.POST)
        if form.is_valid():
            rola = form.save()
            messages.success(request, f'Rola {rola.numero_guia} registrada exitosamente.')
            return redirect('rolas_list')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RolaForm()
    
    context = {
        'form': form,
        'form_sections': _form_sections(form),
        'titulo': 'Registrar Nueva Rola',
    }
    
    return render(request, 'modules/rola_form.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def rola_detalle(request, pk):
    """Vista para ver el detalle de una rola"""
    
    rola = get_object_or_404(Rola, pk=pk, activo=True)
    
    context = {
        'rola': rola,
    }
    
    return render(request, 'modules/rola_detalle.html', context)


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def rola_editar(request, pk):
    """Vista para editar una rola"""
    
    rola = get_object_or_404(Rola, pk=pk, activo=True)
    
    if request.method == 'POST':
        form = RolaForm(request.POST, instance=rola)
        if form.is_valid():
            rola = form.save()
            messages.success(request, f'Rola {rola.numero_guia} actualizada exitosamente.')
            return redirect('rola_detalle', pk=rola.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RolaForm(instance=rola)
    
    context = {
        'form': form,
        'form_sections': _form_sections(form),
        'rola': rola,
        'titulo': f'Editar Rola {rola.numero_guia}',
    }
    
    return render(request, 'modules/rola_form.html', context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def rola_eliminar(request, pk):
    """Vista para eliminar una rola"""
    
    rola = get_object_or_404(Rola, pk=pk, activo=True)
    numero_guia = rola.numero_guia
    
    # Eliminación lógica (marcar como inactiva)
    rola.activo = False
    rola.save()
    
    messages.success(request, f'Rola {numero_guia} eliminada exitosamente.')
    
    return redirect('rolas_list')
