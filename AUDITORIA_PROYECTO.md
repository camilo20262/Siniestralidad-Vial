# Auditoría técnica integral — Sistema predictivo de siniestralidad vial en Bogotá

**Fecha:** 1 de octubre de 2026

**Marco:** CRISP-DM

**Universo principal:** siniestros con heridos o fallecidos, 2018–2024

**Unidad de análisis:** Localidad × Franja horaria × Fecha

**Alcance de esta revisión:** código, notebooks, fuente Excel, datasets procesados, modelos, reportes, pruebas, evidencia de reproducibilidad y dashboard presentes en el repositorio. No se reentrenaron modelos ni se modificaron artefactos oficiales.

## Criterio de estados

- **OK:** la evidencia revisada satisface el control.
- **Parcial:** existe evidencia favorable, pero también una brecha, ambigüedad o alcance no cubierto.
- **Falla:** el control no se cumple o la evidencia demuestra una contradicción material.

## Comprobaciones directas realizadas

- `python -m unittest discover -s tests -v`: **54 pruebas, 0 fallos, 0 errores**.
- `python scripts/verificar_codigo.py --integracion`: resultado **correcto**; reconstrucción exacta del dataset principal, 58.480 decisiones reproducidas, 80 umbrales de etiqueta verificados y 12 evidencias íntegras.
- Revisión independiente de ambos Parquet: 204.560 filas y 16 columnas cada uno; cero nulos y cero duplicados en la clave.
- Recálculo independiente de los tres históricos y de `Alto_Riesgo`: cero diferencias frente a ambos datasets guardados.
- Lectura del Excel fuente: 278.614 siniestros, clave `Codigo_Accidente` única y columnas requeridas presentes.

## Fase 1 — Comprensión del negocio

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Pregunta de investigación, unidad y universo | OK | `notebooks/01_Comprension_del_Negocio.ipynb` define la observación como localidad–fecha–franja, restringe el escenario principal a víctimas y diferencia siniestros de personas. Coincide con `models/victimas/modelo_principal.json` y el dataset principal. | Mantener esta formulación en la tesis y evitar expresiones de riesgo individual o causalidad. |
| Objetivos frente al pipeline vigente | Parcial | Los objetivos ya documentan víctimas, cortes temporales, RF ajustado y umbral 0,52. Sin embargo, el mismo notebook aún dice que el dashboard es una entrega posterior o componente pendiente, mientras `dashboard/app.py` ya implementa una aplicación local funcional. | Actualizar las celdas finales de 01: dashboard local terminado, despliegue público y validación de usuarios pendientes. |
| Interpretación de `Alto_Riesgo` | OK | 01, README, ficha técnica y dashboard explican que 49/80 grupos del escenario de víctimas tienen umbral 0 y que allí la etiqueta significa ocurrencia; en los demás exige dos o tres siniestros. | Repetir esta salvedad en resumen, metodología, resultados y defensa oral. |
| Actores viales en objetivos y pipeline | OK | Motocicleta, peatón y bicicleta aparecen en `02B`, `reports/eda_victimas/` y el filtro descriptivo del dashboard. No forman parte de las 12 variables de `modelo_principal.json`, y 01 declara expresamente que no son predictores. | Conservar la distinción; no presentar el filtro de actor como una predicción específica por actor. |
| Alcance operativo | OK | 01, README, ficha y dashboard califican la salida como priorización académica retrospectiva, no pronóstico futuro ni herramienta lista para asignar recursos. | Mantener esta delimitación hasta contar con validación prospectiva y costos operativos acordados. |

## Fase 2 — Comprensión de los datos

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Columnas y tipos fuente | OK | En `Siniestros` existen `Codigo_Accidente` (`int64`), `Fecha_Acc` (`datetime64`), `AA_Acc` (`int64`), `MM_Acc` (texto), `Hora_Acc` (`int64`), `Localidad` (texto) y `Gravedad_Indicador_Tradicional` (texto). `src/preparacion.py` valida presencia, fecha, año, mes, hora, localidad y unicidad. | Incorporar esta tabla de contrato de datos en la metodología de la tesis. |
| Comprensión inicial de las cuatro hojas | Parcial | `02_Comprension_de_los_Datos.ipynb` inspecciona Siniestros, Vehículos, Actor_vial y Diccionario, pero es básico; dos celdas referencian `.info` sin llamarlo y la celda final solo muestra el último `dtypes`. | Corregir esas celdas o remitir explícitamente al perfilado robusto de 02B y a `data/raw/procedencia_excel.json`. |
| EDA temporal del escenario principal | OK | `02B` y `reports/eda_victimas/` contienen series diaria/mensual, año, mes, día–franja, festivos con denominadores y sensibilidad a 2020, siempre sobre 85.199 siniestros con víctimas. | Conservar la advertencia de que no hay denominadores de exposición al tránsito. |
| EDA espacial del escenario principal | OK | Se revisan 20 localidades, coordenadas, polígonos oficiales, celdas de 100 m y discrepancias geográficas. Se reportan 18 puntos fuera del distrito de referencia y 5.782 discrepancias localidad declarada–polígono, sin reasignación automática. | Explicar en la tesis por qué se conserva la localidad declarada y cómo afecta la incertidumbre espacial. |
| EDA por actor vial | OK | `02B` cruza indicadores del siniestro y la hoja `Actor_vial`; `reports/eda_victimas/conclusion_ejecutiva.md` distingue 203.548 registros de actores de siniestros únicos y advierte que las categorías se solapan. | No sumar participaciones de actores como si fueran categorías excluyentes. |
| EDA del escenario total | Parcial | El escenario total se conserva en 03/04/05 y `reports/evaluation/`, pero no tiene un EDA espacial/temporal tan completo ni tan claramente separado como 02B. Además está afectado por el quiebre de “Solo Daños”. | Rotularlo en tesis y anexos exclusivamente como escenario histórico/de sensibilidad. |

## Fase 3 — Preparación de datos (03 y 03B)

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Históricos excluyen el día objetivo | OK | 03 y `src/preparacion.py` aplican `shift(1)` antes de `rolling(7)` y `rolling(30)`; el rezago semanal usa `shift(7)`. El recálculo sobre ambos Parquet dio máxima diferencia 0 y cero filas discordantes en las tres variables. | Mantener las pruebas `test_lags_excluyen_dia_y_futuro` y la verificación de integración como control de regresión. |
| Umbral de etiqueta solo con entrenamiento | OK | 03 y 03B calculan el cuantil 2/3 exclusivamente con filas hasta 2022-12-31. El recálculo con train produjo cero etiquetas distintas; usar todo 2018–2024 produciría 7.485 diferencias en el escenario total y 1.382 en víctimas. | Conservar el recálculo por corte temporal también durante validación. |
| Duplicados y nulos | OK | Ambos datasets tienen 204.560 filas, 20 localidades, cuatro franjas, 2.557 fechas, **0 duplicados de clave** y **0 celdas nulas**. Los notebooks contienen `assert` equivalentes. | Mantener estos controles como condiciones de fallo, no solo impresiones. |
| Filtro de víctimas | OK | En 2018–2024 quedan 85.199 registros: 81.718 `Con Heridos` y 3.481 `Con Muertos`; quedan **0** `Solo Daños`. `filtrar_victimas` usa una lista positiva de esas dos categorías y 03B muestra el cruce posterior por año y gravedad. | Añadir una aserción explícita de que el conjunto post-filtro de categorías es exactamente esas dos. |
| Umbrales degenerados por localidad–franja | Parcial | Escenario total: **19/80** grupos con umbral 0; víctimas: **49/80**. El caso de víctimas está ampliamente documentado en README, 01, ficha y dashboard; no se encontró documentación equivalente y visible del valor 19 para el escenario total. | Documentar 19/80 en el anexo del escenario original y explicar que, también allí, parte de la etiqueta mide ocurrencia. |
| Separación train/test | OK | Ambos datasets marcan 146.080 filas de train (2018-01-01–2022-12-31) y 58.480 de test (2023-01-01–2024-12-31), sin solapamiento temporal. | Mantener las fechas como constantes documentadas y verificadas. |

## Fase 4 — Modelado (04, 04B y 04C)

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Split final train/test en ambos escenarios | OK | 04 y 04B usan `Periodo`: 2018–2022 para ajuste y 2023–2024 para evaluación. | Conservar el orden temporal y no usar particiones aleatorias para series. |
| Validación interna del escenario original | Falla | `notebooks/04_Modelado.ipynb` aún ejecuta `StratifiedKFold(n_splits=5, shuffle=True)` y `cross_validate`, mezclando fechas. Aunque 05 añadió posteriormente cortes expansivos, el notebook 04 conserva y reporta una validación metodológicamente inválida. | Eliminar o marcar esas salidas como anuladas y reemplazarlas en 04 por cortes expansivos; no basta con llamarlo “legado” si se entrega al jurado. |
| Validación del escenario de víctimas | OK | 04B y 04C usan tres cortes manuales: 2018–2019→2020, 2018–2020→2021 y 2018–2021→2022. En cada corte recalculan etiqueta, preprocesador y modelo con el pasado. | Mantener estos cortes y describirlos como validación temporal expansiva manual, no como `TimeSeriesSplit`. |
| Ajuste de preprocesadores | OK | En 04, los preprocesadores se ajustan con `X_train`; en 04B/04C están dentro de `Pipeline` y cada `fit` recibe solo el train del corte o el train final. No se halló `fit` previo sobre 2018–2024 en la línea vigente. | Conservar el preprocesamiento encapsulado en el pipeline principal. |
| Búsqueda de hiperparámetros | OK | 04C evalúa 8 configuraciones RF × 3 cortes y selecciona por Average Precision media. `modelo_principal.json`, ficha y 01 declaran que es una búsqueda acotada, solo RF y no un óptimo global. | Justificar por presupuesto/alcance por qué no se hizo búsqueda más amplia o anidada. |
| Reutilización de validación para configuración y umbral | Parcial | Las mismas predicciones OOF 2020–2022 se usan primero para elegir configuración y luego para maximizar F1 del umbral. La limitación está declarada en el registro y la ficha. | Presentar esas métricas como de selección; para una estimación independiente usar validación anidada o un tramo adicional. |
| Separación de artefactos | OK | El escenario total escribe en `models/`; víctimas escribe en `models/victimas/`. 04C usa `pipeline_random_forest_ajustado_victimas.pkl` y no reemplaza el RF base. `config/artefactos.json` cataloga principal, base y legado. | Renombrar en una versión futura el alias engañoso `pipeline_modelo_seleccionado.pkl`, que en realidad contiene el RF base. |
| Metadatos de entorno | Parcial | El metadato histórico de 04B declara Python 3.14.5, mientras `.python-version`, el registro oficial y la reproducción usan 3.12.14. La reproducción fue equivalente, pero la discrepancia permanece en `metadata_modelo.json`. | Corregir o explicar la procedencia de esa versión en el catálogo del modelo base. |

## Fase 5 — Evaluación y selección (05 y 05B)

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Condición de holdout limpio | Falla | El código de 04C no usa 2023–2024 para seleccionar configuración ni umbral, pero el periodo ya había sido inspeccionado y usado para comparar modelos durante el desarrollo. README, 01, ficha y registro lo reconocen como **evaluación retrospectiva**, no test futuro intacto. | No llamarlo validación externa, confirmatoria ni prospectiva. Reservar datos posteriores a 2024 o ejecutar un protocolo prospectivo. |
| Umbral de decisión sin mirar 2023–2024 | OK | RF base: 0,55 elegido con OOF 2020–2022 en 04B. RF ajustado principal: 0,52 elegido con OOF 2020–2022 en 04C. Los diagnósticos de umbral sobre Candelaria/test se marcan como no adoptables. | Mantener separados el umbral de etiqueta, el umbral base 0,55 y el umbral principal 0,52. |
| Requisito del encargo “RF víctimas, umbral 0,55” | Parcial | El requisito ya no coincide con la autoridad del repositorio: `modelo_principal.json` registra RF ajustado, umbral **0,52**; 0,55 corresponde al RF base histórico. README, ficha, 05B y dashboard son coherentes con 0,52. | Tomar una decisión formal: actualizar la especificación a 0,52 o volver a promover y versionar el modelo 0,55. No mantener dos “umbrales decididos”. |
| Brier frente a línea base explícita | OK | Escenario total: XGBoost Brier 0,1264 y RF 0,1714 frente a constante train 0,0726. Víctimas: RF ajustado 0,2221 frente a constante train 0,1544. Ambos reportes concluyen que los scores no son probabilidades calibradas. | Mantener Brier y la referencia constante junto a AUC/AP/F1 en toda presentación. |
| Métricas globales y macro territoriales | OK | `reports/evaluation/metricas_macro_localidad.csv` y `reports/evaluation_victimas/metricas_macro_localidad.csv` reportan ambas. En víctimas, F1 global 0,4058 frente a macro 0,3474; recall global 0,6544 frente a macro 0,5583. | Destacar la brecha global–macro en resultados y conclusiones. |
| Candelaria y Sumapaz | OK | Candelaria: 157 positivos, 0 TP y score máximo 0,3227. Sumapaz: 2 positivos, 0 TP; el tamaño impide conclusiones firmes. Los valores constan en tablas, ficha, 05B y dashboard. | Tratar Candelaria como fallo territorial demostrado y Sumapaz como evidencia insuficiente, no como casos equivalentes. |
| Generalización “bajo volumen implica fallo” | OK | La correlación Spearman volumen–recall es -0,0654; 05B y la ficha dicen expresamente que el volumen no explica por sí solo la heterogeneidad. No se halló la generalización incorrecta en textos canónicos actuales. | Conservar el argumento cuantitativo y evitar recuperar esa afirmación en la tesis. |
| Consistencia notebook–CSV–registro | OK | La ejecución aislada reprodujo 14 tablas; la integración actual reproduce exactamente etiquetas y decisiones. F1 0,405789, AUC 0,693324, AP 0,309838, precisión 0,294063, recall 0,654434 y Brier 0,222088 coinciden entre 04C, 05B, CSV, registro, README y ficha. | Mantener `scripts/verificar_codigo.py --integracion` como control antes de cada entrega. |
| Consistencia con texto de tesis | Parcial | No se encontró archivo de tesis `.docx`, `.tex` o PDF propio en el repositorio; por tanto no fue posible contrastar sus cifras y conclusiones. | Incorporar o enlazar una versión congelada de la tesis y automatizar una tabla única de resultados canónicos. |
| Valor incremental del RF | Parcial | La referencia localidad–franja–día obtiene AP 0,3087, AUC 0,6931 y Brier 0,1438, frente a 0,3098, 0,6933 y 0,2221 del RF. Los intervalos exploratorios de diferencia AP/AUC incluyen cero. | Presentarlo como resultado central: no se demostró superioridad concluyente del RF frente a una referencia histórica fuerte. |

## Fase 6 — Dashboard

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Estado de implementación | OK | Existe aplicación Python Dash en `dashboard/` con cinco secciones: resumen, consulta/mapa, historia, evaluación y metodología. Hay código, CSS, datos preparados, manual, pruebas y evidencia de revisión en navegador. | Sustituir en 01 toda mención a dashboard pendiente; aclarar que falta despliegue público, no la aplicación local. |
| Modelo y preprocesador consumidos | OK | `dashboard/data.py` llama a `cargar_consulta()`, que carga el pipeline registrado `pipeline_random_forest_ajustado_victimas.pkl`, verifica SHA-256, esquema, parámetros y predicciones congeladas. No consume los `.pkl` del escenario total. | Mantener el registro como única autoridad y fallar ante cambios de hash. |
| Umbral mostrado y aplicado | Parcial | El dashboard aplica y muestra 0,52 de forma coherente con el modelo principal actual; no satisface el requisito antiguo de 0,55 incluido en el encargo. | Resolver formalmente la especificación 0,52 vs. 0,55 y versionar cualquier cambio. |
| Score frente a probabilidad | OK | La interfaz repite que el score es una puntuación relativa no calibrada; mapa, detalle, descargas y evaluación usan `Score_Priorizacion`/`Score` y no lo presentan como probabilidad literal. | Mantener la advertencia visible junto al valor, no solo en metodología. |
| Filtros requeridos | OK | Consulta: fecha 2023–2024, localidad y franja. Historia: año, localidad, franja y actor descriptivo. Evaluación: año, localidad y franja. El mapa cubre las 20 localidades. | Aclarar siempre que la fecha es consulta retrospectiva y que actor no altera el modelo. |
| Advertencias Candelaria, Sumapaz y Madrugada | Parcial | Evaluación contiene paneles textuales específicos para Candelaria y Sumapaz. Madrugada aparece en la comparación por franja, pero no hay una advertencia textual equivalente que destaque su recall de 39,43 %. | Añadir una tarjeta/aviso explícito: Madrugada es la franja más débil y su recall es 39,43 %. |
| Significado híbrido de `Alto_Riesgo` | OK | La página Metodología muestra una tabla 49/28/3 y explica ocurrencia frente a frecuencia elevada, separándolo del umbral 0,52 del score. | Replicar una versión breve en la vista de consulta o ayuda contextual. |
| Verificación funcional | OK | 15 pruebas específicas del dashboard están incluidas entre las 54 que pasan. `verificar_dashboard.py` comprueba 58.480 predicciones, 20 localidades, métricas, actores y tiempos locales menores de 5 s. | Añadir CI de integración con LFS cuando la infraestructura lo permita. |
| Despliegue y validación de usuarios | Parcial | El dashboard es local (`127.0.0.1`), sin despliegue público, telemetría ni prueba de aceptación con usuarios. | Definir alojamiento, privacidad, responsable de operación y prueba de usabilidad antes de llamarlo producto entregado. |

## Reproducibilidad y estructura transversal

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| README | OK | `README.md` describe escenario principal, variables, modelo, métricas, limitaciones, estructura, ejecución, consulta y dashboard. Está alineado con RF ajustado 0,52. | Añadir una secuencia ejecutable no interactiva que incluya EDA y verificación final. |
| Dependencias y Python | OK | `requirements.txt` fija versiones exactas de 17 dependencias y `.python-version` fija 3.12.14. La ejecución aislada instaló un venv sin `system-site-packages` y pasó `pip check`. | Conservar también el `pip freeze` de cada cierre reproducible. |
| `main.py` y rutas | OK | No existe `main.py`; no hay punto desincronizado que auditar. `src/rutas.py`, notebooks vigentes y dashboard resuelven la raíz del checkout; las pruebas verifican ejecución desde raíz, `notebooks/` y directorio externo. | No crear un `main.py` decorativo; si se crea, convertirlo en orquestador real y probado. |
| Reproducción de la cadena principal | OK | `scripts/reproducir_cadena_aislada.py` ejecutó 03B→04B→04C→05B en 173,53 s, 54/54 celdas de código sin errores, dataset idéntico y 14 tablas equivalentes; la evidencia está en `reports/reproducibilidad/ejecucion_20260913/`. | Repetir la prueba antes del cierre final y conservar commit, entorno y hashes. |
| Ejecución realmente end-to-end | Parcial | La reproducción automatizada no incluye 02B ni arranque/prueba visual del dashboard. 02B puede requerir red si falta la cartografía; el repo actual sí contiene la copia local. Los notebooks legado conservan rutas relativas y una celda `%pip install`. | Crear un comando de orquestación de solo verificación para 02B→03B→04B→04C→05B→dashboard, sin sobrescribir el cierre. |
| Fuente y Git LFS | Parcial | El Excel está versionado por LFS y tiene hash, URL, hojas y dimensiones. La fecha original de descarga es desconocida, la igualdad con la descarga actual no se completó y la licencia específica sigue pendiente. | Resolver licencia y procedencia antes de redistribuir datos o publicar el sistema. |
| Separación vigente/legado | Parcial | `config/artefactos.json` separa principal, base y legado, pero notebooks 03/04/05, modelos raíz y reportes antiguos siguen en rutas prominentes; 04 conserva la validación aleatoria. | Moverlos a directorios `legacy/` o insertar portadas inequívocas de “anulado/no principal” sin romper hashes del cierre actual. |
| Calidad automatizada | OK | 54 pruebas cubren preparación, fuga temporal, rutas, catálogo, modelo, consulta, referencias y dashboard. La integración verifica fuente, reconstrucción, modelo y UI sin reentrenar. | Mantener CI básico y documentar que la integración completa requiere archivos LFS. |

## Resumen ejecutivo (máximo 10 líneas)

1. El escenario principal con víctimas es técnicamente reproducible: lags, etiqueta, datos, modelo y 58.480 decisiones fueron verificados sin diferencias.
2. La falla metodológica más visible es que el escenario original aún conserva y reporta `StratifiedKFold` aleatorio; debe anularse o corregirse antes de la defensa.
3. 2023–2024 no es un holdout limpio: no intervino en la selección de 04C, pero ya fue inspeccionado; toda afirmación debe llamarlo evaluación retrospectiva.
4. El requisito de umbral 0,55 quedó desactualizado: la autoridad actual es RF ajustado con 0,52; 0,55 corresponde al RF base. La especificación debe unificarse formalmente.
5. La calibración es insuficiente en ambos escenarios y el RF no demuestra ventaja concluyente frente a una referencia histórica fuerte; el lenguaje correcto es score de priorización.
6. La heterogeneidad territorial es material: Candelaria falla con evidencia cuantitativa; Sumapaz tiene muestra insuficiente y no sustenta generalizaciones sobre bajo volumen.
7. El dashboard local ya es funcional y consume el artefacto correcto, pero le falta una advertencia textual específica sobre Madrugada, despliegue y validación con usuarios.
8. Antes de entregar al jurado deben alinearse 01 con el dashboard existente, documentarse los 19 umbrales cero del escenario total e incorporarse la tesis para comprobar sus cifras.
