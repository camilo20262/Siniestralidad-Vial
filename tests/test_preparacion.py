import unittest
import numpy as np
import pandas as pd
from src.preparacion import (assign_time_slot, preparar_dataset, filtrar_victimas,
                             agregar_historicos, etiquetar_dataset, HISTORY, KEY)


def eventos():
    return pd.DataFrame({
        'Codigo_Accidente': [1, 2, 3, 4],
        'Fecha_Acc': pd.to_datetime(['2022-01-01', '2022-01-02', '2022-01-03', '2022-01-09']),
        'AA_Acc': [2022]*4, 'MM_Acc': [1]*4, 'Hora_Acc': [0, 6, 12, 23],
        'Localidad': ['A']*4,
        'Gravedad_Indicador_Tradicional': ['Con Heridos', 'Solo Daños', 'Con Muertos', 'Con Heridos']})


class PreparacionTest(unittest.TestCase):
    def test_fronteras_franjas(self):
        self.assertEqual([assign_time_slot(h) for h in [0, 5.99, 6, 11.99, 12, 17.99, 18, 23.99]],
                         ['Madrugada']*2 + ['Mañana']*2 + ['Tarde']*2 + ['Noche']*2)

    def test_horas_invalidas(self):
        for h in [-1, 24, np.nan, np.inf, '6', None, True]:
            with self.subTest(h=h), self.assertRaises(ValueError):
                assign_time_slot(h)

    def test_filtro_victimas_cuadricula_y_ceros(self):
        d = preparar_dataset(eventos(), '2022-01-01', '2022-01-10', '2022-01-07')
        self.assertEqual(d.shape, (40, 16))
        self.assertEqual(d.Num_Accidentes.sum(), 3)
        self.assertEqual(d.Num_Accidentes.eq(0).sum(), 37)
        self.assertFalse(d.duplicated(KEY).any())
        self.assertFalse(d.isna().any().any())
        self.assertEqual(d.Periodo.value_counts().to_dict(), {'train': 28, 'test': 12})

    def test_festivo_y_calendario(self):
        d = preparar_dataset(eventos(), '2022-01-01', '2022-01-10', '2022-01-07')
        self.assertTrue(d.loc[d.Fecha_Acc.eq('2022-01-01'), 'Es_Festivo'].eq(1).all())
        self.assertTrue(d.loc[d.Fecha_Acc.eq('2022-01-10'), 'Es_Festivo'].eq(1).all())
        self.assertTrue(d.loc[d.Fecha_Acc.eq('2022-01-03'), 'Es_Festivo'].eq(0).all())
        self.assertTrue(d.loc[d.Fecha_Acc.eq('2022-01-01'), 'Dia_Semana'].eq('Saturday').all())

    def test_duplicados_y_fecha_incoherente(self):
        for data in [pd.concat([eventos(), eventos().iloc[:1]]), eventos().assign(AA_Acc=2020),
                     eventos().assign(MM_Acc=12), eventos().drop(columns='Hora_Acc')]:
            with self.subTest(), self.assertRaises(ValueError):
                filtrar_victimas(data)

    def test_orden_eventos_no_cambia_dataset(self):
        a = preparar_dataset(eventos(), '2022-01-01', '2022-01-10')
        b = preparar_dataset(eventos().sample(frac=1, random_state=42), '2022-01-01', '2022-01-10')
        pd.testing.assert_frame_equal(a, b, check_exact=True)

    def test_mes_textual_de_fuente_oficial(self):
        a = preparar_dataset(eventos(), '2022-01-01', '2022-01-10')
        b = preparar_dataset(eventos().assign(MM_Acc='Enero'), '2022-01-01', '2022-01-10')
        pd.testing.assert_frame_equal(a, b, check_exact=True)

    def historia(self):
        return pd.DataFrame({'Localidad': ['A']*40, 'Franja_Horaria': ['Noche']*40,
                             'Fecha_Acc': pd.date_range('2022-01-01', periods=40),
                             'Num_Accidentes': np.arange(40)})

    def test_lags_excluyen_dia_y_futuro(self):
        data = self.historia()
        a = agregar_historicos(data)
        data.loc[30:, 'Num_Accidentes'] = 99999
        b = agregar_historicos(data)
        pd.testing.assert_frame_equal(a.loc[:30, HISTORY], b.loc[:30, HISTORY])
        self.assertEqual(a.loc[30, HISTORY[0]], np.mean(np.arange(23, 30)))
        self.assertEqual(a.loc[30, HISTORY[1]], np.mean(np.arange(30)))
        self.assertEqual(a.loc[30, HISTORY[2]], 23)

    def test_grupos_independientes_y_faltantes_iniciales(self):
        a = self.historia()
        b = a.assign(Localidad='B', Num_Accidentes=999)
        resultado = agregar_historicos(pd.concat([a, b]))
        pd.testing.assert_frame_equal(resultado[resultado.Localidad.eq('A')].reset_index(drop=True), agregar_historicos(a))
        first = resultado.groupby(['Localidad', 'Franja_Horaria']).head(1)
        self.assertTrue(first[HISTORY].eq(0).all().all())
        self.assertTrue(first[[f'Sin_Historial_{c}' for c in HISTORY]].eq(1).all().all())

    def test_rechaza_calendario_discontinuo_y_conteos_invalidos(self):
        for data in [self.historia().drop(index=3), self.historia().assign(Num_Accidentes=-1),
                     self.historia().assign(Num_Accidentes=np.inf),
                     self.historia().assign(Num_Accidentes=0.5)]:
            with self.subTest(), self.assertRaises(ValueError):
                agregar_historicos(data)

    def test_etiqueta_no_mira_test_y_comparacion_estricta(self):
        data = self.historia().iloc[:6].copy()
        data['Num_Accidentes'] = [0, 0, 1, 3, 1, 2]
        a, t = etiquetar_dataset(data, '2022-01-04')
        _, tt = etiquetar_dataset(data.assign(Num_Accidentes=[0, 0, 1, 3, 999, 999]), '2022-01-04')
        pd.testing.assert_frame_equal(t, tt)
        self.assertEqual(a.Alto_Riesgo.tolist(), [0, 0, 0, 1, 0, 1])

    def test_grupo_sin_pasado_rechazado(self):
        d = self.historia().iloc[:6].copy()
        d.loc[5, 'Localidad'] = 'B'
        with self.assertRaises(ValueError):
            etiquetar_dataset(d, '2022-01-04')
