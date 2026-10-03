"""Estimación temporal adicional con 2022 reservado para evaluación.

Este módulo no cambia ni promueve el modelo principal. Repite la búsqueda
acotada de 04C usando únicamente validaciones de 2020 y 2021 para elegir la
configuración y el umbral. Después reajusta con 2018–2021 y evalúa una sola vez
en 2022, recalculando la etiqueta con el pasado disponible.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


RANDOM_STATE = 42
GROUP_COLS = ["Localidad", "Franja_Horaria"]
CAT_COLS = ["Localidad", "Franja_Horaria", "Dia_Semana"]
NUM_COLS = [
    "Mes",
    "Es_Fin_de_Semana",
    "Es_Festivo",
    "Accidentes_Prom_7d",
    "Accidentes_Prom_30d",
    "Accidentes_Semana_Anterior",
    "Sin_Historial_Accidentes_Prom_7d",
    "Sin_Historial_Accidentes_Prom_30d",
    "Sin_Historial_Accidentes_Semana_Anterior",
]
FEATURE_COLS = CAT_COLS + NUM_COLS

# Mismo espacio acotado y mismo orden de 04C. El índice es la identidad del
# candidato en las evidencias históricas.
CANDIDATES = [
    {"n_estimators": 200, "max_depth": 12, "min_samples_leaf": 20, "max_features": "sqrt", "class_weight": "balanced"},
    {"n_estimators": 300, "max_depth": 8, "min_samples_leaf": 20, "max_features": "sqrt", "class_weight": "balanced"},
    {"n_estimators": 300, "max_depth": 16, "min_samples_leaf": 20, "max_features": "sqrt", "class_weight": "balanced"},
    {"n_estimators": 300, "max_depth": None, "min_samples_leaf": 20, "max_features": "sqrt", "class_weight": "balanced"},
    {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 10, "max_features": "sqrt", "class_weight": "balanced"},
    {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 40, "max_features": "sqrt", "class_weight": "balanced"},
    {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 20, "max_features": 0.5, "class_weight": "balanced"},
    {"n_estimators": 300, "max_depth": 12, "min_samples_leaf": 20, "max_features": "sqrt", "class_weight": "balanced_subsample"},
]


@dataclass(frozen=True)
class DisenoTemporal:
    cortes_seleccion: tuple[tuple[int, int], ...] = ((2019, 2020), (2020, 2021))
    entrenamiento_evaluacion_hasta: int = 2021
    anio_evaluacion: int = 2022

    def validar(self) -> None:
        if any(train_end >= validation_year for train_end, validation_year in self.cortes_seleccion):
            raise ValueError("Cada validación debe ser posterior a su entrenamiento.")
        selection_years = {year for _, year in self.cortes_seleccion}
        if self.anio_evaluacion in selection_years:
            raise ValueError("El año de evaluación no puede participar en la selección.")
        if self.entrenamiento_evaluacion_hasta >= self.anio_evaluacion:
            raise ValueError("El reajuste debe terminar antes de la evaluación.")


def validar_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    required = set(FEATURE_COLS + ["Fecha_Acc", "Num_Accidentes"])
    missing = required.difference(dataset.columns)
    if missing:
        raise ValueError(f"Faltan columnas: {sorted(missing)}")
    data = dataset.copy()
    data["Fecha_Acc"] = pd.to_datetime(data["Fecha_Acc"], errors="raise")
    if data[list(required)].isna().any().any():
        raise ValueError("La validación temporal no admite valores nulos.")
    if data.duplicated(["Localidad", "Franja_Horaria", "Fecha_Acc"]).any():
        raise ValueError("La unidad localidad–franja–fecha debe ser única.")
    return data


def etiquetar_desde_pasado(train: pd.DataFrame, validation: pd.DataFrame):
    """Calcula el cuantil de etiqueta solo con ``train`` y etiqueta ambos tramos."""
    if train.empty or validation.empty:
        raise ValueError("Los tramos de entrenamiento y validación deben tener filas.")
    if pd.to_datetime(train.Fecha_Acc).max() >= pd.to_datetime(validation.Fecha_Acc).min():
        raise ValueError("El entrenamiento debe terminar antes de la validación.")
    thresholds = (
        train.groupby(GROUP_COLS, observed=True).Num_Accidentes
        .quantile(2 / 3)
        .rename("Umbral_Etiqueta")
        .reset_index()
    )
    train_labeled = train.merge(thresholds, on=GROUP_COLS, how="left", validate="many_to_one")
    validation_labeled = validation.merge(thresholds, on=GROUP_COLS, how="left", validate="many_to_one")
    if train_labeled.Umbral_Etiqueta.isna().any() or validation_labeled.Umbral_Etiqueta.isna().any():
        raise ValueError("La evaluación contiene grupos sin historia de entrenamiento.")
    y_train = (train_labeled.Num_Accidentes > train_labeled.Umbral_Etiqueta).astype(int)
    y_validation = (validation_labeled.Num_Accidentes > validation_labeled.Umbral_Etiqueta).astype(int)
    return train_labeled, validation_labeled, y_train, y_validation, thresholds


def crear_pipeline(params: dict) -> Pipeline:
    preprocessor = ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS)],
        remainder="passthrough",
    )
    model = RandomForestClassifier(random_state=RANDOM_STATE, n_jobs=-1, **params)
    return Pipeline([("preprocesador", preprocessor), ("modelo", model)])


def calcular_metricas(y_true, prediction, score) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, prediction, labels=[0, 1]).ravel()
    return {
        "Average_Precision": average_precision_score(y_true, score),
        "AUC_ROC": roc_auc_score(y_true, score),
        "F1": f1_score(y_true, prediction, zero_division=0),
        "Precision": precision_score(y_true, prediction, zero_division=0),
        "Recall": recall_score(y_true, prediction, zero_division=0),
        "Especificidad": tn / (tn + fp),
        "Balanced_Accuracy": balanced_accuracy_score(y_true, prediction),
        "Brier": brier_score_loss(y_true, score),
        "TN": int(tn),
        "FP": int(fp),
        "FN": int(fn),
        "TP": int(tp),
    }


def seleccionar_umbral(y_true, score, thresholds=None):
    values = np.linspace(0.05, 0.95, 181) if thresholds is None else np.asarray(thresholds, dtype=float)
    rows = []
    for threshold in values:
        prediction = (np.asarray(score) >= threshold).astype(int)
        rows.append({"Umbral": float(threshold), **calcular_metricas(y_true, prediction, score)})
    table = pd.DataFrame(rows)
    best = float(table.loc[table.F1.idxmax(), "Umbral"])
    return best, table


def ejecutar_estimacion(dataset: pd.DataFrame, diseno=None, candidates=None):
    """Ejecuta selección 2020–2021 y evaluación reservada en 2022."""
    diseno = DisenoTemporal() if diseno is None else diseno
    candidates = CANDIDATES if candidates is None else candidates
    diseno.validar()
    data = validar_dataset(dataset)
    years = set(data.Fecha_Acc.dt.year.unique())
    required_years = {2020, 2021, diseno.anio_evaluacion}
    if not required_years.issubset(years):
        raise ValueError(f"Faltan años requeridos: {sorted(required_years - years)}")

    rows = []
    scores_by_candidate = {}
    for candidate_id, params in enumerate(candidates):
        candidate_oof = []
        for train_end, validation_year in diseno.cortes_seleccion:
            train = data[data.Fecha_Acc.dt.year <= train_end].copy()
            validation = data[data.Fecha_Acc.dt.year == validation_year].copy()
            train, validation, y_train, y_validation, _ = etiquetar_desde_pasado(train, validation)
            model = crear_pipeline(params)
            model.fit(train[FEATURE_COLS], y_train)
            score = model.predict_proba(validation[FEATURE_COLS])[:, 1]
            prediction = (score >= 0.5).astype(int)
            rows.append({
                "Candidato": candidate_id,
                "Train_Hasta": train_end,
                "Validacion": validation_year,
                "N_Train": len(train),
                "N_Validacion": len(validation),
                **params,
                **calcular_metricas(y_validation, prediction, score),
            })
            candidate_oof.append(pd.DataFrame({
                "Fecha_Acc": validation.Fecha_Acc.to_numpy(),
                "Localidad": validation.Localidad.to_numpy(),
                "Franja_Horaria": validation.Franja_Horaria.to_numpy(),
                "Alto_Riesgo": y_validation.to_numpy(),
                "Score": score,
                "Candidato": candidate_id,
            }))
        scores_by_candidate[candidate_id] = pd.concat(candidate_oof, ignore_index=True)

    detail = pd.DataFrame(rows)
    parameter_table = pd.DataFrame(candidates)
    parameter_table.index.name = "Candidato"
    summary = (
        detail.groupby("Candidato")
        .agg(
            AP_Media=("Average_Precision", "mean"),
            AP_Std=("Average_Precision", "std"),
            AUC_Media=("AUC_ROC", "mean"),
            F1_Medio=("F1", "mean"),
            Recall_Medio=("Recall", "mean"),
            Brier_Medio=("Brier", "mean"),
        )
        .join(parameter_table)
        .sort_values(["AP_Media", "AP_Std"], ascending=[False, True])
    )
    best_candidate = int(summary.index[0])
    oof = scores_by_candidate[best_candidate]
    best_threshold, threshold_table = seleccionar_umbral(oof.Alto_Riesgo, oof.Score)

    train = data[data.Fecha_Acc.dt.year <= diseno.entrenamiento_evaluacion_hasta].copy()
    evaluation = data[data.Fecha_Acc.dt.year == diseno.anio_evaluacion].copy()
    train, evaluation, y_train, y_evaluation, thresholds = etiquetar_desde_pasado(train, evaluation)
    final_model = crear_pipeline(candidates[best_candidate])
    final_model.fit(train[FEATURE_COLS], y_train)
    evaluation_score = final_model.predict_proba(evaluation[FEATURE_COLS])[:, 1]
    evaluation_prediction = (evaluation_score >= best_threshold).astype(int)
    evaluation_metrics = pd.DataFrame([{
        "Modelo": "Random Forest estimación temporal adicional",
        "Candidato": best_candidate,
        "Umbral": best_threshold,
        "Entrenamiento": f"2018–{diseno.entrenamiento_evaluacion_hasta}",
        "Evaluacion": str(diseno.anio_evaluacion),
        "N_Train": len(train),
        "N_Evaluacion": len(evaluation),
        "Positivos_Evaluacion": int(y_evaluation.sum()),
        **calcular_metricas(y_evaluation, evaluation_prediction, evaluation_score),
    }])
    predictions = pd.DataFrame({
        "Fecha_Acc": evaluation.Fecha_Acc.to_numpy(),
        "Localidad": evaluation.Localidad.to_numpy(),
        "Franja_Horaria": evaluation.Franja_Horaria.to_numpy(),
        "Umbral_Etiqueta": evaluation.Umbral_Etiqueta.to_numpy(),
        "Alto_Riesgo": y_evaluation.to_numpy(),
        "Score": evaluation_score,
        "Umbral_Score": best_threshold,
        "Prediccion": evaluation_prediction,
    })
    if detail.Validacion.max() >= diseno.anio_evaluacion:
        raise AssertionError("La evaluación reservada contaminó la selección.")
    return {
        "detalle": detail,
        "resumen": summary,
        "oof_seleccion": oof,
        "seleccion_umbral": threshold_table,
        "metricas_evaluacion": evaluation_metrics,
        "predicciones_evaluacion": predictions,
        "umbrales_etiqueta_evaluacion": thresholds,
        "mejor_candidato": best_candidate,
        "mejor_umbral": best_threshold,
        "diseno": diseno,
    }
