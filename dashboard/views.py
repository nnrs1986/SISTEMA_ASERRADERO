import json
import re
from decimal import Decimal, InvalidOperation
from decimal import ROUND_HALF_UP

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Max, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from .condiciones import LogoEmpresa
from .forms import (
    ActivoMaquinaForm,
    ConfiguracionEmpresaForm,
    ConfiguracionNominaForm,
    ConsumibleForm,
    HerramientaForm,
    MantenimientoGeneralForm,
    NominaDetalleForm,
    NominaPeriodoForm,
    OrdenTrabajoForm,
    PersonalizacionSistemaForm,
    PrestamoHerramientaForm,
    TrabajadorForm,
)
from .models import (
    ActivoMaquina,
    ConfiguracionEmpresa,
    ConfiguracionMantenimiento,
    ConfiguracionNomina,
    Consumible,
    Herramienta,
    LineaProduccion,
    NominaDetalle,
    NominaPeriodo,
    OrdenTrabajo,
    PrestamoHerramienta,
    Trabajador,
)
from aserrio.barcodes import code128_svg
from aserrio.forms import PaqueteAserrioForm
from aserrio.models import PaqueteAserrio
from rolas.models import Rola
from secado.forms import SecadoRegistroForm
from secado.models import SecadoPaquete, SecadoRegistro
from reproceso.forms import MAQUINAS_CHOICES, ReprocesoPaqueteForm, ReprocesoRegistroForm
from reproceso.models import ReprocesoPaquete, ReprocesoRegistro


def _codigo_ya_existe_en_sistema(codigo_paquete):
    """Comprueba si ese código ya fue usado por cualquier paquete del sistema."""
    return (
        PaqueteAserrio.objects.filter(codigo_paquete=codigo_paquete).exists()
        or ReprocesoPaquete.objects.filter(codigo_paquete=codigo_paquete).exists()
    )


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Vista para el login de usuarios"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña inválidos')
    
    return render(request, 'login.html')


@login_required(login_url='login')
def dashboard_view(request):
    """Vista principal del dashboard"""
    rolas_activas = Rola.objects.filter(activo=True)
    total_rolas = rolas_activas.count()
    volumen_rolas = rolas_activas.aggregate(
        estereos=Sum('metros_estereos'),
        metros_cubicos=Sum('metros_cubicos_rola'),
    )
    volumen_rolas_total = (
        (volumen_rolas['estereos'] or 0)
        + (volumen_rolas['metros_cubicos'] or 0)
    )
    paquetes_aserrio = PaqueteAserrio.objects.aggregate(
        total=Sum('volumen_total'),
    )['total'] or 0
    total_paquetes = PaqueteAserrio.objects.count()
    modulos = [
        {
            'nombre': 'Rolas',
            'icono': '🪵',
            'descripcion': 'Registro y control de materia prima que ingresa al aserradero.',
            'url': reverse('rolas_list'),
            'estado': 'activo',
            'cantidad': total_rolas,
            'unidad': 'rolas activas',
            'detalle': volumen_rolas_total,
        },
        {
            'nombre': 'Aserrío',
            'icono': '🪚',
            'descripcion': 'Control del proceso de aserrado y paquetes de madera.',
            'url': reverse('aserrio'),
            'estado': 'activo',
            'cantidad': total_paquetes,
            'unidad': 'paquetes registrados',
            'detalle': paquetes_aserrio,
        },
        {
            'nombre': 'Secado',
            'icono': '🌡️',
            'descripcion': 'Consulta y control del proceso de secado de la madera.',
            'url': reverse('secado'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Reproceso',
            'icono': '♻️',
            'descripcion': 'Gestión de materiales de madera que requieren reproceso.',
            'url': reverse('reproceso'),
            'estado': 'activo',
        },
        {
            'nombre': 'Inventario',
            'icono': '📦',
            'descripcion': 'Control de existencias y productos disponibles.',
            'url': reverse('inventario'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Ventas',
            'icono': '💰',
            'descripcion': 'Registro y seguimiento de ventas y pedidos.',
            'url': reverse('ventas'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Despacho',
            'icono': '🚚',
            'descripcion': 'Organización de entregas y logística de salida.',
            'url': reverse('despacho'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Mantenimiento',
            'icono': '🛠️',
            'descripcion': 'Control y seguimiento de actividades de mantenimiento y equipos.',
            'url': reverse('mantenimiento'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Administrativo',
            'icono': '📋',
            'descripcion': 'Acceso a procesos administrativos y reportes generales.',
            'url': reverse('administrativo'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Guías',
            'icono': '📄',
            'descripcion': 'Consulta y gestión de documentación y guías.',
            'url': reverse('guias'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Permisología',
            'icono': '🔐',
            'descripcion': 'Administración de permisos y accesos al sistema.',
            'url': reverse('permisologia'),
            'estado': 'preparacion',
        },
        {
            'nombre': 'Personal',
            'icono': '👥',
            'descripcion': 'Gestión del personal, colaboradores y organización de la planta.',
            'url': reverse('personal'),
            'estado': 'preparacion',
        },
    ]
    context = {
        'user': request.user,
        'is_admin': request.user.is_staff or request.user.is_superuser,
        'modulos': modulos,
        'fecha_actual': timezone.localdate(),
        'estadisticas': [
            {'etiqueta': 'Módulos Incluidos', 'valor': len(modulos), 'icono': '▦'},
            {
                'etiqueta': 'Usuarios Activos',
                'valor': get_user_model().objects.filter(is_active=True).count(),
                'icono': '♙',
            },
            {'etiqueta': 'Carros de Rolas', 'valor': total_rolas, 'icono': '◉'},
            {'etiqueta': 'Paquetes de Aserrío', 'valor': total_paquetes, 'icono': '▤'},
        ],
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='login')
def logout_view(request):
    """Vista para el logout"""
    logout(request)
    return redirect('login')


# Vistas para cada módulo
@login_required(login_url='login')
def rolas_view(request):
    """Redirecciona a la lista de rolas"""
    return redirect('/dashboard/rolas/')


@login_required(login_url='login')
def aserrio_view(request):
    """Muestra los paquetes de aserrío registrados."""
    paquetes = PaqueteAserrio.objects.order_by('-fecha', '-consecutivo_diario')
    page_obj = Paginator(paquetes, 25).get_page(request.GET.get('page'))
    context = {
        'module': 'Aserrio',
        'paquetes': page_obj,
        'total_paquetes': paquetes.count(),
    }
    return render(request, 'modules/aserrio.html', context)


def _aserrio_form_sections(form):
    return [
        ('Información del turno', [
            form['fecha'], form['turno'], form['nombre_supervisor'],
            form['nombre_operador'],
        ]),
        ('Madera y proceso', [
            form['especie_madera'], form['tipo_rola'], form['maquinas_proceso'],
            form['incluye_recuperacion'], form['maquina_recuperacion'],
        ]),
        ('Contenido del paquete', [
            form['largo'], form['ancho'], form['espesor'], form['m3_pieza'],
            form['cantidad_piezas'], form['volumen_total'], form['ch_estimado'],
            form['tipo_elemento'], form['calidad_visual'],
        ]),
    ]


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def aserrio_crear_view(request):
    """Registra un paquete y le asigna un código correlativo por fecha."""
    if request.method == 'POST':
        form = PaqueteAserrioForm(request.POST)
        if form.is_valid():
            paquete = form.save(commit=False)
            for intento in range(3):
                try:
                    with transaction.atomic():
                        ultimo_consecutivo = PaqueteAserrio.objects.filter(
                            fecha=paquete.fecha,
                        ).aggregate(Max('consecutivo_diario'))['consecutivo_diario__max'] or 0
                        paquete.consecutivo_diario = ultimo_consecutivo
                        while True:
                            paquete.consecutivo_diario += 1
                            paquete.codigo_paquete = (
                                f'ASR-{paquete.fecha:%Y%m%d}-{paquete.consecutivo_diario:04d}'
                            )
                            if not _codigo_ya_existe_en_sistema(paquete.codigo_paquete):
                                break
                        paquete.save()
                    messages.success(
                        request,
                        f"Paquete {paquete.codigo_paquete} registrado. Producción del día: {paquete.consecutivo_diario}.",
                    )
                    return redirect('aserrio_paquete', codigo_paquete=paquete.codigo_paquete)
                except IntegrityError:
                    if intento == 2:
                        form.add_error(None, 'No se pudo asignar un código único. Intente guardar nuevamente.')
    else:
        form = PaqueteAserrioForm(initial={'fecha': timezone.localdate()})

    return render(request, 'modules/aserrio_form.html', {
        'form': form,
        'form_sections': _aserrio_form_sections(form),
        'titulo': 'Agregar Aserrío',
        'texto_boton': 'Guardar paquete',
        'cancel_url': reverse('aserrio'),
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def aserrio_editar_view(request, codigo_paquete):
    paquete = get_object_or_404(PaqueteAserrio, codigo_paquete=codigo_paquete)
    if request.method == 'POST':
        form = PaqueteAserrioForm(request.POST, instance=paquete)
        if form.is_valid():
            paquete = form.save(commit=False)
            paquete.fecha_edicion = timezone.now()
            try:
                with transaction.atomic():
                    paquete.save()
            except IntegrityError:
                form.add_error(
                    None,
                    'No se pudo guardar el paquete porque la producción de esa fecha ya tiene ese consecutivo.',
                )
            else:
                messages.success(request, f'Paquete {paquete.codigo_paquete} actualizado correctamente.')
                return redirect('aserrio_paquete', codigo_paquete=paquete.codigo_paquete)
    else:
        form = PaqueteAserrioForm(instance=paquete)

    return render(request, 'modules/aserrio_form.html', {
        'form': form,
        'form_sections': _aserrio_form_sections(form),
        'titulo': f'Editar paquete {paquete.codigo_paquete}',
        'texto_boton': 'Guardar cambios',
        'cancel_url': reverse('aserrio_paquete', kwargs={'codigo_paquete': paquete.codigo_paquete}),
    })


@login_required(login_url='login')
def aserrio_buscar_paquete_view(request):
    """Busca un paquete por el código ingresado por el lector de barras."""
    codigo_paquete = request.GET.get('codigo_paquete', '').strip().upper()
    if codigo_paquete and PaqueteAserrio.objects.filter(codigo_paquete=codigo_paquete).exists():
        return redirect('aserrio_paquete', codigo_paquete=codigo_paquete)

    messages.error(request, 'No se encontró un paquete con ese código de barras.')
    return redirect('aserrio')


@login_required(login_url='login')
def aserrio_paquete_view(request, codigo_paquete):
    paquete = get_object_or_404(PaqueteAserrio, codigo_paquete=codigo_paquete)
    etiquetas_maquinas = dict(PaqueteAserrio.MAQUINAS_CHOICES)
    maquinas_proceso = [
        etiquetas_maquinas[codigo]
        for codigo in paquete.maquinas_proceso
        if codigo in etiquetas_maquinas
    ]
    return render(request, 'modules/aserrio_paquete.html', {
        'paquete': paquete,
        'barcode_svg': code128_svg(paquete.codigo_paquete),
        'maquinas_proceso': maquinas_proceso,
    })


@login_required(login_url='login')
def secado_view(request):
    """Muestra el resumen de las cargas de secado registradas."""
    registros = list(
        SecadoRegistro.objects
        .annotate(
            volumen_total=Sum('paquetes__paquete__volumen_total'),
            promedio_final=Avg('paquetes__ch_final'),
        )
        .prefetch_related('paquetes__paquete')
    )
    especies_por_codigo = dict(PaqueteAserrio.ESPECIE_CHOICES)
    for registro in registros:
        codigos_especie = {
            item.paquete.especie_madera
            for item in registro.paquetes.all()
        }
        registro.especies = ', '.join(
            especies_por_codigo[codigo]
            for codigo in sorted(codigos_especie)
        )

    return render(request, 'modules/secado_lista.html', {
        'module': 'Secado',
        'registros': registros,
    })


@login_required(login_url='login')
def secado_detalle_view(request, registro_id):
    """Muestra la información completa de un proceso de secado."""
    registro = get_object_or_404(
        SecadoRegistro.objects.prefetch_related('paquetes__paquete'),
        pk=registro_id,
    )
    resumen = registro.paquetes.aggregate(
        volumen_total=Sum('paquete__volumen_total'),
        promedio_estimado=Avg('paquete__ch_estimado'),
        promedio_final=Avg('ch_final'),
    )
    especies_por_codigo = dict(PaqueteAserrio.ESPECIE_CHOICES)
    paquetes = list(registro.paquetes.all())
    especies = {
        item.paquete.especie_madera
        for item in paquetes
    }
    return render(request, 'modules/secado_detalle.html', {
        'module': 'Secado',
        'registro': registro,
        'paquetes': paquetes,
        'volumen_total': resumen['volumen_total'],
        'promedio_estimado': resumen['promedio_estimado'],
        'promedio_final': resumen['promedio_final'],
        'especies': ', '.join(
            especies_por_codigo[codigo]
            for codigo in sorted(especies)
        ),
    })


@login_required(login_url='login')
def secado_form_view(request, registro_id=None):
    """Crea una carga de secado o actualiza sus datos y paquetes."""
    registro = (
        get_object_or_404(SecadoRegistro, pk=registro_id)
        if registro_id is not None
        else None
    )
    if request.method == 'POST':
        form = SecadoRegistroForm(request.POST)
        if form.is_valid():
            packages = form.cleaned_data['paquetes_json']
            existing_ids = (
                set(registro.paquetes.values_list('paquete_id', flat=True))
                if registro is not None
                else set()
            )
            submitted_ids = {item['paquete'].pk for item in packages}
            dried_package = (
                SecadoPaquete.objects
                .filter(
                    paquete_id__in=submitted_ids - existing_ids,
                    registro__fecha_fin__isnull=False,
                )
                .select_related('paquete')
                .first()
            )
            if dried_package is not None:
                form.add_error(
                    'paquetes_json',
                    f'El paquete {dried_package.paquete.codigo_paquete} ya está seco.',
                )
            elif registro is not None:
                if not existing_ids.issubset(submitted_ids):
                    form.add_error(
                        None,
                        'No se pueden quitar paquetes existentes de un registro de secado.',
                    )
                else:
                    with transaction.atomic():
                        registro.fecha_inicio = form.cleaned_data['fecha_inicio']
                        registro.fecha_fin = form.cleaned_data['fecha_fin']
                        registro.turno = form.cleaned_data['turno']
                        registro.nombre_supervisor = form.cleaned_data['nombre_supervisor']
                        registro.save(update_fields=[
                            'fecha_inicio',
                            'fecha_fin',
                            'turno',
                            'nombre_supervisor',
                        ])
                        rows_by_package = {
                            item.paquete_id: item
                            for item in registro.paquetes.all()
                        }
                        for item in packages:
                            secado_paquete = rows_by_package.get(item['paquete'].pk)
                            if secado_paquete is not None:
                                secado_paquete.ch_final = item['ch_final']
                        SecadoPaquete.objects.bulk_update(
                            [
                                rows_by_package[item['paquete'].pk]
                                for item in packages
                                if item['paquete'].pk in rows_by_package
                            ],
                            ['ch_final'],
                        )
                        SecadoPaquete.objects.bulk_create([
                            SecadoPaquete(
                                registro=registro,
                                paquete=item['paquete'],
                                ch_final=item['ch_final'],
                            )
                            for item in packages
                            if item['paquete'].pk not in rows_by_package
                        ])
                    messages.success(request, 'Registro de secado actualizado correctamente.')
                    return redirect('secado')
            else:
                with transaction.atomic():
                    registro = SecadoRegistro.objects.create(
                        fecha_inicio=form.cleaned_data['fecha_inicio'],
                        fecha_fin=form.cleaned_data['fecha_fin'],
                        turno=form.cleaned_data['turno'],
                        nombre_supervisor=form.cleaned_data['nombre_supervisor'],
                    )
                    SecadoPaquete.objects.bulk_create([
                        SecadoPaquete(
                            registro=registro,
                            paquete=item['paquete'],
                            ch_final=item['ch_final'],
                        )
                        for item in packages
                    ])
                promedio_estimado = registro.paquetes.aggregate(
                    promedio=Avg('paquete__ch_estimado'),
                )['promedio']
                messages.success(
                    request,
                    f'Registro de secado guardado con {registro.paquetes.count()} paquetes. '
                    f'CH estimado promedio: {promedio_estimado:.2f}%.',
                )
                return redirect('secado')
    else:
        if registro is None:
            initial = {
                'fecha_inicio': timezone.localdate(),
                'fecha_fin': None,
                'paquetes_json': '[]',
            }
            submitted_packages = []
        else:
            record_packages = list(registro.paquetes.select_related('paquete'))
            submitted_packages = [
                {
                    'paquete': item.paquete,
                    'ch_final': item.ch_final if item.ch_final is not None else '',
                }
                for item in record_packages
            ]
            initial = {
                'fecha_inicio': registro.fecha_inicio,
                'fecha_fin': registro.fecha_fin,
                'turno': registro.turno,
                'nombre_supervisor': registro.nombre_supervisor,
                'paquetes_json': json.dumps([
                    {
                        'id': item.paquete_id,
                        'ch_final': (
                            str(item.ch_final) if item.ch_final is not None else ''
                        ),
                    }
                    for item in record_packages
                ]),
            }
        form = SecadoRegistroForm(initial=initial)

    if request.method == 'POST':
        submitted_packages = []
        try:
            posted_items = json.loads(request.POST.get('paquetes_json', '[]'))
        except json.JSONDecodeError:
            posted_items = []
        if isinstance(posted_items, list):
            package_ids = [
                int(item['id'])
                for item in posted_items
                if isinstance(item, dict) and str(item.get('id', '')).isdigit()
            ]
            packages = PaqueteAserrio.objects.in_bulk(package_ids)
            for item in posted_items:
                if not isinstance(item, dict):
                    continue
                package_id = item.get('id')
                if isinstance(package_id, int) or (
                    isinstance(package_id, str) and package_id.isdigit()
                ):
                    paquete = packages.get(int(package_id))
                    if paquete is not None:
                        submitted_packages.append({
                            'paquete': paquete,
                            'ch_final': item.get('ch_final', ''),
                        })

    context = {
        'module': 'Secado',
        'form': form,
        'paquetes_iniciales': submitted_packages,
        'busqueda_url': reverse('secado_buscar_paquete'),
        'is_edit': registro_id is not None,
    }
    return render(request, 'modules/secado.html', context)


@login_required(login_url='login')
@require_http_methods(["GET"])
def secado_buscar_paquete_view(request):
    """Devuelve los datos de un paquete para incorporarlo al formulario de secado."""
    codigo_paquete = request.GET.get('codigo_paquete', '').strip().upper()
    if not codigo_paquete:
        return JsonResponse({'error': 'Ingrese el código del paquete.'}, status=400)
    fecha_inicio = parse_date(request.GET.get('fecha_inicio', ''))
    if fecha_inicio is None:
        return JsonResponse({'error': 'Seleccione una fecha inicial válida para el secado.'}, status=400)

    try:
        paquete = PaqueteAserrio.objects.get(codigo_paquete=codigo_paquete)
    except PaqueteAserrio.DoesNotExist:
        return JsonResponse(
            {'error': f'No existe un paquete de aserrío con el código {codigo_paquete}.'},
            status=404,
        )

    if fecha_inicio < paquete.fecha:
        return JsonResponse(
            {
                'error': (
                    f'El paquete {paquete.codigo_paquete} fue creado el '
                    f'{paquete.fecha:%d/%m/%Y} y no existía en la fecha indicada '
                    f'para el secado.'
                ),
            },
            status=409,
        )

    if SecadoPaquete.objects.filter(
        paquete=paquete,
        registro__fecha_fin__isnull=False,
    ).exists():
        return JsonResponse(
            {'error': f'El paquete {paquete.codigo_paquete} ya está seco.'},
            status=409,
        )

    return JsonResponse({
        'id': paquete.pk,
        'codigo': paquete.codigo_paquete,
        'largo': str(paquete.largo),
        'ancho': str(paquete.ancho),
        'espesor': str(paquete.espesor),
        'cantidad_piezas': paquete.cantidad_piezas,
        'volumen_total': f'{paquete.volumen_total:.3f}',
        'ch_estimado': paquete.ch_estimado,
    })


@login_required(login_url='login')
def reproceso_view(request):
    """Muestra los procesos de reproceso y sus paquetes generados."""
    registros = ReprocesoRegistro.objects.select_related(
        'paquete_origen',
    ).prefetch_related('paquetes_generados')
    etiquetas_maquinas = dict(MAQUINAS_CHOICES)
    for registro in registros:
        registro.maquinas_display = ', '.join(
            etiquetas_maquinas[codigo]
            for codigo in registro.maquinas_proceso
            if codigo in etiquetas_maquinas
        )
    return render(request, 'modules/reproceso.html', {
        'module': 'Reproceso',
        'registros': registros,
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def reproceso_crear_view(request):
    """Registra el reproceso de un paquete seco y genera sus códigos de salida."""
    paquete_inicial = None
    if request.method == 'POST':
        form = ReprocesoRegistroForm(request.POST)
        if form.is_valid():
            paquete_origen = get_object_or_404(
                PaqueteAserrio,
                pk=form.cleaned_data['paquete_origen_id'],
            )
            for intento in range(3):
                try:
                    with transaction.atomic():
                        registro = ReprocesoRegistro.objects.create(
                            fecha=form.cleaned_data['fecha'],
                            nombre_supervisor=form.cleaned_data['nombre_supervisor'],
                            paquete_origen=paquete_origen,
                            maquinas_proceso=form.cleaned_data['maquinas_proceso'],
                        )
                        for producto in form.cleaned_data['productos_json']:
                            ultimo_consecutivo = ReprocesoPaquete.objects.filter(
                                fecha=registro.fecha,
                            ).aggregate(Max('consecutivo_diario'))['consecutivo_diario__max'] or 0
                            consecutivo = ultimo_consecutivo
                            while True:
                                consecutivo += 1
                                codigo_paquete = f'RPR-{registro.fecha:%Y%m%d}-{consecutivo:04d}'
                                if not _codigo_ya_existe_en_sistema(codigo_paquete):
                                    break
                            ReprocesoPaquete.objects.create(
                                registro=registro,
                                fecha=registro.fecha,
                                consecutivo_diario=consecutivo,
                                codigo_paquete=codigo_paquete,
                                **producto,
                            )
                    codigos = ', '.join(
                        registro.paquetes_generados.values_list('codigo_paquete', flat=True)
                    )
                    messages.success(
                        request,
                        f'Reproceso guardado. Paquetes generados: {codigos}.',
                    )
                    return redirect('reproceso')
                except IntegrityError:
                    if intento == 2:
                        form.add_error(
                            None,
                            'No se pudo asignar un código único a los paquetes. Intente guardar nuevamente.',
                        )
        paquete_id = form.cleaned_data.get('paquete_origen_id')
        if paquete_id and SecadoPaquete.objects.filter(
            paquete_id=paquete_id,
            registro__fecha_fin__isnull=False,
        ).exists():
            paquete_inicial = PaqueteAserrio.objects.get(pk=paquete_id)
    else:
        form = ReprocesoRegistroForm(initial={
            'fecha': timezone.localdate(),
            'productos_json': '[]',
        })

    return render(request, 'modules/reproceso_form.html', {
        'module': 'Reproceso',
        'form': form,
        'busqueda_url': reverse('reproceso_buscar_paquete'),
        'paquete_inicial': (
            {
                'id': paquete_inicial.pk,
                'codigo': paquete_inicial.codigo_paquete,
                'largo': f'{paquete_inicial.largo:.3f}',
                'ancho': f'{paquete_inicial.ancho:.3f}',
                'espesor': f'{paquete_inicial.espesor:.3f}',
                'dimensiones': (
                    f'{paquete_inicial.largo:.3f} × {paquete_inicial.ancho:.3f} '
                    f'× {paquete_inicial.espesor:.3f} m'
                ),
                'cantidad_piezas': paquete_inicial.cantidad_piezas,
                'volumen_total': f'{paquete_inicial.volumen_total:.3f}',
            }
            if paquete_inicial else None
        ),
        'producto_choices': ReprocesoPaquete.PRODUCTO_CHOICES,
        'calidad_choices': PaqueteAserrio.CALIDAD_CHOICES,
    })


@login_required(login_url='login')
@require_http_methods(['GET'])
def reproceso_paquete_detalle_view(request, paquete_id):
    """Muestra la información detallada de un paquete generado en reproceso."""
    paquete = get_object_or_404(
        ReprocesoPaquete.objects.select_related('registro__paquete_origen'),
        pk=paquete_id,
    )
    return render(request, 'modules/reproceso_paquete_detalle.html', {
        'module': 'Reproceso',
        'paquete': paquete,
        'registro': paquete.registro,
        'barcode_svg': code128_svg(paquete.codigo_paquete),
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def reproceso_paquete_editar_view(request, paquete_id):
    """Edita un paquete de salida y conserva las piezas totales del paquete origen."""
    paquete = get_object_or_404(
        ReprocesoPaquete.objects.select_related('registro__paquete_origen'),
        pk=paquete_id,
    )
    registro = paquete.registro

    if request.method == 'POST':
        form = ReprocesoPaqueteForm(request.POST, instance=paquete)
        if form.is_valid():
            paquete_actualizado = form.save(commit=False)
            with transaction.atomic():
                registro = ReprocesoRegistro.objects.select_for_update().get(pk=registro.pk)
                paquetes_hermanos = list(
                    registro.paquetes_generados.exclude(pk=paquete.pk).order_by('-consecutivo_diario')
                )
                cantidad_origen = registro.paquete_origen.cantidad_piezas
                cantidad_otros = sum(item.cantidad_piezas for item in paquetes_hermanos[1:])
                cantidad_balance = cantidad_origen - cantidad_otros - paquete_actualizado.cantidad_piezas

                if cantidad_balance < 0:
                    form.add_error(
                        'cantidad_piezas',
                        'La cantidad excede las piezas disponibles del paquete de origen.',
                    )
                elif paquetes_hermanos and cantidad_balance < 1:
                    form.add_error(
                        'cantidad_piezas',
                        'Debe quedar al menos una pieza en el paquete hermano que se ajustará.',
                    )
                elif not paquetes_hermanos and cantidad_balance != 0:
                    form.add_error(
                        'cantidad_piezas',
                        f'Este proceso tiene un solo paquete; debe conservar las {cantidad_origen} piezas.',
                    )
                else:
                    paquete_actualizado.save()
                    if paquetes_hermanos:
                        paquete_balance = paquetes_hermanos[0]
                        paquete_balance.cantidad_piezas = cantidad_balance
                        paquete_balance.save(update_fields=['cantidad_piezas', 'm3_pieza', 'volumen_total'])
            if not form.errors:
                messages.success(
                    request,
                    'Paquete actualizado. Se conservó la totalidad de piezas del paquete de origen.',
                )
                return redirect('reproceso')
    else:
        form = ReprocesoPaqueteForm(instance=paquete)
    paquete_balance = (
        registro.paquetes_generados.exclude(pk=paquete.pk).order_by('-consecutivo_diario').first()
    )

    return render(request, 'modules/reproceso_paquete_editar.html', {
        'module': 'Reproceso',
        'paquete': paquete,
        'registro': registro,
        'form': form,
        'paquete_balance': paquete_balance,
    })


@login_required(login_url='login')
@require_http_methods(['GET'])
def reproceso_buscar_paquete_view(request):
    """Devuelve los datos de un paquete cuyo proceso de secado ya finalizó."""
    codigo_paquete = request.GET.get('codigo_paquete', '').strip().upper()
    if not codigo_paquete:
        return JsonResponse({'error': 'Ingrese el código del paquete.'}, status=400)
    fecha_reproceso = parse_date(request.GET.get('fecha', ''))
    if fecha_reproceso is None:
        return JsonResponse({'error': 'Seleccione una fecha válida para el reproceso.'}, status=400)

    try:
        paquete = PaqueteAserrio.objects.get(codigo_paquete=codigo_paquete)
    except PaqueteAserrio.DoesNotExist:
        return JsonResponse(
            {'error': f'No existe un paquete de aserrío con el código {codigo_paquete}.'},
            status=404,
        )

    if fecha_reproceso < paquete.fecha:
        return JsonResponse(
            {
                'error': (
                    f'El paquete {paquete.codigo_paquete} fue creado el '
                    f'{paquete.fecha:%d/%m/%Y}; no se puede reprocesar antes de '
                    f'esa fecha.'
                ),
            },
            status=409,
        )

    if ReprocesoRegistro.objects.filter(paquete_origen=paquete).exists():
        return JsonResponse(
            {'error': f'El paquete {paquete.codigo_paquete} ya fue usado en un reproceso.'},
            status=409,
        )

    if not SecadoPaquete.objects.filter(
        paquete=paquete,
        registro__fecha_fin__isnull=False,
    ).exists():
        return JsonResponse(
            {'error': 'El paquete todavía no ha pasado por el proceso de secado.'},
            status=400,
        )

    secado = (
        SecadoPaquete.objects
        .filter(paquete=paquete, registro__fecha_fin__isnull=False)
        .select_related('registro')
        .order_by('-registro__fecha_fin')
        .first()
    )
    if fecha_reproceso < secado.registro.fecha_fin:
        return JsonResponse(
            {
                'error': (
                    f'El paquete {paquete.codigo_paquete} terminó el secado el '
                    f'{secado.registro.fecha_fin:%d/%m/%Y}; no se puede '
                    f'reprocesar antes de esa fecha.'
                ),
            },
            status=409,
        )

    return JsonResponse({
        'id': paquete.pk,
        'codigo': paquete.codigo_paquete,
        'largo': f'{paquete.largo:.3f}',
        'ancho': f'{paquete.ancho:.3f}',
        'espesor': f'{paquete.espesor:.3f}',
        'cantidad_piezas': paquete.cantidad_piezas,
        'volumen_total': f'{paquete.volumen_total:.3f}',
        'dimensiones': f'{paquete.largo:.3f} × {paquete.ancho:.3f} × {paquete.espesor:.3f} m',
    })


@login_required(login_url='login')
def inventario_view(request):
    """Vista del módulo de Inventario con filtros por estado y departamento."""
    filtro = request.GET.get('filtro', 'todos').lower()
    texto_busqueda = request.GET.get('q', '').strip()

    items = []

    for paquete in PaqueteAserrio.objects.all().order_by('-fecha', '-consecutivo_diario'):
        if ReprocesoRegistro.objects.filter(paquete_origen=paquete).exists():
            continue

        tiene_secado = SecadoPaquete.objects.filter(paquete=paquete).exists()

        items.append({
            'codigo': paquete.codigo_paquete,
            'fecha': paquete.fecha,
            'largo': paquete.largo,
            'ancho': paquete.ancho,
            'espesor': paquete.espesor,
            'volumen': paquete.volumen_total,
            'departamento': 'Secado' if tiene_secado else 'Aserrío',
            'estado': 'secado' if tiene_secado else 'aserrio',
            'paso_secado': tiene_secado,
            'vendido': False,
        })

    for paquete in ReprocesoPaquete.objects.select_related('registro__paquete_origen').order_by('-fecha', '-consecutivo_diario'):
        origen_secado = False
        if paquete.registro and paquete.registro.paquete_origen:
            origen_secado = SecadoPaquete.objects.filter(
                paquete=paquete.registro.paquete_origen,
            ).exists()

        items.append({
            'codigo': paquete.codigo_paquete,
            'fecha': paquete.fecha,
            'largo': paquete.largo,
            'ancho': paquete.ancho,
            'espesor': paquete.espesor,
            'volumen': paquete.volumen_total,
            'departamento': 'Reproceso',
            'estado': 'reproceso',
            'paso_secado': origen_secado,
            'vendido': False,
        })

    items.sort(key=lambda item: item['fecha'], reverse=True)

    filtro_map = {
        'todos': lambda item: True,
        'aserrio': lambda item: item['estado'] == 'aserrio',
        'secado': lambda item: item['paso_secado'] or item['estado'] == 'secado',
        'reproceso': lambda item: item['departamento'] == 'Reproceso',
        'vendidos': lambda item: item['vendido'],
    }

    if filtro not in filtro_map:
        filtro = 'todos'

    elementos_filtrados = [
        item for item in items
        if filtro_map[filtro](item)
    ]

    if texto_busqueda:
        texto_busqueda = texto_busqueda.lower()
        elementos_filtrados = [
            item for item in elementos_filtrados
            if (
                texto_busqueda in item['codigo'].lower()
                or texto_busqueda in item['departamento'].lower()
                or texto_busqueda in item['estado'].lower()
            )
        ]

    total_por_estado = {
        'todos': len(items),
        'aserrio': sum(1 for item in items if item['estado'] == 'aserrio'),
        'secado': sum(1 for item in items if item['paso_secado'] or item['estado'] == 'secado'),
        'reproceso': sum(1 for item in items if item['departamento'] == 'Reproceso'),
        'vendidos': sum(1 for item in items if item['vendido']),
    }
    m3_total = sum(item['volumen'] for item in elementos_filtrados if not item['vendido'])

    context = {
        'module': 'Inventario',
        'items': elementos_filtrados,
        'filtro': filtro,
        'texto_busqueda': texto_busqueda,
        'totales': total_por_estado,
        'total_stock': sum(1 for item in items if not item['vendido']),
        'm3_total': m3_total,
    }
    return render(request, 'modules/inventario.html', context)


@login_required(login_url='login')
def ventas_view(request):
    """Vista del módulo de Ventas"""
    context = {'module': 'Ventas'}
    return render(request, 'modules/ventas.html', context)


@login_required(login_url='login')
def despacho_view(request):
    """Vista del módulo de Despacho"""
    context = {'module': 'Despacho'}
    return render(request, 'modules/despacho.html', context)


@login_required(login_url='login')
def mantenimiento_view(request):
    """Vista base del módulo de Mantenimiento."""
    context = {'module': 'Mantenimiento'}
    return render(request, 'modules/mantenimiento.html', context)


@login_required(login_url='login')
def mantenimiento_indicadores_view(request):
    """Muestra indicadores disponibles para las órdenes y los activos."""
    hoy = timezone.localdate()
    ordenes_pendientes = OrdenTrabajo.objects.filter(tiempos_ejecucion='')
    duracion_horas = Decimal('0')
    duraciones_con_horas = 0
    formato_horas = re.compile(r'\s*(\d+(?:[.,]\d+)?)\s*(?:h|horas?)\s*', re.IGNORECASE)

    for duracion in ordenes_pendientes.values_list('duracion_estimada', flat=True):
        coincidencia = formato_horas.fullmatch(duracion or '')
        if coincidencia:
            try:
                duracion_horas += Decimal(coincidencia.group(1).replace(',', '.'))
                duraciones_con_horas += 1
            except InvalidOperation:
                continue

    ordenes_por_tipo = OrdenTrabajo.objects.aggregate(
        preventivo=Count('pk', filter=Q(tipo_orden='preventivo')),
        correctivo=Count('pk', filter=Q(tipo_orden='correctivo')),
    )
    total_ordenes = OrdenTrabajo.objects.count()
    otros_tipos = total_ordenes - ordenes_por_tipo['preventivo'] - ordenes_por_tipo['correctivo']
    if total_ordenes:
        grados_preventivo = round(ordenes_por_tipo['preventivo'] * 360 / total_ordenes)
        grados_correctivo = round(ordenes_por_tipo['correctivo'] * 360 / total_ordenes)
        grados_otros = 360 - grados_preventivo - grados_correctivo
    else:
        grados_preventivo = grados_correctivo = grados_otros = 0

    return render(request, 'modules/mantenimiento_indicadores.html', {
        'fecha_actualizacion': hoy,
        'ordenes_pendientes': ordenes_pendientes.count(),
        'horas_pendientes_estimadas': duracion_horas,
        'duraciones_con_horas': duraciones_con_horas,
        'ordenes_por_tipo': ordenes_por_tipo,
        'otros_tipos': otros_tipos,
        'total_ordenes': total_ordenes,
        'grados_preventivo': grados_preventivo,
        'grados_correctivo': grados_correctivo,
        'grados_otros': grados_otros,
    })


@login_required(login_url='login')
def mantenimiento_financiero_view(request):
    """Presenta la vista financiera y las métricas que requieren datos de costos."""
    return render(request, 'modules/mantenimiento_financiero.html', {
        'fecha_actualizacion': timezone.localdate(),
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def mantenimiento_ordenes_trabajo_view(request):
    if request.method == 'POST':
        form = OrdenTrabajoForm(request.POST)
        if form.is_valid():
            orden = form.save()
            messages.success(request, f'La orden OT-{orden.numero_orden:05d} se registró correctamente.')
            return redirect('mantenimiento_ordenes_trabajo')
    else:
        form = OrdenTrabajoForm()

    ordenes = Paginator(OrdenTrabajo.objects.all(), 20).get_page(request.GET.get('page'))
    return render(request, 'modules/mantenimiento_ordenes_trabajo.html', {
        'module': 'Mantenimiento',
        'form': form,
        'ordenes': ordenes,
    })


def _secciones_herramienta_form(form):
    secciones_campos = [
        {
            'titulo': 'Identificación de la herramienta',
            'icono': '🏷️',
            'nombres': (
                'codigo_interno', 'nombre', 'descripcion', 'categoria', 'subcategoria',
                'marca', 'modelo', 'numero_serie', 'foto', 'codigo_barras',
            ),
        },
        {
            'titulo': 'Identificación técnica',
            'icono': '⚙️',
            'nombres': (
                'tipo_herramienta', 'material', 'potencia', 'voltaje', 'frecuencia',
                'peso', 'dimensiones', 'capacidad_trabajo', 'capacidad_especifica',
                'area_trabajo',
            ),
        },
        {
            'titulo': 'Información de la adquisición',
            'icono': '🧾',
            'nombres': (
                'tipo_adquisicion', 'fecha_adquisicion', 'proveedor', 'fabricante',
                'numero_factura', 'orden_factura', 'precio_adquisicion', 'moneda',
                'tiempo_garantia', 'fecha_vencimiento_garantia', 'vida_util_estimada',
            ),
        },
        {
            'titulo': 'Ubicación física',
            'icono': '📍',
            'nombres': (
                'empresa', 'planta', 'edificio', 'departamento', 'area', 'sector',
                'almacen', 'estanteria', 'ubicacion_especifica',
            ),
        },
        {
            'titulo': 'Asignación y responsabilidad',
            'icono': '👷',
            'nombres': (
                'tipo_asignacion', 'trabajador_responsable', 'departamento_responsable',
                'area_cargo', 'fecha_entrega', 'responsable_entrega',
                'fecha_prevista_devolucion', 'condicion_entrega',
            ),
        },
        {
            'titulo': 'Estado y disponibilidad',
            'icono': '✅',
            'nombres': (
                'estado_operativo', 'condicion_fisica', 'disponibilidad',
                'estado_conservacion', 'fecha_ultima_evaluacion',
                'responsable_evaluacion', 'observaciones',
            ),
        },
    ]
    return [
        {
            'titulo': seccion['titulo'],
            'icono': seccion['icono'],
            'campos': [form[nombre] for nombre in seccion['nombres']],
        }
        for seccion in secciones_campos
    ]


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def mantenimiento_herramientas_view(request):
    if request.method == 'POST':
        form = HerramientaForm(request.POST, request.FILES)
        if form.is_valid():
            herramienta = form.save()
            messages.success(
                request,
                f'La herramienta {herramienta.codigo_interno} se registró correctamente.',
            )
            return redirect('mantenimiento_herramientas')
    else:
        form = HerramientaForm()

    return render(request, 'modules/mantenimiento_herramientas.html', {
        'form': form,
        'secciones': _secciones_herramienta_form(form),
        'herramientas': Herramienta.objects.order_by('-fecha_registro', 'nombre'),
        'mostrar_formulario': request.method == 'POST' or request.GET.get('registrar') == '1',
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def mantenimiento_prestamos_herramientas_view(request):
    if request.method == 'POST':
        form = PrestamoHerramientaForm(request.POST)
        if form.is_valid():
            PrestamoHerramienta.objects.create(
                herramienta=form.cleaned_data['herramienta'],
                fecha_prestamo=form.cleaned_data['fecha_prestamo'],
                nombre_solicitante=form.cleaned_data['nombre_solicitante'],
                fecha_devolucion=form.cleaned_data['fecha_devolucion'],
                nombre_responsable=form.cleaned_data['nombre_responsable'],
            )
            messages.success(request, 'El préstamo de herramienta se registró correctamente.')
            return redirect('mantenimiento_prestamos_herramientas')
    else:
        form = PrestamoHerramientaForm()

    return render(request, 'modules/mantenimiento_prestamos_herramientas.html', {
        'form': form,
        'prestamos': PrestamoHerramienta.objects.select_related('herramienta'),
        'sku_no_encontrado': getattr(form, 'sku_no_encontrado', False),
    })


@login_required(login_url='login')
@require_http_methods(['GET'])
def mantenimiento_planilla_prestamo_herramientas_view(request):
    return render(request, 'modules/planilla_prestamo_herramientas.html')


def _secciones_consumible_form(form):
    secciones_campos = [
        {
            'titulo': 'Identificación del consumible',
            'icono': '🏷️',
            'nombres': (
                'codigo_interno', 'nombre', 'categoria', 'descripcion', 'subcategoria',
                'marca', 'fabricante', 'modelo', 'codigo_fabricante', 'codigo_barras',
                'foto_frente', 'foto_lado', 'foto_perfil',
            ),
        },
        {
            'titulo': 'Características técnicas',
            'icono': '⚙️',
            'nombres': (
                'material', 'diametro', 'espesor', 'numero_dientes', 'compatibilidad',
                'vida_util_estimada', 'aplicacion', 'ficha_tecnica',
            ),
        },
        {
            'titulo': 'Información comercial',
            'icono': '🧾',
            'nombres': (
                'proveedor_habitual', 'precio_compra', 'ultimo_precio_compra', 'moneda',
                'fecha_ultima_entrega', 'tiempo_entrega', 'cantidad_minima_compra',
            ),
        },
        {
            'titulo': 'Información de almacenamiento',
            'icono': '📦',
            'nombres': (
                'unidad_medida', 'presentacion', 'cantidad_por_presentacion',
                'stock_disponible', 'ubicacion',
                'stock_minimo', 'stock_maximo', 'stock_seguridad',
                'requiere_condiciones_especiales', 'condiciones_almacenamiento',
            ),
        },
        {
            'titulo': 'Control del consumo',
            'icono': '🏭',
            'nombres': (
                'departamento_consumo', 'maquina_asociada', 'proceso_productivo',
                'consumo_promedio_mensual', 'frecuencia_reposicion', 'responsable_consumo',
                'criticidad_consumo',
            ),
        },
        {
            'titulo': 'Clasificación administrativa',
            'icono': '📊',
            'nombres': (
                'estado', 'tipo_consumible', 'criticidad_administrativa',
                'centro_costo_asociado', 'cuenta_contable_asociada',
            ),
        },
    ]
    return [
        {
            'titulo': seccion['titulo'],
            'icono': seccion['icono'],
            'campos': [form[nombre] for nombre in seccion['nombres']],
        }
        for seccion in secciones_campos
    ]


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def mantenimiento_consumibles_view(request):
    if request.method == 'POST':
        form = ConsumibleForm(request.POST, request.FILES)
        if form.is_valid():
            consumible = form.save()
            messages.success(
                request,
                f'El consumible {consumible.codigo_interno} se guardó correctamente.',
            )
            return redirect('mantenimiento_consumibles')
    else:
        form = ConsumibleForm()

    secciones = _secciones_consumible_form(form)
    consumibles = Consumible.objects.order_by('-fecha_registro', 'nombre')
    return render(request, 'modules/mantenimiento_consumibles.html', {
        'module': 'Mantenimiento',
        'form': form,
        'secciones': secciones,
        'consumibles': consumibles,
        'form_id': 'nuevo-consumible',
        'form_title': 'Registrar un consumible',
        'form_description': 'Los campos marcados con * son obligatorios.',
        'submit_text': 'Guardar consumible',
        'editing': False,
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def mantenimiento_consumible_editar_view(request, consumible_id):
    consumible = get_object_or_404(Consumible, pk=consumible_id)
    if request.method == 'POST':
        form = ConsumibleForm(request.POST, request.FILES, instance=consumible)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'El consumible {consumible.codigo_interno} se actualizó correctamente.',
            )
            return redirect('mantenimiento_consumible_detalle', consumible_id=consumible.pk)
    else:
        form = ConsumibleForm(instance=consumible)

    return render(request, 'modules/mantenimiento_consumibles.html', {
        'module': 'Mantenimiento',
        'form': form,
        'secciones': _secciones_consumible_form(form),
        'consumible': consumible,
        'form_id': 'editar-consumible',
        'form_title': f'Editar consumible: {consumible.nombre}',
        'form_description': 'Actualiza los datos que necesites. Los campos marcados con * son obligatorios.',
        'submit_text': 'Actualizar consumible',
        'editing': True,
    })


@login_required(login_url='login')
@require_http_methods(['POST'])
def mantenimiento_consumible_eliminar_view(request, consumible_id):
    consumible = get_object_or_404(Consumible, pk=consumible_id)
    codigo_interno = consumible.codigo_interno
    consumible.delete()
    messages.success(request, f'El consumible {codigo_interno} se eliminó correctamente.')
    return redirect('mantenimiento_consumibles')


@login_required(login_url='login')
def mantenimiento_consumible_detalle_view(request, consumible_id):
    consumible = get_object_or_404(Consumible, pk=consumible_id)
    secciones_campos = [
        {
            'titulo': 'Identificación del consumible',
            'campos': (
                'codigo_interno', 'nombre', 'categoria', 'descripcion', 'subcategoria',
                'marca', 'fabricante', 'modelo', 'codigo_fabricante', 'codigo_barras',
            ),
        },
        {
            'titulo': 'Características técnicas',
            'campos': (
                'material', 'diametro', 'espesor', 'numero_dientes', 'compatibilidad',
                'vida_util_estimada', 'aplicacion',
            ),
        },
        {
            'titulo': 'Información comercial',
            'campos': (
                'proveedor_habitual', 'precio_compra', 'ultimo_precio_compra', 'moneda',
                'fecha_ultima_entrega', 'tiempo_entrega', 'cantidad_minima_compra',
            ),
        },
        {
            'titulo': 'Información de almacenamiento',
            'campos': (
                'unidad_medida', 'presentacion', 'cantidad_por_presentacion',
                'stock_disponible', 'ubicacion', 'stock_minimo', 'stock_maximo',
                'stock_seguridad', 'requiere_condiciones_especiales',
                'condiciones_almacenamiento',
            ),
        },
        {
            'titulo': 'Control del consumo',
            'campos': (
                'departamento_consumo', 'maquina_asociada', 'proceso_productivo',
                'consumo_promedio_mensual', 'frecuencia_reposicion', 'responsable_consumo',
                'criticidad_consumo',
            ),
        },
        {
            'titulo': 'Clasificación administrativa',
            'campos': (
                'estado', 'tipo_consumible', 'criticidad_administrativa',
                'centro_costo_asociado', 'cuenta_contable_asociada',
            ),
        },
    ]
    secciones = []
    for seccion in secciones_campos:
        campos = []
        for nombre in seccion['campos']:
            campo = Consumible._meta.get_field(nombre)
            valor = getattr(consumible, nombre)
            if nombre == 'requiere_condiciones_especiales':
                valor = 'Sí' if valor is True else 'No' if valor is False else ''
            elif campo.choices:
                valor = getattr(consumible, f'get_{nombre}_display')() if valor else ''
            elif nombre == 'fecha_ultima_entrega' and valor:
                valor = valor.strftime('%d/%m/%Y')
            campos.append({
                'label': campo.verbose_name,
                'valor': valor if valor not in (None, '') else '—',
            })
        secciones.append({'titulo': seccion['titulo'], 'campos': campos})

    fotos = [
        {'label': 'Frente', 'archivo': consumible.foto_frente},
        {'label': 'Lado', 'archivo': consumible.foto_lado},
        {'label': 'Perfil', 'archivo': consumible.foto_perfil},
    ]
    return render(request, 'modules/mantenimiento_consumible_detalle.html', {
        'module': 'Mantenimiento',
        'consumible': consumible,
        'secciones': secciones,
        'fotos': [foto for foto in fotos if foto['archivo']],
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def mantenimiento_activos_view(request):
    configuracion = ConfiguracionMantenimiento.objects.first()
    if configuracion is None:
        messages.info(request, 'Primero completa la información general y la organización de producción.')
        return redirect('mantenimiento_general')

    formulario_activo = None
    maquina_solicitada = None
    linea_solicitada = None
    if request.method == 'POST':
        linea_solicitada = request.POST.get('linea_descripcion', '')
        maquina_solicitada = request.POST.get('maquina', '')
        maquina_configurada = any(
            linea.descripcion == linea_solicitada and maquina == maquina_solicitada
            for linea in configuracion.lineas_produccion.all()
            for maquina in linea.maquinas
        )
        if not maquina_configurada:
            messages.error(request, 'La máquina seleccionada ya no pertenece a la organización de producción.')
            return redirect('mantenimiento_activos')

        formulario_activo = ActivoMaquinaForm(request.POST)
        if formulario_activo.is_valid():
            activo = ActivoMaquina.objects.filter(
                configuracion=configuracion,
                linea_descripcion=linea_solicitada,
                maquina=maquina_solicitada,
            ).first()
            if activo is None:
                ActivoMaquina.objects.create(
                    configuracion=configuracion,
                    linea_descripcion=linea_solicitada,
                    maquina=maquina_solicitada,
                    especificaciones=formulario_activo.cleaned_data['especificaciones'],
                    elementos=formulario_activo.cleaned_data['elementos'],
                )
                messages.success(request, f'La ficha de {maquina_solicitada} se guardó correctamente.')
            else:
                activo.especificaciones = formulario_activo.cleaned_data['especificaciones']
                activo.elementos = formulario_activo.cleaned_data['elementos']
                activo.save(update_fields=['especificaciones', 'elementos'])
                messages.success(request, f'La ficha de {maquina_solicitada} se actualizó correctamente.')
            return redirect('mantenimiento_activos')

    maquinas_activos = []
    for linea in configuracion.lineas_produccion.all():
        for maquina in linea.maquinas:
            activo = ActivoMaquina.objects.filter(
                configuracion=configuracion,
                linea_descripcion=linea.descripcion,
                maquina=maquina,
            ).first()
            especificaciones = activo.especificaciones if activo else []
            elementos = activo.elementos if activo else []
            es_formulario_solicitado = (
                formulario_activo is not None
                and linea.descripcion == linea_solicitada
                and maquina == maquina_solicitada
            )
            form = formulario_activo if es_formulario_solicitado else ActivoMaquinaForm(
                initial={
                    'especificaciones': json.dumps(especificaciones, ensure_ascii=False),
                    'elementos': json.dumps(elementos, ensure_ascii=False),
                }
            )
            maquinas_activos.append({
                'linea': linea.descripcion,
                'maquina': maquina,
                'especificaciones': especificaciones,
                'elementos': elementos,
                'form': form,
                'editor_abierto': es_formulario_solicitado,
            })

    return render(request, 'modules/mantenimiento_activos.html', {
        'module': 'Mantenimiento',
        'configuracion': configuracion,
        'maquinas_activos': maquinas_activos,
    })


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def mantenimiento_general_view(request):
    configuracion = ConfiguracionMantenimiento.objects.first()
    if configuracion is None:
        configuracion = ConfiguracionMantenimiento()
    lineas = (
        list(configuracion.lineas_produccion.values('descripcion', 'maquinas'))
        if configuracion.pk else []
    )
    editando = (
        request.method == 'POST'
        or configuracion.pk is None
        or request.GET.get('editar') == '1'
    )

    if request.method == 'POST':
        form = MantenimientoGeneralForm(request.POST, instance=configuracion)
        if form.is_valid():
            with transaction.atomic():
                configuracion = form.save()
                configuracion.lineas_produccion.all().delete()
                LineaProduccion.objects.bulk_create([
                    LineaProduccion(
                        configuracion=configuracion,
                        descripcion=linea['descripcion'],
                        maquinas=linea['maquinas'],
                        orden=orden,
                    )
                    for orden, linea in enumerate(form.cleaned_data['lineas'], start=1)
                ])
                maquinas_configuradas = {
                    (linea['descripcion'], maquina)
                    for linea in form.cleaned_data['lineas']
                    for maquina in linea['maquinas']
                }
                activos_obsoletos = [
                    activo_id
                    for activo_id, descripcion, maquina in (
                        configuracion.activos_maquina.values_list(
                            'pk',
                            'linea_descripcion',
                            'maquina',
                        )
                    )
                    if (descripcion, maquina) not in maquinas_configuradas
                ]
                if activos_obsoletos:
                    configuracion.activos_maquina.filter(pk__in=activos_obsoletos).delete()
            messages.success(request, 'La información general del aserradero se guardó correctamente.')
            return redirect('mantenimiento_general')
    else:
        form = MantenimientoGeneralForm(
            instance=configuracion,
            initial={'lineas': json.dumps(lineas)},
        )

    return render(request, 'modules/mantenimiento_general.html', {
        'module': 'Mantenimiento',
        'form': form,
        'configuracion': configuracion,
        'editando': editando,
        'lineas_configuracion': lineas,
        'lineas_iniciales': (
            request.POST.get('lineas', '[]')
            if form.is_bound else form.initial.get('lineas', '[]')
        ),
        'tag_identificacion': configuracion.tag_identificacion if configuracion.pk else '',
    })


@login_required(login_url='login')
def administrativo_view(request):
    """Vista del módulo de Administrativo"""
    context = {'module': 'Administrativo'}
    return render(request, 'modules/administrativo.html', context)


def _codigo_nomina(fecha_pago):
    prefijo = f'NOM-{fecha_pago:%Y%m%d}-'
    consecutivo = NominaPeriodo.objects.filter(codigo__startswith=prefijo).count() + 1
    codigo = f'{prefijo}{consecutivo:03d}'
    while NominaPeriodo.objects.filter(codigo=codigo).exists():
        consecutivo += 1
        codigo = f'{prefijo}{consecutivo:03d}'
    return codigo


def _calcular_porcentaje(base, porcentaje):
    return (base * porcentaje / Decimal('100')).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP,
    )


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def nomina_dashboard_view(request):
    seccion = request.GET.get('seccion', 'nomina')
    if request.method == 'POST':
        seccion = request.POST.get('seccion', 'nomina')
    if seccion not in {'nomina', 'salario', 'deducciones', 'aportes', 'reportes'}:
        seccion = 'nomina'

    trabajadores = Trabajador.objects.order_by('nombres')
    periodos = NominaPeriodo.objects.all()
    trabajador_id = request.GET.get('trabajador')
    periodo_id = request.GET.get('periodo')
    if request.method == 'POST':
        trabajador_id = request.POST.get('trabajador')
        periodo_id = request.POST.get('periodo') or None

    trabajador = get_object_or_404(trabajadores, pk=trabajador_id) if trabajador_id else None
    periodo = get_object_or_404(periodos, pk=periodo_id) if periodo_id else None
    configuracion, _ = ConfiguracionNomina.objects.get_or_create(pk=1)

    if request.method == 'POST' and seccion == 'salario':
        configuracion_form = ConfiguracionNominaForm(request.POST, instance=configuracion)
        if configuracion_form.is_valid():
            configuracion_form.save()
            messages.success(request, 'La configuración de aportes patronales se guardó correctamente.')
            return redirect(f"{reverse('nomina_dashboard')}?seccion=salario")
    else:
        configuracion_form = ConfiguracionNominaForm(instance=configuracion)

    detalle = None
    hoy = timezone.localdate()
    periodo_form = NominaPeriodoForm(
        instance=periodo,
        initial={
            'periodo_desde': hoy,
            'periodo_hasta': hoy,
            'fecha_pago': hoy,
        },
    )
    if trabajador and periodo:
        detalle = NominaDetalle.objects.filter(periodo=periodo, trabajador=trabajador).first()
    detalle_form = NominaDetalleForm(instance=detalle)

    if request.method == 'POST' and seccion == 'nomina':
        if not trabajador:
            messages.error(request, 'Selecciona un trabajador para registrar la nómina.')
        else:
            periodo_form = NominaPeriodoForm(request.POST, instance=periodo)
            detalle_form = NominaDetalleForm(request.POST, instance=detalle)
            if periodo_form.is_valid() and detalle_form.is_valid():
                with transaction.atomic():
                    periodo_guardado = periodo_form.save(commit=False)
                    if not periodo_guardado.pk:
                        periodo_guardado.codigo = _codigo_nomina(periodo_guardado.fecha_pago)
                    periodo_guardado.save()

                    detalle_guardado = detalle_form.save(commit=False)
                    detalle_guardado.periodo = periodo_guardado
                    detalle_guardado.trabajador = trabajador
                    if not detalle_guardado.pk:
                        detalle_guardado.trabajador_nombre = trabajador.nombres
                        detalle_guardado.cedula_identidad = trabajador.cedula_identidad
                        detalle_guardado.cargo = trabajador.cargo
                        detalle_guardado.area_trabajo = trabajador.area_trabajo
                        detalle_guardado.departamento = trabajador.departamento
                        detalle_guardado.seccion = trabajador.seccion
                        detalle_guardado.tipo_contrato = trabajador.tipo_contrato
                        detalle_guardado.salario_base = trabajador.salario_contratacion or Decimal('0')
                        detalle_guardado.ivss_patronal_porcentaje = configuracion.ivss_patronal_porcentaje
                        detalle_guardado.rpe_patronal_porcentaje = configuracion.rpe_patronal_porcentaje
                        detalle_guardado.faov_patronal_porcentaje = configuracion.faov_patronal_porcentaje
                        detalle_guardado.inces_porcentaje = configuracion.inces_porcentaje
                        detalle_guardado.pensiones_porcentaje = configuracion.pensiones_porcentaje
                    elif not request.POST.get('numero_cuenta', '').strip():
                        detalle_guardado.numero_cuenta = detalle.numero_cuenta

                    salario = detalle_guardado.salario_base
                    detalle_guardado.ivss_deduccion = _calcular_porcentaje(salario, Decimal('4'))
                    detalle_guardado.rpe_deduccion = _calcular_porcentaje(salario, Decimal('0.5'))
                    detalle_guardado.faov_deduccion = _calcular_porcentaje(salario, Decimal('1'))
                    detalle_guardado.ivss_patronal = _calcular_porcentaje(
                        salario, detalle_guardado.ivss_patronal_porcentaje
                    )
                    detalle_guardado.rpe_patronal = _calcular_porcentaje(
                        salario, detalle_guardado.rpe_patronal_porcentaje
                    )
                    detalle_guardado.faov_patronal = _calcular_porcentaje(
                        salario, detalle_guardado.faov_patronal_porcentaje
                    )
                    detalle_guardado.inces = _calcular_porcentaje(
                        salario, detalle_guardado.inces_porcentaje
                    )
                    detalle_guardado.pensiones = _calcular_porcentaje(
                        salario, detalle_guardado.pensiones_porcentaje
                    )
                    detalle_guardado.total_asignaciones = sum(
                        (
                            salario,
                            detalle_guardado.horas_extras,
                            detalle_guardado.bono_produccion,
                            detalle_guardado.bono_nocturno,
                            detalle_guardado.vacaciones,
                        ),
                        Decimal('0'),
                    )
                    detalle_guardado.total_deducciones = sum(
                        (
                            detalle_guardado.ivss_deduccion,
                            detalle_guardado.rpe_deduccion,
                            detalle_guardado.faov_deduccion,
                            detalle_guardado.anticipo_salarial,
                            detalle_guardado.prestamo_personal,
                        ),
                        Decimal('0'),
                    )
                    detalle_guardado.neto_pagar = (
                        detalle_guardado.total_asignaciones
                        - detalle_guardado.total_deducciones
                    )
                    detalle_guardado.total_aportes = sum(
                        (
                            detalle_guardado.ivss_patronal,
                            detalle_guardado.rpe_patronal,
                            detalle_guardado.faov_patronal,
                            detalle_guardado.inces,
                            detalle_guardado.pensiones,
                        ),
                        Decimal('0'),
                    )
                    detalle_guardado.save()
                messages.success(
                    request,
                    f'La nómina de {trabajador.nombres} quedó guardada bajo {periodo_guardado.codigo}.',
                )
                return redirect(
                    f"{reverse('nomina_dashboard')}?seccion=nomina"
                    f"&periodo={periodo_guardado.pk}&trabajador={trabajador.pk}"
                )

    context = {
        'module': 'Nómina y RRHH',
        'seccion': seccion,
        'configuracion': configuracion,
        'trabajadores': trabajadores,
        'trabajador_seleccionado': trabajador,
        'periodos': periodos,
        'periodo_seleccionado': periodo,
        'detalle': detalle,
        'periodo_form': periodo_form,
        'detalle_form': detalle_form,
        'configuracion_form': configuracion_form,
    }
    return render(request, 'modules/nomina_dashboard.html', context)


@login_required(login_url='login')
def guias_view(request):
    """Vista del módulo de Guías"""
    context = {'module': 'Guías'}
    return render(request, 'modules/guias.html', context)


@login_required(login_url='login')
def permisologia_view(request):
    """Muestra el módulo de Permisología, pendiente de contenido."""
    return render(request, 'modules/permisologia.html', {'module': 'Permisología'})


@login_required(login_url='login')
def personal_view(request):
    """Vista base del módulo de Personal con listado de trabajadores."""
    trabajadores = Trabajador.objects.order_by('nombres')
    total_colaboradores = trabajadores.count()
    context = {
        'module': 'Personal',
        'resumen': {
            'total_colaboradores': total_colaboradores,
            'activos': trabajadores.filter(trabajador_activo=True).count(),
            'ausentes': trabajadores.filter(trabajador_activo=False).count(),
            'cumpleanos': 0,
        },
        'quick_actions': [
            {
                'titulo': 'Registrar empleado',
                'descripcion': 'Agregar nuevo personal al sistema.',
                'icono': '➕',
                'url': reverse('personal_registrar'),
            },
            {'titulo': 'Control de asistencia', 'descripcion': 'Seguimiento de ingreso y salida.', 'icono': '🕒'},
            {'titulo': 'Asignaciones', 'descripcion': 'Organizar tareas y turnos por área.', 'icono': '🧭'},
        ],
        'trabajadores': trabajadores,
    }
    return render(request, 'modules/personal.html', context)


@login_required(login_url='login')
def personal_registrar_view(request):
    """Formulario para registrar los datos básicos del trabajador."""
    if request.method == 'POST':
        form = TrabajadorForm(request.POST, request.FILES)
        if form.is_valid():
            trabajador = form.save()
            messages.success(request, 'El trabajador fue registrado correctamente.')
            return redirect('personal_editar', trabajador_id=trabajador.pk)
    else:
        form = TrabajadorForm()

    context = {
        'module': 'Personal',
        'form': form,
        'title': 'Registrar empleado',
        'submit_text': 'Guardar trabajador',
    }
    return render(request, 'modules/personal_form.html', context)


@login_required(login_url='login')
def personal_detalle_view(request, trabajador_id):
    """Muestra el detalle completo de un trabajador sin permitir edición."""
    trabajador = get_object_or_404(Trabajador, pk=trabajador_id)
    context = {
        'module': 'Personal',
        'trabajador': trabajador,
        'title': f'Detalle del trabajador: {trabajador.nombres}',
    }
    return render(request, 'modules/personal_detail.html', context)


@login_required(login_url='login')
@require_http_methods(['GET', 'POST'])
def personal_editar_view(request, trabajador_id):
    """Edita la información registrada de un trabajador."""
    trabajador = get_object_or_404(Trabajador, pk=trabajador_id)
    if request.method == 'POST':
        form = TrabajadorForm(request.POST, request.FILES, instance=trabajador)
        if form.is_valid():
            form.save()
            messages.success(request, 'La información del trabajador fue actualizada correctamente.')
            return redirect('personal')
    else:
        form = TrabajadorForm(instance=trabajador)

    context = {
        'module': 'Personal',
        'form': form,
        'title': f'Editar trabajador: {trabajador.nombres}',
        'submit_text': 'Actualizar trabajador',
    }
    return render(request, 'modules/personal_form.html', context)


@login_required(login_url='login')
def configuracion_view(request):
    """Vista de configuración del sistema, visible solo para administradores."""
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('dashboard')

    configuracion, _ = ConfiguracionEmpresa.objects.get_or_create(pk=1)
    if request.method == 'POST':
        if request.POST.get('guardar_apariencia'):
            apariencia_form = PersonalizacionSistemaForm(
                request.POST,
                instance=configuracion,
            )
            form = ConfiguracionEmpresaForm(instance=configuracion)
            if apariencia_form.is_valid():
                apariencia_form.save()
                messages.success(request, 'La apariencia del sistema se guardó correctamente.')
                return redirect('configuracion')
        else:
            form = ConfiguracionEmpresaForm(
                request.POST,
                request.FILES,
                instance=configuracion,
            )
            apariencia_form = PersonalizacionSistemaForm(instance=configuracion)
            if form.is_valid():
                configuracion = form.save(commit=False)
                logo = form.cleaned_data.get('logo')
                if logo:
                    almacenamiento = FileSystemStorage(location=settings.BASE_DIR / 'static')
                    if almacenamiento.exists(LogoEmpresa):
                        almacenamiento.delete(LogoEmpresa)
                    almacenamiento.save(LogoEmpresa, logo)
                    configuracion.logo_path = LogoEmpresa
                configuracion.save()
                messages.success(request, 'La información de la empresa se guardó correctamente.')
                return redirect('configuracion')
    else:
        form = ConfiguracionEmpresaForm(instance=configuracion)
        apariencia_form = PersonalizacionSistemaForm(instance=configuracion)

    context = {
        'module': 'Configuración',
        'form': form,
        'apariencia_form': apariencia_form,
    }
    return render(request, 'modules/configuracion.html', context)
