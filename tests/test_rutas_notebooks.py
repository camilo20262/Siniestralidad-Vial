import ast
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from src.rutas import ROOT, RAW_FILE, DATASET_FILE


class RutasTest(unittest.TestCase):
    def configuracion(self, name, cwd, override=None):
        notebook = json.loads((ROOT/'notebooks'/name).read_text())
        source = ''.join(next(c['source'] for c in notebook['cells'] if c['cell_type'] == 'code'))
        names = {'ROOT', 'RAW_FILE', 'PROCESSED_PATH', 'REPORTS_PATH', 'OUTPUT_FILE', 'DATA_FILE', 'MODELS_PATH'}
        tree = ast.parse(source)
        nodes = [node for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)]
        code = compile(ast.Module(body=nodes, type_ignores=[]), name, 'exec')
        scope = {'Path': Path, 'os': os}
        previous = Path.cwd()
        try:
            os.chdir(cwd)
            with patch.dict(os.environ, {}, clear=True):
                if override:
                    os.environ['SINIESTRALIDAD_ROOT'] = str(override)
                exec(code, scope)
        finally:
            os.chdir(previous)
        return scope

    def test_rutas_raiz_notebooks_y_directorio_externo(self):
        names = ['02_Comprension_de_los_Datos.ipynb', '03B_Preparacion_Datos_Con_Victimas.ipynb', '04B_Modelado_Con_Victimas.ipynb',
                 '04C_Ajuste_Hiperparametros_Con_Victimas.ipynb']
        with tempfile.TemporaryDirectory() as temp:
            for name in names:
                for cwd, override in [(ROOT, None), (ROOT/'notebooks', None), (Path(temp), ROOT)]:
                    with self.subTest(notebook=name, cwd=str(cwd)):
                        scope = self.configuracion(name, cwd, override)
                        self.assertEqual(scope['ROOT'], ROOT)
                        for key in ('DATA_FILE', 'OUTPUT_FILE'):
                            if key in scope:
                                self.assertEqual(scope[key], DATASET_FILE)
                        if 'RAW_FILE' in scope:
                            self.assertEqual(scope['RAW_FILE'], RAW_FILE)

    def test_copia_aislada_no_resuelve_original(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            (root/'src').mkdir()
            (root/'src/preparacion.py').touch()
            scope = self.configuracion('03B_Preparacion_Datos_Con_Victimas.ipynb', root)
            self.assertEqual(scope['ROOT'], root)
            self.assertNotEqual(scope['RAW_FILE'], RAW_FILE)

    def test_todas_las_celdas_principales_compilan(self):
        for name in ['03B', '04B', '04C', '05B']:
            path = next((ROOT/'notebooks').glob(name+'*.ipynb'))
            nb = json.loads(path.read_text())
            for i, cell in enumerate(nb['cells']):
                if cell['cell_type'] == 'code':
                    compile(''.join(cell['source']), f'{path.name}:{i}', 'exec')
