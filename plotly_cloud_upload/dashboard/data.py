"""Datos de solo lectura y cálculos de presentación; nunca entrena modelos."""
from dataclasses import dataclass
from functools import cached_property
import json
from pathlib import Path
import unicodedata

import numpy as np
import pandas as pd
from shapely.geometry import shape, mapping
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix,
                             f1_score, precision_score, recall_score, roc_auc_score)

from src.consulta_retrospectiva import (cargar_consulta, validar_fecha_y_alcance,
                                        ALCANCE_CONSULTA, ADVERTENCIA_SCORE)
from src.rutas import ROOT, sha256_archivo

SLOTS = ['Madrugada', 'Mañana', 'Tarde', 'Noche']
DAYS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
FLAGS = {'Motocicleta': 'Con_Moto', 'Peatón': 'Con_Peaton', 'Bicicleta': 'Con_Bicicleta'}
KEYS = ['Fecha_Acc', 'Localidad', 'Franja_Horaria']
REPORTS = ['metricas_globales', 'comparacion_referencias_historicas',
           'bootstrap_rf_vs_referencia_resumen', 'importancia_permutacion_random_forest_ajustado',
           'calibracion_por_deciles', 'metricas_random_forest_ajustado_por_localidad',
           'metricas_random_forest_ajustado_por_franja']

# Opt-in pendiente de aprobación académica del texto exacto. Cuando está en
# False, la evidencia complementaria no forma parte de las dependencias de inicio.
MOSTRAR_VALIDACION_INDEPENDIENTE = False
VALIDACION_INDEPENDIENTE_MANIFEST = Path(__file__).with_name('validacion_independiente_manifest.json')


def normalize(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('El nombre de localidad de la cartografía debe ser texto no vacío.')
    return ''.join(c for c in unicodedata.normalize('NFD', value.upper())
                   if unicodedata.category(c) != 'Mn').strip()


def _read_json(path, description):
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'No se pudo leer {description} como JSON válido.') from exc
    if not isinstance(value, dict):
        raise ValueError(f'{description.capitalize()} debe contener un objeto JSON.')
    return value


def _manifest_files(manifest):
    files = manifest.get('archivos') if isinstance(manifest, dict) else None
    if not isinstance(files, dict):
        raise ValueError("El manifiesto del dashboard no contiene el objeto 'archivos'.")
    return files


def _prediction_evidence_hash(registry, path):
    evidences = registry.get('evidencias') if isinstance(registry, dict) else None
    if not isinstance(evidences, list):
        raise ValueError('El registro del modelo no contiene una lista de evidencias.')
    matches = [item for item in evidences
               if isinstance(item, dict) and item.get('ruta') == path]
    if len(matches) != 1 or not isinstance(matches[0].get('sha256'), str):
        raise ValueError('El registro del modelo no contiene la evidencia única de predicciones requerida.')
    return matches[0]['sha256']


def _prepare_geojson(geo, localities):
    features = geo.get('features') if isinstance(geo, dict) else None
    if not isinstance(features, list) or not features:
        raise ValueError("La cartografía no contiene una lista no vacía de 'features'.")
    names = {normalize(value): value for value in localities}
    for position, feature in enumerate(features, start=1):
        if not isinstance(feature, dict):
            raise ValueError(f'La entidad cartográfica {position} no es un objeto válido.')
        properties = feature.get('properties')
        if not isinstance(properties, dict):
            raise ValueError(f'La entidad cartográfica {position} no contiene propiedades válidas.')
        source_name = properties.get('LOCNOMBRE')
        try:
            normalized = normalize(source_name)
        except ValueError as exc:
            raise ValueError(f'La entidad cartográfica {position} no contiene una localidad legible.') from exc
        if normalized not in names:
            raise ValueError(f'La cartografía contiene una localidad desconocida: {source_name}.')
        geometry = feature.get('geometry')
        if not isinstance(geometry, dict):
            raise ValueError(f'La geometría de {source_name} está ausente o no es válida.')
        properties['Localidad'] = names[normalized]
        try:
            feature['geometry'] = mapping(shape(geometry).simplify(.00008, preserve_topology=True))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f'La geometría de {source_name} no se pudo interpretar.') from exc
    covered = {feature['properties']['Localidad'] for feature in features}
    if covered != set(names.values()):
        missing = sorted(set(names.values()) - covered)
        detail = f" Faltan: {', '.join(missing)}." if missing else ''
        raise ValueError(f'La cartografía no cubre las veinte localidades.{detail}')
    return geo


def cargar_validacion_independiente():
    """Carga la evidencia opt-in sin mezclarla con el manifiesto oficial."""
    manifest = _read_json(VALIDACION_INDEPENDIENTE_MANIFEST,
                          'el manifiesto complementario de validación')
    files = _manifest_files(manifest)
    if len(files) != 1:
        raise ValueError('El manifiesto complementario debe registrar una sola evidencia.')
    relative_path, expected_hash = next(iter(files.items()))
    if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
        raise ValueError('La ruta y la huella de la validación adicional no son válidas.')
    path = (ROOT / relative_path).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError('La evidencia complementaria debe permanecer dentro del repositorio.')
    if sha256_archivo(path) != expected_hash:
        raise ValueError('La validación independiente no coincide con su manifiesto complementario.')
    result = _read_json(path, 'la evidencia de validación independiente')
    selection = result.get('seleccion')
    evaluation = result.get('evaluacion_separada')
    if (not isinstance(selection, dict) or not isinstance(evaluation, dict)
            or not isinstance(evaluation.get('metricas'), dict)):
        raise ValueError('La evidencia de validación independiente tiene un esquema incompleto.')
    if result.get('modelo_oficial_modificado') is not False:
        raise ValueError('La evidencia complementaria no confirma la preservación del modelo oficial.')
    return result


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


def preparar_base_historica(data):
    """Precalcula una copia de solo lectura para los filtros descriptivos."""
    base = data.copy()
    try:
        base['Fecha_Acc'] = pd.to_datetime(base.Fecha_Acc, errors='raise')
    except (TypeError, ValueError) as exc:
        raise ValueError('Las fechas del dataset no son válidas para el análisis histórico.') from exc
    if base.Fecha_Acc.isna().any():
        raise ValueError('El dataset contiene fechas nulas para el análisis histórico.')
    base['_Anio_Historia'] = base.Fecha_Acc.dt.year
    base['_Dia_Num_Historia'] = base.Fecha_Acc.dt.dayofweek
    base['_Mes_Historia'] = base.Fecha_Acc.dt.to_period('M').astype(str)
    return base


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
        raw_cache_key = (fecha, franja)
        try:
            cached = self._map_rows_cache.get(raw_cache_key)
        except TypeError:
            cached = None
        if cached is not None:
            return cached
        # Misma validación temporal que la consulta pública, sin inferencia redundante.
        dates = validar_fecha_y_alcance(self.consulta.datos, fecha)
        cache_key = (dates, franja)
        cached = self._map_rows_cache.get(cache_key)
        if cached is not None:
            return cached
        rows = self.predictions[(self.predictions.Fecha_Acc == dates) &
                                self.predictions.Franja_Horaria.eq(franja)]
        if len(rows) != len(self.localidades):
            raise ValueError('No hay resultados completos para esta selección.')
        rows = rows[KEYS + ['Score', 'Prediccion']].rename(
            columns={'Score': 'Score_Priorizacion', 'Prediccion': 'Alerta_Modelo'})
        rows['Fecha_Acc'] = rows.Fecha_Acc.dt.strftime('%Y-%m-%d')
        result = self.attach_trace(rows.sort_values('Score_Priorizacion', ascending=False))
        self._map_rows_cache[cache_key] = result
        try:
            self._map_rows_cache[raw_cache_key] = result
        except TypeError:
            pass
        return result

    @cached_property
    def _map_rows_cache(self):
        """Resultados congelados por fecha y franja, reutilizados dentro del proceso."""
        return {}

    def history(self, year='Todos', localidad='Todas', franja='Todas', actor='Todos'):
        if year not in ['Todos', *range(2018, 2025)]:
            raise ValueError('Año fuera de 2018–2024.')
        if localidad not in ['Todas', *self.localidades] or franja not in ['Todas', *SLOTS]:
            raise ValueError('Localidad o franja no válida.')
        if actor not in ['Todos', *FLAGS]:
            raise ValueError('Actor no válido.')
        required = {'_Anio_Historia', '_Dia_Num_Historia', '_Mes_Historia'}
        if not required.issubset(self.consulta.datos.columns):
            raise ValueError('La base histórica del dashboard no fue preparada al iniciar.')
        grid = self.consulta.datos
        if year != 'Todos':
            grid = grid[grid._Anio_Historia.eq(year)]
        if localidad != 'Todas':
            grid = grid[grid.Localidad.eq(localidad)]
        if franja != 'Todas':
            grid = grid[grid.Franja_Horaria.eq(franja)]
        grid = grid[KEYS + ['Num_Accidentes', '_Dia_Num_Historia', '_Mes_Historia']].copy()
        grid = grid.rename(columns={'Num_Accidentes': 'Siniestros',
                                    '_Dia_Num_Historia': 'Dia_Num',
                                    '_Mes_Historia': 'Mes'})
        if actor != 'Todos':
            counts = self.actors[self.actors.Actor.eq(actor)][KEYS + ['Siniestros']]
            grid = grid.drop(columns='Siniestros').merge(counts, on=KEYS, how='left', validate='one_to_one')
            grid['Siniestros'] = grid.Siniestros.fillna(0).astype(int)
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
    manifest = _read_json(manifest_path, 'el manifiesto del dashboard')
    manifest_files = _manifest_files(manifest)
    required = ['data/dashboard/siniestros_actores.parquet', 'data/reference/localidades_sdp_referencia.geojson',
                *[f'reports/evaluation_victimas/{name}.csv' for name in REPORTS]]
    for name in required:
        if sha256_archivo(ROOT / name) != manifest_files.get(name):
            raise ValueError(f'Integridad incorrecta del recurso del dashboard: {name}')
    consulta = cargar_consulta()
    consulta.datos = preparar_base_historica(consulta.datos)
    pred_path = 'reports/evaluation_victimas/predicciones_random_forest_ajustado_2023_2024.parquet'
    expected = _prediction_evidence_hash(consulta.modelo.registro, pred_path)
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
    geo = _prepare_geojson(
        _read_json(ROOT / required[1], 'la cartografía de localidades'),
        consulta.modelo.registro['categorias']['Localidad'],
    )
    reports = {name: pd.read_csv(ROOT / f'reports/evaluation_victimas/{name}.csv') for name in REPORTS}
    if MOSTRAR_VALIDACION_INDEPENDIENTE:
        reports['validacion_independiente'] = cargar_validacion_independiente()
    return DashboardData(consulta, preds, actors, geo, reports, manifest)
