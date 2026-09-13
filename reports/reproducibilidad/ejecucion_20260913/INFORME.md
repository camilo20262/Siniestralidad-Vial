# Informe de reproducibilidad — 13 de septiembre de 2026

## Resultado

**Reproducción equivalente.** Se ejecutó completa la cadena 03B → 04B → 04C → 05B
en una carpeta aislada y un entorno virtual nuevo, sin acceso a los paquetes del
entorno original mediante `system-site-packages`. Se instalaron los requisitos
declarados. No se copiaron modelos, datos procesados ni reportes oficiales para
alimentar los notebooks: se reconstruyeron desde una copia del Excel original.

Los **181 archivos oficiales comprobados permanecieron intactos**, verificados
mediante SHA-256. Esto incluye los notebooks originales: las salidas de esta
prueba están guardadas exclusivamente en las copias de este ensayo.

## Ejecuciones guardadas

| Notebook | Celdas de código ejecutadas | Errores | Tiempo |
| --- | ---: | ---: | ---: |
| [03B — Preparación](notebooks/03B_Preparacion_Datos_Con_Victimas.ipynb) | 9 | 0 | 32,62 s |
| [04B — Modelado](notebooks/04B_Modelado_Con_Victimas.ipynb) | 12 | 0 | 44,74 s |
| [04C — Ajuste](notebooks/04C_Ajuste_Hiperparametros_Con_Victimas.ipynb) | 6 | 0 | 73,74 s |
| [05B — Evaluación](notebooks/05B_Evaluacion_Con_Victimas.ipynb) | 27 | 0 | 22,43 s |
| Total | 54 | 0 | 173,53 s |

Los tiempos corresponden a la ejecución de notebooks; excluyen la preparación
del entorno y las comprobaciones externas. Se realizaron nuevamente los 40
ajustes de modelos previstos en 04B y 04C. Se generaron 57 archivos de reportes.

## Comparación contra la versión oficial

- **Dataset:** coincidencia exacta de las 204.560 filas y 16 columnas, incluyendo
  tipos, orden, variables, fechas, conteos, etiquetas y división train/test.
- **Selección inicial:** Random Forest; mismas 12 variables y semilla 42;
  umbral base 0,55.
- **Ajuste:** mismo candidato 3 y mismo umbral 0,52. Configuración seleccionada:
  300 árboles, profundidad sin límite, mínimo de 20 observaciones por hoja,
  `max_features="sqrt"` y `class_weight="balanced"`.
- **Cuatro modelos:** mismos esquemas de entrada e hiperparámetros.
- **14 tablas:** equivalentes. Incluyen validación temporal, predicciones fuera
  de muestra de 2020–2022, búsquedas y umbrales, predicciones retrospectivas de
  2023–2024, métricas globales y territoriales, referencias históricas y resumen
  del bootstrap.
- **Predicciones finales:** las 58.480 decisiones de alerta coinciden. La mayor
  diferencia de puntuación fue `4,440892098500626e-16`, muy inferior a la tolerancia
  absoluta prefijada de `1e-10`; no se cambió la tolerancia para obtener el resultado.
- **Modelo ajustado:** incluso su archivo serializado coincide en SHA-256. Los
  tres modelos base no son idénticos en bytes, pero reproducen la configuración
  y las predicciones dentro de la tolerancia.

### Métricas finales reproducidas

| Métrica | Random Forest ajustado, umbral 0,52 |
| --- | ---: |
| Average Precision | 0,3098375997 |
| AUC-ROC | 0,6933242182 |
| F1 | 0,4057890187 |
| Precisión | 0,2940629673 |
| Recall | 0,6544342508 |
| Brier | 0,2220882670 |
| Verdaderos negativos / falsos positivos | 29.895 / 17.467 |
| Falsos negativos / verdaderos positivos | 3.842 / 7.276 |

## Particularidades registradas

1. El nuevo entorno usa Python 3.12.14. Los metadatos originales de 04B declaran
   Python 3.14.5 y los de 04C, Python 3.12.14. La equivalencia observada acredita
   esta ejecución concreta; no garantiza resultados idénticos en cualquier
   versión o plataforma. Se conserva la lista completa de dependencias resueltas.
2. 05B necesita un registro de modelo cerrado. Se construyó uno **local y no
   oficial** con los artefactos regenerados. No se precargaron reportes oficiales
   como resultados esperados. El código de los cuatro notebooks no se modificó.
3. La primera comparación marcó una diferencia artificial de configuración en
   XGBoost porque `NaN != NaN` para su parámetro `missing`. Se corrigió únicamente
   el comparador, se comprobó que detecta cambios reales y se repitió la auditoría
   sin reentrenar ni alterar resultados. El JSON anterior se conserva como
   `resultado_previo_*.json`; el estado vigente es el de `resultado.json`.
4. Hubo avisos de identificadores de celdas ausentes en el formato original y de
   comunicación local del kernel. No hubo errores de ejecución. Los notebooks
   originales no se reescribieron para resolver esos avisos.

## Qué queda cerrado y qué no

Queda cerrada la comprobación solicitada del recorrido completo con
reentrenamiento y la conservación de 03B y 04B ejecutados en copias aisladas.
No se promovió un modelo nuevo ni se sobrescribió el modelo principal.

La prueba demuestra **reproducibilidad**, no mejora del desempeño. 2023–2024
sigue siendo una evaluación retrospectiva ya analizada; no vuelve a ser un
test intacto por repetirla. Se mantienen las advertencias sobre calibración,
desigualdad territorial y ventaja limitada frente a referencias históricas.

Detalle verificable: [resultado.json](resultado.json),
[ejecuciones_notebooks.json](ejecuciones_notebooks.json) y
[entorno.json](entorno.json). Instrucciones: [README](../README.md).
