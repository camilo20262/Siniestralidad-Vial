"""Controles del orquestador sin instalar entornos ni reentrenar."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from scripts import verificar_flujo_completo as flow
from scripts.verificar_dashboard_http import callback_payload


class FlujoCompletoTest(unittest.TestCase):
    def test_cadena_incluye_eda_y_no_precarga_resultados(self):
        self.assertTrue(flow.NAMES[0].startswith('02B'))
        self.assertEqual(flow.NAMES[1:], flow.chain.NAMES)
        for path in flow.EXTRA_INPUTS:
            self.assertFalse(path.startswith(('models/', 'reports/', 'data/processed/', 'data/dashboard/')))

    def test_rechaza_rutas_y_carpetas_existentes(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(flow, 'ROOT', Path(temporary)):
            for name in ['', '.', '..', '../salida', '/tmp/salida', 'otra/salida', 'otra\\salida']:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    flow.destination(name)
            path = flow.destination('ensayo')
            path.mkdir(parents=True)
            marker = path/'conservar.txt'
            marker.write_text('No sobrescribir')
            with self.assertRaises(FileExistsError):
                flow.destination('ensayo')
            self.assertEqual(marker.read_text(), 'No sobrescribir')

    def test_diferencias_tablas_parametros_o_seleccion_no_pasan(self):
        for field, item in [('tablas', {'equivalente': False}),
                            ('seleccion', {'coincidencias': {'umbral': False}}),
                            ('modelos', {'mismo_esquema': True, 'mismos_hiperparametros': False})]:
            result = {'tablas': [{'equivalente': True}],
                      'seleccion': [{'coincidencias': {'umbral': True}}],
                      'modelos': [{'mismo_esquema': True, 'mismos_hiperparametros': True}]}
            self.assertTrue(flow.equivalent(result))
            result[field] = [item]
            self.assertFalse(flow.equivalent(result))

    def test_callback_rechaza_contrato_incompleto(self):
        spec = {'outputs': {'id': 'page', 'property': 'children'},
                'inputs': [{'id': 'navigation', 'property': 'value'}], 'state': []}
        body = callback_payload('page.children', spec, ['query'])
        self.assertEqual(body['inputs'][0]['value'], 'query')
        self.assertEqual(body['changedPropIds'], ['navigation.value'])
        with self.assertRaises(ValueError):
            callback_payload('page.children', spec, [])
