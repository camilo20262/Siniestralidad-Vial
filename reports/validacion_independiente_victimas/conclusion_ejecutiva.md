# Estimación temporal adicional con 2022 separado

**Fecha:** 2 de octubre de 2026\
**Estado:** evidencia complementaria; no reemplaza `rf_victimas_bogota_v1.0`.

## Diseño

La configuración se seleccionó por Average Precision media en los cortes
2018–2019 → 2020 y 2018–2020 → 2021. El umbral se eligió por F1 agregado
usando solo las predicciones fuera de muestra de 2020–2021. Después se reajustó
la configuración elegida con 2018–2021 y se evaluó una vez en 2022. En cada
corte se recalculó la etiqueta con el pasado disponible.

## Resultado

- Candidato seleccionado: **3**.
- Umbral seleccionado sin 2022: **0.540**.
- Evaluación 2022: F1 **0.4017**, AP **0.3077**,
  AUC-ROC **0.6959**, precisión **0.2995**,
  recall **0.6096** y Brier **0.2228**.
- Casos 2022: 29,200; positivos: 5,533;
  TP 3,373, FP 7,889, FN 2,160, TN 15,778.

## Interpretación

2022 no intervino en la configuración ni en el umbral de **este procedimiento**.
Sin embargo, ya había sido inspeccionado por las validaciones históricas del
proyecto; por tanto, esta es una separación metodológica adicional, no una prueba
prospectiva, externa o nunca observada. No se serializó ningún modelo y no se
modificaron el pipeline, el umbral 0,52 ni el registro oficiales.
