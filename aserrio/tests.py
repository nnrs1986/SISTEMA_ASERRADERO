from decimal import Decimal

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import PaqueteAserrioForm
from .models import PaqueteAserrio


class PaqueteAserrioFormTests(TestCase):
	def datos_validos(self):
		return {
			'fecha': '2026-10-14',
			'turno': 'turno_1',
			'nombre_supervisor': 'Ana Supervisor',
			'nombre_operador': 'Luis Operador',
			'especie_madera': 'pino',
			'tipo_rola': 'gruesa',
			'maquinas_proceso': ['sierra_principal', 'multiple_de_disco'],
			'incluye_recuperacion': 'False',
			'maquina_recuperacion': '',
			'largo': '2.000',
			'ancho': '0.500',
			'espesor': '0.100',
			'cantidad_piezas': '10',
			'ch_estimado': '12',
			'tipo_elemento': 'tabla',
			'calidad_visual': 'primera',
		}

	def test_requiere_exactamente_una_maquina_principal(self):
		datos = self.datos_validos()
		datos['maquinas_proceso'] = ['sierra_principal', 'sierra_doble']
		form = PaqueteAserrioForm(data=datos)

		self.assertFalse(form.is_valid())
		self.assertIn('maquinas_proceso', form.errors)

	def test_rechaza_dimensiones_con_mas_de_tres_decimales(self):
		datos = self.datos_validos()
		datos['largo'] = '2.0001'
		form = PaqueteAserrioForm(data=datos)

		self.assertFalse(form.is_valid())
		self.assertIn('largo', form.errors)

	def test_recuperacion_requiere_seleccionar_maquina(self):
		datos = self.datos_validos()
		datos['incluye_recuperacion'] = 'True'
		form = PaqueteAserrioForm(data=datos)

		self.assertFalse(form.is_valid())
		self.assertIn('maquina_recuperacion', form.errors)

	def test_acepta_ch_estimado_entero_mayor_a_cien(self):
		datos = self.datos_validos()
		datos['ch_estimado'] = '125'
		form = PaqueteAserrioForm(data=datos)

		self.assertTrue(form.is_valid(), form.errors)

	def test_muestra_ficha_de_captura(self):
		usuario = get_user_model().objects.create_user(username='capturista', password='clave-segura')
		self.client.force_login(usuario)
		response = self.client.get(reverse('aserrio_crear'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Máquinas en el proceso')
		self.assertContains(response, '¿Incluye recuperación de madera?')
		self.assertContains(response, 'm³ por pieza')
		self.assertContains(response, 'Volumen total (m³)')
		self.assertContains(response, 'id="id_incluye_recuperacion_1" checked')
		campo_maquinas = PaqueteAserrioForm()['maquinas_proceso']
		self.assertEqual(str(campo_maquinas).count('type="checkbox"'), len(PaqueteAserrio.MAQUINAS_CHOICES))
		self.assertIsInstance(campo_maquinas.field.widget, forms.CheckboxSelectMultiple)
		self.assertEqual(PaqueteAserrioForm().fields['turno'].widget.attrs['class'], 'form-control')
		self.assertEqual(PaqueteAserrioForm().fields['m3_pieza'].initial, '0')
		self.assertEqual(PaqueteAserrioForm().fields['volumen_total'].initial, '0')

	def test_guarda_volumenes_y_consecutivo_diario(self):
		usuario = get_user_model().objects.create_user(username='operador', password='clave-segura')
		self.client.force_login(usuario)
		url = reverse('aserrio_crear')

		for consecutivo in (1, 2):
			response = self.client.post(url, self.datos_validos())
			self.assertEqual(response.status_code, 302)
			paquete = PaqueteAserrio.objects.get(consecutivo_diario=consecutivo)
			self.assertEqual(paquete.codigo_paquete, f'ASR-20261014-{consecutivo:04d}')
			self.assertEqual(paquete.m3_pieza, Decimal('0.100000000'))
			self.assertEqual(paquete.volumen_total, Decimal('1.000000000'))
			self.assertRedirects(
				response,
				reverse('aserrio_paquete', kwargs={'codigo_paquete': paquete.codigo_paquete}),
			)

		paquete = PaqueteAserrio.objects.get(consecutivo_diario=1)
		listado = self.client.get(reverse('aserrio'))
		self.assertEqual(listado.status_code, 200)
		self.assertContains(listado, 'Paquetes registrados (2)')
		self.assertContains(listado, paquete.codigo_paquete)
		self.assertContains(listado, '1.000')
		self.assertNotContains(listado, '1.000000000')

		detalle = self.client.get(
			reverse('aserrio_paquete', kwargs={'codigo_paquete': paquete.codigo_paquete}),
		)
		self.assertEqual(detalle.status_code, 200)
		self.assertContains(detalle, 'Código de barras del paquete')
		self.assertContains(detalle, '<svg')
		self.assertContains(detalle, 'ASR-20261014-0001')
		self.assertContains(detalle, 'Información completa del paquete')
		self.assertContains(detalle, '0.100')
		self.assertNotContains(detalle, '1.000000000')

		busqueda = self.client.get(reverse('aserrio_buscar_paquete'), {
			'codigo_paquete': paquete.codigo_paquete.lower(),
		})
		self.assertRedirects(
			busqueda,
			reverse('aserrio_paquete', kwargs={'codigo_paquete': paquete.codigo_paquete}),
		)

	def test_edita_paquete_existente_conservando_codigo_y_marcando_edicion(self):
		usuario = get_user_model().objects.create_user(username='editor', password='clave-segura')
		self.client.force_login(usuario)
		crear = self.client.post(reverse('aserrio_crear'), self.datos_validos())
		self.assertEqual(crear.status_code, 302)
		paquete = PaqueteAserrio.objects.get()
		codigo_original = paquete.codigo_paquete
		fecha_registro_original = paquete.fecha_registro
		url_editar = reverse('aserrio_editar', kwargs={'codigo_paquete': codigo_original})

		formulario = self.client.get(url_editar)
		self.assertEqual(formulario.status_code, 200)
		self.assertContains(formulario, 'Guardar cambios')
		self.assertContains(formulario, 'value="2.000"')

		datos = self.datos_validos()
		datos['largo'] = '3.000'
		datos['cantidad_piezas'] = '8'
		response = self.client.post(url_editar, datos)

		self.assertRedirects(
			response,
			reverse('aserrio_paquete', kwargs={'codigo_paquete': codigo_original}),
		)
		paquete.refresh_from_db()
		self.assertEqual(paquete.codigo_paquete, codigo_original)
		self.assertEqual(paquete.consecutivo_diario, 1)
		self.assertEqual(paquete.fecha_registro, fecha_registro_original)
		self.assertEqual(paquete.largo, Decimal('3.000'))
		self.assertEqual(paquete.m3_pieza, Decimal('0.150000000'))
		self.assertEqual(paquete.volumen_total, Decimal('1.200000000'))
		self.assertIsNotNone(paquete.fecha_edicion)

		detalle = self.client.get(
			reverse('aserrio_paquete', kwargs={'codigo_paquete': codigo_original}),
		)
		self.assertContains(detalle, 'Este paquete fue editado el')
		self.assertContains(detalle, codigo_original)
		listado = self.client.get(reverse('aserrio'))
		self.assertContains(listado, 'Editado')
		self.assertContains(listado, reverse('aserrio_editar', kwargs={'codigo_paquete': codigo_original}))
