import unittest
import copy
from unittest.mock import patch
import pandas as pd
import src.consulta_retrospectiva as module
from src.consulta_retrospectiva import ConsultaRetrospectiva
from src.modelo_principal import ModeloPrincipal
from test_modelo_principal import PipelineFalso, REGISTRO, entrada


class ConsultaTest(unittest.TestCase):
    def setUp(self):
        self.data = entrada().assign(Fecha_Acc=['2023-01-01', '2023-01-02', '2023-01-03'],
                                     Periodo='test', Num_Accidentes=999, Alto_Riesgo=1)
        self.consulta = ConsultaRetrospectiva(ModeloPrincipal(PipelineFalso(), REGISTRO), self.data)
        self.loc, self.slot = self.data.iloc[0][['Localidad', 'Franja_Horaria']]

    def test_consulta_score_y_antecedentes_sin_filtrar_resultado_observado(self):
        result = self.consulta.consultar('2023-01-02', self.loc, self.slot)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.Score_Priorizacion.iloc[0], .52)
        self.assertEqual(result.Alerta_Modelo.iloc[0], 1)
        self.assertIn('Accidentes_Prom_7d', result)
        self.assertNotIn('Num_Accidentes', result)
        self.assertNotIn('Alto_Riesgo', result)

    def test_no_admite_futuro_fechas_invalidas_o_grupos_nuevos(self):
        for date, loc, slot in [('2026-01-01', self.loc, self.slot), ('2022-12-31', self.loc, self.slot),
                                ('no-fecha', self.loc, self.slot), (pd.NaT, self.loc, self.slot),
                                ('2023-01-02 01:00', self.loc, self.slot),
                                ('2023-01-02T00:00:00Z', self.loc, self.slot),
                                ('2023-01-02', 'ZZZ', self.slot), ('2023-01-02', self.loc, 'ZZZ')]:
            with self.subTest(date=date), self.assertRaises(ValueError):
                self.consulta.consultar(date, loc, slot)

    def test_rechaza_duplicados(self):
        self.consulta.datos = pd.concat([self.data, self.data])
        with self.assertRaises(ValueError):
            self.consulta.consultar('2023-01-02', self.loc, self.slot)

    def test_rechaza_fecha_ambigua(self):
        for date in ['01/02/2023', '2023/01/02', '2023-1-2', '20230102']:
            with self.subTest(date=date), self.assertRaisesRegex(ValueError, 'AAAA-MM-DD'):
                self.consulta.consultar(date, self.loc, self.slot)

    def test_cargador_rechaza_dataset_alterado_antes_de_leerlo(self):
        modelo = ModeloPrincipal(PipelineFalso(), copy.deepcopy(REGISTRO))
        with patch.object(module, 'cargar_modelo_principal', return_value=modelo), \
             patch.object(module, 'sha256_archivo', return_value='hash_distinto'), \
             patch.object(module.pd, 'read_parquet') as read:
            with self.assertRaisesRegex(ValueError, 'versión registrada'):
                module.cargar_consulta()
            read.assert_not_called()

    def test_cargador_acepta_integridad_y_rechaza_claves_duplicadas(self):
        modelo = ModeloPrincipal(PipelineFalso(), copy.deepcopy(REGISTRO))
        with patch.object(module, 'cargar_modelo_principal', return_value=modelo), \
             patch.object(module, 'sha256_archivo', return_value=REGISTRO['datos']['sha256']), \
             patch.object(module.pd, 'read_parquet', return_value=self.data) as read:
            self.assertIsInstance(module.cargar_consulta(), ConsultaRetrospectiva)
            read.return_value = pd.concat([self.data, self.data])
            with self.assertRaisesRegex(ValueError, 'duplicadas'):
                module.cargar_consulta()
