import json
from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from aserrio.models import PaqueteAserrio
from .models import SecadoPaquete, SecadoRegistro


class SecadoViewTests(TestCase):
    def setUp(self):
        usuario = get_user_model().objects.create_user(
            username='supervisor',
            password='clave-segura',
        )
        self.client.force_login(usuario)
        self.paquete_uno = self.crear_paquete(
            codigo='ASR-20261014-0001',
            consecutivo=1,
            ch_estimado=12,
        )
        self.paquete_dos = self.crear_paquete(
            codigo='ASR-20261014-0002',
            consecutivo=2,
            ch_estimado=14,
        )

    def crear_paquete(self, codigo, consecutivo, ch_estimado):
        return PaqueteAserrio.objects.create(
            fecha=date(2026, 10, 14),
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
            ch_estimado=ch_estimado,
            tipo_elemento='tabla',
            calidad_visual='primera',
        )

    def datos_registro(self, paquetes):
        return {
            'fecha_inicio': '2026-10-15',
            'fecha_fin': '2026-10-20',
            'turno': 'turno_2',
            'nombre_supervisor': 'María Supervisora',
            'paquetes_json': json.dumps(paquetes),
        }

    def test_pantalla_principal_solo_muestra_boton_y_resumen(self):
        response = self.client.get(reverse('secado'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agregar proceso de secado')
        self.assertContains(response, 'Volumen total (m³)')
        self.assertContains(response, 'Promedio CH final')
        self.assertNotContains(response, 'Código ID del paquete')

        formulario = self.client.get(reverse('secado_agregar'))
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, 'Código ID del paquete')
        self.assertContains(formulario, 'Ese paquete ya está agregado a la lista actual.')
        self.assertContains(formulario, 'Promedio CH estimado (%)')
        self.assertContains(formulario, 'Turno de secado')
        self.assertContains(formulario, 'Fecha final del proceso')

    def test_busca_paquete_por_codigo_sin_distinguir_mayusculas(self):
        response = self.client.get(reverse('secado_buscar_paquete'), {
            'codigo_paquete': self.paquete_uno.codigo_paquete.lower(),
            'fecha_inicio': '2026-10-15',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['codigo'], self.paquete_uno.codigo_paquete)
        self.assertEqual(response.json()['ancho'], '0.500')
        self.assertEqual(response.json()['volumen_total'], '1.000')
        self.assertEqual(response.json()['ch_estimado'], 12)

    def test_busqueda_rechaza_paquete_que_ya_finalizo_secado(self):
        registro = SecadoRegistro.objects.create(
            fecha_inicio=date(2026, 10, 15),
            fecha_fin=date(2026, 10, 20),
            turno='turno_1',
            nombre_supervisor='Ana Supervisora',
        )
        SecadoPaquete.objects.create(registro=registro, paquete=self.paquete_uno)

        response = self.client.get(reverse('secado_buscar_paquete'), {
            'codigo_paquete': self.paquete_uno.codigo_paquete,
            'fecha_inicio': '2026-10-15',
        })

        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()['error'],
            f'El paquete {self.paquete_uno.codigo_paquete} ya está seco.',
        )

    def test_busqueda_informa_si_el_paquete_no_existe(self):
        response = self.client.get(reverse('secado_buscar_paquete'), {
            'codigo_paquete': 'ASR-NO-EXISTE',
            'fecha_inicio': '2026-10-15',
        })

        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    def test_busqueda_rechaza_paquete_antes_de_su_fecha_de_aserrio(self):
        response = self.client.get(reverse('secado_buscar_paquete'), {
            'codigo_paquete': self.paquete_uno.codigo_paquete,
            'fecha_inicio': '2026-10-13',
        })

        self.assertEqual(response.status_code, 409)
        self.assertIn('fue creado el 14/10/2026', response.json()['error'])

    def test_guarda_paquetes_y_permite_ch_final_pendiente(self):
        response = self.client.post(reverse('secado_agregar'), self.datos_registro([
            {'id': self.paquete_uno.pk, 'ch_final': '10.50'},
            {'id': self.paquete_dos.pk, 'ch_final': ''},
        ]))

        self.assertRedirects(response, reverse('secado'))
        registro = SecadoRegistro.objects.get()
        self.assertEqual(registro.fecha_inicio, date(2026, 10, 15))
        self.assertEqual(registro.turno, 'turno_2')
        self.assertEqual(registro.nombre_supervisor, 'María Supervisora')
        self.assertEqual(registro.paquetes.count(), 2)
        self.assertEqual(
            registro.paquetes.get(paquete=self.paquete_uno).ch_final,
            Decimal('10.50'),
        )
        self.assertIsNone(registro.paquetes.get(paquete=self.paquete_dos).ch_final)

        response = self.client.get(reverse('secado'))
        registro_resumen = response.context['registros'][0]
        self.assertEqual(registro_resumen.fecha_fin, date(2026, 10, 20))
        self.assertEqual(registro_resumen.volumen_total, Decimal('2.000000000'))
        self.assertEqual(registro_resumen.promedio_final, Decimal('10.5'))
        self.assertEqual(registro_resumen.especies, 'Pino')
        self.assertContains(response, 'Agregar proceso de secado')
        self.assertContains(response, 'Supervisor / responsable')

        detalle = self.client.get(reverse(
            'secado_detalle',
            kwargs={'registro_id': registro.pk},
        ))
        self.assertEqual(detalle.status_code, 200)
        self.assertContains(detalle, 'Proceso de secado #1')
        self.assertContains(detalle, 'ASR-20261014-0001')
        self.assertContains(detalle, '20/10/2026')
        self.assertContains(detalle, 'María Supervisora')
        self.assertContains(detalle, '1.000')
        self.assertNotContains(detalle, '1.000000000')

    def test_completa_ch_final_en_un_registro_guardado(self):
        self.client.post(reverse('secado_agregar'), self.datos_registro([
            {'id': self.paquete_uno.pk, 'ch_final': ''},
            {'id': self.paquete_dos.pk, 'ch_final': ''},
        ]))
        registro = SecadoRegistro.objects.get()
        url = reverse('secado_editar', kwargs={'registro_id': registro.pk})
        paquete_tres = self.crear_paquete(
            codigo='ASR-20261014-0003',
            consecutivo=3,
            ch_estimado=16,
        )

        formulario = self.client.get(url)
        self.assertEqual(formulario.status_code, 200)
        self.assertContains(formulario, 'Completar registro de secado')
        self.assertContains(formulario, 'Código ID del paquete')
        self.assertContains(formulario, 'Agregar paquete')

        response = self.client.post(url, self.datos_registro([
            {'id': self.paquete_uno.pk, 'ch_final': '10'},
            {'id': self.paquete_dos.pk, 'ch_final': '20'},
            {'id': paquete_tres.pk, 'ch_final': ''},
        ]))

        self.assertRedirects(response, reverse('secado'))
        self.assertEqual(registro.paquetes.count(), 3)
        self.assertEqual(
            registro.paquetes.get(paquete=paquete_tres).ch_final,
            None,
        )
        response = self.client.get(reverse('secado'))
        self.assertEqual(response.context['registros'][0].promedio_final, Decimal('15'))

    def test_no_guarda_codigos_inexistentes_ni_paquetes_duplicados(self):
        for paquetes in (
            [{'id': 999999, 'ch_final': ''}],
            [
                {'id': self.paquete_uno.pk, 'ch_final': ''},
                {'id': self.paquete_uno.pk, 'ch_final': ''},
            ],
        ):
            response = self.client.post(
                reverse('secado_agregar'),
                self.datos_registro(paquetes),
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(SecadoRegistro.objects.exists())
            self.assertFalse(SecadoPaquete.objects.exists())

    def test_no_guarda_secado_anterior_a_la_fecha_de_aserrio(self):
        datos = self.datos_registro([
            {'id': self.paquete_uno.pk, 'ch_final': ''},
        ])
        datos['fecha_inicio'] = '2026-10-13'

        response = self.client.post(reverse('secado_agregar'), datos)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'fue creado el 14/10/2026')
        self.assertContains(response, 'package-dialog')
        self.assertFalse(SecadoRegistro.objects.exists())
        self.assertFalse(SecadoPaquete.objects.exists())

    def test_no_guarda_paquetes_que_ya_finalizaron_secado(self):
        registro = SecadoRegistro.objects.create(
            fecha_inicio=date(2026, 10, 15),
            fecha_fin=date(2026, 10, 20),
            turno='turno_1',
            nombre_supervisor='Ana Supervisora',
        )
        SecadoPaquete.objects.create(registro=registro, paquete=self.paquete_uno)

        response = self.client.post(
            reverse('secado_agregar'),
            self.datos_registro([{'id': self.paquete_uno.pk, 'ch_final': ''}]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'El paquete {self.paquete_uno.codigo_paquete} ya está seco.')
        self.assertEqual(SecadoRegistro.objects.count(), 1)
        self.assertEqual(SecadoPaquete.objects.count(), 1)
