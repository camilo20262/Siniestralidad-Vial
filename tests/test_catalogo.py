"""Impide que el catálogo vigente pierda rutas o apunte al modelo base."""
import json
import unittest
import pandas as pd
from src.rutas import ROOT


class CatalogoTest(unittest.TestCase):
    def setUp(self):
        self.catalogo = json.loads((ROOT/'config/artefactos.json').read_text())

    def test_rutas_catalogadas_existen(self):
        def rutas(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key != 'politica':
                        yield from rutas(child)
            elif isinstance(value, list):
                for child in value:
                    yield from rutas(child)
            elif isinstance(value, str) and value.startswith(('models/', 'data/', 'reports/', 'notebooks/')):
                yield value
        for path in rutas(self.catalogo):
            with self.subTest(path=path):
                self.assertTrue((ROOT/path).exists(), path)

    def test_principal_coincide_con_registro_y_no_con_alias_base(self):
        registro = json.loads((ROOT/self.catalogo['autoridad_modelo']).read_text())
        principal = self.catalogo['principal']
        self.assertEqual(principal['pipeline'], registro['artefacto']['ruta'])
        self.assertEqual(principal['dataset'], registro['datos']['ruta'])
        self.assertEqual(principal['estado'], 'vigente')
        self.assertNotIn(principal['pipeline'], self.catalogo['referencia_base_no_principal']['artefactos'])
        self.assertFalse(set(principal['notebooks']) & set(self.catalogo['legacy_todos_los_siniestros']['notebooks']))

    def test_cada_modelo_tiene_estado_inequivoco(self):
        models = self.catalogo['modelos']
        self.assertGreaterEqual(len(models), 7)
        self.assertEqual(models['rf_ajustado_victimas']['estado'], 'vigente')
        self.assertEqual(models['rf_ajustado_victimas']['umbral_score'], 0.52)
        self.assertEqual(models['rf_base_victimas']['estado'], 'historico')
        self.assertEqual(models['rf_base_victimas']['umbral_score'], 0.55)
        self.assertEqual({value['estado'] for value in models.values()}, {'vigente', 'historico'})
        self.assertEqual(sum(value['estado'] == 'vigente' for value in models.values()), 1)

    def test_portadas_de_legado_y_evidencia_ejecutada(self):
        self.assertIn('PORTADA DE LEGADO', (ROOT/'models/README.md').read_text())
        self.assertTrue((ROOT/'legacy/README.md').is_file())
        for name in ['03_Preparacion_de_los_Datos (3).ipynb', '04_Modelado.ipynb', '05_Evaluacion.ipynb']:
            notebook = json.loads((ROOT/'notebooks'/name).read_text())
            first = ''.join(notebook['cells'][0]['source'])
            with self.subTest(name=name):
                self.assertIn('LEGADO', first)
        for name, expected in [('03B_Preparacion_Datos_Con_Victimas.ipynb', '9/9'),
                               ('04B_Modelado_Con_Victimas.ipynb', '12/12')]:
            notebook = json.loads((ROOT/'notebooks'/name).read_text())
            first = ''.join(notebook['cells'][0]['source'])
            with self.subTest(name=name):
                self.assertIn('flujo_completo_20261001_02/notebooks', first)
                self.assertIn(expected, first)

    def test_especificacion_vigente_distingue_umbral_principal_y_base(self):
        registro = json.loads((ROOT/self.catalogo['autoridad_modelo']).read_text())
        spec = (ROOT/'docs/ESPECIFICACION_VIGENTE.md').read_text()
        self.assertEqual(registro['id_modelo'], 'rf_victimas_bogota_v1.0')
        self.assertEqual(registro['decision']['umbral_score'], 0.52)
        self.assertEqual(registro['decision']['operador'], '>=')
        self.assertEqual(registro['referencia_base']['umbral_score'], 0.55)
        self.assertIn(registro['id_modelo'], spec)
        self.assertIn(registro['artefacto']['ruta'], spec)
        self.assertIn(registro['referencia_base']['artefacto'], spec)
        self.assertIn('ESP-MODELO-01', spec)
        self.assertIn('**0,52**', spec)
        self.assertIn('**0,55**', spec)
        decision = (ROOT/'docs/decisiones/umbral_modelo.md').read_text()
        self.assertIn('DEC-UMB-01', decision)
        self.assertIn('TODO institucional', decision)
        self.assertIn('0,3577', decision)
        thresholds = pd.read_csv(ROOT/'reports/tuning_victimas/seleccion_umbral.csv')
        row_052 = thresholds.iloc[(thresholds.Umbral - 0.52).abs().argmin()]
        row_055 = thresholds.iloc[(thresholds.Umbral - 0.55).abs().argmin()]
        self.assertGreater(row_052.F1, row_055.F1)
        self.assertGreater(row_052.Recall, row_055.Recall)
        self.assertLess(row_052.Precision, row_055.Precision)
        metadata = json.loads((ROOT/registro['referencia_base']['metadata']).read_text())
        self.assertAlmostEqual(metadata['umbral_candidato'], 0.55)

    def test_procedencia_entornos_distingue_declaracion_y_reproduccion(self):
        nota = (ROOT/'docs/PROCEDENCIA_ENTORNOS_MODELOS.md').read_text()
        ensayo = ROOT/'reports/reproducibilidad/ejecucion_20260913'
        resultado = json.loads((ensayo/'resultado.json').read_text())
        entorno = json.loads((ensayo/'entorno.json').read_text())
        for seleccion in resultado['seleccion']:
            metadata = json.loads((ROOT/'models/victimas'/seleccion['archivo']).read_text())
            with self.subTest(archivo=seleccion['archivo']):
                self.assertEqual(metadata['version_python'], seleccion['python_oficial'])
                self.assertEqual(entorno['python'].split()[0], seleccion['python_reproduccion'])
                self.assertIn(metadata['version_python'], nota)
        self.assertIn('no versión del intérprete', nota)
        self.assertIn('no compatibilidad', nota)
        for documento in ('README.md', 'models/victimas/README.md',
                          'reports/reproducibilidad/README.md'):
            self.assertIn('docs/PROCEDENCIA_ENTORNOS_MODELOS.md', (ROOT/documento).read_text())
