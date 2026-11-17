from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import RolaForm


class RolaFormTests(TestCase):
	def datos_formulario(self, **cambios):
		datos = {
			'fecha': '2026-09-30',
			'numero_guia': 'GUIA-001',
			'metros_estereos': '12.50',
			'metros_cubicos_rola': '8.25',
			'tipo_madera_especie': 'pino',
			'tipo_madera': 'mediana',
			'empresa_vendedora': 'Proveedor de prueba',
			'empresa_comercializadora': 'Comercializadora de prueba',
			'cantidad_rolas_estimacion': '20',
			'placa_carro': 'ABC-123',
			'color_carro': 'Verde',
			'nombre_chofer': 'Chofer de prueba',
			'nombre_supervisor': 'Supervisor de prueba',
			'largo_camion': '6.00',
			'ancho_camion': '2.40',
			'altura_camion': '2.20',
			'cantidad_cargas': '1',
			'metros_estereos_verificacion': '0.01',
			'cantidad_rolas_verificacion': '18',
			'clasificacion_visual': 'buena',
			'metros_cubicos_verificacion': '0.01',
		}
		datos.update(cambios)
		return datos

	def test_guarda_campos_de_ingreso_y_verificacion(self):
		form = RolaForm(data=self.datos_formulario())

		self.assertTrue(form.is_valid(), form.errors)
		rola = form.save()

		self.assertEqual(rola.empresa_comercializadora, 'Comercializadora de prueba')
		self.assertEqual(rola.color_carro, 'Verde')
		self.assertEqual(rola.cantidad_rolas_estimacion, 20)
		self.assertEqual(rola.cantidad_cargas, 1)
		self.assertEqual(rola.clasificacion_visual, 'buena')
		self.assertEqual(str(rola.metros_estereos_verificacion), '31.68')
		self.assertEqual(str(rola.metros_cubicos_verificacion), '19.01')

	def test_verificacion_interna_usa_el_factor_de_cada_tipo_de_madera(self):
		resultados_esperados = {
			'leña': ('31.68', '15.84'),
			'fina': ('31.68', '17.42'),
			'mediana': ('31.68', '19.01'),
			'gruesa': ('31.68', '20.59'),
		}

		for tipo_madera, resultados in resultados_esperados.items():
			with self.subTest(tipo_madera=tipo_madera):
				form = RolaForm(data=self.datos_formulario(
					numero_guia=f'GUIA-{tipo_madera}',
					tipo_madera=tipo_madera,
					metros_estereos_verificacion='0.01',
					metros_cubicos_verificacion='0.01',
				))

				self.assertTrue(form.is_valid(), form.errors)
				rola = form.save()
				self.assertEqual(
					str(rola.metros_estereos_verificacion),
					resultados[0],
				)
				self.assertEqual(
					str(rola.metros_cubicos_verificacion),
					resultados[1],
				)

	def test_verificacion_interna_multiplica_el_resultado_por_cantidad_de_cargas(self):
		form = RolaForm(data=self.datos_formulario(
			cantidad_cargas='3',
			metros_estereos_verificacion='0.01',
			metros_cubicos_verificacion='0.01',
		))

		self.assertTrue(form.is_valid(), form.errors)
		rola = form.save()

		self.assertEqual(str(rola.metros_estereos_verificacion), '31.68')
		self.assertEqual(str(rola.metros_cubicos_verificacion), '19.01')

	def test_verificacion_interna_calcula_el_resultado_esperado_para_tres_cargas(self):
		form = RolaForm(data=self.datos_formulario(
			largo_camion='12.00',
			ancho_camion='2.40',
			altura_camion='2.10',
			cantidad_cargas='3',
			metros_estereos_verificacion='0.01',
			metros_cubicos_verificacion='0.01',
		))

		self.assertTrue(form.is_valid(), form.errors)
		rola = form.save()

		self.assertEqual(str(rola.metros_estereos_verificacion), '60.48')
		self.assertEqual(str(rola.metros_cubicos_verificacion), '36.29')

	def test_metros_cubicos_multiplica_metros_estereos_solo_por_factor(self):
		resultados_esperados = {
			'leña': '15.84',
			'fina': '17.42',
			'mediana': '19.01',
			'gruesa': '20.59',
		}

		for tipo_madera, resultado_esperado in resultados_esperados.items():
			with self.subTest(tipo_madera=tipo_madera):
				form = RolaForm(data=self.datos_formulario(
					numero_guia=f'GUIA-M3-{tipo_madera}',
					tipo_madera=tipo_madera,
					cantidad_cargas='3',
				))

				self.assertTrue(form.is_valid(), form.errors)
				rola = form.save()
				self.assertEqual(
					str(rola.metros_cubicos_verificacion),
					resultado_esperado,
				)

	def test_verificacion_interna_no_calcula_sin_cantidad_de_cargas_valida(self):
		for cantidad_cargas in ('', '0'):
			with self.subTest(cantidad_cargas=cantidad_cargas):
				form = RolaForm(data=self.datos_formulario(
					numero_guia=f'GUIA-CARGAS-{cantidad_cargas or "VACIA"}',
					cantidad_cargas=cantidad_cargas,
				))

				self.assertTrue(form.is_valid(), form.errors)
				rola = form.save()
				self.assertIsNone(rola.metros_estereos_verificacion)
				self.assertIsNone(rola.metros_cubicos_verificacion)

	def test_formulario_de_alta_muestra_campos_nuevos(self):
		usuario = get_user_model().objects.create_user(username='capturista', password='clave-prueba')
		self.client.force_login(usuario)

		respuesta = self.client.get(reverse('rola_crear'))

		self.assertEqual(respuesta.status_code, 200)
		self.assertContains(respuesta, 'Empresa Comercializadora')
		self.assertContains(respuesta, 'Color del Carro')
		self.assertContains(respuesta, 'Cantidad de Cargas')
		self.assertContains(respuesta, 'Clasificación Visual')
		self.assertContains(respuesta, 'cantidadCargas.addEventListener')
		self.assertContains(respuesta, 'id="id_otra_especie"')
		self.assertContains(respuesta, 'disabled')
		self.assertContains(respuesta, 'id="id_metros_estereos_verificacion"')
		self.assertContains(respuesta, 'id="id_metros_cubicos_verificacion"')
		self.assertEqual(
			RolaForm().fields['metros_estereos_verificacion'].widget.attrs['readonly'],
			'readonly',
		)
		self.assertEqual(
			RolaForm().fields['metros_cubicos_verificacion'].widget.attrs['readonly'],
			'readonly',
		)

	def test_campo_otra_especie_se_habilita_solo_para_otro(self):
		usuario = get_user_model().objects.create_user(username='capturista', password='clave-prueba')
		self.client.force_login(usuario)
		form = RolaForm()
		campo = form.fields['otra_especie']

		self.assertTrue(campo.widget.attrs['disabled'])
		self.assertFalse(campo.disabled)
		self.assertContains(
			self.client.get(reverse('rola_crear')),
			"otraEspecie.disabled = especie.value !== 'otro';",
		)

	def test_mixta_historica_solo_aparece_al_editar(self):
		rola = RolaForm(data=self.datos_formulario()).save()
		rola.tipo_madera = 'mixta'
		rola.save(update_fields=['tipo_madera'])

		formulario_edicion = RolaForm(instance=rola)
		opciones_edicion = dict(formulario_edicion.fields['tipo_madera'].choices)
		opciones_alta = dict(RolaForm().fields['tipo_madera'].choices)

		self.assertIn('mixta', opciones_edicion)
		self.assertNotIn('mixta', opciones_alta)

	def test_especie_otro_se_guarda_y_se_ofrece_en_siguientes_formularios(self):
		form = RolaForm(data=self.datos_formulario(
			numero_guia='GUIA-002',
			tipo_madera_especie='otro',
			otra_especie='Roble rojo',
		))

		self.assertTrue(form.is_valid(), form.errors)
		rola = form.save()

		siguiente_formulario = RolaForm()
		opciones = dict(siguiente_formulario.fields['tipo_madera_especie'].choices)
		self.assertEqual(rola.tipo_madera_especie, 'Roble rojo')
		self.assertIn('Roble rojo', opciones)

	def test_especie_guardada_se_puede_seleccionar_sin_especificarla_de_nuevo(self):
		RolaForm(data=self.datos_formulario(
			tipo_madera_especie='otro',
			otra_especie='Roble rojo',
		)).save()
		form = RolaForm(data=self.datos_formulario(
			numero_guia='GUIA-003',
			tipo_madera_especie='Roble rojo',
		))

		self.assertTrue(form.is_valid(), form.errors)
		self.assertEqual(form.cleaned_data['tipo_madera_especie'], 'Roble rojo')

	def test_clasificacion_visual_usa_opciones_de_calidad(self):
		form = RolaForm(data=self.datos_formulario(clasificacion_visual='excelente'))

		self.assertTrue(form.is_valid(), form.errors)
		self.assertEqual(
			list(form.fields['clasificacion_visual'].choices)[1:],
			[
				('mala', 'Mala'),
				('regular', 'Regular'),
				('buena', 'Buena'),
				('excelente', 'Excelente'),
			],
		)
		self.assertEqual(form.save().clasificacion_visual, 'excelente')

	def test_edicion_conserva_clasificacion_visual_anterior(self):
		rola = RolaForm(data=self.datos_formulario()).save()
		rola.clasificacion_visual = 'mediana'
		rola.save(update_fields=['clasificacion_visual'])

		form = RolaForm(instance=rola)

		self.assertIn(
			('mediana', 'Mediana (registro anterior)'),
			form.fields['clasificacion_visual'].choices,
		)

	def test_detalle_muestra_resultados_de_verificacion(self):
		rola = RolaForm(data=self.datos_formulario()).save()
		usuario = get_user_model().objects.create_user(username='supervisor', password='clave-prueba')
		self.client.force_login(usuario)

		respuesta = self.client.get(reverse('rola_detalle', args=[rola.pk]))

		self.assertEqual(respuesta.status_code, 200)
		self.assertContains(respuesta, 'mE verificados')
		self.assertContains(respuesta, 'm³ verificados')
		self.assertContains(respuesta, 'Comercializadora de prueba')
