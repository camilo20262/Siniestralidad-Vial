# Ficha técnica del modelo principal

**Random Forest ajustado — siniestros con víctimas en Bogotá**  
Versión académica 1.0 · Identificador: `rf_victimas_bogota_v1.0` · Cierre: 12 de septiembre de 2026.

## 1. Decisión de cierre

Se declara al **Random Forest ajustado con umbral de score 0,52** como modelo principal del prototipo de tesis. Esta decisión fija la versión que se utilizará como referencia en la documentación y en la integración del dashboard. Es un cierre académico: su utilidad operativa todavía requiere validación futura.

La configuración base se conserva como comparación: Random Forest de 200 árboles, profundidad máxima 12 y umbral 0,55. Los archivos de ambos modelos tienen identidad y resultados separados.

El [registro del modelo principal](../../models/victimas/modelo_principal.json) identifica el pipeline, sus hiperparámetros completos, variables, umbral, referencias y huellas SHA-256. La entrada de carga es `src.modelo_principal.cargar_modelo_principal()`. El archivo histórico `pipeline_modelo_seleccionado.pkl` corresponde al modelo base de 04B, aunque su nombre sugiera otra cosa.

## 2. Propósito y alcance

El modelo asigna una puntuación a cada combinación **localidad × franja horaria × fecha** para identificar casos etiquetados como `Alto_Riesgo`. Está destinado a la exploración académica y la priorización de condiciones asociadas con la frecuencia de siniestros con víctimas registrados en Bogotá.

La puntuación se encuentra entre 0 y 1, pero **no está calibrada como probabilidad**. Tampoco representa la probabilidad individual de accidentarse, el número de personas que resultarán lesionadas o fallecidas, ni la peligrosidad causal de una localidad.

## 3. Datos y definición de la etiqueta

Fuente local: hoja `Siniestros` de `data/raw/base-anuario-de-siniestralidad-2024.xlsx`. Se incluyen los registros `Con Heridos` y `Con Muertos` de `Gravedad_Indicador_Tradicional`. Los conteos son de **siniestros**, no de personas. El escenario de solo daños queda fuera de este modelo; los reportes de cobertura permiten contrastar ambos universos.

El dataset preparado por 03B contiene 204.560 filas: 20 localidades × cuatro franjas × 2.557 días, incluyendo combinaciones con cero siniestros registrados. Agrupa 85.199 siniestros con víctimas.

| Periodo | Filas localidad–franja–día | Siniestros | Etiquetas positivas | Prevalencia |
|---|---:|---:|---:|---:|
| Entrenamiento 2018–2022 | 146.080 | 59.288 | 24.907 | 17,05 % |
| Evaluación retrospectiva 2023–2024 | 58.480 | 25.911 | 11.118 | 19,01 % |

Hay dos umbrales distintos:

- **Umbral de etiqueta:** cuantil 2/3 del conteo diario de cada localidad–franja en entrenamiento. `Alto_Riesgo = 1` cuando el conteo del día es estrictamente mayor que ese valor.
- **Umbral de decisión:** `Score_Priorizacion >= 0.52` activa `Alerta_Modelo = 1`. Es el punto de corte del modelo seleccionado con validación temporal.

| Umbral del conteo | Combinaciones | Condición para etiqueta positiva |
|---|---:|---|
| 0 | 49 | Al menos un siniestro con víctima |
| 1 | 28 | Dos o más siniestros con víctimas |
| 2 | 3 | Tres o más siniestros con víctimas |

La etiqueta combina ocurrencia y frecuencia elevada según el grupo. Una alerta de una localidad no equivale necesariamente al mismo volumen absoluto en otra. Los 80 umbrales quedan registrados en [umbrales_etiqueta_principal.csv](../../models/victimas/umbrales_etiqueta_principal.csv).

## 4. Entradas y preprocesamiento

El pipeline recibe estas 12 variables, preparadas conforme a 03B:

| Variable | Significado y formato |
|---|---|
| `Localidad` | Una de las 20 categorías registradas, con nombres y acentos originales |
| `Franja_Horaria` | `Madrugada` 00:00–05:59, `Mañana` 06:00–11:59, `Tarde` 12:00–17:59, `Noche` 18:00–23:59 |
| `Dia_Semana` | Nombre en inglés, como `Monday`, generado por 03B |
| `Mes` | Entero de 1 a 12 |
| `Es_Fin_de_Semana` | Indicador 0/1 para sábado o domingo |
| `Es_Festivo` | Indicador 0/1 del calendario colombiano utilizado en 03B |
| `Accidentes_Prom_7d` | Promedio de conteos anteriores dentro de los últimos siete días del grupo |
| `Accidentes_Prom_30d` | Promedio de conteos anteriores dentro de los últimos 30 días del grupo |
| `Accidentes_Semana_Anterior` | Conteo del mismo grupo siete días antes |
| `Sin_Historial_Accidentes_Prom_7d` | Indicador 0/1 de ausencia de historial para el promedio de siete días |
| `Sin_Historial_Accidentes_Prom_30d` | Indicador 0/1 de ausencia de historial para el promedio de 30 días |
| `Sin_Historial_Accidentes_Semana_Anterior` | Indicador 0/1 de ausencia del conteo de siete días antes |

Las tres variables categóricas se transforman con `OneHotEncoder(handle_unknown='ignore')`; las numéricas pasan sin estandarización. Aunque el pipeline permite categorías desconocidas, el cargador de referencia las rechaza porque quedan fuera del universo evaluado.

Los promedios aplican un desplazamiento de un día y excluyen el día que se predice. Al inicio de la serie usan el historial disponible; los faltantes iniciales se rellenan con cero y se acompañan de sus indicadores. El conteo del día, la etiqueta, `Periodo` y la fecha no entran directamente como predictores.

La evaluación presupone que los conteos de días anteriores ya están disponibles. No valida pronósticos de varios días sin actualizar los históricos, ni la disponibilidad real de la fuente en tiempo operativo. El cargador recibe variables preparadas; no crea históricos a partir de una fecha solicitada.

## 5. Configuración y selección

| Parámetro | Valor cerrado |
|---|---|
| `n_estimators` | 300 |
| `max_depth` | `None`, sin límite explícito |
| `min_samples_leaf` | 20 |
| `min_samples_split` | 2 |
| `max_features` | `sqrt` |
| `class_weight` | `balanced` |
| `criterion` | `gini` |
| `bootstrap` | `True` |
| `random_state` | 42 |
| `n_jobs` | -1 |
| Umbral del score | 0,52, con comparación `>=` |

04B seleccionó la familia Random Forest. Después, 04C comparó **ocho configuraciones de esta familia**: entrenar 2018–2019 y validar 2020; entrenar 2018–2020 y validar 2021; entrenar 2018–2021 y validar 2022. La etiqueta, el preprocesamiento y el modelo se ajustan con el pasado disponible en cada corte.

El candidato 3 obtuvo la mayor Average Precision media: **0,2552**, frente a **0,2493** del candidato base. La desviación entre los tres años fue 0,0653; describe variación temporal y no es un intervalo de confianza ni una prueba de significancia. Se selecciona el mejor candidato de esta búsqueda acotada, sin afirmar que sea el óptimo global.

Una vez elegida la configuración, se tomó el umbral que maximiza el F1 agregado de sus predicciones fuera de muestra de 2020–2022: 0,52. Las mismas validaciones participan en la selección de configuración y de umbral; las métricas de selección no constituyen una evaluación independiente. El periodo 2023–2024 no intervino en el cálculo de esta búsqueda, pero ya había sido inspeccionado durante el desarrollo: se mantiene su carácter retrospectivo.

Finalmente se entrenó con 2018–2022. La elección por F1 no incorpora costos operativos acordados para falsas alertas y omisiones; el umbral sigue siendo exploratorio.

## 6. Resultados verificados en 05B

| Métrica | RF base, umbral 0,55 | RF ajustado, umbral 0,52 |
|---|---:|---:|
| F1 | 0,3982 | 0,4058 |
| AUC-ROC | 0,6853 | 0,6933 |
| Average Precision | 0,3038 | 0,3098 |
| Precisión | 30,11 % | 29,41 % |
| Recall | 58,77 % | 65,44 % |
| Brier, menor es mejor | 0,2304 | 0,2221 |
| Positivos detectados | 6.534 | 7.276 |
| Falsas alertas | 15.168 | 17.467 |
| Positivos omitidos | 4.584 | 3.842 |
| Negativos correctos | 32.194 | 29.895 |

El modelo ajustado detecta 742 positivos adicionales y genera 2.299 falsas alertas adicionales: aproximadamente **3,10 falsas alertas adicionales por cada positivo adicional detectado**. Estos cambios en precisión y recall reflejan conjuntamente el ajuste de configuración y el cambio de umbral.

La línea base que asigna a todas las filas la prevalencia de entrenamiento tiene Brier **0,1544**, mejor que el **0,2221** del modelo. El score puede apoyar el ordenamiento de casos, pero su interpretación como probabilidad de alto riesgo no está respaldada por esta evaluación.

## 7. Limitaciones territoriales y temporales

- **Candelaria:** 157 etiquetas positivas y ninguna detectada. El score máximo de 0,3227 queda por debajo del umbral 0,52. No se adopta el umbral territorial calculado retrospectivamente en 05B.
- **Sumapaz:** dos etiquetas positivas y ninguna detectada. Su tamaño impide conclusiones territoriales robustas.
- **Madrugada:** recall 39,43 %, frente a 74,42 % en Noche y 74,80 % en Mañana. Sigue siendo la franja con menor recall.
- **Promedio territorial:** F1 macro 0,3474 frente a F1 global 0,4058. La mejora global no supone una detección homogénea.
- **Volumen histórico:** correlación de Spearman con recall de aproximadamente -0,065. No permite atribuir el problema general al bajo volumen.
- **Importancia:** localidad y franja dominan la permutación. La importancia predictiva no demuestra causalidad; se estimó en una muestra de 5.000 filas con tres repeticiones.
- **Generalización:** no hay evaluación prospectiva ni estimación concluyente de incertidumbre. Los conteos registrados no se ajustan por exposición al tránsito, población o distancia recorrida.

## 8. Identidad, carga y mantenimiento

Pipeline principal: `models/victimas/pipeline_random_forest_ajustado_victimas.pkl`. Incluye el preprocesador y el clasificador ajustados. Las salidas oficiales del cargador son `Score_Priorizacion` y `Alerta_Modelo`; esta última aplica el umbral cerrado. Usar directamente `pipeline.predict()` aplicaría la regla de clasificación interna y no garantiza el punto de corte 0,52.

El entorno de entrenamiento declarado es Python 3.12.14 y scikit-learn 1.9.0. La verificación se realizó con pandas 3.0.3, NumPy 2.5.1, joblib 1.5.3 y PyArrow 23.0.1. El registro distingue el entorno verificado de las versiones declaradas al entrenar; no se ha probado compatibilidad arbitraria entre versiones.

Desde la raíz del proyecto:

```python
import pandas as pd
from src.modelo_principal import cargar_modelo_principal

modelo = cargar_modelo_principal()
datos = pd.read_parquet('data/processed/dataset_victimas_localidad_franja_fecha.parquet')
resultado = modelo.predecir(datos.loc[datos.Periodo.eq('test')].head())
```

El registro y el pipeline se localizan desde el módulo, sin depender del directorio activo una vez importado. El cargador comprueba identidad del artefacto, versión de scikit-learn, columnas y parámetros; también valida las entradas. Se usan exclusivamente los artefactos locales del proyecto.

La comprobación completa se ejecuta con `.venv/bin/python scripts/verificar_modelo_principal.py`. Reproduce las 58.480 predicciones retrospectivas, sus métricas, los 80 umbrales de etiqueta y las huellas de las evidencias. No entrena modelos. El [resultado del cierre](verificacion_cierre.json) conserva la verificación de esta versión.

Reentrenar 04C puede reemplazar el archivo del modelo ajustado. Si cambia su contenido, el cargador detiene la carga hasta que se revise el nuevo modelo. Cualquier cambio de datos, etiqueta, configuración o umbral requiere reevaluar con 05B, actualizar expresamente registro y ficha, y asignar una nueva versión. El dataset y los resultados 2018–2024 no representan datos actuales en tiempo real.

## 9. Evidencias del cierre

### Ampliación de la evaluación, sin cambiar el modelo

La ampliación de 05B incorpora una referencia de tasa histórica por localidad–franja–día de semana, estimada solo con entrenamiento. En 2023–2024 obtiene AP 0,3087, AUC 0,6931 y Brier 0,1438, frente a 0,3098, 0,6933 y 0,2221 del RF ajustado. En los tres cortes temporales la AP media es 0,2503 para la referencia y 0,2552 para el RF. Los intervalos exploratorios del bootstrap semanal pareado de la diferencia en AP y AUC incluyen cero; no demuestran equivalencia ni superioridad concluyente del RF.

Se conserva `rf_victimas_bogota_v1.0` y su umbral 0,52 como referencia académica, sin reentrenamiento ni sustitución. El valor incremental frente a esta alternativa sencilla debe formar parte de la discusión. Las evidencias congeladas se comparan numéricamente con tolerancia absoluta de 1e-12 antes de conservar sus bytes originales; las decisiones se verifican exactamente. Esto evita confundir redondeo de sumas paralelas con cambios del modelo.

Resultados adicionales: [comparación histórica](../evaluation_victimas/comparacion_referencias_historicas.csv), [bootstrap](../evaluation_victimas/bootstrap_rf_vs_referencia_resumen.csv), [conclusión ampliada](../evaluation_victimas/conclusion_ejecutiva.md) y [verificación de 05B](../evaluation_victimas/verificacion_ampliacion_05b.json).

### Archivos de referencia

- [Registro oficial](../../models/victimas/modelo_principal.json) y [catálogo de artefactos](../../models/victimas/README.md).
- [Búsqueda temporal de 04C](../tuning_victimas/busqueda_temporal_resumen.csv) y [selección del umbral](../tuning_victimas/seleccion_umbral.csv).
- [Métricas globales de 05B](../evaluation_victimas/metricas_globales.csv), [localidades](../evaluation_victimas/metricas_random_forest_ajustado_por_localidad.csv) y [franjas](../evaluation_victimas/metricas_random_forest_ajustado_por_franja.csv).
- [Brier frente a líneas base](../evaluation_victimas/comparacion_brier_lineas_base.csv) y [conclusión del 05B](../evaluation_victimas/conclusion_ejecutiva.md).
