"""Referencias históricas y comparación pareada, sin ajustar modelos de ML."""

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score


def comprobar_corte(pasado, futuro):
    if pasado.empty or futuro.empty:
        raise ValueError('Los dos periodos deben contener observaciones.')
    a = pd.to_datetime(pasado.Fecha_Acc)
    b = pd.to_datetime(futuro.Fecha_Acc)
    if a.isna().any() or b.isna().any() or a.max() >= b.min():
        raise ValueError('El entrenamiento debe ser estrictamente anterior a la evaluación.')


def etiquetar_corte(pasado, futuro):
    """Recalcula el cuantil exclusivamente en el entrenamiento del corte."""
    comprobar_corte(pasado, futuro)
    claves = ['Localidad', 'Franja_Horaria']
    umbrales = pasado.groupby(claves, observed=True).Num_Accidentes.quantile(2 / 3)
    resultado = []
    for frame in (pasado, futuro):
        copia = frame.copy()
        valores = copia.set_index(claves).index.map(umbrales)
        if pd.isna(valores).any():
            raise ValueError('No hay umbral histórico para algún grupo.')
        copia['Alto_Riesgo'] = (copia.Num_Accidentes.to_numpy() > np.asarray(valores)).astype(int)
        resultado.append(copia)
    return (*resultado, umbrales)


def tasa_historica(pasado, futuro, claves):
    """Media de etiquetas de train; grupos inéditos reciben la media global de train.

    No consulta las etiquetas del futuro. Conserva el orden y el índice de entrada.
    """
    comprobar_corte(pasado, futuro)
    if not pasado.Alto_Riesgo.isin([0, 1]).all():
        raise ValueError('Las etiquetas históricas deben ser binarias y no nulas.')
    media = float(pasado.Alto_Riesgo.mean())
    if not claves:
        return np.full(len(futuro), media), pd.DataFrame({'Tasa': [media], 'Observaciones_Train': [len(pasado)]}), 0
    if pasado[claves].isna().any().any() or futuro[claves].isna().any().any():
        raise ValueError('Las claves no pueden tener valores faltantes.')
    tabla = pasado.groupby(claves, observed=True).Alto_Riesgo.agg(Tasa='mean', Observaciones_Train='size')
    valores = futuro[claves].merge(tabla.reset_index(), on=claves, how='left', validate='many_to_one', sort=False)
    faltantes = int(valores.Tasa.isna().sum())
    return valores.Tasa.fillna(media).to_numpy(), tabla.reset_index(), faltantes


def metricas_score(y, score):
    y, score = np.asarray(y), np.asarray(score, dtype=float)
    if y.ndim != 1 or score.shape != y.shape or not len(y):
        raise ValueError('Las etiquetas y scores deben ser vectores del mismo tamaño, no vacíos.')
    if not np.isin(y, [0, 1]).all() or not np.isfinite(score).all() or ((score < 0) | (score > 1)).any():
        raise ValueError('Etiquetas binarias y scores finitos entre cero y uno son obligatorios.')
    ambas = len(np.unique(y)) == 2
    return {'Average_Precision': average_precision_score(y, score) if ambas else np.nan,
            'AUC_ROC': roc_auc_score(y, score) if ambas else np.nan,
            'Brier': brier_score_loss(y, score)}


def bootstrap_pareado(fechas, y, score_a, score_b, repeticiones=300, dias_bloque=7, semilla=42):
    """Percentiles exploratorios de A-B en bloques temporales, sin reentrenamiento.

    Cada bloque conserva todas sus localidades/franjas; el último puede ser corto.
    No corrige incertidumbre de selección ni convierte test en prueba independiente.
    """
    fechas = pd.DatetimeIndex(pd.to_datetime(fechas))
    y, a, b = np.asarray(y), np.asarray(score_a), np.asarray(score_b)
    ma, mb = metricas_score(y, a), metricas_score(y, b)
    if len(fechas) != len(y) or fechas.isna().any() or dias_bloque < 1 or repeticiones < 2:
        raise ValueError('Fechas, tamaño de bloque o repeticiones inválidos.')
    bloque = np.asarray((fechas.normalize() - fechas.min().normalize()).days // dias_bloque)
    grupos = [np.flatnonzero(bloque == k) for k in np.unique(bloque)]
    if len(grupos) < 2:
        raise ValueError('Se necesitan al menos dos bloques temporales.')
    rng = np.random.default_rng(semilla)
    filas = []
    for repeticion in range(repeticiones):
        ix = np.concatenate([grupos[i] for i in rng.integers(0, len(grupos), len(grupos))])
        m1, m2 = metricas_score(y[ix], a[ix]), metricas_score(y[ix], b[ix])
        filas.append({'Repeticion': repeticion, **{m: m1[m] - m2[m] for m in ma}})
    replicas = pd.DataFrame(filas)
    resumen = pd.DataFrame([{'Metrica': m, 'Diferencia_A_Menos_B': ma[m] - mb[m],
                             'P025': replicas[m].quantile(.025), 'P975': replicas[m].quantile(.975),
                             'Replicas_Validas': int(replicas[m].notna().sum()),
                             'Bloques': len(grupos), 'Dias_Bloque': dias_bloque,
                             'Semilla': semilla} for m in ma])
    return resumen, replicas
