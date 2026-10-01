"""Datos de solo lectura y cálculos de presentación; nunca entrena modelos."""
from dataclasses import dataclass
from functools import cached_property
import json
import unicodedata

import numpy as np
import pandas as pd
from shapely.geometry import shape, mapping
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)

from src.consulta_retrospectiva import cargar_consulta, ALCANCE_CONSULTA, ADVERTENCIA_SCORE
from src.rutas import ROOT, sha256_archivo

SLOTS = ['Madrugada', 'Mañana', 'Tarde', 'Noche']
DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
FLAGS = {'Motocicleta': 'Con_Moto', 'Peatón': 'Con_Peaton', 'Bicicleta': 'Con_Bicicleta'}
KEYS = ['Fecha_Acc', 'Localidad', 'Franja_Horaria']
REPORTS = ['metricas_globales', 'comparacion_referencias_historicas',
           'bootstrap_rf_vs_referencia_resumen', 'importancia_permutacion_random_forest_ajustado',
           'calibracion_por_deciles', 'metricas_random_forest_ajustado_por_localidad',
           'metricas_random_forest_ajustado_por_franja']


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.upper())
                   if unicodedata.category(c) != 'Mn').strip()


def preparar_actores(raw):
    """Conteos no excluyentes de siniestros con participación, no de personas."""
    from src.preparacion import filtrar_victimas
    events = filtrar_victimas(raw)
    parts = []
    for actor, flag in FLAGS.items():
        subset = events[events[flag].astype(str).str.strip().str.upper().eq('SI')]
        counts = subset.groupby(KEYS).size().rename('Siniestros').reset_index()
        counts['Actor'] = actor
        parts.append(counts)
    return pd.concat(parts, ignore_index=True), events


def resumen_metricas(frame):
    """Métricas del subconjunto; no inventa AUC/AP para clases ausentes."""
    if frame.empty:
        return {k: None for k in ['Observaciones', 'Positivos', 'Prevalencia', 'F1', 'Precision',
                                  'Recall', 'AUC_ROC', 'Average_Precision', 'Brier', 'TN', 'FP', 'FN', 'TP']}
    y, pred, score = frame.Alto_Riesgo, frame.Prediccion, frame.Score
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {'Observaciones': len(frame), 'Positivos': int(y.sum()), 'Prevalencia': float(y.mean()),
            'F1': float(f1_score(y, pred, zero_division=0)),
            'Precision': float(precision_score(y, pred, zero_division=0)),
            'Recall': float(recall_score(y, pred, zero_division=0)) if y.sum() else None,
            'AUC_ROC': float(roc_auc_score(y, score)) if y.nunique() == 2 else None,
            'Average_Precision': float(average_precision_score(y, score)) if y.sum() else None,
            'Brier': float(brier_score_loss(y, score)),
            'TN': int(tn), 'FP': int(fp), 'FN': int(fn), 'TP': int(tp)}


@dataclass
class DashboardData:
    consulta: object
    predictions: pd.DataFrame
    actors: pd.DataFrame
    geojson: dict
    reports: dict
    manifest: dict

    @property
    def registro(self):
        return self.consulta.modelo.registro

    @property
    def localidades(self):
        return sorted(self.registro['categorias']['Localidad'])

    @cached_property
    def label_thresholds(self):
        # Solo train del dataset verificado; nunca se usan conteos del día consultado.
        train = self.consulta.datos[self.consulta.datos.Periodo.eq('train')]
        return train.groupby(['Localidad', 'Franja_Horaria']).Num_Accidentes.quantile(2 / 3)

    def label_rule(self, localidad, franja):
        try:
            threshold = float(self.label_thresholds.loc[(localidad, franja)])
        except KeyError as exc:
            raise ValueError('No hay umbral histórico para esta localidad y franja.') from exc
        if not np.isfinite(threshold) or threshold < 0:
            raise ValueError('Umbral histórico del conteo no válido.')
        return {'umbral_conteo': threshold, 'minimo_siniestros': int(np.floor(threshold)) + 1}

    def attach_trace(self, frame):
        frame = frame.copy()
        reg = self.registro
        frame['Umbral_Score'] = reg['decision']['umbral_score']
        frame['Id_Modelo'] = reg['id_modelo']
        frame['Version_Modelo'] = reg['version']
        frame['Tipo_Evaluacion'] = reg['datos']['evaluacion']['tipo']
        frame['Evaluacion_Desde'] = reg['datos']['evaluacion']['desde']
        frame['Evaluacion_Hasta'] = reg['datos']['evaluacion']['hasta']
        frame['Alcance_Consulta'] = ALCANCE_CONSULTA
        frame['Advertencia_Score'] = ADVERTENCIA_SCORE
        return frame

    def map_rows(self, fecha, franja):
        if franja not in SLOTS:
            raise ValueError('Seleccione una franja válida.')
        # Misma validación de fecha y de alcance que la consulta pública.
        self.consulta.consultar(fecha, self.localidades[0], franja)
        dates = pd.Timestamp(fecha)
        rows = self.predictions[(self.predictions.Fecha_Acc == dates) &
                                self.predictions.Franja_Horaria.eq(franja)]
        if len(rows) != len(self.localidades):
            raise ValueError('No hay resultados completos para esta selección.')
        rows = rows[KEYS + ['Score', 'Prediccion']].rename(
            columns={'Score': 'Score_Priorizacion', 'Prediccion': 'Alerta_Modelo'})
        rows['Fecha_Acc'] = rows.Fecha_Acc.dt.strftime('%Y-%m-%d')
        return self.attach_trace(rows.sort_values('Score_Priorizacion', ascending=False))

    def history(self, year='Todos', localidad='Todas', franja='Todas', actor='Todos'):
        if year not in ['Todos', *range(2018, 2025)]:
            raise ValueError('Año fuera de 2018–2024.')
        if localidad not in ['Todas', *self.localidades] or franja not in ['Todas', *SLOTS]:
            raise ValueError('Localidad o franja no válida.')
        if actor not in ['Todos', *FLAGS]:
            raise ValueError('Actor no válido.')
        grid = self.consulta.datos.copy()
        grid['Fecha_Acc'] = pd.to_datetime(grid.Fecha_Acc)
        if year != 'Todos':
            grid = grid[grid.Fecha_Acc.dt.year.eq(year)]
        if localidad != 'Todas':
            grid = grid[grid.Localidad.eq(localidad)]
        if franja != 'Todas':
            grid = grid[grid.Franja_Horaria.eq(franja)]
        grid = grid[KEYS + ['Num_Accidentes']].rename(columns={'Num_Accidentes': 'Siniestros'})
        if actor != 'Todos':
            counts = self.actors[self.actors.Actor.eq(actor)][KEYS + ['Siniestros']]
            grid = grid.drop(columns='Siniestros').merge(counts, on=KEYS, how='left', validate='one_to_one')
            grid['Siniestros'] = grid.Siniestros.fillna(0).astype(int)
        grid['Dia_Num'] = grid.Fecha_Acc.dt.dayofweek
        grid['Mes'] = grid.Fecha_Acc.dt.to_period('M').astype(str)
        return grid

    def evaluation(self, year='Todos', localidad='Todas', franja='Todas'):
        if year not in ['Todos', 2023, 2024] or localidad not in ['Todas', *self.localidades] or franja not in ['Todas', *SLOTS]:
            raise ValueError('Filtros de evaluación no válidos.')
        rows = self.predictions
        if year != 'Todos':
            rows = rows[rows.Fecha_Acc.dt.year.eq(year)]
        if localidad != 'Todas':
            rows = rows[rows.Localidad.eq(localidad)]
        if franja != 'Todas':
            rows = rows[rows.Franja_Horaria.eq(franja)]
        return rows.copy()


def load_data():
    """Una carga por proceso. Verifica artefactos, no accede a servicios externos."""
    manifest_path = ROOT / 'data/dashboard/manifest.json'
    if not manifest_path.exists():
        raise RuntimeError('Faltan agregados del dashboard. Ejecute python scripts/preparar_dashboard.py.')
    manifest = json.loads(manifest_path.read_text())
    required = ['data/dashboard/siniestros_actores.parquet', 'data/reference/localidades_sdp_referencia.geojson',
                *[f'reports/evaluation_victimas/{name}.csv' for name in REPORTS]]
    for name in required:
        if sha256_archivo(ROOT / name) != manifest['archivos'].get(name):
            raise ValueError(f'Integridad incorrecta del recurso del dashboard: {name}')
    consulta = cargar_consulta()
    pred_path = 'reports/evaluation_victimas/predicciones_random_forest_ajustado_2023_2024.parquet'
    expected = next(x['sha256'] for x in consulta.modelo.registro['evidencias'] if x['ruta'] == pred_path)
    if sha256_archivo(ROOT / pred_path) != expected:
        raise ValueError('Las predicciones no coinciden con la evaluación cerrada.')
    preds = pd.read_parquet(ROOT / pred_path)
    preds['Fecha_Acc'] = pd.to_datetime(preds.Fecha_Acc)
    if preds.duplicated(KEYS).any() or len(preds) != consulta.modelo.registro['datos']['evaluacion']['filas']:
        raise ValueError('Claves de predicciones incorrectas.')
    grid = consulta.datos[consulta.datos.Periodo.eq('test')].copy()
    grid['Fecha_Acc'] = pd.to_datetime(grid.Fecha_Acc)
    check = grid[KEYS + ['Alto_Riesgo']].merge(preds, on=KEYS, how='outer', validate='one_to_one', indicator=True)
    if not check['_merge'].eq('both').all() or not check.Alto_Riesgo_x.eq(check.Alto_Riesgo_y).all():
        raise ValueError('Dataset y predicciones no describen los mismos casos.')
    if not preds.Prediccion.eq((preds.Score >= consulta.modelo.registro['decision']['umbral_score']).astype(int)).all():
        raise ValueError('Las alertas no respetan el umbral cerrado.')
    actors = pd.read_parquet(ROOT / required[0])
    actors['Fecha_Acc'] = pd.to_datetime(actors.Fecha_Acc)
    geo = json.loads((ROOT / required[1]).read_text())
    nombres = {normalize(x): x for x in consulta.modelo.registro['categorias']['Localidad']}
    for feature in geo['features']:
        feature['properties']['Localidad'] = nombres[normalize(feature['properties']['LOCNOMBRE'])]
        # Simplificación solo visual, en memoria; el GeoJSON original no se modifica.
        feature['geometry'] = mapping(shape(feature['geometry']).simplify(.00008, preserve_topology=True))
    if {f['properties']['Localidad'] for f in geo['features']} != set(nombres.values()):
        raise ValueError('La cartografía no cubre las veinte localidades.')
    reports = {name: pd.read_csv(ROOT / f'reports/evaluation_victimas/{name}.csv') for name in REPORTS}
    return DashboardData(consulta, preds, actors, geo, reports, manifest)
