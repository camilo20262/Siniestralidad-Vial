# Siniestralidad Vial en Bogotá

Prototipo académico de aprendizaje automático para identificar combinaciones de **localidad, franja horaria y fecha** con frecuencia elevada de accidentes registrados en Bogotá, utilizando datos de **2018–2024**.

El proyecto sigue las etapas de CRISP-DM y busca apoyar la exploración y priorización preventiva. Actualmente incluye preparación de datos, entrenamiento, evaluación retrospectiva y validación temporal expansiva. El dashboard está pendiente.

## Datos y definición del problema

La fuente utilizada es `base-anuario-de-siniestralidad-2024.xlsx`, con las hojas Siniestros, Vehiculos, Actor_vial y Diccionario. Contiene 278.614 siniestros de 2015–2024; el filtro del estudio conserva 177.099 accidentes de 2018–2024.

El dataset procesado contiene **204.560 filas y 16 columnas**: 20 localidades × 4 franjas × 2.557 días. Incluye combinaciones sin accidentes registrados.

- **Franjas:** madrugada (00:00–05:59), mañana (06:00–11:59), tarde (12:00–17:59) y noche (18:00–23:59).
- **Objetivo `Alto_Riesgo`:** el conteo del día supera el cuantil 2/3 histórico de su localidad y franja, calculado en entrenamiento.
- **Predictores:** localidad, franja, calendario, festivos, históricos de 7 y 30 días, conteo de siete días atrás e indicadores de ausencia de historial.
- **Partición principal:** entrenamiento 2018–2022 y evaluación retrospectiva 2023–2024.

La etiqueta mide frecuencia elevada respecto al historial del grupo. No representa gravedad, riesgo individual ni una comparación directa de peligrosidad entre localidades. Los vehículos y actores viales se exploran, pero sus hojas todavía no se integran como predictores del modelo principal.

## Estructura actual

```text
Siniestralidad-Vial/
├── data/
│   ├── raw/                  # Excel original, almacenado con Git LFS
│   └── processed/            # Dataset preparado en Parquet
├── notebooks/
│   ├── 01_Comprension_del_Negocio.ipynb
│   ├── 02_Comprension_de_los_Datos.ipynb
│   ├── 03_Preparacion_de_los_Datos (3).ipynb
│   ├── 04_Modelado.ipynb
│   └── 05_Evaluacion.ipynb
├── models/                   # Tres modelos y dos preprocesadores
├── reports/evaluation/       # CSV, figuras, predicciones y conclusiones
├── .gitattributes
├── .gitignore
└── README.md
```

## Preparación del entorno

Se necesitan Python, Git y Git LFS. El Excel supera el tamaño permitido para archivos Git ordinarios; para descargar su contenido completo:

```bash
git lfs install
git clone https://github.com/camilo20262/Siniestralidad-Vial.git
cd Siniestralidad-Vial
git lfs pull
```

Crea un entorno virtual e instala las dependencias usadas por los notebooks:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pandas numpy matplotlib scikit-learn xgboost joblib pyarrow openpyxl holidays jupyterlab
```

En Windows, activa el entorno con `.venv\Scripts\activate` en lugar de `source .venv/bin/activate`.

El entorno local consultado usa Python 3.14.5, pandas 3.0.3, NumPy 2.5.1, scikit-learn 1.9.0, XGBoost 3.4.0 y joblib 1.5.3. Son una referencia del entorno actual, no una garantía de compatibilidad entre versiones. Aún no existe un archivo de dependencias con versiones fijadas; los modelos serializados pueden requerir versiones compatibles con las usadas al entrenarlos.

## Ejecución

Inicia Jupyter desde `notebooks/`, porque las rutas del código son relativas a esa carpeta:

```bash
cd notebooks
jupyter lab
```

Selecciona el entorno instalado y ejecuta las celdas de cada notebook en orden.

| Notebook | Propósito |
|---|---|
| 01 | Objetivos, alcance y comprensión del negocio. |
| 02 | Exploración de la estructura y calidad de los datos originales. |
| 03 | Limpieza, variables históricas, etiqueta y exportación del dataset. |
| 04 | Entrenamiento y guardado de Regresión Logística, Random Forest y XGBoost. |
| 05 | Evaluación de artefactos, calibración, sensibilidad, errores y validación temporal. |

Para consultar la evaluación con los artefactos incluidos, puede ejecutarse directamente **05**. Este notebook también entrena modelos experimentales en sus análisis de sensibilidad y validación temporal, por lo que su ejecución completa requiere más tiempo que cargar y predecir. Los modelos originales se conservan.

Ejecutar **03** vuelve a generar el dataset procesado; ejecutar **04** vuelve a entrenar y guardar los modelos y preprocesadores. Los reportes de **05** se escriben en `reports/evaluation/`.

## Resultados actuales

Evaluación retrospectiva de 2023–2024 con umbral de decisión 0,5:

| Modelo | F1 | AUC-ROC | Average Precision | Precisión | Recall |
|---|---:|---:|---:|---:|---:|
| XGBoost | 0,1973 | 0,7053 | 0,1329 | 0,1476 | 0,2972 |
| Regresión Logística | 0,1803 | 0,6577 | 0,1128 | 0,1330 | 0,2798 |
| Random Forest | 0,1551 | 0,6506 | 0,1053 | 0,1071 | 0,2809 |

XGBoost presenta el mejor desempeño relativo en este periodo. Produce 1.096 verdaderos positivos, 6.328 falsos positivos y 2.592 falsos negativos. La Average Precision de la línea base es 0,0631.

**La validación temporal interna ofrece un resultado diferente:** en los cortes expansivos con validaciones de 2020–2022, Random Forest obtiene la mayor Average Precision media (0,2245), seguido de XGBoost (0,2179) y Regresión Logística (0,2103). Esta comparación no demuestra por sí sola diferencias estadísticamente significativas y debe distinguirse del resultado retrospectivo de 2023–2024.

Otros hallazgos:

- El score medio de XGBoost es 29,23 %, frente a una prevalencia observada de 6,31 %: las puntuaciones no están bien calibradas.
- Eliminar `Localidad` en el modelo experimental reduce el AUC-ROC a 0,5887. Persisten señales territoriales indirectas en los históricos y en la etiqueta.
- Cambiar de 0,5 a 0,455 en 2024 agrega 176 positivos detectados y 1.523 falsas alertas: 8,65 falsas alertas adicionales por cada positivo adicional. El umbral 0,455 es exploratorio, seleccionado con 2023.
- El desempeño varía entre localidades y franjas; las métricas por grupo deben leerse junto con su prevalencia y número de positivos.

## Reportes principales

- [Conclusión ejecutiva](reports/evaluation/conclusion_ejecutiva.md)
- [Métricas globales](reports/evaluation/metricas_globales_umbral_05.csv)
- [Validación temporal: resumen](reports/evaluation/validacion_temporal_2018_2022_resumen.csv)
- [Calibración](reports/evaluation/resumen_calibracion_modelos.csv)
- [Métricas macro por localidad](reports/evaluation/metricas_macro_localidad.csv)
- [Errores por franja](reports/evaluation/errores_xgboost_por_franja.csv)
- [Importancia por permutación](reports/evaluation/importancia_permutacion_xgboost.csv)

## Limitaciones y próximos pasos

2023–2024 ya se utilizó para comparar modelos: constituye una evaluación retrospectiva, no una prueba final independiente. La validación temporal expansiva incorporada ajusta los umbrales de etiqueta, preprocesadores y modelos utilizando el pasado disponible en cada corte.

Los predictores históricos suponen disponibilidad de los conteos de días anteriores. La evaluación no valida pronósticos de varios días sin actualización del historial. La caída del volumen registrado entre periodos tampoco demuestra por sí sola subregistro.

La importancia de variables no representa causalidad ni porcentaje de accidentes explicado. En particular, la importancia elevada de Sumapaz puede reflejar la identificación de un grupo casi siempre negativo.

Los siguientes pasos son evaluar calibración con datos temporalmente separados, definir el costo operativo de alertas y omisiones, cuantificar incertidumbre y realizar una evaluación posterior independiente. El dashboard deberá presentar inicialmente **puntuaciones relativas**, con sus limitaciones, en lugar de probabilidades literales. El prototipo **no está listo para producción**.
