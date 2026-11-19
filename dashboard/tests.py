import json
import base64
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory
from django.core.files.uploadedfile import SimpleUploadedFile

from .condiciones import LogoEmpresa
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
    PerfilUsuario,
    PrestamoHerramienta,
    Trabajador,
)


class DashboardViewTests(TestCase):
    def test_dashboard_muestra_modulos_y_resumen_dinamico(self):
        usuario = get_user_model().objects.create_user(
            username='operador',
            password='clave-segura',
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['modulos']), 10)
        self.assertEqual(response.context['estadisticas'][1]['valor'], 1)
        self.assertContains(response, 'Wisdom Tech')
        self.assertContains(response, 'Innovando el Futuro, Transformando el Presente')
        self.assertContains(response, 'RIF: J-1783881-6')
        self.assertContains(response, 'Bienvenido, operador')
        self.assertContains(response, 'Módulos del sistema')
        self.assertContains(response, 'En preparación')
        self.assertContains(response, reverse('rolas_list'))
        self.assertContains(response, reverse('aserrio'))
        self.assertEqual(response.content.count(b'<svg viewBox="0 0 24 24">'), 23)
        self.assertContains(response, f'/static/{LogoEmpresa}')

    def test_dashboard_muestra_nombre_eslogan_rif_y_cargo_configurados(self):
        usuario = get_user_model().objects.create_user(
            username='operador',
            first_name='Ana',
            last_name='Pérez',
            password='clave-segura',
        )
        PerfilUsuario.objects.create(usuario=usuario, cargo='Supervisora')
        ConfiguracionEmpresa.objects.filter(pk=1).update(
            nombre='Maderas del Sur',
            slogan='Calidad que perdura',
            rif='J-98765432-1',
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Maderas del Sur')
        self.assertContains(response, 'Calidad que perdura')
        self.assertContains(response, 'RIF: J-98765432-1')
        self.assertContains(response, 'Ana Pérez')
        self.assertContains(response, 'Supervisora')
        self.assertNotContains(response, 'Administrador')

    def test_configuracion_guarda_datos_empresa_en_base_de_datos(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='clave-segura',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('configuracion'),
            {
                'nombre': 'Aserradero El Roble',
                'slogan': 'Madera responsable',
                'rif': 'J-12345678-9',
            },
        )

        self.assertRedirects(response, reverse('configuracion'))
        configuracion = ConfiguracionEmpresa.objects.get(pk=1)
        self.assertEqual(configuracion.nombre, 'Aserradero El Roble')
        self.assertEqual(configuracion.slogan, 'Madera responsable')
        self.assertEqual(configuracion.rif, 'J-12345678-9')

        dashboard = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard, 'Aserradero El Roble')
        self.assertContains(dashboard, 'Madera responsable')
        self.assertContains(dashboard, 'J-12345678-9')

    def test_configuracion_guarda_y_aplica_las_paletas_del_sistema(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='clave-segura',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('configuracion'),
            {
                'color_fondo': 'azulado',
                'color_sidebar': 'azul',
                'color_modulos': 'verde',
                'guardar_apariencia': '1',
            },
        )

        self.assertRedirects(response, reverse('configuracion'))
        configuracion = ConfiguracionEmpresa.objects.get(pk=1)
        self.assertEqual(configuracion.color_fondo, 'azulado')
        self.assertEqual(configuracion.color_sidebar, 'azul')
        self.assertEqual(configuracion.color_modulos, 'verde')

        dashboard = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard, '--dashboard-background: #eef4f9')
        self.assertContains(dashboard, '--sidebar-start: #17365d')
        self.assertContains(dashboard, '--module-start: #16794b')
        modulo = self.client.get(reverse('aserrio'))
        self.assertContains(modulo, 'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)')

    def test_configuracion_guarda_y_aplica_las_nuevas_paletas(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='clave-segura',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('configuracion'),
            {
                'color_fondo': 'marron',
                'color_sidebar': 'salvia',
                'color_modulos': 'petroleo',
                'guardar_apariencia': '1',
            },
        )

        self.assertRedirects(response, reverse('configuracion'))
        configuracion = ConfiguracionEmpresa.objects.get(pk=1)
        self.assertEqual(configuracion.color_fondo, 'marron')
        self.assertEqual(configuracion.color_sidebar, 'salvia')
        self.assertEqual(configuracion.color_modulos, 'petroleo')

        dashboard = self.client.get(reverse('dashboard'))
        self.assertContains(dashboard, '--dashboard-background: #dcc4ac')
        self.assertContains(dashboard, '--sidebar-start: #34483f')
        self.assertContains(dashboard, '--sidebar-end: #6b8a75')
        self.assertContains(dashboard, '--module-start: #28717a')
        self.assertContains(dashboard, '--module-end: #4f9a9b')
        self.assertContains(dashboard, '.welcome-panel')
        self.assertContains(
            dashboard,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )

        secado = self.client.get(reverse('secado'))
        self.assertEqual(secado.status_code, 200)
        self.assertContains(secado, '.overview-header')
        self.assertContains(
            secado,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )

        reproceso = self.client.get(reverse('reproceso'))
        self.assertEqual(reproceso.status_code, 200)
        self.assertContains(reproceso, '.reprocess-header')
        self.assertContains(
            reproceso,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )

        rolas = self.client.get(reverse('rolas_list'))
        self.assertEqual(rolas.status_code, 200)
        self.assertContains(
            rolas,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )

        aserrio = self.client.get(reverse('aserrio'))
        self.assertEqual(aserrio.status_code, 200)
        self.assertContains(
            aserrio,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )

        formulario_secado = self.client.get(reverse('secado_agregar'))
        self.assertEqual(formulario_secado.status_code, 200)
        self.assertContains(
            formulario_secado,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )

        formulario_reproceso = self.client.get(reverse('reproceso_agregar'))
        self.assertEqual(formulario_reproceso.status_code, 200)
        self.assertContains(
            formulario_reproceso,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )

    def test_permisologia_esta_vacia(self):
        usuario = get_user_model().objects.create_user(
            username='operador',
            password='clave-segura',
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse('permisologia'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Personalización de la apariencia')
        self.assertNotContains(response, 'color_fondo')

    def test_configuracion_muestra_datos_de_empresa_y_apariencia(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='clave-segura',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('configuracion'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Información de la empresa')
        self.assertContains(response, 'Personalización de la apariencia')
        self.assertContains(response, 'Guardar apariencia')

    def test_configuracion_guarda_logo_en_ruta_indicada_y_persiste_la_ruta(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='clave-segura',
            is_staff=True,
        )
        self.client.force_login(admin)

        with TemporaryDirectory() as directorio:
            with self.settings(BASE_DIR=Path(directorio)):
                response = self.client.post(
                    reverse('configuracion'),
                    {
                        'nombre': 'Aserradero El Roble',
                        'slogan': 'Madera responsable',
                        'rif': 'J-12345678-9',
                        'logo': SimpleUploadedFile(
                            'logo.png',
                            b'\x89PNG\r\n\x1a\ncontenido de prueba',
                            content_type='image/png',
                        ),
                    },
                )

                self.assertRedirects(response, reverse('configuracion'))
                self.assertTrue((Path(directorio) / 'static' / LogoEmpresa).is_file())
                configuracion = ConfiguracionEmpresa.objects.get(pk=1)
                self.assertEqual(configuracion.logo_path, LogoEmpresa)

    @patch('dashboard.context_processors.finders.find', return_value='C:/static/images/logo_empresa.png')
    def test_dashboard_muestra_logo_configurado_a_la_derecha_de_cerrar_sesion(self, _find_logo):
        usuario = get_user_model().objects.create_user(
            username='operador',
            password='clave-segura',
        )
        self.client.force_login(usuario)

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="topbar-actions"')
        self.assertContains(response, 'class="topbar-logo"')
        self.assertContains(response, f'src="/static/{LogoEmpresa}"')
        self.assertNotContains(response, 'class="company-logo"')
        self.assertEqual(response.content.count(b'class="topbar-logo"'), 1)


class MantenimientoOrdenesTrabajoViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='ordenes',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def test_acceso_desde_mantenimiento_muestra_formulario_y_logo_de_empresa(self):
        inicio = self.client.get(reverse('mantenimiento'))

        self.assertContains(inicio, reverse('mantenimiento_ordenes_trabajo'))
        response = self.client.get(reverse('mantenimiento_ordenes_trabajo'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Orden de trabajo')
        self.assertContains(response, 'Se asigna al guardar')
        self.assertContains(response, 'Wisdom Tech')
        self.assertContains(response, 'Logo de Wisdom Tech')
        self.assertContains(response, 'Correctivo')
        self.assertContains(response, 'Ejecución y cierre')
        self.assertContains(response, 'Firmas de cierre')
        self.assertContains(response, 'Órdenes registradas')

    def test_guarda_orden_con_numero_correlativo_como_clave_primaria_y_la_lista(self):
        response = self.client.post(
            reverse('mantenimiento_ordenes_trabajo'),
            {
                'titulo': 'Reparación de sierra',
                'tipo_orden': 'correctivo',
                'fecha_emision': '2026-11-14',
                'solicitante': 'María Pérez',
                'descripcion_trabajo': 'Cambio de rodamiento',
                'detalle_trabajo': 'Sustituir el rodamiento del eje principal.',
                'responsable': 'Luis Gómez',
                'fecha_programada': '2026-11-16',
                'prioridad': 'alta',
                'materiales_estimados': 'Rodamiento 6204',
                'mano_obra_estimada': '125.50',
                'materiales_utilizados': 'Rodamiento 6204',
                'tiempos_ejecucion': 'Inicio 08:00, fin 10:30',
                'observaciones': 'Equipo probado.',
                'hallazgos': 'Desgaste en el rodamiento.',
                'firma_responsable': 'Luis Gómez',
                'firma_supervisor': 'Ana Ruiz',
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_ordenes_trabajo'))
        orden = OrdenTrabajo.objects.get()
        self.assertEqual(orden.pk, orden.numero_orden)
        self.assertEqual(orden.numero_orden, 1)
        self.assertEqual(orden.mano_obra_estimada, 125.50)

        listado = self.client.get(reverse('mantenimiento_ordenes_trabajo'))
        self.assertContains(listado, 'OT-00001')
        self.assertContains(listado, 'Reparación de sierra')
        self.assertContains(listado, 'María Pérez')
        self.assertContains(listado, 'Luis Gómez')

    def test_tipo_de_orden_invalido_no_se_guarda(self):
        response = self.client.post(
            reverse('mantenimiento_ordenes_trabajo'),
            {
                'titulo': 'Orden inválida',
                'tipo_orden': 'otro',
                'solicitante': 'María Pérez',
                'descripcion_trabajo': 'Revisión',
                'detalle_trabajo': 'Revisar el equipo.',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(OrdenTrabajo.objects.count(), 0)
        self.assertIn('tipo_orden', response.context['form'].errors)


class MantenimientoIndicadoresViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='indicadores',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def test_panel_resume_backlog_y_muestra_indicadores_sin_datos_operativos(self):
        OrdenTrabajo.objects.create(
            titulo='Ajuste de sierra',
            tipo_orden='preventivo',
            duracion_estimada='4 horas',
            solicitante='Ana',
            descripcion_trabajo='Ajuste',
            detalle_trabajo='Ajustar la sierra principal.',
        )
        OrdenTrabajo.objects.create(
            titulo='Reparación de motor',
            tipo_orden='correctivo',
            duracion_estimada='1,5 h',
            solicitante='Luis',
            descripcion_trabajo='Reparación',
            detalle_trabajo='Reparar el motor.',
            tiempos_ejecucion='Inicio 08:00, fin 10:00',
        )
        OrdenTrabajo.objects.create(
            titulo='Inspección de equipo',
            tipo_orden='inspeccion',
            duracion_estimada='media jornada',
            solicitante='Eva',
            descripcion_trabajo='Inspección',
            detalle_trabajo='Inspeccionar el equipo.',
        )

        response = self.client.get(reverse('mantenimiento_indicadores'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['ordenes_pendientes'], 2)
        self.assertEqual(response.context['horas_pendientes_estimadas'], Decimal('4'))
        self.assertEqual(response.context['duraciones_con_horas'], 1)
        self.assertEqual(response.context['ordenes_por_tipo']['preventivo'], 1)
        self.assertEqual(response.context['ordenes_por_tipo']['correctivo'], 1)
        self.assertContains(response, 'Visión de alto nivel ejecutiva')
        self.assertContains(response, 'Sin datos')
        self.assertContains(response, 'no horas trabajadas')
        self.assertContains(response, reverse('mantenimiento_ordenes_trabajo'))


class MantenimientoFinancieroViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='financiero',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def test_panel_presenta_metricas_formulas_y_graficos_sin_inventar_costos(self):
        response = self.client.get(reverse('mantenimiento_financiero'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Visión ejecutiva')
        self.assertContains(
            response,
            'background: linear-gradient(135deg, var(--sidebar-start) 0%, var(--sidebar-end) 100%)',
        )
        self.assertContains(response, 'Costo total de mantenimiento')
        self.assertContains(response, 'Costo de mantenimiento / RAV')
        self.assertContains(response, 'Costo por hora de parada')
        self.assertContains(response, 'Margen de contribución por línea / producto')
        self.assertContains(response, 'Análisis de Reparar vs. Reemplazar')
        self.assertContains(response, 'Margen bruto total esperado')
        self.assertContains(response, 'Unidades totales producidas')
        self.assertContains(response, 'Sin datos')
        self.assertContains(response, '2–4% anual')


class MantenimientoGeneralViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='mantenimiento',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def test_boton_general_abre_el_formulario_de_configuracion(self):
        response = self.client.get(reverse('mantenimiento'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse('mantenimiento_general'))
        self.assertContains(response, reverse('mantenimiento_activos'))
        self.assertEqual(
            response.content.count(b"window.alert('En construcci\xc3\xb3n.')"),
            0,
        )
        self.assertContains(response, reverse('mantenimiento_indicadores'))
        self.assertContains(response, reverse('mantenimiento_financiero'))

        formulario = self.client.get(reverse('mantenimiento_general'))
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, 'Nombre de ciudad o parroquia')
        self.assertContains(formulario, '¿Tiene patio de rolas?')
        self.assertContains(formulario, '¿Clasifica rolas?')
        self.assertContains(formulario, 'Agregar máquina')
        self.assertContains(formulario, 'Agregar línea de producción')

    def test_guarda_configuracion_seccionada_y_lineas_organizadas(self):
        response = self.client.post(
            reverse('mantenimiento_general'),
            {
                'ciudad_parroquia': 'San Carlos',
                'nombre_aserradero': 'Aserradero El Roble',
                'tiene_patios_rolas': 'true',
                'clasifica_rolas': 'false',
                'tipo_produccion': 'seccionada',
                'cantidad_lineas': '2',
                'lineas': '["Línea 1 - Aserrío verde", "Línea 2 - Secado"]',
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_general'))
        configuracion = ConfiguracionMantenimiento.objects.get()
        self.assertEqual(configuracion.ciudad_parroquia, 'San Carlos')
        self.assertEqual(configuracion.tag_identificacion, 'SAN-ASE-EL')
        self.assertTrue(configuracion.tiene_patios_rolas)
        self.assertFalse(configuracion.clasifica_rolas)
        self.assertEqual(configuracion.cantidad_lineas, 2)
        self.assertEqual(
            list(configuracion.lineas_produccion.values_list('descripcion', flat=True)),
            ['Línea 1 - Aserrío verde', 'Línea 2 - Secado'],
        )

    def test_tag_identificacion_usa_solo_la_primera_palabra_si_no_hay_otra(self):
        configuracion = ConfiguracionMantenimiento(
            ciudad_parroquia='La Victoria',
            nombre_aserradero='Roble',
        )

        self.assertEqual(configuracion.tag_identificacion, 'LAV-ROB')

    def test_guarda_maquinas_por_linea_y_las_muestra_al_editar(self):
        response = self.client.post(
            reverse('mantenimiento_general'),
            {
                'ciudad_parroquia': 'San Carlos',
                'nombre_aserradero': 'Aserradero El Roble',
                'tiene_patios_rolas': 'true',
                'clasifica_rolas': 'false',
                'tipo_produccion': 'seccionada',
                'cantidad_lineas': '2',
                'lineas': (
                    '[{"descripcion":"Línea de aserrío","maquinas":["Sierra principal","Canteadora"]},'
                    '{"descripcion":"Línea de secado","maquinas":["Horno 1"]}]'
                ),
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_general'))
        self.assertEqual(
            list(LineaProduccion.objects.order_by('orden').values_list('descripcion', 'maquinas')),
            [
                ('Línea de aserrío', ['Sierra principal', 'Canteadora']),
                ('Línea de secado', ['Horno 1']),
            ],
        )

        ficha = self.client.get(reverse('mantenimiento_general'))
        self.assertEqual(ficha.status_code, 200)
        self.assertContains(ficha, 'Ficha general del aserradero')
        self.assertContains(ficha, 'Editar')
        self.assertContains(ficha, 'Sierra principal')

        formulario = self.client.get(f'{reverse("mantenimiento_general")}?editar=1')
        self.assertEqual(
            json.loads(formulario.context['lineas_iniciales']),
            [
                {
                    'descripcion': 'Línea de aserrío',
                    'maquinas': ['Sierra principal', 'Canteadora'],
                },
                {'descripcion': 'Línea de secado', 'maquinas': ['Horno 1']},
            ],
        )

    def test_edita_configuracion_guardada(self):
        configuracion = ConfiguracionMantenimiento.objects.create(
            ciudad_parroquia='San Carlos',
            nombre_aserradero='Aserradero El Roble',
            tiene_patios_rolas=True,
            clasifica_rolas=False,
            tipo_produccion='completa',
        )
        LineaProduccion.objects.create(
            configuracion=configuracion,
            descripcion='Línea de aserrío',
            maquinas=['Sierra principal'],
        )

        response = self.client.post(
            f'{reverse("mantenimiento_general")}?editar=1',
            {
                'ciudad_parroquia': 'Barinas',
                'nombre_aserradero': 'Aserradero Los Pinos',
                'tiene_patios_rolas': 'false',
                'clasifica_rolas': 'true',
                'tipo_produccion': 'completa',
                'cantidad_lineas': '',
                'lineas': '[{"descripcion":"Línea de producción","maquinas":["Sierra nueva"]}]',
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_general'))
        configuracion.refresh_from_db()
        self.assertEqual(configuracion.ciudad_parroquia, 'Barinas')
        self.assertEqual(configuracion.nombre_aserradero, 'Aserradero Los Pinos')
        self.assertEqual(
            list(configuracion.lineas_produccion.values_list('descripcion', 'maquinas')),
            [('Línea de producción', ['Sierra nueva'])],
        )

    def test_rechaza_nombres_de_linea_repetidos_sin_distinguir_mayusculas_o_espacios(self):
        response = self.client.post(
            reverse('mantenimiento_general'),
            {
                'ciudad_parroquia': 'San Carlos',
                'nombre_aserradero': 'Aserradero El Roble',
                'tiene_patios_rolas': 'true',
                'clasifica_rolas': 'false',
                'tipo_produccion': 'seccionada',
                'cantidad_lineas': '2',
                'lineas': (
                    '[{"descripcion":"Linea 1","maquinas":["Sierra principal"]},'
                    '{"descripcion":"  linea   1 ","maquinas":["Canteadora"]}]'
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Los nombres de las líneas de producción no pueden repetirse.')
        self.assertFalse(ConfiguracionMantenimiento.objects.exists())

    def test_linea_nueva_requiere_al_menos_una_maquina(self):
        response = self.client.post(
            reverse('mantenimiento_general'),
            {
                'ciudad_parroquia': 'Barinas',
                'nombre_aserradero': 'Los Pinos',
                'tiene_patios_rolas': 'false',
                'clasifica_rolas': 'true',
                'tipo_produccion': 'completa',
                'cantidad_lineas': '',
                'lineas': '[{"descripcion":"Línea de aserrío","maquinas":[]}]',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agrega al menos una máquina para cada línea de producción.')
        self.assertFalse(ConfiguracionMantenimiento.objects.exists())

    def test_produccion_completa_no_requiere_cantidad_de_lineas(self):
        response = self.client.post(
            reverse('mantenimiento_general'),
            {
                'ciudad_parroquia': 'Barinas',
                'nombre_aserradero': 'Los Pinos',
                'tiene_patios_rolas': 'false',
                'clasifica_rolas': 'true',
                'tipo_produccion': 'completa',
                'cantidad_lineas': '',
                'lineas': '["Línea única - Aserrío completo"]',
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_general'))
        configuracion = ConfiguracionMantenimiento.objects.get()
        self.assertIsNone(configuracion.cantidad_lineas)
        self.assertEqual(configuracion.tipo_produccion, 'completa')

    def test_produccion_seccionada_exige_cantidad_de_lineas(self):
        response = self.client.post(
            reverse('mantenimiento_general'),
            {
                'ciudad_parroquia': 'Barinas',
                'nombre_aserradero': 'Los Pinos',
                'tiene_patios_rolas': 'false',
                'clasifica_rolas': 'true',
                'tipo_produccion': 'seccionada',
                'cantidad_lineas': '',
                'lineas': '["Línea 1 - Aserrío"]',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Indica cuántas líneas de producción tiene.')
        self.assertFalse(ConfiguracionMantenimiento.objects.exists())


class MantenimientoActivosViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='activos',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def crear_configuracion(self):
        configuracion = ConfiguracionMantenimiento.objects.create(
            ciudad_parroquia='San Carlos',
            nombre_aserradero='Aserradero El Roble',
            tiene_patios_rolas=True,
            clasifica_rolas=False,
            tipo_produccion='seccionada',
            cantidad_lineas=1,
        )
        LineaProduccion.objects.create(
            configuracion=configuracion,
            descripcion='Línea de aserrío',
            maquinas=['Sierra circular', 'Sierra múltiple', 'Refrendino'],
            orden=1,
        )
        return configuracion

    def test_sin_configuracion_general_redirige_a_completarla(self):
        response = self.client.get(reverse('mantenimiento_activos'))

        self.assertRedirects(response, reverse('mantenimiento_general'))

    def test_muestra_las_maquinas_de_la_organizacion_de_produccion(self):
        self.crear_configuracion()

        response = self.client.get(reverse('mantenimiento_activos'))

        self.assertEqual(response.status_code, 200)
        for maquina in ('Sierra circular', 'Sierra múltiple', 'Refrendino'):
            self.assertContains(response, maquina)
        self.assertContains(response, 'Agregar información')
        self.assertContains(response, 'Ver ficha general')

    def test_guarda_y_muestra_especificaciones_de_la_maquina(self):
        configuracion = self.crear_configuracion()
        especificaciones = [
            {'nombre': 'Motor', 'valor': 'Trifásico'},
            {'nombre': 'Marca', 'valor': 'Roble'},
            {'nombre': 'KVA', 'valor': '15'},
            {'nombre': 'RPM', 'valor': '1800'},
            {'nombre': 'Tamaño', 'valor': '12 pulgadas'},
        ]

        response = self.client.post(
            reverse('mantenimiento_activos'),
            {
                'linea_descripcion': 'Línea de aserrío',
                'maquina': 'Sierra circular',
                'especificaciones': json.dumps(especificaciones),
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_activos'))
        activo = ActivoMaquina.objects.get()
        self.assertEqual(activo.configuracion, configuracion)
        self.assertEqual(activo.linea_descripcion, 'Línea de aserrío')
        self.assertEqual(activo.maquina, 'Sierra circular')
        self.assertEqual(activo.especificaciones, especificaciones)

        ficha = self.client.get(reverse('mantenimiento_activos'))
        self.assertContains(ficha, 'Ficha técnica')
        self.assertContains(ficha, 'Trifásico')
        self.assertContains(ficha, '12 pulgadas')

    def test_guarda_y_muestra_varios_elementos_de_la_maquina(self):
        self.crear_configuracion()
        elementos = [
            {
                'tipo_elemento': 'Motor principal',
                'descripcion': 'Motor trifásico de 15 HP',
                'tipos': ['mecanico', 'electrico'],
            },
            {
                'tipo_elemento': 'Motor de alimentación',
                'descripcion': 'Motor de 5 HP',
                'tipos': ['electrico'],
            },
        ]

        response = self.client.post(
            reverse('mantenimiento_activos'),
            {
                'linea_descripcion': 'Línea de aserrío',
                'maquina': 'Sierra circular',
                'especificaciones': '[{"nombre":"Tamaño","valor":"12 pulgadas"}]',
                'elementos': json.dumps(elementos),
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_activos'))
        activo = ActivoMaquina.objects.get()
        self.assertEqual(activo.elementos, elementos)

        ficha = self.client.get(reverse('mantenimiento_activos'))
        self.assertContains(ficha, 'Motor principal')
        self.assertContains(ficha, 'Motor trifásico de 15 HP')
        self.assertContains(ficha, 'Motor de alimentación')
        self.assertContains(ficha, 'Mecánico')
        self.assertContains(ficha, 'Eléctrico')

    def test_valida_tipo_y_descripcion_de_los_elementos(self):
        self.crear_configuracion()

        response = self.client.post(
            reverse('mantenimiento_activos'),
            {
                'linea_descripcion': 'Línea de aserrío',
                'maquina': 'Sierra circular',
                'especificaciones': '[{"nombre":"Tamaño","valor":"12 pulgadas"}]',
                'elementos': json.dumps([{
                    'tipo_elemento': 'Motor',
                    'descripcion': 'Motor de 15 HP',
                    'tipos': ['hidraulico'],
                }]),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Selecciona si el elemento es mecánico')
        self.assertFalse(ActivoMaquina.objects.exists())

    def test_rechaza_especificaciones_de_una_maquina_no_configurada(self):
        self.crear_configuracion()

        response = self.client.post(
            reverse('mantenimiento_activos'),
            {
                'linea_descripcion': 'Línea inventada',
                'maquina': 'Máquina ajena',
                'especificaciones': '[{"nombre":"Motor","valor":"15"}]',
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_activos'))
        self.assertFalse(ActivoMaquina.objects.exists())

    def test_valida_especificaciones_y_no_guarda_filas_vacias(self):
        self.crear_configuracion()

        response = self.client.post(
            reverse('mantenimiento_activos'),
            {
                'linea_descripcion': 'Línea de aserrío',
                'maquina': 'Sierra circular',
                'especificaciones': '[{"nombre":"Motor","valor":""}]',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Completa el nombre y el valor')
        self.assertFalse(ActivoMaquina.objects.exists())


class MantenimientoConsumiblesViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='consumibles',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def test_boton_abre_formulario_con_las_seis_secciones_y_campos(self):
        inicio = self.client.get(reverse('mantenimiento'))

        self.assertContains(inicio, reverse('mantenimiento_consumibles'))
        response = self.client.get(reverse('mantenimiento_consumibles'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Identificación del consumible')
        self.assertContains(response, 'Características técnicas')
        self.assertContains(response, 'Información comercial')
        self.assertContains(response, 'Información de almacenamiento')
        self.assertContains(response, 'Control del consumo')
        self.assertContains(response, 'Clasificación administrativa')
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertEqual(len(response.context['form'].fields), 50)
        self.assertIsNone(response.context['form']['estado'].value())
        self.assertIsNone(
            response.context['form']['requiere_condiciones_especiales'].value()
        )

    def test_solo_exige_codigo_y_nombre_y_no_precarga_valores(self):
        response = self.client.post(
            reverse('mantenimiento_consumibles'),
            {'codigo_interno': 'SK-003', 'nombre': 'Consumible nuevo'},
        )

        self.assertRedirects(response, reverse('mantenimiento_consumibles'))
        consumible = Consumible.objects.get(codigo_interno='SK-003')
        self.assertEqual(consumible.estado, '')
        self.assertIsNone(consumible.requiere_condiciones_especiales)

        listado = self.client.get(reverse('mantenimiento_consumibles'))
        self.assertContains(listado, 'SK-003')
        self.assertContains(listado, 'Consumible nuevo')
        self.assertContains(listado, 'Sin registrar')
        self.assertContains(
            listado,
            reverse('mantenimiento_consumible_detalle', args=[consumible.pk]),
        )

    def test_edita_un_consumible_existente(self):
        consumible = Consumible.objects.create(
            codigo_interno='SK-EDIT',
            nombre='Nombre original',
            descripcion='Descripción original',
        )

        formulario = self.client.get(
            reverse('mantenimiento_consumible_editar', args=[consumible.pk]),
        )

        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, 'Editar consumible: Nombre original')
        self.assertContains(formulario, 'value="Nombre original"')
        self.assertContains(formulario, 'Actualizar consumible')
        self.assertContains(
            self.client.get(reverse('mantenimiento_consumibles')),
            reverse('mantenimiento_consumible_editar', args=[consumible.pk]),
        )

        response = self.client.post(
            reverse('mantenimiento_consumible_editar', args=[consumible.pk]),
            {
                'codigo_interno': 'SK-EDIT',
                'nombre': 'Nombre corregido',
                'descripcion': 'Descripción actualizada',
                'stock_disponible': '12',
            },
        )

        self.assertRedirects(
            response,
            reverse('mantenimiento_consumible_detalle', args=[consumible.pk]),
        )
        consumible.refresh_from_db()
        self.assertEqual(consumible.nombre, 'Nombre corregido')
        self.assertEqual(consumible.descripcion, 'Descripción actualizada')
        self.assertEqual(consumible.stock_disponible, 12)

    def test_elimina_un_consumible_solo_por_post(self):
        consumible = Consumible.objects.create(
            codigo_interno='SK-DELETE',
            nombre='Consumible a eliminar',
        )
        otro_consumible = Consumible.objects.create(
            codigo_interno='SK-KEEP',
            nombre='Consumible que permanece',
        )
        url_eliminar = reverse(
            'mantenimiento_consumible_eliminar',
            args=[consumible.pk],
        )

        listado = self.client.get(reverse('mantenimiento_consumibles'))
        self.assertContains(listado, url_eliminar)
        self.assertContains(listado, 'Editar')
        self.assertContains(listado, 'Eliminar')
        self.assertEqual(self.client.get(url_eliminar).status_code, 405)

        response = self.client.post(url_eliminar)

        self.assertRedirects(response, reverse('mantenimiento_consumibles'))
        self.assertFalse(Consumible.objects.filter(pk=consumible.pk).exists())
        self.assertTrue(Consumible.objects.filter(pk=otro_consumible.pk).exists())

    def test_guarda_ficha_completa_y_archivos_adjuntos(self):
        import io
        from PIL import Image

        imagen_buffer = io.BytesIO()
        Image.new('RGB', (1, 1), color='white').save(imagen_buffer, format='PNG')
        contenido_imagen = imagen_buffer.getvalue()
        archivos = {
            'foto_frente': SimpleUploadedFile(
                'frente.png', contenido_imagen, content_type='image/png',
            ),
            'foto_lado': SimpleUploadedFile(
                'lado.png', contenido_imagen, content_type='image/png',
            ),
            'foto_perfil': SimpleUploadedFile(
                'perfil.png', contenido_imagen, content_type='image/png',
            ),
            'ficha_tecnica': SimpleUploadedFile(
                'ficha.pdf', b'%PDF-1.4\nFicha tecnica', content_type='application/pdf',
            ),
        }
        datos = {
            'codigo_interno': 'SK-001',
            'nombre': 'Disco de corte',
            'descripcion': 'Disco para sierra circular de producción.',
            'categoria': 'Aserrío',
            'material': 'Acero',
            'diametro': '300.00',
            'precio_compra': '25.50',
            'moneda': 'USD',
            'fecha_ultima_entrega': '2026-11-01',
            'tiempo_entrega': '7',
            'stock_minimo': '2',
            'stock_maximo': '20',
            'stock_disponible': '8',
            'unidad_medida': 'unidades',
            'ubicacion': 'Bodega A',
            'requiere_condiciones_especiales': 'False',
            'criticidad_consumo': 'alta',
            'estado': 'activo',
            'tipo_consumible': 'directo',
            'criticidad_administrativa': 'critico',
        }

        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            response = self.client.post(
                reverse('mantenimiento_consumibles'),
                data={**datos, **archivos},
            )
            consumible = Consumible.objects.get(codigo_interno='SK-001')
            detalle = self.client.get(reverse(
                'mantenimiento_consumible_detalle',
                args=[consumible.pk],
            ))

        self.assertRedirects(response, reverse('mantenimiento_consumibles'))
        consumible = Consumible.objects.get(codigo_interno='SK-001')
        self.assertEqual(consumible.nombre, 'Disco de corte')
        self.assertEqual(consumible.stock_disponible, 8)
        self.assertEqual(consumible.ubicacion, 'Bodega A')
        self.assertEqual(consumible.criticidad_consumo, 'alta')
        self.assertEqual(consumible.estado, 'activo')
        self.assertTrue(consumible.foto_frente.name)
        self.assertTrue(consumible.foto_lado.name)
        self.assertTrue(consumible.foto_perfil.name)
        self.assertTrue(consumible.ficha_tecnica.name)
        listado = self.client.get(reverse('mantenimiento_consumibles'))
        self.assertContains(listado, 'Disco para sierra circular')
        self.assertRegex(listado.content.decode(), r'8[,.]00 unidades')
        self.assertContains(listado, 'Bodega A')
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, 'Características técnicas')
        self.assertContains(detalle, 'Acero')
        self.assertContains(detalle, 'Ver o descargar PDF')
        self.assertContains(detalle, 'Vista frente')

    def test_rechaza_ficha_tecnica_que_no_es_un_pdf(self):
        response = self.client.post(
            reverse('mantenimiento_consumibles'),
            data={
                'codigo_interno': 'SK-002',
                'nombre': 'Rodamiento',
                'ficha_tecnica': SimpleUploadedFile(
                    'ficha.pdf', b'contenido incorrecto', content_type='application/pdf',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'El archivo no contiene un documento PDF válido.')
        self.assertFalse(Consumible.objects.exists())


class MantenimientoHerramientasViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='herramientas',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def test_acceso_desde_mantenimiento_y_formulario_de_registro(self):
        inicio = self.client.get(reverse('mantenimiento'))
        self.assertContains(inicio, reverse('mantenimiento_herramientas'))

        listado = self.client.get(reverse('mantenimiento_herramientas'))
        self.assertEqual(listado.status_code, 200)
        self.assertContains(listado, 'Registrar herramienta')
        self.assertNotContains(listado, 'Identificación técnica')

        formulario = self.client.get(
            reverse('mantenimiento_herramientas'),
            {'registrar': '1'},
        )
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, '.consumable-input,')
        self.assertContains(formulario, '.consumable-file')
        for titulo in (
            'Identificación de la herramienta',
            'Identificación técnica',
            'Información de la adquisición',
            'Ubicación física',
            'Asignación y responsabilidad',
            'Estado y disponibilidad',
        ):
            self.assertContains(formulario, titulo)
        self.assertEqual(len(formulario.context['form'].fields), 55)

    def test_registra_herramienta_y_solo_exige_codigo_y_nombre(self):
        response = self.client.post(
            reverse('mantenimiento_herramientas'),
            {
                'codigo_interno': 'HT-001',
                'nombre': 'Taladro industrial',
                'voltaje': '220 V',
                'disponibilidad': 'Disponible',
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_herramientas'))
        herramienta = Herramienta.objects.get(codigo_interno='HT-001')
        self.assertEqual(herramienta.nombre, 'Taladro industrial')
        self.assertEqual(herramienta.voltaje, '220 V')
        self.assertEqual(herramienta.disponibilidad, 'Disponible')
        self.assertContains(
            self.client.get(reverse('mantenimiento_herramientas')),
            'Taladro industrial',
        )


class MantenimientoPrestamosHerramientasViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='prestamos',
            password='clave-segura',
        )
        self.client.force_login(usuario)

    def test_planilla_de_impresion_contiene_dos_copias_con_todos_los_datos(self):
        prestamos = self.client.get(reverse('mantenimiento_prestamos_herramientas'))
        self.assertContains(
            prestamos,
            reverse('mantenimiento_planilla_prestamo_herramientas'),
        )
        self.assertContains(prestamos, 'Imprimir planilla')

        response = self.client.get(
            reverse('mantenimiento_planilla_prestamo_herramientas')
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count(b'class="loan-copy"'), 2)
        self.assertContains(response, '@page')
        self.assertContains(response, 'window.print()')
        for campo in (
            'Datos generales',
            'Datos del trabajador',
            'Herramienta entregada',
            'En caso de accesorio entregado',
            'Autorización y entrega',
            'Fecha prevista de devolución',
            'Código del trabajador',
            'Área donde utilizará la herramienta',
            'Orden de trabajo',
            'Condición',
            'Nombre del accesorio',
            'Autorizado por',
            'Entregado por',
            'Quien recibe',
        ):
            self.assertContains(response, campo)
        self.assertNotContains(response, '<input')

    def test_registra_prestamo_de_herramienta_existente_y_muestra_el_listado(self):
        herramienta = Herramienta.objects.create(
            codigo_interno='HT-010',
            nombre='Sierra circular',
        )

        response = self.client.post(
            reverse('mantenimiento_prestamos_herramientas'),
            {
                'sku': 'HT-010',
                'fecha_prestamo': '2026-11-13',
                'nombre_solicitante': 'María Pérez',
                'fecha_devolucion': '2026-11-15',
                'nombre_responsable': 'Luis Gómez',
            },
        )

        self.assertRedirects(response, reverse('mantenimiento_prestamos_herramientas'))
        prestamo = PrestamoHerramienta.objects.get()
        self.assertEqual(prestamo.herramienta, herramienta)
        self.assertEqual(prestamo.nombre_solicitante, 'María Pérez')
        listado = self.client.get(reverse('mantenimiento_prestamos_herramientas'))
        self.assertContains(listado, 'HT-010')
        self.assertContains(listado, 'Sierra circular')
        self.assertContains(listado, 'María Pérez')
        self.assertContains(listado, 'Luis Gómez')

    def test_sku_no_registrado_muestra_alerta_y_no_crea_prestamo(self):
        response = self.client.post(
            reverse('mantenimiento_prestamos_herramientas'),
            {
                'sku': 'NO-EXISTE',
                'fecha_prestamo': '2026-11-13',
                'nombre_solicitante': 'María Pérez',
                'fecha_devolucion': '2026-11-15',
                'nombre_responsable': 'Luis Gómez',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'la herramienta solicitada no existe o no esta registrada en la base de datos',
        )
        self.assertTrue(response.context['sku_no_encontrado'])
        self.assertFalse(PrestamoHerramienta.objects.exists())


class NominaDashboardTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='nomina',
            password='clave-segura',
        )
        self.client.force_login(usuario)
        self.trabajador = Trabajador.objects.create(
            nombres='Ana Pérez',
            cedula_identidad='V-12345678',
            fecha_nacimiento='1990-01-01',
            tipo_contrato='indeterminado',
            area_trabajo='Aserrío',
            departamento='Producción',
            seccion='Línea 1',
            cargo='Operadora',
            salario_contratacion=Decimal('1000.00'),
        )

    def test_listado_completo_y_dashboard_del_trabajador_seleccionado(self):
        administrativo = self.client.get(reverse('administrativo'))
        self.assertContains(administrativo, reverse('nomina_dashboard'))

        listado = self.client.get(
            f"{reverse('nomina_dashboard')}?seccion=nomina"
        )
        self.assertEqual(listado.status_code, 200)
        self.assertContains(listado, '<section class="payroll-directory">')
        self.assertContains(listado, 'Nombre y apellido')
        self.assertNotContains(listado, '<div class="payroll-workspace">')

        response = self.client.get(
            f"{reverse('nomina_dashboard')}?trabajador={self.trabajador.pk}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nómina y pagos')
        self.assertContains(response, 'Configuración salarial')
        self.assertContains(response, '<div class="payroll-workspace">')
        self.assertNotContains(response, '<section class="payroll-directory">')
        self.assertContains(response, 'Ana Pérez')
        self.assertEqual(
            response.context['trabajador_seleccionado'].salario_contratacion,
            Decimal('1000.00'),
        )
        self.assertContains(response, 'Información del trabajador')
        self.assertContains(response, 'Espacio reservado')

    def test_guarda_nomina_y_calcula_totales_en_el_periodo(self):
        ConfiguracionNomina.objects.create(
            ivss_patronal_porcentaje=Decimal('10.00'),
            rpe_patronal_porcentaje=Decimal('2.00'),
            faov_patronal_porcentaje=Decimal('1.00'),
            inces_porcentaje=Decimal('0.50'),
            pensiones_porcentaje=Decimal('1.50'),
        )
        response = self.client.post(
            reverse('nomina_dashboard'),
            {
                'seccion': 'nomina',
                'trabajador': self.trabajador.pk,
                'periodo_desde': '2026-11-01',
                'periodo_hasta': '2026-11-15',
                'fecha_pago': '2026-11-17',
                'metodo_pago': 'transferencia',
                'horas_extras': '100.00',
                'bono_produccion': '50.00',
                'bono_nocturno': '25.00',
                'vacaciones': '10.00',
                'anticipo_salarial': '15.00',
                'prestamo_personal': '20.00',
                'numero_cuenta': '0123456789012345',
            },
        )

        periodo = NominaPeriodo.objects.get()
        detalle = NominaDetalle.objects.get()
        self.assertRedirects(
            response,
            f"{reverse('nomina_dashboard')}?seccion=nomina"
            f"&periodo={periodo.pk}&trabajador={self.trabajador.pk}",
        )
        self.assertEqual(periodo.codigo, 'NOM-20261117-001')
        self.assertEqual(detalle.salario_base, Decimal('1000.00'))
        self.assertEqual(detalle.total_asignaciones, Decimal('1185.00'))
        self.assertEqual(detalle.ivss_deduccion, Decimal('40.00'))
        self.assertEqual(detalle.rpe_deduccion, Decimal('5.00'))
        self.assertEqual(detalle.faov_deduccion, Decimal('10.00'))
        self.assertEqual(detalle.total_deducciones, Decimal('90.00'))
        self.assertEqual(detalle.neto_pagar, Decimal('1095.00'))
        self.assertEqual(detalle.total_aportes, Decimal('150.00'))
        self.assertEqual(detalle.ivss_patronal_porcentaje, Decimal('10.00'))
        self.assertEqual(detalle.numero_cuenta_enmascarado, '************2345')

        dashboard = self.client.get(response.url)
        self.assertContains(dashboard, periodo.codigo)
        self.assertContains(dashboard, '2345')
        self.assertNotContains(dashboard, '0123456789012345')

        otro_trabajador = Trabajador.objects.create(
            nombres='Luis Gómez',
            cedula_identidad='V-87654321',
            fecha_nacimiento='1988-02-02',
            codigo_trabajador='TEST-002',
            salario_contratacion=Decimal('800.00'),
        )
        segunda_nomina = self.client.post(
            reverse('nomina_dashboard'),
            {
                'seccion': 'nomina',
                'periodo': periodo.pk,
                'trabajador': otro_trabajador.pk,
                'periodo_desde': '2026-11-01',
                'periodo_hasta': '2026-11-15',
                'fecha_pago': '2026-11-17',
                'metodo_pago': 'transferencia',
                'horas_extras': '0',
                'bono_produccion': '0',
                'bono_nocturno': '0',
                'vacaciones': '0',
                'anticipo_salarial': '0',
                'prestamo_personal': '0',
                'numero_cuenta': '',
            },
        )
        self.assertEqual(segunda_nomina.status_code, 302)
        self.assertEqual(periodo.detalles.count(), 2)

    def test_no_guarda_periodo_si_fechas_no_son_validas(self):
        response = self.client.post(
            reverse('nomina_dashboard'),
            {
                'seccion': 'nomina',
                'trabajador': self.trabajador.pk,
                'periodo_desde': '2026-11-16',
                'periodo_hasta': '2026-11-01',
                'fecha_pago': '2026-11-17',
                'metodo_pago': 'transferencia',
                'horas_extras': '0',
                'bono_produccion': '0',
                'bono_nocturno': '0',
                'vacaciones': '0',
                'anticipo_salarial': '0',
                'prestamo_personal': '0',
                'numero_cuenta': '',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'La fecha final debe ser igual o posterior a la inicial.')
        self.assertFalse(NominaPeriodo.objects.exists())
        self.assertFalse(NominaDetalle.objects.exists())

    def test_configuracion_salarial_guarda_tasas_patronales(self):
        response = self.client.post(
            f"{reverse('nomina_dashboard')}?seccion=salario",
            {
                'seccion': 'salario',
                'ivss_patronal_porcentaje': '10',
                'rpe_patronal_porcentaje': '2',
                'faov_patronal_porcentaje': '1',
                'inces_porcentaje': '0.5',
                'pensiones_porcentaje': '1.5',
            },
        )

        self.assertRedirects(
            response,
            f"{reverse('nomina_dashboard')}?seccion=salario",
        )
        configuracion = ConfiguracionNomina.objects.get(pk=1)
        self.assertEqual(configuracion.ivss_patronal_porcentaje, Decimal('10.00'))
        self.assertEqual(configuracion.pensiones_porcentaje, Decimal('1.50'))
