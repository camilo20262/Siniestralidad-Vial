import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import pandas as pd
import sklearn
import src.modelo_principal as module

REGISTRO = json.loads(module.REGISTRO.read_text())


class PipelineFalso:
    feature_names_in_ = np.array(REGISTRO['variables'])
    classes_ = np.array([0, 1])

    def __init__(self):
        self.named_steps = {'modelo': self}

    def get_params(self, deep=False):
        return REGISTRO['hiperparametros']

    def predict_proba(self, x):
        score = x.Mes.map({1: .5199, 2: .52, 3: .8}).to_numpy()
        return np.column_stack([1-score, score])


def entrada():
    data = pd.DataFrame(0., index=[9, 3, 7], columns=REGISTRO['variables'])
    for c, values in REGISTRO['categorias'].items():
        data[c] = values[0]
    data['Mes'] = [1, 2, 3]
    return data


class ModeloTest(unittest.TestCase):
    def setUp(self):
        self.modelo = module.ModeloPrincipal(PipelineFalso(), copy.deepcopy(REGISTRO))

    def test_umbral_inclusivo_y_conservacion_indice(self):
        result = self.modelo.predecir(entrada())
        self.assertEqual(result.Alerta_Modelo.tolist(), [0, 1, 1])
        self.assertEqual(result.index.tolist(), [9, 3, 7])

    def test_orden_filas_y_columnas_extra(self):
        data = entrada()
        pd.testing.assert_frame_equal(self.modelo.predecir(data.iloc[::-1]), self.modelo.predecir(data).iloc[::-1])
        pd.testing.assert_frame_equal(self.modelo.predecir(data.assign(Alto_Riesgo=99)), self.modelo.predecir(data))

    def test_rechaza_entradas_invalidas(self):
        x = entrada()
        invalidas = [None, x.iloc[:0], x.drop(columns='Mes'), x.assign(Mes=0), x.assign(Mes=1.5),
                     x.assign(Mes='1'), x.assign(Es_Festivo=2), x.assign(Localidad='INEXISTENTE'),
                     x.assign(Accidentes_Prom_7d=np.nan), x.assign(Accidentes_Prom_7d=np.inf),
                     x.assign(Accidentes_Prom_7d=-1), pd.concat([x, x[['Mes']]], axis=1)]
        for n, data in enumerate(invalidas):
            with self.subTest(caso=n), self.assertRaises(ValueError):
                self.modelo.predecir(data)

    def test_rechaza_salida_invalida_pipeline(self):
        for output in [np.ones((3, 1)), np.full((3, 2), np.nan), np.full((3, 2), 2)]:
            with self.subTest(), patch.object(self.modelo.pipeline, 'predict_proba', return_value=output), self.assertRaises(ValueError):
                self.modelo.predecir(entrada())

    def test_cargador_verifica_hash_antes_de_deserializar(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reg = copy.deepcopy(REGISTRO)
            reg['artefacto']['ruta'] = 'modelo.pkl'
            reg['artefacto']['sha256'] = '0'*64
            (root/'modelo.pkl').write_bytes(b'no es un modelo')
            path = root/'registro.json'
            path.write_text(json.dumps(reg))
            with patch.object(module, 'ROOT', root), patch.object(module, 'REGISTRO', path), patch.object(module.joblib, 'load') as load:
                with self.assertRaisesRegex(ValueError, 'cambió'):
                    module.cargar_modelo_principal()
                load.assert_not_called()

    def test_cargador_version_y_esquema(self):
        from hashlib import sha256
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reg = copy.deepcopy(REGISTRO)
            reg['artefacto'] = {'ruta': 'modelo.pkl', 'sha256': sha256(b'fixture').hexdigest()}
            (root/'modelo.pkl').write_bytes(b'fixture')
            path = root/'registro.json'
            path.write_text(json.dumps(reg))
            with patch.object(module, 'ROOT', root), patch.object(module, 'REGISTRO', path), patch.object(module.joblib, 'load', return_value=PipelineFalso()):
                self.assertIsInstance(module.cargar_modelo_principal(), module.ModeloPrincipal)
                with patch.object(module.sklearn, '__version__', '0.0'):
                    with self.assertRaises(RuntimeError):
                        module.cargar_modelo_principal()
                for attr, value in [('feature_names_in_', np.array(['incorrecta'])), ('classes_', np.array([1, 0]))]:
                    with patch.object(PipelineFalso, attr, value), self.assertRaises(ValueError):
                        module.cargar_modelo_principal()
                with patch.object(PipelineFalso, 'get_params', return_value={}), self.assertRaises(ValueError):
                    module.cargar_modelo_principal()
