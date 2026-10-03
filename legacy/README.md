# Manifiesto de artefactos históricos

Los artefactos siguientes son **legado** del escenario de todos los siniestros,
incluidos los registros de solo daños. No forman parte de la línea vigente con
víctimas y no alimentan el dashboard:

- `notebooks/03_Preparacion_de_los_Datos (3).ipynb`
- `notebooks/04_Modelado.ipynb`
- `notebooks/05_Evaluacion.ipynb`
- `models/modelo_logistica.pkl`
- `models/modelo_random_forest.pkl`
- `models/modelo_xgboost.pkl`
- `models/preprocesador_arboles.pkl`
- `models/preprocesador_logistica.pkl`
- `reports/evaluation/`

Se conservaron en sus rutas originales porque los notebooks cerrados, sus
salidas ejecutadas, pruebas y documentos históricos las citan directamente.
Moverlos rompería esa trazabilidad y contradiría la política de no reescribir
artefactos cerrados. Cada notebook tiene una portada inequívoca y
[`config/artefactos.json`](../config/artefactos.json) asigna el estado
`historico` a cada modelo.

La línea vigente está en 02B → 03B → 04B → 04C → 05B y su única
autoridad es `models/victimas/modelo_principal.json`.
