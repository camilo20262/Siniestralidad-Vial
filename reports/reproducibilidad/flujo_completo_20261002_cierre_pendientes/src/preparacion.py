"""Preparación de 03B como funciones puras, sin escrituras ni entrenamiento.

Se preservan el cuantil 2/3, el calendario diario completo y los tipos/orden
del dataset cerrado. Una fila sin registro significa cero eventos registrados,
no una garantía de ausencia de siniestros. No se infieren coberturas nuevas.
"""
import itertools
import holidays
import numpy as np
import pandas as pd

USECOLS = ['Codigo_Accidente', 'Fecha_Acc', 'AA_Acc', 'MM_Acc', 'Hora_Acc',
           'Localidad', 'Gravedad_Indicador_Tradicional']
KEY = ['Localidad', 'Franja_Horaria', 'Fecha_Acc']
GROUP = KEY[:2]
TIME_SLOTS = ['Madrugada', 'Mañana', 'Tarde', 'Noche']
HISTORY = ['Accidentes_Prom_7d', 'Accidentes_Prom_30d', 'Accidentes_Semana_Anterior']
FINAL_COLS = [*KEY, 'Num_Accidentes', 'Dia_Semana', 'Mes', 'Es_Fin_de_Semana',
              'Es_Festivo', *HISTORY, *[f'Sin_Historial_{c}' for c in HISTORY],
              'Periodo', 'Alto_Riesgo']


def filtrar_victimas(siniestros, inicio='2018-01-01', fin='2024-12-31'):
    faltan = set(USECOLS) - set(siniestros.columns)
    if faltan:
        raise ValueError(f'Faltan columnas de la fuente: {sorted(faltan)}')
    if siniestros.Codigo_Accidente.isna().any() or not siniestros.Codigo_Accidente.is_unique:
        raise ValueError('Codigo_Accidente debe ser único y no nulo; no deduplicar silenciosamente.')
    data = siniestros.copy()
    data['Fecha_Acc'] = pd.to_datetime(data.Fecha_Acc, errors='raise')
    if data.Fecha_Acc.isna().any():
        raise ValueError('Fecha de siniestro nula.')
    if not data.AA_Acc.eq(data.Fecha_Acc.dt.year).all():
        raise ValueError('AA_Acc no coincide con el año de Fecha_Acc.')
    meses = {name: i for i, name in enumerate(['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
                                             'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'], 1)}
    mes_fuente = pd.to_numeric(data.MM_Acc, errors='coerce').fillna(data.MM_Acc.astype(str).str.strip().str.lower().map(meses))
    if not mes_fuente.eq(data.Fecha_Acc.dt.month).all():
        raise ValueError('MM_Acc no coincide con el mes de Fecha_Acc.')
    data = data[data.Fecha_Acc.dt.normalize().between(pd.Timestamp(inicio), pd.Timestamp(fin))
                & data.Gravedad_Indicador_Tradicional.isin(['Con Heridos', 'Con Muertos'])].copy()
    if data.empty or data[['Localidad', 'Hora_Acc']].isna().any().any():
        raise ValueError('Se requieren siniestros con víctimas y localidad/hora válidas.')
    if not data.Localidad.map(lambda x: isinstance(x, str) and bool(x.strip())).all():
        raise ValueError('Localidad debe ser texto no vacío.')
    data['Franja_Horaria'] = data.Hora_Acc.map(assign_time_slot)
    data['Fecha_Acc'] = data.Fecha_Acc.dt.normalize()
    return data


def assign_time_slot(hour):
    if isinstance(hour, (bool, np.bool_)) or not isinstance(hour, (int, float, np.number)):
        raise ValueError('Hora_Acc debe ser numérica entre 0 (incluido) y 24 (excluido).')
    if not np.isfinite(hour) or not 0 <= hour < 24:
        raise ValueError('Hora_Acc fuera de [0, 24).')
    return TIME_SLOTS[int(hour // 6)]


def crear_cuadricula(event_count, localities, inicio='2018-01-01', fin='2024-12-31'):
    dates = pd.date_range(inicio, fin, freq='D')
    if not len(dates) or not len(localities) or len(set(localities)) != len(localities):
        raise ValueError('Calendario o localidades inválidos.')
    if event_count.duplicated(KEY).any():
        raise ValueError('Conteos duplicados por localidad, franja y fecha.')
    counts = event_count.Num_Accidentes
    if not pd.api.types.is_numeric_dtype(counts) or not np.isfinite(counts).all() or (counts < 0).any() or (counts % 1 != 0).any():
        raise ValueError('Los conteos deben ser enteros, finitos y no negativos.')
    grid = pd.DataFrame(itertools.product(sorted(localities), TIME_SLOTS, dates), columns=KEY)
    if not pd.MultiIndex.from_frame(event_count[KEY]).isin(pd.MultiIndex.from_frame(grid[KEY])).all():
        raise ValueError('Hay eventos fuera de la cuadrícula solicitada.')
    dataset = grid.merge(event_count, on=KEY, how='left', validate='one_to_one')
    dataset['Num_Accidentes'] = dataset.Num_Accidentes.fillna(0).astype(int)
    co_holidays = holidays.Colombia(years=range(dates.min().year, dates.max().year + 1))
    dataset['Dia_Semana'] = dataset.Fecha_Acc.dt.day_name()
    dataset['Mes'] = dataset.Fecha_Acc.dt.month
    dataset['Es_Fin_de_Semana'] = dataset.Fecha_Acc.dt.dayofweek.isin([5, 6]).astype(int)
    dataset['Es_Festivo'] = dataset.Fecha_Acc.dt.date.astype('object').isin(co_holidays).astype(int)
    return dataset


def agregar_historicos(dataset):
    dataset = dataset.copy()
    dataset['Fecha_Acc'] = pd.to_datetime(dataset.Fecha_Acc)
    dataset = dataset.sort_values(KEY).reset_index(drop=True)
    if dataset.empty or dataset[KEY + ['Num_Accidentes']].isna().any().any() or dataset.duplicated(KEY).any():
        raise ValueError('La cuadrícula debe ser no vacía, única y sin faltantes.')
    counts = dataset.Num_Accidentes
    if not pd.api.types.is_numeric_dtype(counts) or not np.isfinite(counts).all() or (counts < 0).any() or (counts % 1 != 0).any():
        raise ValueError('Los conteos deben ser enteros, finitos y no negativos.')
    dif = dataset.groupby(GROUP).Fecha_Acc.diff().dropna()
    if not dif.eq(pd.Timedelta(days=1)).all():
        raise ValueError('Los lags requieren días consecutivos por localidad y franja.')
    grouped = dataset.groupby(GROUP).Num_Accidentes
    dataset[HISTORY[0]] = grouped.transform(lambda x: x.shift(1).rolling(7, min_periods=1).mean())
    dataset[HISTORY[1]] = grouped.transform(lambda x: x.shift(1).rolling(30, min_periods=1).mean())
    dataset[HISTORY[2]] = grouped.transform(lambda x: x.shift(7))
    for col in HISTORY:
        dataset[f'Sin_Historial_{col}'] = dataset[col].isna().astype(int)
    dataset[HISTORY] = dataset[HISTORY].fillna(0)
    return dataset


def etiquetar_dataset(dataset, train_end='2022-12-31'):
    dataset = dataset.copy()
    dataset['Periodo'] = np.where(dataset.Fecha_Acc <= pd.Timestamp(train_end), 'train', 'test')
    train = dataset[dataset.Periodo.eq('train')]
    if train.empty:
        raise ValueError('No hay observaciones de entrenamiento.')
    thresholds = train.groupby(GROUP).Num_Accidentes.quantile(2 / 3).rename('Umbral_P66_Train').reset_index()
    dataset = dataset.merge(thresholds, on=GROUP, how='left', validate='many_to_one')
    if dataset.Umbral_P66_Train.isna().any():
        raise ValueError('Hay grupos sin umbral de entrenamiento.')
    dataset['Alto_Riesgo'] = (dataset.Num_Accidentes > dataset.Umbral_P66_Train).astype(int)
    return dataset, thresholds


def preparar_dataset(siniestros, inicio='2018-01-01', fin='2024-12-31', train_end='2022-12-31'):
    sin = filtrar_victimas(siniestros, inicio, fin)
    events = sin.groupby(KEY).size().rename('Num_Accidentes').reset_index()
    grid = crear_cuadricula(events, sorted(sin.Localidad.unique()), inicio, fin)
    dataset, _ = etiquetar_dataset(agregar_historicos(grid), train_end)
    dataset = dataset.loc[:, FINAL_COLS].copy()
    dataset['Fecha_Acc'] = dataset.Fecha_Acc.astype(str)
    return dataset
