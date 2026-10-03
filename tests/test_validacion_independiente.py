import json
import unittest

import numpy as np
import pandas as pd

from src.rutas import ROOT
from src.validacion_independiente import DisenoTemporal, etiquetar_desde_pasado, seleccionar_umbral


class ValidacionIndependienteTest(unittest.TestCase):
    def test_2022_no_participa_en_seleccion(self):
        design = DisenoTemporal()
        design.validar()
        self.assertEqual([year for _, year in design.cortes_seleccion], [2020, 2021])
        self.assertEqual(design.entrenamiento_evaluacion_hasta, 2021)
        self.assertEqual(design.anio_evaluacion, 2022)
        self.assertNotIn(design.anio_evaluacion, [year for _, year in design.cortes_seleccion])

    def test_etiqueta_de_validacion_depende_solo_del_pasado(self):
        train = pd.DataFrame({
            "Localidad": ["A"] * 6,
            "Franja_Horaria": ["Noche"] * 6,
            "Fecha_Acc": pd.date_range("2020-01-01", periods=6),
            "Num_Accidentes": [0, 0, 1, 1, 2, 4],
        })
        validation = pd.DataFrame({
            "Localidad": ["A", "A"],
            "Franja_Horaria": ["Noche", "Noche"],
            "Fecha_Acc": pd.to_datetime(["2021-01-01", "2021-01-02"]),
            "Num_Accidentes": [0, 99],
        })
        _, _, _, y_validation, thresholds = etiquetar_desde_pasado(train, validation)
        changed = validation.copy()
        changed["Num_Accidentes"] = [50, 100]
        _, _, _, _, changed_thresholds = etiquetar_desde_pasado(train, changed)
        pd.testing.assert_frame_equal(thresholds, changed_thresholds)
        self.assertEqual(y_validation.tolist(), [0, 1])

    def test_seleccion_umbral_maximiza_f1_sin_redondear_scores(self):
        y = np.array([0, 0, 1, 1])
        score = np.array([0.10, 0.51, 0.52, 0.90])
        threshold, table = seleccionar_umbral(y, score, thresholds=[0.50, 0.52, 0.55])
        self.assertEqual(threshold, 0.52)
        self.assertEqual(table.loc[table.Umbral.eq(0.52), "F1"].iloc[0], 1.0)

    def test_evidencia_congelada_declara_separacion(self):
        path = ROOT / "reports/validacion_independiente_victimas/resultado.json"
        self.assertTrue(path.is_file(), path)
        result = json.loads(path.read_text())
        self.assertEqual(result["estado"], "estimacion_adicional_completada")
        self.assertEqual(result["seleccion"]["anios_validacion"], [2020, 2021])
        self.assertEqual(result["evaluacion_separada"]["anio"], 2022)
        self.assertFalse(result["evaluacion_separada"]["participo_en_seleccion"])
        self.assertFalse(result["modelo_oficial_modificado"])


if __name__ == "__main__":
    unittest.main()
