import unittest
import copy
import io
import json
import runpy
from contextlib import redirect_stdout
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

    def test_cada_resultado_conserva_trazabilidad_al_serializar(self):
        for fecha in self.data.Fecha_Acc:
            with self.subTest(fecha=fecha):
                result = self.consulta.consultar(fecha, self.loc, self.slot)
                row = json.loads(result.to_json(orient='records'))[0]
                self.assertEqual(row['Id_Modelo'], REGISTRO['id_modelo'])
                self.assertEqual(row['Version_Modelo'], REGISTRO['version'])
                self.assertIsInstance(row['Version_Modelo'], str)
                self.assertEqual(row['Tipo_Evaluacion'], 'retrospectiva')
                self.assertEqual(row['Evaluacion_Desde'], '2023-01-01')
                self.assertEqual(row['Evaluacion_Hasta'], '2024-12-31')
                self.assertEqual(row['Umbral_Score'], .52)
                self.assertIn('no es un pronóstico', row['Alcance_Consulta'])
                self.assertIn('no una probabilidad calibrada', row['Advertencia_Score'])
                self.assertIn('no operativo', row['Advertencia_Score'])

    def test_identidad_y_periodo_proceden_del_registro_no_de_constantes(self):
        registro = copy.deepcopy(REGISTRO)
        registro.update(id_modelo='modelo_fixture', version='2.0')
        registro['datos']['evaluacion'].update(desde='2023-01-02', hasta='2023-01-03')
        consulta = ConsultaRetrospectiva(ModeloPrincipal(PipelineFalso(), registro), self.data)
        row = consulta.consultar('2023-01-02', self.loc, self.slot).iloc[0]
        self.assertEqual(row.Id_Modelo, 'modelo_fixture')
        self.assertEqual(row.Version_Modelo, '2.0')
        self.assertEqual(row.Evaluacion_Desde, '2023-01-02')
        self.assertEqual(row.Evaluacion_Hasta, '2023-01-03')

    def test_trazabilidad_no_altera_prediccion_antecedentes_ni_registro(self):
        datos_antes = self.data.copy(deep=True)
        registro_antes = copy.deepcopy(self.consulta.modelo.registro)
        for fecha in self.data.Fecha_Acc:
            fila = self.data[self.data.Fecha_Acc.eq(fecha)]
            esperado = self.consulta.modelo.predecir(fila)
            actual = self.consulta.consultar(fecha, self.loc, self.slot)
            pd.testing.assert_frame_equal(actual[esperado.columns], esperado)
            columnas = ['Fecha_Acc', *REGISTRO['variables']]
            pd.testing.assert_frame_equal(actual[columnas], fila[columnas])
        pd.testing.assert_frame_equal(self.data, datos_antes)
        self.assertEqual(self.consulta.modelo.registro, registro_antes)

    def test_cli_incluye_trazabilidad_en_json(self):
        salida = io.StringIO()
        args = ['consultar_modelo.py', '--fecha', '2023-01-02',
                '--localidad', self.loc, '--franja', self.slot]
        with patch.object(module, 'cargar_consulta', return_value=self.consulta), \
             patch('sys.argv', args), redirect_stdout(salida):
            runpy.run_path(str(module.ROOT / 'scripts/consultar_modelo.py'), run_name='__main__')
        rows = json.loads(salida.getvalue())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['Id_Modelo'], REGISTRO['id_modelo'])
        self.assertEqual(rows[0]['Version_Modelo'], REGISTRO['version'])
        self.assertEqual(rows[0]['Advertencia_Score'], module.ADVERTENCIA_SCORE)
        self.assertEqual(rows[0]['Score_Priorizacion'], .52)
        self.assertEqual(rows[0]['Alerta_Modelo'], 1)

    def test_no_admite_futuro_fechas_invalidas_o_grupos_nuevos(self):
        for date, loc, slot in [('2026-01-01', self.loc, self.slot), ('2022-12-31', self.loc, self.slot),
                                ('no-fecha', self.loc, self.slot), (pd.NaT, self.loc, self.slot),
                                ('2023-01-02 01:00', self.loc, self.slot),
                                ('2023-01-02T00:00:00Z', self.loc, self.slot),
                                ('2023-01-02', 'ZZZ', self.slot), ('2023-01-02', self.loc, 'ZZZ')]:
            with self.subTest(date=date), self.assertRaises(ValueError):
                self.consulta.consultar(date, loc, slot)

    def test_validacion_temporal_reutilizable_no_ejecuta_modelo(self):
        with patch.object(self.consulta.modelo, 'predecir',
                          side_effect=AssertionError('no debe inferir')):
            fecha = module.validar_fecha_y_alcance(self.consulta.datos, '2023-01-02')
        self.assertEqual(fecha, pd.Timestamp('2023-01-02'))
        with self.assertRaisesRegex(ValueError, 'periodo retrospectivo'):
            module.validar_fecha_y_alcance(self.consulta.datos, '2025-01-01')

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
