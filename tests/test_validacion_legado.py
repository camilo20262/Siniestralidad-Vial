"""Control de regresión de la anulación metodológica de 04, sin entrenar."""
import ast
import json
import unittest

from src.rutas import ROOT


class ValidacionLegadoTest(unittest.TestCase):
    def setUp(self):
        self.notebook = json.loads((ROOT / 'notebooks/04_Modelado.ipynb').read_text())

    def test_no_hay_validadores_aleatorios_ejecutables(self):
        banned = {'StratifiedKFold', 'KFold', 'ShuffleSplit', 'StratifiedShuffleSplit',
                  'train_test_split', 'cross_validate', 'cross_val_score'}
        for index, cell in enumerate(self.notebook['cells']):
            if cell['cell_type'] != 'code':
                continue
            source = ''.join(cell['source'])
            tree = ast.parse(source)
            compile(tree, f'04_Modelado:{index}', 'exec')
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
            imports = {alias.name for node in ast.walk(tree)
                       if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
            attrs = {node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
            self.assertFalse(banned & (names | imports | attrs))

    def test_seccion_anulada_no_conserva_salidas_ni_codigo(self):
        section = self.notebook['cells'][28:34]
        for cell in section:
            self.assertEqual(cell['cell_type'], 'markdown')
            self.assertNotIn('outputs', cell)
        text = '\n'.join(''.join(cell['source']) for cell in section)
        self.assertIn('ANULADA', text)
        self.assertIn('No es un holdout intacto', text)
        self.assertNotIn('0.3807', text)
        self.assertNotIn('0.3987', text)

    def test_referencias_temporales_y_autoridad_existen(self):
        for path in ['notebooks/05_Evaluacion.ipynb',
                     'models/victimas/modelo_principal.json',
                     'reports/correcciones/04_validacion_aleatoria_anulada.md',
                     'reports/evaluation/validacion_temporal_2018_2022_detalle.csv',
                     'reports/evaluation/validacion_temporal_2018_2022_resumen.csv',
                     'reports/evaluation/predicciones_validacion_temporal_2020_2022.parquet',
                     'reports/evaluation/10_validacion_temporal_2018_2022.png']:
            self.assertTrue((ROOT / path).is_file(), path)


if __name__ == '__main__':
    unittest.main()
