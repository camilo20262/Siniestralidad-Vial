"""Carga de solo lectura para Plotly Cloud, basada en resultados congelados.

La aplicación publicada no vuelve a ejecutar el modelo. Reproduce exactamente
los casos retrospectivos 2023–2024 conservados en la evidencia de evaluación.
"""

from dataclasses import dataclass
import json

import numpy as np
import pandas as pd

from dashboard.data import (
    DashboardData,
    KEYS,
    REPORTS,
    _prepare_geojson,
    _read_json,
    preparar_base_historica,
)
from src.consulta_retrospectiva import (
    ADVERTENCIA_SCORE,
    ALCANCE_CONSULTA,
    validar_fecha_y_alcance,
)
from src.rutas import ROOT, sha256_archivo


def _prediction_hash(registry, relative_path):
    matches = [
        item
        for item in registry.get("evidencias", [])
        if isinstance(item, dict) and item.get("ruta") == relative_path
    ]
    if len(matches) != 1 or not isinstance(matches[0].get("sha256"), str):
        raise ValueError("El registro no contiene la evidencia de predicciones requerida.")
    return matches[0]["sha256"]


@dataclass(frozen=True)
class FrozenModelReference:
    """Referencia documental del modelo; no carga el artefacto de entrenamiento."""

    registro: dict


@dataclass
class FrozenConsulta:
    """Consulta casos ya evaluados, sin recalcular predicciones."""

    modelo: FrozenModelReference
    datos: pd.DataFrame
    predictions: pd.DataFrame

    def consultar(self, fecha, localidad, franja):
        fecha = validar_fecha_y_alcance(self.datos, fecha)
        registro = self.modelo.registro
        if localidad not in registro["categorias"]["Localidad"]:
            raise ValueError("Seleccione una localidad válida.")
        if franja not in registro["categorias"]["Franja_Horaria"]:
            raise ValueError("Seleccione una franja válida.")

        dates = pd.to_datetime(self.datos["Fecha_Acc"])
        row = self.datos[
            self.datos["Periodo"].eq("test")
            & dates.eq(fecha)
            & self.datos["Localidad"].eq(localidad)
            & self.datos["Franja_Horaria"].eq(franja)
        ]
        frozen = self.predictions[
            self.predictions["Fecha_Acc"].eq(fecha)
            & self.predictions["Localidad"].eq(localidad)
            & self.predictions["Franja_Horaria"].eq(franja)
        ]
        if len(row) != 1 or len(frozen) != 1:
            raise ValueError("La consulta debe identificar un único caso retrospectivo.")

        result = row[["Fecha_Acc", *registro["variables"]]].copy()
        prediction = frozen.iloc[0]
        result[registro["decision"]["columna_score"]] = float(prediction["Score"])
        result[registro["decision"]["columna_alerta"]] = int(prediction["Prediccion"])
        evaluation = registro["datos"]["evaluacion"]
        result["Umbral_Score"] = registro["decision"]["umbral_score"]
        result["Id_Modelo"] = registro["id_modelo"]
        result["Version_Modelo"] = registro["version"]
        result["Tipo_Evaluacion"] = evaluation["tipo"]
        result["Evaluacion_Desde"] = evaluation["desde"]
        result["Evaluacion_Hasta"] = evaluation["hasta"]
        result["Alcance_Consulta"] = ALCANCE_CONSULTA
        result["Advertencia_Score"] = ADVERTENCIA_SCORE
        return result


def load_cloud_data():
    """Verifica y carga solo los recursos necesarios para la aplicación web."""

    registry_path = ROOT / "models/victimas/modelo_principal.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    dataset_path = ROOT / registry["datos"]["ruta"]
    if sha256_archivo(dataset_path) != registry["datos"]["sha256"]:
        raise ValueError("El dataset no coincide con la versión registrada.")
    data = pd.read_parquet(dataset_path)
    if data.duplicated(KEYS).any():
        raise ValueError("El dataset tiene claves duplicadas.")
    data = preparar_base_historica(data)

    prediction_name = (
        "reports/evaluation_victimas/"
        "predicciones_random_forest_ajustado_2023_2024.parquet"
    )
    prediction_path = ROOT / prediction_name
    if sha256_archivo(prediction_path) != _prediction_hash(registry, prediction_name):
        raise ValueError("Las predicciones no coinciden con la evaluación cerrada.")
    predictions = pd.read_parquet(prediction_path)
    predictions["Fecha_Acc"] = pd.to_datetime(predictions["Fecha_Acc"])
    if predictions.duplicated(KEYS).any():
        raise ValueError("Las predicciones tienen claves duplicadas.")
    if len(predictions) != registry["datos"]["evaluacion"]["filas"]:
        raise ValueError("El número de predicciones no coincide con el registro.")

    test = data[data["Periodo"].eq("test")].copy()
    test["Fecha_Acc"] = pd.to_datetime(test["Fecha_Acc"])
    check = test[KEYS + ["Alto_Riesgo"]].merge(
        predictions,
        on=KEYS,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )
    if not check["_merge"].eq("both").all():
        raise ValueError("Dataset y predicciones no describen los mismos casos.")
    if not check["Alto_Riesgo_x"].eq(check["Alto_Riesgo_y"]).all():
        raise ValueError("Las etiquetas congeladas no coinciden con el dataset.")
    expected_alerts = (
        predictions["Score"] >= registry["decision"]["umbral_score"]
    ).astype(int)
    if not predictions["Prediccion"].eq(expected_alerts).all():
        raise ValueError("Las alertas congeladas no respetan el umbral registrado.")
    if not np.isfinite(predictions["Score"]).all():
        raise ValueError("Las puntuaciones congeladas no son finitas.")

    manifest_path = ROOT / "data/dashboard/manifest.json"
    manifest = _read_json(manifest_path, "el manifiesto del dashboard")
    manifest_files = manifest.get("archivos")
    if not isinstance(manifest_files, dict):
        raise ValueError("El manifiesto del dashboard no contiene archivos válidos.")
    required = [
        "data/dashboard/siniestros_actores.parquet",
        "data/reference/localidades_sdp_referencia.geojson",
        *[f"reports/evaluation_victimas/{name}.csv" for name in REPORTS],
    ]
    for relative_path in required:
        if sha256_archivo(ROOT / relative_path) != manifest_files.get(relative_path):
            raise ValueError(
                f"Integridad incorrecta del recurso del dashboard: {relative_path}"
            )

    actors = pd.read_parquet(ROOT / required[0])
    actors["Fecha_Acc"] = pd.to_datetime(actors["Fecha_Acc"])
    geojson = _prepare_geojson(
        _read_json(ROOT / required[1], "la cartografía de localidades"),
        registry["categorias"]["Localidad"],
    )
    reports = {
        name: pd.read_csv(ROOT / f"reports/evaluation_victimas/{name}.csv")
        for name in REPORTS
    }
    consulta = FrozenConsulta(FrozenModelReference(registry), data, predictions)
    return DashboardData(consulta, predictions, actors, geojson, reports, manifest)

