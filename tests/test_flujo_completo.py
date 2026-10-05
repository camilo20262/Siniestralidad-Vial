"""Controles del orquestador sin instalar entornos ni reentrenar."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import nbformat
from scripts import verificar_flujo_completo as flow
from scripts.verificar_dashboard_http import callback_payload


class FlujoCompletoTest(unittest.TestCase):
    def test_setup_conserva_lista_notebooks_al_copiar_codigo(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for folder in ['notebooks', 'data/raw', 'scripts', 'src']:
                (root/folder).mkdir(parents=True)
            (root/'data/raw/base-anuario-de-siniestralidad-2024.xlsx').write_bytes(b'fixture')
            (root/'requirements.txt').write_text('')
            (root/'requirements-dev.txt').write_text('-r requirements.txt\n')
            (root/'scripts/verificar_modelo_principal.py').write_text('# fixture')
            (root/'src/rutas.py').write_text('# fixture')
            names = ['eda.ipynb', 'preparacion.ipynb']
            for name in names:
                nbformat.write(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell('1 + 1')]),
                               root/'notebooks'/name)
            run = root/'reports/reproducibilidad/ensayo'
            with patch.object(flow.chain, 'ROOT', root), \
                 patch.object(flow.chain.subprocess, 'check_output', return_value='fixture'), \
                 patch.object(flow.chain.venv.EnvBuilder, 'create', side_effect=RuntimeError('fin del fixture')):
                with self.assertRaisesRegex(RuntimeError, 'fin del fixture'):
                    flow.chain.setup(run, names=names)
            self.assertEqual(sorted(p.name for p in (run/'notebooks').iterdir()), names)
            self.assertEqual((run/'requirements-dev.txt').read_text(), '-r requirements.txt\n')
            for name in names:
                nb = nbformat.read(run/'notebooks'/name, as_version=4)
                self.assertEqual(nb.cells[0].source, '1 + 1')
                self.assertIsNone(nb.cells[0].execution_count)

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
