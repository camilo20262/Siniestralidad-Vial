"""Genera evidencia adicional con 2022 separado de configuración y umbral.

No carga, reemplaza ni serializa modelos oficiales. La carpeta de salida debe
ser nueva para preservar las evidencias ya cerradas.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys

import pandas as pd
import sklearn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.validacion_independiente import ejecutar_estimacion


def digest(path: Path) -> str:
    value = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def serializable(value):
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--salida",
        type=Path,
        default=ROOT / "reports/validacion_independiente_victimas",
        help="Carpeta nueva para las evidencias; nunca se sobrescribe.",
    )
    args = parser.parse_args()
    output = args.salida.resolve()
    if output.exists():
        raise FileExistsError(f"No se sobrescriben evidencias existentes: {output}")
    output.mkdir(parents=True, exist_ok=False)

    data_path = ROOT / "data/processed/dataset_victimas_localidad_franja_fecha.parquet"
    result = ejecutar_estimacion(pd.read_parquet(data_path))
    result["detalle"].to_csv(output / "busqueda_2020_2021_detalle.csv", index=False, encoding="utf-8-sig")
    result["resumen"].to_csv(output / "busqueda_2020_2021_resumen.csv", encoding="utf-8-sig")
    result["oof_seleccion"].to_parquet(output / "predicciones_oof_2020_2021.parquet", index=False)
    result["seleccion_umbral"].to_csv(output / "seleccion_umbral_2020_2021.csv", index=False, encoding="utf-8-sig")
    result["metricas_evaluacion"].to_csv(output / "evaluacion_temporal_separada_2022.csv", index=False, encoding="utf-8-sig")
    result["predicciones_evaluacion"].to_parquet(output / "predicciones_evaluacion_2022.parquet", index=False)
    result["umbrales_etiqueta_evaluacion"].to_csv(output / "umbrales_etiqueta_2018_2021.csv", index=False, encoding="utf-8-sig")

    metric = result["metricas_evaluacion"].iloc[0].to_dict()
    design = result["diseno"]
    record = {
        "estado": "estimacion_adicional_completada",
        "fecha": "2026-10-02",
        "proposito": "Separar una evaluación de la selección de configuración y umbral sin cambiar el modelo oficial.",
        "seleccion": {
            "cortes": [
                {"train_hasta": train_end, "validacion": year}
                for train_end, year in design.cortes_seleccion
            ],
            "anios_validacion": [year for _, year in design.cortes_seleccion],
            "candidatos": int(result["resumen"].shape[0]),
            "mejor_candidato": result["mejor_candidato"],
            "umbral": result["mejor_umbral"],
        },
        "evaluacion_separada": {
            "train_hasta": design.entrenamiento_evaluacion_hasta,
            "anio": design.anio_evaluacion,
            "participo_en_seleccion": False,
            "metricas": metric,
        },
        "alcance": (
            "Separación procedimental adicional. 2022 no participa en esta selección, "
            "pero ya había sido inspeccionado en el desarrollo histórico; no es una prueba prospectiva ni externa."
        ),
        "modelo_oficial_modificado": False,
        "dataset": str(data_path.relative_to(ROOT)),
        "dataset_sha256": digest(data_path),
        "version_python": platform.python_version(),
        "version_sklearn": sklearn.__version__,
    }
    (output / "resultado.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2, default=serializable), encoding="utf-8"
    )
    summary = f"""# Estimación temporal adicional con 2022 separado

**Fecha:** 2 de octubre de 2026\
**Estado:** evidencia complementaria; no reemplaza `rf_victimas_bogota_v1.0`.

## Diseño

La configuración se seleccionó por Average Precision media en los cortes
2018–2019 → 2020 y 2018–2020 → 2021. El umbral se eligió por F1 agregado
usando solo las predicciones fuera de muestra de 2020–2021. Después se reajustó
la configuración elegida con 2018–2021 y se evaluó una vez en 2022. En cada
corte se recalculó la etiqueta con el pasado disponible.

## Resultado

- Candidato seleccionado: **{result['mejor_candidato']}**.
- Umbral seleccionado sin 2022: **{result['mejor_umbral']:.3f}**.
- Evaluación 2022: F1 **{metric['F1']:.4f}**, AP **{metric['Average_Precision']:.4f}**,
  AUC-ROC **{metric['AUC_ROC']:.4f}**, precisión **{metric['Precision']:.4f}**,
  recall **{metric['Recall']:.4f}** y Brier **{metric['Brier']:.4f}**.
- Casos 2022: {int(metric['N_Evaluacion']):,}; positivos: {int(metric['Positivos_Evaluacion']):,};
  TP {int(metric['TP']):,}, FP {int(metric['FP']):,}, FN {int(metric['FN']):,}, TN {int(metric['TN']):,}.

## Interpretación

2022 no intervino en la configuración ni en el umbral de **este procedimiento**.
Sin embargo, ya había sido inspeccionado por las validaciones históricas del
proyecto; por tanto, esta es una separación metodológica adicional, no una prueba
prospectiva, externa o nunca observada. No se serializó ningún modelo y no se
modificaron el pipeline, el umbral 0,52 ni el registro oficiales.
"""
    (output / "conclusion_ejecutiva.md").write_text(summary, encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2, default=serializable))


if __name__ == "__main__":
    main()
