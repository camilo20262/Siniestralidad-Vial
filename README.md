# Siniestralidad vial con víctimas en Bogotá

Prototipo académico de aprendizaje automático para priorizar combinaciones de **localidad, franja horaria y fecha** asociadas con la ocurrencia o frecuencia elevada de siniestros con personas heridas o fallecidas en Bogotá. El periodo analizado es **2018–2024** y la metodología sigue CRISP-DM.

## Escenario principal

El escenario principal utiliza únicamente siniestros **con víctimas**. Esta decisión evita mezclar dos universos de registro no comparables: desde 2022, el IPAT dejó de ser obligatorio para accidentes con solo daños materiales. La cobertura anual de siniestros con víctimas se mantiene estable entre 2022 y 2024, mientras que los registros de solo daños caen de 12.557 a 1.115 entre 2022 y 2023.

- **Unidad de análisis:** localidad × franja horaria × fecha.
- **Franjas:** madrugada, mañana, tarde y noche.
- **Entrenamiento:** 2018–2022.
- **Evaluación retrospectiva:** 2023–2024.
- **Modelo principal cerrado:** Random Forest ajustado, versión académica `rf_victimas_bogota_v1.0`.
- **Umbral de decisión exploratorio:** 0,52, elegido con predicciones fuera de muestra de 2020–2022.
- **Objetivo `Alto_Riesgo`:** el conteo supera el cuantil 2/3 histórico de su localidad y franja, calculado sin usar datos futuros.

En 49 de las 80 combinaciones localidad–franja el umbral histórico es cero. En esos grupos, la etiqueta significa que ocurrió al menos un siniestro con víctima; en los grupos de mayor volumen conserva el sentido de frecuencia superior a lo habitual. Por ello, el modelo produce una **puntuación de priorización**, no una probabilidad individual de accidente.

El escenario original con todos los siniestros se conserva en los notebooks 03, 04 y 05 como análisis de sensibilidad y evidencia del cambio de cobertura.

También en ese escenario original hay grupos cuya etiqueta mide ocurrencia:
**19 de 80 (23,75 %)** tienen umbral de conteo cero, frente a **49 de 80 (61,25 %)**
en el principal con víctimas. Estos porcentajes son de grupos, no prevalencias
de la etiqueta. El [anexo de interpretación](docs/ANEXO_INTERPRETACION_ETIQUETA.md)
documenta la distribución completa, los grupos y su comprobación con entrenamiento.

## Modelo principal y ficha técnica

La [especificación vigente ESP-MODELO-01](docs/ESPECIFICACION_VIGENTE.md) formaliza
**RF ajustado, umbral 0,52** como requisito de las consultas y del dashboard.
Sustituye el requisito antiguo de 0,55, que se conserva únicamente para el RF base.
Esta aclaración no cambia modelos, umbrales calculados ni resultados históricos.

La [ficha técnica del modelo](reports/modelo_principal/ficha_tecnica_modelo.md) formaliza el cierre académico del 12 de septiembre de 2026. La configuración es de 300 árboles, profundidad sin límite, mínimo 20 observaciones por hoja, `max_features='sqrt'`, `class_weight='balanced'`, semilla 42 y umbral de score **0,52**.

El [registro oficial](models/victimas/modelo_principal.json) identifica el pipeline ajustado y conserva sus variables, parámetros, resultados y huellas de integridad. La entrada de referencia es `src.modelo_principal.cargar_modelo_principal()`: su método `predecir(datos_preparados)` devuelve el score y la alerta aplicando el umbral cerrado.

El modelo base de 200 árboles y umbral 0,55 se mantiene como referencia. **`pipeline_modelo_seleccionado.pkl` y `metadata_modelo.json` son archivos históricos de 04B y corresponden al modelo base.** Consulte el [catálogo de artefactos](models/victimas/README.md) para evitar confundirlos con el modelo principal.

Puede comprobar el cierre con `.venv/bin/python scripts/verificar_modelo_principal.py`. La comprobación reproduce las predicciones de 05B y detecta cambios en el modelo, los datos o las evidencias. Si se reentrena, se debe actualizar expresamente la versión después de evaluarla.

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
│   ├── evaluation_victimas/
│   └── modelo_principal/          # Ficha técnica y comprobación del cierre
├── src/                          # Carga e inferencia del modelo principal
├── scripts/                      # Generación de notebooks y verificación
├── dashboard/                     # Dashboard web interactivo
├── requirements.txt
└── README.md
```

## Ejecución reproducible

El entorno local verificado usa Python **3.12.14**, Git y Git LFS. La versión de Python se registra en `.python-version`. Después de clonar el repositorio y descargar los archivos LFS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd notebooks
jupyter lab
```

Los metadatos históricos del modelo base declaran Python **3.14.5**; no son una
instrucción para cambiar el entorno actual. La [nota de procedencia de entornos](docs/PROCEDENCIA_ENTORNOS_MODELOS.md)
distingue esa declaración del modelo ajustado y del ensayo aislado en **3.12.14**,
conservando los metadatos originales y los límites de lo comprobado.

Para reproducir el escenario principal se utiliza **02B** para el EDA espacial y la cadena **03B → 04B → 04C → 05B**. **No reejecute entrenamientos sobre el cierre oficial:** 04C puede sobrescribir su modelo ajustado. Use `python scripts/reproducir_cadena_aislada.py` para una nueva carpeta aislada. El notebook 05B compara las configuraciones base y ajustada. La [ejecución de septiembre 13](reports/reproducibilidad/ejecucion_20260913/INFORME.md) conserva la evidencia histórica anterior a la extracción de funciones de preparación; no se reescribió.

## Verificación del código sin reentrenar

Desde la raíz, con el entorno activado:

```sh
python scripts/verificar_codigo.py
python scripts/verificar_codigo.py --integracion
```

La primera orden usa fixtures pequeños para probar preparación, etiquetas, lags,
calendario, rutas, cargador, entradas inválidas, umbral y consulta retrospectiva.
La segunda requiere los artefactos reales: verifica la fuente, reconstruye el
dataset en memoria y exige igualdad exacta, reproduce las 58.480 decisiones del
modelo cerrado y comprueba consultas individuales. No modifica datos, modelos ni
reportes. Con `--salida ruta_nueva.json` guarda un informe nuevo sin sobrescribir.

Los scripts también funcionan usando su ruta absoluta desde otro directorio.
03B, 04B y 04C pueden abrirse desde la raíz o `notebooks/`; para un kernel ubicado
fuera del checkout se puede definir `SINIESTRALIDAD_ROOT` con la ruta del proyecto.
El ejecutor aislado fija esta variable a su copia para no escribir en el original.

La preparación se comparte entre 03B y `src/preparacion.py`. La procedencia y sus
limitaciones se explican en [data/raw/README.md](data/raw/README.md).
El [catálogo de artefactos](config/artefactos.json) separa principal, referencia
base y legado sin mover archivos que participan en verificaciones de integridad.

### Consulta retrospectiva sin dashboard

```sh
python scripts/consultar_modelo.py --fecha 2023-01-01 --localidad "CANDELARIA" --franja "Noche"
```

Use los nombres exactos de localidad registrados en el dataset. La consulta
verifica el dataset y el modelo, selecciona las variables históricas ya preparadas
y devuelve score, alerta y umbral 0,52. Rechaza fechas fuera de 2023–2024 y grupos
desconocidos. **No construye históricos nuevos, no pronostica fechas futuras y no
implementa una interfaz web.**

Cada registro devuelto incluye también la trazabilidad de la consulta, tanto en
la función de Python como en el JSON de la línea de comandos:

| Campo | Contenido |
| --- | --- |
| `Id_Modelo` y `Version_Modelo` | Identificador y versión tomados del registro del modelo cargado |
| `Tipo_Evaluacion` | `retrospectiva` |
| `Evaluacion_Desde` y `Evaluacion_Hasta` | Periodo registrado: `2023-01-01` a `2024-12-31` |
| `Alcance_Consulta` | Advierte que se consultan casos históricos, no pronósticos para fechas nuevas |
| `Advertencia_Score` | Aclara que el score no es una probabilidad calibrada y que el uso es académico, no operativo |

Estos campos acompañan al `Umbral_Score` ya existente. Son columnas de la salida
para conservarse al exportar, no variables predictoras. No cambian el score ni
la decisión del modelo.

`.github/workflows/pruebas.yml` configura pruebas de CI en push/pull request. La
verificación de integración es manual y requiere descargar Git LFS. La ejecución
local no certifica que el flujo remoto haya pasado: debe comprobarse al publicarlo.

## Ampliaciones de las actividades 3.1 y 5.1

**3.1 — notebook 02B:** incorpora serie diaria y mensual con calendario completo, cruces día–franja–actor, festivos con denominadores y referencia del mismo día semanal, sensibilidad a 2020 y revisión de la hoja `Actor_vial`. Distingue siniestros de registros de personas y utiliza polígonos oficiales SDP/Catastro, centros medianos de eventos y celdas de 100 × 100 m. La cartografía y su procedencia se conservan en `data/reference/`; no se reasignan localidades ni se modifica el dataset del modelo. Consulte la [conclusión de 3.1](reports/eda_victimas/conclusion_ejecutiva.md).

**5.1 — notebook 05B:** añade tasas históricas estimadas solo con entrenamiento, comprobación en los cortes 2020–2022, comparación anual y bootstrap pareado en bloques semanales. La tasa localidad–franja–día de semana obtiene AP **0,3087**, AUC **0,6931** y Brier **0,1438**, frente a **0,3098**, **0,6933** y **0,2221** del RF ajustado. Los intervalos exploratorios de la diferencia en AP/AUC incluyen cero: no se afirma superioridad concluyente del RF sobre esta referencia. El modelo principal y el umbral **0,52** se conservan. Consulte la [comparación](reports/evaluation_victimas/comparacion_referencias_historicas.csv) y la [conclusión ampliada](reports/evaluation_victimas/conclusion_ejecutiva.md).

05B comprueba equivalencia numérica antes de conservar las evidencias congeladas, evitando que diferencias aritméticas de aproximadamente 1e-16 alteren sus huellas al reexportarlas. Los nuevos reportes se guardan por separado. Las funciones de referencia y bootstrap tienen pruebas en `tests/`, ejecutables con `python -m unittest discover -s tests -v`.

La primera ejecución de 02B descarga la cartografía si falta; las siguientes verifican y reutilizan la copia local. Las dependencias geográficas están incluidas en `requirements.txt`. Los antiguos scripts generadores se detienen si detectan estos notebooks ampliados, para evitar sobrescribirlos.

## Dashboard

La aplicación vigente está implementada en **Python Dash**. Desde la raíz, con
el entorno activado y las dependencias instaladas:

```sh
python -m dashboard.app
```

Abra **http://127.0.0.1:8050**. Incluye resumen, consulta retrospectiva y mapa de
las 20 localidades, filtros descriptivos por año/territorio/franja/actor,
evaluación filtrada, referencias históricas, metodología y descargas con contexto.
La [guía del dashboard](dashboard/README.md) explica instalación, uso, arquitectura,
interpretación y diagnóstico. La maqueta `dashboard/dist/` se conserva como legado.

Los datos oficiales y el modelo no se modifican. `data/dashboard/` contiene
agregados descriptivos adicionales comprobados contra el EDA. La consulta solo
admite 2023–2024; los scores no se presentan como probabilidades. La cartografía
es local y no necesita claves ni servicios de mapas. No hay despliegue público.

Verificación con datos reales: `python scripts/verificar_dashboard.py`.

## Alcance y limitaciones

La evaluación 2023–2024 es retrospectiva y ya participó en la comparación final; no constituye una prueba futura independiente. El prototipo no está listo para producción ni estima causalidad, gravedad futura o riesgo individual. Antes de un uso operativo se requiere validación prospectiva, calibración temporal separada, costos de falsas alertas y omisiones, e incertidumbre por subgrupo.

Reportes recomendados: [ficha técnica](reports/modelo_principal/ficha_tecnica_modelo.md), [conclusión ejecutiva](reports/evaluation_victimas/conclusion_ejecutiva.md), [métricas globales](reports/evaluation_victimas/metricas_globales.csv), [métricas del ajustado por localidad](reports/evaluation_victimas/metricas_random_forest_ajustado_por_localidad.csv) y [calibración](reports/evaluation_victimas/comparacion_brier_lineas_base.csv).
