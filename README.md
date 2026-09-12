# Siniestralidad vial con víctimas en Bogotá

Prototipo académico de aprendizaje automático para priorizar combinaciones de **localidad, franja horaria y fecha** asociadas con la ocurrencia o frecuencia elevada de siniestros con personas heridas o fallecidas en Bogotá. El periodo analizado es **2018–2024** y la metodología sigue CRISP-DM.

## Escenario principal

El escenario principal utiliza únicamente siniestros **con víctimas**. Esta decisión evita mezclar dos universos de registro no comparables: desde 2022, el IPAT dejó de ser obligatorio para accidentes con solo daños materiales. La cobertura anual de siniestros con víctimas se mantiene estable entre 2022 y 2024, mientras que los registros de solo daños caen de 12.557 a 1.115 entre 2022 y 2023.

- **Unidad de análisis:** localidad × franja horaria × fecha.
- **Franjas:** madrugada, mañana, tarde y noche.
- **Entrenamiento:** 2018–2022.
- **Evaluación retrospectiva:** 2023–2024.
- **Modelo seleccionado:** Random Forest ajustado.
- **Umbral operativo exploratorio:** 0,52, elegido con predicciones fuera de muestra de 2020–2022.
- **Objetivo `Alto_Riesgo`:** el conteo supera el cuantil 2/3 histórico de su localidad y franja, calculado sin usar datos futuros.

En 49 de las 80 combinaciones localidad–franja el umbral histórico es cero. En esos grupos, la etiqueta significa que ocurrió al menos un siniestro con víctima; en los grupos de mayor volumen conserva el sentido de frecuencia superior a lo habitual. Por ello, el modelo produce una **puntuación de priorización**, no una probabilidad individual de accidente.

El escenario original con todos los siniestros se conserva en los notebooks 03, 04 y 05 como análisis de sensibilidad y evidencia del cambio de cobertura.

## Resultados principales

Evaluación retrospectiva del modelo seleccionado sobre 2023–2024:

| Modelo | Umbral | F1 | AUC-ROC | Average Precision | Precisión | Recall |
|---|---:|---:|---:|---:|---:|---:|
| **Random Forest ajustado** | **0,52** | **0,4058** | **0,6933** | **0,3098** | **0,2941** | **0,6544** |
| Random Forest base | 0,55 | 0,3982 | 0,6853 | 0,3038 | 0,3011 | 0,5877 |
| XGBoost | 0,50 | 0,3937 | 0,6800 | 0,3020 | 0,2793 | 0,6670 |
| Regresión Logística | 0,50 | 0,3633 | 0,6411 | 0,2702 | 0,2452 | 0,7004 |

El Random Forest ajustado detecta 7.276 positivos y omite 3.842; genera 17.467 falsas alertas. Mejora modestamente el ordenamiento y la cobertura frente a la configuración base, a cambio de más falsas alertas. La selección se hizo sin utilizar 2023–2024.

Hallazgos que deben acompañar cualquier uso del prototipo:

- El Brier del modelo ajustado es **0,2221**: mejora frente al modelo base, pero continúa peor que la línea base constante de **0,1544**. Los scores no deben comunicarse como probabilidades.
- Candelaria conserva 157 positivos y recall 0 con el modelo ajustado: su score máximo (0,3227) no alcanza el umbral global 0,52.
- Madrugada sigue siendo la franja más débil, aunque su recall sube a 39,43 %; Noche y Mañana alcanzan aproximadamente 74–75 %.
- Localidad y franja horaria son las variables con mayor importancia por permutación; esto no implica causalidad.

## Estructura

```text
Siniestralidad_Vial/
├── data/
│   ├── raw/                       # Fuente original
│   └── processed/                 # Datasets preparados
├── notebooks/
│   ├── 01_Comprension_del_Negocio.ipynb
│   ├── 02_Comprension_de_los_Datos.ipynb
│   ├── 02B_EDA_y_Analisis_Espacial_Con_Victimas.ipynb
│   ├── 03_Preparacion_de_los_Datos (3).ipynb
│   ├── 03B_Preparacion_Datos_Con_Victimas.ipynb
│   ├── 04_Modelado.ipynb
│   ├── 04B_Modelado_Con_Victimas.ipynb
│   ├── 04C_Ajuste_Hiperparametros_Con_Victimas.ipynb
│   ├── 05_Evaluacion.ipynb
│   └── 05B_Evaluacion_Con_Victimas.ipynb
├── models/
│   └── victimas/                  # Pipeline y modelos del escenario principal
├── reports/
│   ├── data_quality/
│   ├── eda_victimas/
│   ├── modeling_victimas/
│   ├── tuning_victimas/
│   └── evaluation_victimas/
├── dashboard/                     # Dashboard web interactivo
├── requirements.txt
└── README.md
```

## Ejecución reproducible

Se requieren Python, Git y Git LFS. Después de clonar el repositorio y descargar los archivos LFS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd notebooks
jupyter lab
```

Para reproducir el escenario principal, ejecutar **02B** para el EDA espacial y después **03B**, **04B**, **04C** y **05B**. El notebook 04C guarda el modelo ajustado en un archivo separado y no reemplaza el modelo base. El notebook 05B compara ambos y desarrolla la evaluación detallada del modelo ajustado.

## Dashboard

El dashboard en `dashboard/dist/` permite explorar métricas globales, por localidad y por franja. Presenta explícitamente la limitación de calibración y evita interpretar los scores como probabilidades. Sus datos proceden de los CSV generados por 05B.

## Alcance y limitaciones

La evaluación 2023–2024 es retrospectiva y ya participó en la comparación final; no constituye una prueba futura independiente. El prototipo no está listo para producción ni estima causalidad, gravedad futura o riesgo individual. Antes de un uso operativo se requiere validación prospectiva, calibración temporal separada, costos de falsas alertas y omisiones, e incertidumbre por subgrupo.

Reportes recomendados: [conclusión ejecutiva](reports/evaluation_victimas/conclusion_ejecutiva.md), [métricas globales](reports/evaluation_victimas/metricas_globales.csv), [métricas por localidad](reports/evaluation_victimas/metricas_random_forest_por_localidad.csv) y [calibración](reports/evaluation_victimas/comparacion_brier_lineas_base.csv).
