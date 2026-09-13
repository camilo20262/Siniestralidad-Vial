import unittest
import numpy as np
import pandas as pd
from src.evaluacion_referencias import tasa_historica, etiquetar_corte, bootstrap_pareado


class ReferenciasTest(unittest.TestCase):
    def setUp(self):
        self.train = pd.DataFrame({'Fecha_Acc': pd.date_range('2020-01-01', periods=4),
                                   'Localidad': ['A'] * 4, 'Franja_Horaria': ['Noche'] * 4,
                                   'Num_Accidentes': [0, 0, 1, 3], 'Alto_Riesgo': [0, 0, 0, 1]})
        self.test = pd.DataFrame({'Fecha_Acc': pd.date_range('2021-01-01', periods=2),
                                  'Localidad': ['B', 'A'], 'Franja_Horaria': ['Noche'] * 2,
                                  'Num_Accidentes': [0, 2], 'Alto_Riesgo': [1, 1]}, index=[9, 3])

    def test_futuro_no_interviene_y_grupo_nuevo_usa_global(self):
        a, _, n = tasa_historica(self.train, self.test, ['Localidad'])
        b, _, _ = tasa_historica(self.train, self.test.drop(columns='Alto_Riesgo'), ['Localidad'])
        np.testing.assert_array_equal(a, [.25, .25]); np.testing.assert_array_equal(a, b)
        self.assertEqual(n, 1)

    def test_corte_temporal_obligatorio(self):
        with self.assertRaises(ValueError): tasa_historica(self.test, self.train, [])

    def test_etiqueta_cuantil_y_estrictamente_mayor(self):
        futuro = self.test.assign(Localidad='A', Num_Accidentes=[1, 2])
        a, b, _ = etiquetar_corte(self.train, futuro)
        self.assertEqual(a.Alto_Riesgo.tolist(), [0, 0, 0, 1])
        self.assertEqual(b.Alto_Riesgo.tolist(), [0, 1])

    def test_orden_no_se_pierde(self):
        tr = self.train.copy(); tr['Localidad'] = ['A', 'A', 'B', 'B']
        score, _, _ = tasa_historica(tr, self.test, ['Localidad'])
        np.testing.assert_array_equal(score, [.5, 0])

    def test_bootstrap_identico_cero_y_reproducible(self):
        dates = pd.date_range('2023-01-01', periods=28).repeat(2)
        y = np.tile([0, 1], 28); s = np.tile([.2, .8], 28)
        a, r = bootstrap_pareado(dates, y, s, s, repeticiones=10)
        b, rr = bootstrap_pareado(dates, y, s, s, repeticiones=10)
        self.assertTrue((a[['Diferencia_A_Menos_B', 'P025', 'P975']] == 0).all().all())
        pd.testing.assert_frame_equal(a, b); pd.testing.assert_frame_equal(r, rr)

    def test_score_invalido(self):
        with self.assertRaises(ValueError):
            bootstrap_pareado(pd.date_range('2020-01-01', periods=14), [0, 1]*7, [2]*14, [.5]*14)


if __name__ == '__main__':
    unittest.main()
