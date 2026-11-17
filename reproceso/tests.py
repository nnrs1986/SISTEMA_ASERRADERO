import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from aserrio.models import PaqueteAserrio
from secado.models import SecadoPaquete, SecadoRegistro
from .models import ReprocesoPaquete, ReprocesoRegistro


class ReprocesoViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='operador',
            password='clave-segura',
        )
        self.client.force_login(usuario)
        self.paquete_seco = self.crear_paquete('ASR-20261020-0001', 1)
        self.paquete_humedo = self.crear_paquete('ASR-20261020-0002', 2)
        registro_secado = SecadoRegistro.objects.create(
            fecha_inicio=date(2026, 10, 20),
            fecha_fin=date(2026, 10, 22),
            turno='turno_1',
            nombre_supervisor='Supervisor secado',
        )
        SecadoPaquete.objects.create(registro=registro_secado, paquete=self.paquete_seco)
        registro_pendiente = SecadoRegistro.objects.create(
            fecha_inicio=date(2026, 10, 21),
            turno='turno_1',
            nombre_supervisor='Supervisor secado',
        )
        SecadoPaquete.objects.create(registro=registro_pendiente, paquete=self.paquete_humedo)

    def crear_paquete(self, codigo, consecutivo):
        return PaqueteAserrio.objects.create(
            fecha=date(2026, 10, 20),
            turno='turno_1',
            nombre_supervisor='Ana Supervisor',
            nombre_operador='Luis Operador',
            especie_madera='pino',
            tipo_rola='gruesa',
            maquinas_proceso=['sierra_principal'],
            incluye_recuperacion=False,
            codigo_paquete=codigo,
            consecutivo_diario=consecutivo,
            largo=Decimal('2.000'),
            ancho=Decimal('0.500'),
            espesor=Decimal('0.100'),
            cantidad_piezas=10,
            ch_estimado=12,
            tipo_elemento='tabla',
            calidad_visual='primera',
        )

    def datos_reproceso(self, paquete_id=None):
        return {
            'fecha': '2026-10-24',
            'nombre_supervisor': 'María Supervisora',
            'paquete_origen_id': paquete_id or self.paquete_seco.pk,
            'maquinas_proceso': ['cepilladora', 'moldurera'],
            'productos_json': json.dumps([
                {
                    'tipo_producto': 's4s',
                    'largo': '1.800',
                    'ancho': '0.120',
                    'espesor': '0.030',
                    'cantidad_piezas': '6',
                    'calidad_visual': 'primera',
                },
                {
                    'tipo_producto': 'deck',
                    'largo': '2.000',
                    'ancho': '0.100',
                    'espesor': '0.025',
                    'cantidad_piezas': '4',
                    'calidad_visual': 'segunda',
                },
            ]),
        }

    def test_modulo_presenta_lista_y_formulario_independiente(self):
        response = self.client.get(reverse('reproceso'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar proceso de reproceso')

        formulario = self.client.get(reverse('reproceso_agregar'))
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, 'Nombre del supervisor')
        self.assertContains(formulario, 'Lijadora de banda')
        self.assertContains(formulario, 'Machihembrado')

    def test_busqueda_solo_devuelve_paquetes_con_secado_finalizado(self):
        response = self.client.get(reverse('reproceso_buscar_paquete'), {
            'codigo_paquete': self.paquete_seco.codigo_paquete.lower(),
            'fecha': '2026-10-24',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['codigo'], self.paquete_seco.codigo_paquete)
        self.assertEqual(response.json()['dimensiones'], '2.000 × 0.500 × 0.100 m')
        self.assertEqual(response.json()['volumen_total'], '1.000')

        pendiente = self.client.get(reverse('reproceso_buscar_paquete'), {
            'codigo_paquete': self.paquete_humedo.codigo_paquete,
            'fecha': '2026-10-24',
        })
        self.assertEqual(pendiente.status_code, 400)
        self.assertIn('pasado por el proceso de secado', pendiente.json()['error'])

        inexistente = self.client.get(reverse('reproceso_buscar_paquete'), {
            'codigo_paquete': 'ASR-NO-EXISTE',
            'fecha': '2026-10-24',
        })
        self.assertEqual(inexistente.status_code, 404)
        self.assertIn('No existe', inexistente.json()['error'])

    def test_busqueda_rechaza_reproceso_antes_del_fin_del_secado(self):
        response = self.client.get(reverse('reproceso_buscar_paquete'), {
            'codigo_paquete': self.paquete_seco.codigo_paquete,
            'fecha': '2026-10-21',
        })

        self.assertEqual(response.status_code, 409)
        self.assertIn('terminó el secado el 22/10/2026', response.json()['error'])

    def test_busqueda_rechaza_reproceso_anterior_a_la_fecha_de_aserrio(self):
        paquete_futuro = self.crear_paquete('ASR-20261023-0001', 3)
        paquete_futuro.fecha = date(2026, 10, 23)
        paquete_futuro.save(update_fields=['fecha'])
        registro_secado = SecadoRegistro.objects.create(
            fecha_inicio=date(2026, 10, 21),
            fecha_fin=date(2026, 10, 22),
            turno='turno_1',
            nombre_supervisor='Supervisor secado',
        )
        SecadoPaquete.objects.create(registro=registro_secado, paquete=paquete_futuro)

        response = self.client.get(reverse('reproceso_buscar_paquete'), {
            'codigo_paquete': paquete_futuro.codigo_paquete,
            'fecha': '2026-10-22',
        })

        self.assertEqual(response.status_code, 409)
        self.assertIn('fue creado el 23/10/2026', response.json()['error'])

    def test_busqueda_rechaza_paquete_ya_usado_en_reproceso(self):
        ReprocesoRegistro.objects.create(
            fecha=date(2026, 10, 24),
            nombre_supervisor='María Supervisora',
            paquete_origen=self.paquete_seco,
            maquinas_proceso=['cepilladora'],
        )

        response = self.client.get(reverse('reproceso_buscar_paquete'), {
            'codigo_paquete': self.paquete_seco.codigo_paquete,
            'fecha': '2026-10-24',
        })

        self.assertEqual(response.status_code, 409)
        self.assertIn('ya fue usado en un reproceso', response.json()['error'])

    def test_guarda_reproceso_y_crea_codigo_y_volumen_por_producto(self):
        response = self.client.post(reverse('reproceso_agregar'), self.datos_reproceso())
        self.assertRedirects(response, reverse('reproceso'))

        registro = ReprocesoRegistro.objects.get()
        self.assertEqual(registro.paquete_origen, self.paquete_seco)
        self.assertEqual(registro.maquinas_proceso, ['cepilladora', 'moldurera'])
        self.assertEqual(registro.paquetes_generados.count(), 2)
        s4s = registro.paquetes_generados.get(tipo_producto='s4s')
        self.assertEqual(s4s.codigo_paquete, 'RPR-20261024-0001')
        self.assertEqual(s4s.volumen_total, Decimal('0.038880000'))
        self.assertEqual(s4s.cantidad_piezas, 6)
        deck = registro.paquetes_generados.get(tipo_producto='deck')
        self.assertEqual(deck.codigo_paquete, 'RPR-20261024-0002')

        lista = self.client.get(reverse('reproceso'))
        paquete = ReprocesoRegistro.objects.get().paquetes_generados.first()
        self.assertContains(lista, 'RPR-20261024-0001')
        self.assertContains(lista, 'ASR-20261020-0001')
        self.assertContains(lista, 'Ver')
        self.assertContains(lista, reverse('reproceso_paquete_ver', args=[paquete.pk]))
        self.assertContains(lista, 'Editar')

    def test_detalle_del_paquete_de_reproceso_muestra_sus_datos(self):
        response = self.client.post(reverse('reproceso_agregar'), self.datos_reproceso())
        paquete = ReprocesoPaquete.objects.get(codigo_paquete='RPR-20261024-0001')

        detalle = self.client.get(reverse('reproceso_paquete_ver', args=[paquete.pk]))
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, 'Paquete de reproceso')
        self.assertContains(detalle, paquete.codigo_paquete)
        self.assertContains(detalle, 'Piezas')
        self.assertContains(detalle, reverse('reproceso_paquete_editar', args=[paquete.pk]))

    def test_generacion_de_codigo_reproceso_ignora_codigos_ya_usados_en_aserrio(self):
        self.crear_paquete('RPR-20261024-0001', 99)

        response = self.client.post(reverse('reproceso_agregar'), self.datos_reproceso())

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ReprocesoPaquete.objects.filter(codigo_paquete='RPR-20261024-0002').exists())
        self.assertFalse(ReprocesoPaquete.objects.filter(codigo_paquete='RPR-20261024-0001').exists())

    def test_rechaza_reproceso_cuya_suma_no_coincide_con_el_paquete_origen(self):
        datos = self.datos_reproceso()
        productos = json.loads(datos['productos_json'])
        productos[0]['cantidad_piezas'] = '5'
        datos['productos_json'] = json.dumps(productos)

        response = self.client.post(reverse('reproceso_agregar'), datos)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'debe ser 10')
        self.assertFalse(ReprocesoRegistro.objects.exists())

    def test_edita_paquete_y_ajusta_el_hermano_sin_cambiar_el_total(self):
        self.client.post(reverse('reproceso_agregar'), self.datos_reproceso())
        paquete = ReprocesoPaquete.objects.get(consecutivo_diario=1)
        response = self.client.post(
            reverse('reproceso_paquete_editar', args=[paquete.pk]),
            {
                'tipo_producto': 's4s',
                'largo': '1.800',
                'ancho': '0.120',
                'espesor': '0.030',
                'cantidad_piezas': '7',
                'calidad_visual': 'primera',
            },
        )

        self.assertRedirects(response, reverse('reproceso'))
        paquete.refresh_from_db()
        hermano = ReprocesoPaquete.objects.get(consecutivo_diario=2)
        self.assertEqual(paquete.cantidad_piezas, 7)
        self.assertEqual(hermano.cantidad_piezas, 3)
        self.assertEqual(
            paquete.cantidad_piezas + hermano.cantidad_piezas,
            self.paquete_seco.cantidad_piezas,
        )

    def test_no_acepta_paquete_sin_secado_finalizado(self):
        response = self.client.post(
            reverse('reproceso_agregar'),
            self.datos_reproceso(self.paquete_humedo.pk),
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ReprocesoRegistro.objects.exists())
        self.assertFalse(ReprocesoPaquete.objects.exists())

    def test_no_guarda_reproceso_anterior_al_fin_del_secado(self):
        datos = self.datos_reproceso()
        datos['fecha'] = '2026-10-21'

        response = self.client.post(reverse('reproceso_agregar'), datos)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'terminó el secado el 22/10/2026')
        self.assertContains(response, 'package-dialog')
        self.assertFalse(ReprocesoRegistro.objects.exists())

    def test_no_guarda_reproceso_anterior_a_la_fecha_de_aserrio(self):
        paquete_futuro = self.crear_paquete('ASR-20261023-0001', 3)
        paquete_futuro.fecha = date(2026, 10, 23)
        paquete_futuro.save(update_fields=['fecha'])
        registro_secado = SecadoRegistro.objects.create(
            fecha_inicio=date(2026, 10, 21),
            fecha_fin=date(2026, 10, 22),
            turno='turno_1',
            nombre_supervisor='Supervisor secado',
        )
        SecadoPaquete.objects.create(registro=registro_secado, paquete=paquete_futuro)
        datos = self.datos_reproceso(paquete_futuro.pk)
        datos['fecha'] = '2026-10-22'

        response = self.client.post(reverse('reproceso_agregar'), datos)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'fue creado el 23/10/2026')
        self.assertContains(response, 'package-dialog')
        self.assertFalse(ReprocesoRegistro.objects.exists())

    def test_no_acepta_paquete_inexistente_ni_ya_usado(self):
        response = self.client.post(
            reverse('reproceso_agregar'),
            self.datos_reproceso(999999),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No existe un paquete con ese ID.')
        self.assertContains(response, 'package-dialog')
        self.assertFalse(ReprocesoRegistro.objects.exists())

        ReprocesoRegistro.objects.create(
            fecha=date(2026, 10, 24),
            nombre_supervisor='María Supervisora',
            paquete_origen=self.paquete_seco,
            maquinas_proceso=['cepilladora'],
        )
        response = self.client.post(
            reverse('reproceso_agregar'),
            self.datos_reproceso(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este paquete ya fue usado en un reproceso.')
        self.assertEqual(ReprocesoRegistro.objects.count(), 1)
        self.assertFalse(ReprocesoPaquete.objects.exists())

    def test_no_guarda_reproceso_sin_producto_o_maquinas_validas(self):
        datos = self.datos_reproceso()
        datos['productos_json'] = '[]'
        response = self.client.post(reverse('reproceso_agregar'), datos)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ReprocesoRegistro.objects.exists())

        datos = self.datos_reproceso()
        datos['maquinas_proceso'] = ['maquina_invalida']
        response = self.client.post(reverse('reproceso_agregar'), datos)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ReprocesoRegistro.objects.exists())
