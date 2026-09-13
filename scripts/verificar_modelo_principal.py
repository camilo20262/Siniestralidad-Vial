"""Verifica el cierre sin entrenar ni modificar modelos o reportes.

Uso desde la raíz: .venv/bin/python scripts/verificar_modelo_principal.py
"""

from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score, brier_score_loss, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.modelo_principal import cargar_modelo_principal  # noqa: E402


def verificar():
    modelo = cargar_modelo_principal()
    registro = modelo.registro
    for evidencia in registro['evidencias']:
        actual = sha256((ROOT / evidencia['ruta']).read_bytes()).hexdigest()
        if actual != evidencia['sha256']:
            raise AssertionError(f"Evidencia modificada después del cierre: {evidencia['ruta']}")

    dataset = pd.read_parquet(ROOT / registro['datos']['ruta'])
    train = dataset[dataset.Periodo.eq('train')]
    test = dataset[dataset.Periodo.eq('test')].copy()
    assert len(train) == registro['datos']['entrenamiento']['filas']
    assert len(test) == registro['datos']['evaluacion']['filas']
    keys = ['Localidad', 'Franja_Horaria']
    umbrales = pd.read_csv(ROOT / registro['etiqueta']['archivo_umbrales'])
    calculados = train.groupby(keys).Num_Accidentes.quantile(2 / 3)
    np.testing.assert_allclose(
        umbrales.set_index(keys).Umbral_Etiqueta.sort_index(), calculados.sort_index(),
        rtol=0, atol=0,
    )
    etiquetas = dataset.merge(umbrales, on=keys, validate='many_to_one', how='left')
    assert etiquetas.Umbral_Etiqueta.notna().all()
    np.testing.assert_array_equal(
        etiquetas.Alto_Riesgo, (etiquetas.Num_Accidentes > etiquetas.Umbral_Etiqueta).astype(int),
    )

    resultado = modelo.predecir(test)
    assert resultado.index.equals(test.index)
    score, pred = resultado.Score_Priorizacion, resultado.Alerta_Modelo
    y = test.Alto_Riesgo
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    metricas = {
        'F1': f1_score(y, pred), 'AUC_ROC': roc_auc_score(y, score),
        'Average_Precision': average_precision_score(y, score),
        'Precision': precision_score(y, pred), 'Recall': recall_score(y, pred),
        'Brier': brier_score_loss(y, score), 'TN': int(tn), 'FP': int(fp),
        'FN': int(fn), 'TP': int(tp),
    }
    esperado = registro['evaluacion']['metricas']
    for nombre, valor in metricas.items():
        np.testing.assert_allclose(valor, esperado[nombre], rtol=0, atol=1e-10)

    archivo_pred = ROOT / 'reports/evaluation_victimas/predicciones_random_forest_ajustado_2023_2024.parquet'
    previas = pd.read_parquet(archivo_pred)
    actuales = test[['Fecha_Acc', *keys, 'Alto_Riesgo']].copy()
    actuales['Score'] = score
    actuales['Prediccion'] = pred
    actuales['Fecha_Acc'] = pd.to_datetime(actuales.Fecha_Acc)
    previas['Fecha_Acc'] = pd.to_datetime(previas.Fecha_Acc)
    orden = ['Fecha_Acc', *keys]
    actuales = actuales.sort_values(orden).reset_index(drop=True)
    previas = previas.sort_values(orden).reset_index(drop=True)
    assert not actuales.duplicated(orden).any() and not previas.duplicated(orden).any()
    pd.testing.assert_frame_equal(actuales[orden], previas[orden], check_dtype=False)
    np.testing.assert_allclose(actuales.Score, previas.Score, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(actuales.Prediccion, previas.Prediccion)
    np.testing.assert_array_equal(actuales.Alto_Riesgo, previas.Alto_Riesgo)

    # Las entradas inválidas deben fallar explícitamente; no generar scores engañosos.
    muestra = test.head(3).copy()
    pruebas = [muestra.drop(columns='Mes'), muestra.assign(Localidad='DESCONOCIDA'),
               muestra.assign(Es_Festivo=2), muestra.assign(Accidentes_Prom_7d=np.nan)]
    for entrada in pruebas:
        try:
            modelo.predecir(entrada)
        except ValueError:
            continue
        raise AssertionError('Se aceptó una entrada fuera del contrato.')
    inversa = modelo.predecir(muestra.iloc[::-1])
    directa = modelo.predecir(muestra)
    pd.testing.assert_frame_equal(inversa, directa.iloc[::-1], atol=1e-12, rtol=0)
    return {'resultado': 'correcto', 'modelo': registro['id_modelo'],
            'observaciones_verificadas': len(test), 'umbrales_etiqueta_verificados': len(umbrales),
            'evidencias_integras': len(registro['evidencias']),
            'predicciones_coinciden_con_05B': True, 'umbral_score': registro['decision']['umbral_score'],
            'metricas_reproducidas': metricas, 'validaciones_entrada': 4,
            'modelos_reentrenados': 0}


if __name__ == '__main__':
    print(json.dumps(verificar(), ensure_ascii=False, indent=2))
