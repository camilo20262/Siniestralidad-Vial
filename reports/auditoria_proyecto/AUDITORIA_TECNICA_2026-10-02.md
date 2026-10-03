# Auditoría técnica completa — Sistema predictivo de siniestralidad vial en Bogotá

**Fecha:** 2 de octubre de 2026\
**Marco:** CRISP-DM\
**Escenario principal:** siniestros con heridos o fallecidos, 2018–2024\
**Unidad de análisis:** Localidad × Franja horaria × Fecha\
**Alcance:** notebooks, Excel fuente, Parquet procesados, modelos, reportes, código, pruebas, reproducción aislada y dashboard disponibles en el repositorio.

## Criterio y comprobaciones directas

- **OK:** el control se satisface con evidencia ejecutable o trazable.
- **Parcial:** el control se satisface solo en parte o queda una limitación relevante.
- **Falla:** el control no se satisface o no puede sostenerse la afirmación prevista.

Comprobaciones ejecutadas el 2 de octubre de 2026:

- `.venv/bin/python -m unittest discover -s tests -v`: **70 pruebas, 0 fallos y 0 errores**.
- `.venv/bin/python scripts/verificar_codigo.py --integracion`: resultado **correcto**; reconstrucción exacta del dataset principal, 80 umbrales y 58.480 decisiones verificadas.
- `.venv/bin/python scripts/verificar_dashboard.py`: resultado **correcto**; cinco páginas, 20 localidades, métricas y conteos de actores consistentes.
- Revisión independiente de ambos Parquet: 204.560 × 16, cero nulos, cero duplicados de la clave y diferencias máximas de 0 al recalcular los tres históricos.
- Lectura independiente del Excel: 278.614 siniestros, `Codigo_Accidente` único, columnas requeridas presentes y 85.199 registros con víctimas en 2018–2024.
- Se revisó la evidencia de la reproducción integral aislada del 1–2 de octubre: cinco notebooks, 66 celdas, cero errores, 24 tablas EDA y 14 tablas de modelado/evaluación equivalentes, prueba HTTP y revisión visual.

## Fase 1 — Comprensión del negocio

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Objetivo general y pregunta de investigación | OK | `01_Comprension_del_Negocio.ipynb` formula una evaluación retrospectiva por localidad × fecha × franja sobre siniestros con víctimas. Distingue priorización, causalidad y riesgo individual. Coincide con el dataset y el registro `rf_victimas_bogota_v1.0`. | Mantener literalmente esta delimitación en resumen, metodología y defensa. |
| Objetivos específicos frente al pipeline actual | OK | Los seis objetivos cubren preparación, EDA, históricos sin fuga, comparación temporal, evaluación y dashboard local. El recorrido declarado 02B→03B→04B→04C→05B→dashboard coincide con los artefactos existentes. | No recuperar objetivos antiguos de k-fold aleatorio, mapas a nivel de calle o pronóstico en tiempo real. |
| Cambio de escenario total a víctimas | OK | El escenario principal se limita a `Con Heridos` y `Con Muertos`; 01, README, ficha técnica y catálogo tratan 03/04/05 como antecedente o sensibilidad. | Conservar ambos resultados separados en todo documento y figura. |
| Variables de actor vial | OK | Motocicleta, peatón y bicicleta se analizan en 02B, reportes EDA y filtros descriptivos del dashboard. No aparecen entre las 12 variables del modelo; 01 lo declara expresamente. | No afirmar que el modelo genera alertas por actor ni interpretar el filtro descriptivo como entrada predictiva. |
| Interpretación de `Alto_Riesgo` | OK | 01 y el anexo documentan la etiqueta híbrida: con víctimas, 49/80 grupos tienen umbral 0, 28 umbral 1 y 3 umbral 2. | Usar “ocurrencia o frecuencia elevada” y evitar “alta peligrosidad” sin matices. |
| Alcance operativo | OK | El proyecto se presenta como prototipo académico retrospectivo, sin pronóstico de fechas nuevas ni autorización para asignar recursos. | Exigir validación prospectiva, oportunidad de datos y costos de decisión antes de uso operativo. |

## Fase 2 — Comprensión de los datos

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Columnas y tipos de la fuente | OK | En `Siniestros` existen `Codigo_Accidente` (`int64`), `Fecha_Acc` (`datetime64`), `AA_Acc` (`int64`), `MM_Acc` (texto), `Hora_Acc` (`int64`), `Localidad` y `Gravedad_Indicador_Tradicional` (texto). `src/preparacion.py` valida semántica, no solo presencia. | Incluir este contrato de datos en la tesis. |
| Perfilado de las cuatro hojas | OK | 02 inspecciona Siniestros, Vehículos, Actor_vial y Diccionario; las 26 celdas están ejecutadas. Las llamadas `.info()` y la presentación de tipos por hoja están cubiertas por pruebas. | Mantener la advertencia sobre uniones uno-a-muchos. |
| EDA temporal del escenario principal | OK | 02B y `reports/eda_victimas/` contienen series diaria/mensual, año, mes, día–franja, festivos con denominadores y sensibilidad a 2020 sobre 85.199 siniestros con víctimas. | Explicar que no existen denominadores de exposición al tránsito. |
| EDA espacial del escenario principal | OK | Hay cobertura de coordenadas, polígonos oficiales, centros medianos, celdas de 100 m y control localidad declarada–polígono. Se reportan 18 puntos fuera del polígono y 5.782 discrepancias sin reasignación automática. | Justificar la conservación de la localidad declarada y la incertidumbre espacial. |
| EDA por actor vial | OK | 02B cruza indicadores por localidad, día y franja, y revisa la hoja `Actor_vial`. Distingue registros de personas, siniestros y categorías solapadas. | No sumar porcentajes de actores como categorías excluyentes. |
| EDA del escenario total | Parcial | El escenario histórico cuenta con preparación y evaluación, pero no un EDA territorial/temporal equivalente a 02B y está afectado por el cambio de cobertura de `Solo Daños`. | Presentarlo exclusivamente como análisis histórico/de sensibilidad. |
| Procedencia y licencia | Parcial | `procedencia_excel.json` registra URL, hash, tamaño y hojas. La fecha original de descarga es desconocida, no se completó la comparación binaria con la descarga vigente y la licencia específica sigue pendiente. | Confirmar licencia y condiciones de redistribución antes de publicar datos o producto. |

## Fase 3 — Preparación de datos (03 y 03B)

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Históricos excluyen el día objetivo | OK | 03 y `src/preparacion.py` usan `shift(1)` antes de `rolling(7)` y `rolling(30)`; el rezago semanal es `shift(7)`. El recálculo independiente dio diferencia máxima 0 en ambos datasets. | Mantener `test_lags_excluyen_dia_y_futuro` como control obligatorio. |
| Umbral de etiqueta solo con entrenamiento | OK | El cuantil 2/3 se calcula por localidad–franja únicamente hasta 2022-12-31. Las validaciones temporales lo recalculan dentro de cada corte. La integración reproduce exactamente las etiquetas. | No precalcular etiquetas con 2018–2024 antes de validar. |
| Duplicados y nulos | OK | Ambos Parquet tienen 204.560 filas, 20 localidades, cuatro franjas y 2.557 fechas; cero duplicados de `(Localidad, Franja_Horaria, Fecha_Acc)` y cero nulos. | Conservar los `assert` y fallar ante cualquier violación. |
| Filtro de víctimas | OK | En 2018–2024 quedan 81.718 `Con Heridos` y 3.481 `Con Muertos`; **cero** `Solo Daños`. El filtro usa lista positiva, no exclusión ambigua. | Añadir/retener una aserción de conjunto exacto de categorías post-filtro. |
| Umbrales degenerados | OK | Escenario total: **19/80 (23,75 %)**; víctimas: **49/80 (61,25 %)**. Ambos valores están ahora documentados en README, anexo y notebooks correspondientes. | Mantener los porcentajes como proporción de grupos, no de observaciones positivas. |
| Separación temporal | OK | Cada dataset contiene 146.080 filas train (2018–2022) y 58.480 test (2023–2024), sin solapamiento. | Congelar las fechas en el contrato de datos. |
| Ejecución guardada | Parcial | 03 está ejecutado; 03B raíz conserva 9 celdas sin ejecución, aunque existe una copia ejecutada y verificada en la reproducción integral. | Para la entrega, enlazar explícitamente la copia ejecutada o conservar salidas oficiales en una versión de solo lectura. |

## Fase 4 — Modelado (04, 04B y 04C)

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Split final temporal | OK | En ambos escenarios el ajuste final usa 2018–2022 y la evaluación retrospectiva 2023–2024. | No volver a introducir particiones aleatorias. |
| Validación interna del escenario total | OK | La antigua `StratifiedKFold(shuffle=True)` fue anulada el 1/10/2026: se retiraron imports, llamadas y salidas ejecutables. 04 remite a los cortes expansivos de la sección 20 de 05; pruebas específicas impiden su reintroducción. | En la tesis citar solo la evidencia temporal y, si se menciona la anterior, rotularla como anulada. |
| Validación del escenario de víctimas | OK | 04B/04C usan 2018–2019→2020, 2018–2020→2021 y 2018–2021→2022. En cada corte se recalculan etiqueta, preprocesamiento y modelo. | Describirlos como cortes expansivos manuales. |
| Preprocesadores sin fuga | OK | En la línea principal los transformadores están dentro de `Pipeline`; cada `fit` recibe solo el entrenamiento del corte o 2018–2022. En 04 histórico, los ajustes finales también usan `X_train`. | Mantener el pipeline como unidad serializada. |
| Búsqueda de hiperparámetros | OK | 04C prueba 8 configuraciones RF × 3 cortes y elige el candidato 3 por AP media 0,2552. Registro y ficha dicen que es una búsqueda acotada, no exhaustiva. | Justificar el presupuesto de búsqueda y no llamarlo óptimo global. |
| Reutilización de OOF para configuración y umbral | Parcial | Las mismas predicciones OOF 2020–2022 seleccionan la configuración y luego el umbral de F1. La limitación está declarada. | Para una estimación independiente, usar validación anidada o un tramo adicional no utilizado. |
| Separación de artefactos | OK | Legado en `models/`; víctimas en `models/victimas/`; el principal es `pipeline_random_forest_ajustado_victimas.pkl`. `config/artefactos.json` distingue principal, base y legado. | Renombrar en una versión futura el alias histórico `pipeline_modelo_seleccionado.pkl`, que contiene el RF base. |
| Entornos | Parcial | El base histórico declara Python 3.14.5; principal y reproducciones usan 3.12.14. `PROCEDENCIA_ENTORNOS_MODELOS.md` explica la diferencia y la reproducción fue equivalente, pero el entorno original del base no está certificado independientemente. | Tratar 3.12.14 como requisito vigente y conservar la discrepancia como procedencia histórica. |
| Ejecución guardada | Parcial | 04C está ejecutado; 04B raíz conserva 12 celdas sin ejecución. La reproducción aislada ejecutó ambas fases sin errores y reprodujo 14 tablas. | Referenciar la evidencia aislada en la entrega y evitar reentrenar sobre el cierre. |

## Fase 5 — Evaluación y selección (05 y 05B)

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Holdout 2023–2024 limpio | Falla | 04C no usa 2023–2024 para seleccionar configuración ni umbral, pero el periodo ya fue inspeccionado y usado en comparaciones del desarrollo. Todos los textos canónicos lo llaman evaluación retrospectiva. | No presentarlo como test final independiente, validación externa o prueba prospectiva; reservar datos posteriores a 2024. |
| Umbral de decisión sin mirar 2023–2024 | OK | RF base: 0,55; RF ajustado: 0,52. Ambos maximizan F1 con predicciones fuera de muestra 2020–2022. Los análisis de Candelaria sobre test son diagnósticos y no se adoptan. | Mantener separados umbral de etiqueta, umbral base y umbral principal. |
| Brier contra línea base | OK | Total: XGBoost 0,1264 y RF 0,1714 frente a constante train 0,0726. Víctimas: RF ajustado 0,2221 frente a constante train 0,1544. En ambos escenarios la calibración es peor. | Usar “score/puntuación”, nunca probabilidad literal. |
| Métricas globales y macro | OK | Víctimas: F1 global 0,4058 vs. macro 0,3474; recall global 0,6544 vs. macro 0,5583. El escenario total también exporta métricas macro. | Mostrar ambos niveles en tesis y defensa. |
| Candelaria | OK | 157 positivos, 0 TP, recall 0 y score máximo 0,3227, inferior a 0,52. La falla está cuantificada en CSV, notebook y dashboard. | Mantenerla como limitación territorial demostrada. |
| Sumapaz | OK | Solo 2 positivos y 0 TP; score máximo 0,1965. El repositorio evita equiparar esta muestra con Candelaria. | Presentarla como evidencia insuficiente, no como prueba general. |
| Generalización por bajo volumen | OK | Spearman entre volumen histórico y recall = -0,0654; los textos actuales indican que el volumen no explica por sí solo el desempeño. | No reintroducir “todas las localidades de bajo volumen fallan”. |
| Consistencia numérica técnica | OK | Integración y reproducción aislada coinciden con 05B, CSV y registro: F1 0,405789; AUC 0,693324; AP 0,309838; precisión 0,294063; recall 0,654434; Brier 0,222088. | Ejecutar la integración antes de cada entrega. |
| Consistencia con la tesis | Parcial | No existe `.docx`, `.tex` o PDF de tesis en el repositorio. No fue posible verificar las cifras del manuscrito. | Incorporar/enlazar una versión congelada y generar tablas desde una fuente canónica. |
| Valor incremental del RF | Parcial | Tasa histórica localidad–franja–día: AP 0,3087, AUC 0,6931, Brier 0,1438; RF: AP 0,3098, AUC 0,6933, Brier 0,2221. Bootstrap: intervalos de diferencia AP y AUC incluyen cero. | Tratar este resultado como hallazgo central; no afirmar superioridad concluyente del RF. |

## Fase 6 — Dashboard

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| Estado actual | OK | Existe aplicación Python Dash con Resumen, Consulta/mapa, Historia, Evaluación y Metodología; incluye CSS, manual, datos, pruebas HTTP y revisión visual. | Distinguir “aplicación local funcional” de “producto público desplegado”. |
| Modelo y preprocesador | OK | `dashboard/data.py` usa el cargador del registro oficial, valida hashes y consume `pipeline_random_forest_ajustado_victimas.pkl`; no usa artefactos del escenario total. | Mantener el registro como autoridad única. |
| Umbral 0,55 solicitado vs. 0,52 vigente | Parcial | El encargo menciona 0,55, pero `ESP-MODELO-01`, 01, registro, 05B y dashboard sustituyen formalmente ese requisito por 0,52. El 0,55 corresponde al RF base. La implementación es internamente consistente, pero no coincide con el texto del encargo. | Aceptar formalmente la especificación 0,52 en la tesis/acta o revertir mediante una nueva versión evaluada; no sostener dos umbrales “vigentes”. |
| Score frente a probabilidad | OK | Interfaz, mapa, detalles y descargas usan `Score_Priorizacion` y repiten que no es probabilidad calibrada. | Mantener el aviso junto al valor. |
| Filtros | OK | Consulta: fecha 2023–2024, localidad y franja. Historia: año, localidad, franja y actor descriptivo. Evaluación: año, localidad y franja. | Recordar que actor no altera el modelo y que las fechas son retrospectivas. |
| Advertencias territoriales y horarias | OK | Hay paneles específicos para Candelaria y Sumapaz. Madrugada aparece con aviso contextual y recall 39,43 % derivado del reporte; su prueba automática pasa. | Mantener el valor derivado, no codificado manualmente. |
| Etiqueta híbrida | OK | Metodología muestra 49/28/3 y la consulta explica el mínimo de siniestros de la localidad–franja, separado del umbral del score. | Conservar la explicación contextual en consulta y metodología. |
| Verificación funcional | OK | 70 pruebas pasan; verificador de dashboard confirma 58.480 predicciones y 20 localidades. La reproducción integral realizó 23 peticiones HTTP y revisión visual de cinco secciones. | Añadir pruebas de accesibilidad y carga si se pretende publicar. |
| Despliegue y aceptación | Parcial | Solo escucha en `127.0.0.1`; no hay despliegue, telemetría, prueba formal de usuarios ni auditoría exhaustiva de accesibilidad. | Definir alojamiento, operación, privacidad y aceptación antes de llamarlo producto final. |

## Reproducibilidad y estructura transversal

| Elemento revisado | Estado (OK / Parcial / Falla) | Evidencia concreta encontrada | Acción recomendada |
|---|---|---|---|
| README | OK | Describe escenario principal, etiqueta, modelo, métricas, limitaciones, rutas, verificación, reproducción integral y dashboard. | Mantenerlo sincronizado con la especificación oficial. |
| Dependencias | OK | `requirements.txt` fija 17 dependencias directas; `.python-version` fija 3.12.14. El ensayo aislado creó un entorno sin `system-site-packages` y pasó `pip check`. | Conservar también el `pip freeze` de cada cierre. |
| `main.py` | OK | No existe `main.py`; no hay una ruta desincronizada que auditar. `src/rutas.py` y pruebas resuelven raíz, `notebooks/` y directorio externo. | Si se crea, debe ser un orquestador real y probado. |
| Ejecución integral en entorno limpio | OK | `verificar_flujo_completo.py` reconstruyó 02B→03B→04B→04C→05B→dashboard desde Excel y cartografía congelada en 290,37 s, sin precargar resultados oficiales y sin modificar 248 archivos controlados. | Repetir antes del cierre final; instalación del entorno puede requerir Internet. |
| Notebooks raíz y evidencia ejecutada | Parcial | 03B y 04B oficiales no guardan salidas, aunque sus copias aisladas sí. 04 y 05 legado tienen una celda editada sin ejecución para no atribuir una corrida nueva. | Enlazar la ejecución aislada como evidencia canónica y explicar por qué no se reescriben los notebooks oficiales. |
| Separación vigente/legado | Parcial | El catálogo distingue principal/base/legado, pero 03/04/05 y `models/` raíz siguen en rutas prominentes. 04 ya porta una portada inequívoca de anulación. | Mover a `legacy/` en una versión futura o mantener portadas y catálogo visibles. |
| CI | OK | GitHub Actions ejecuta pruebas en push/PR y permite integración manual con LFS. | Hacer obligatoria la integración para el tag final si la infraestructura lo permite. |
| Integridad de artefactos | OK | Registro oficial contiene hashes del pipeline, dataset y evidencias; el cargador verifica antes de deserializar y la integración exige coincidencia exacta. | Versionar expresamente cualquier reentrenamiento. |

## Resumen ejecutivo (máximo 10 líneas)

1. La línea principal con víctimas es reproducible: preparación, 80 umbrales, modelo y 58.480 decisiones coinciden exactamente; pasan 70 pruebas.
2. La validación aleatoria del escenario original ya fue anulada y retirada; la evidencia vigente usa cortes temporales expansivos.
3. 2023–2024 no es un holdout limpio porque fue inspeccionado durante el desarrollo; solo puede llamarse evaluación retrospectiva.
4. La calibración es deficiente en ambos escenarios y el RF principal tiene Brier 0,2221 frente a 0,1544 de la constante de entrenamiento.
5. El RF apenas supera en AP/AUC a una tasa histórica simple y es claramente peor en Brier; no hay superioridad concluyente demostrada.
6. Candelaria es un fallo cuantificado; Sumapaz tiene muestra insuficiente y no respalda generalizaciones sobre bajo volumen.
7. El dashboard local funciona y consume el artefacto correcto, pero el encargo dice 0,55 mientras la especificación vigente usa 0,52; debe formalizarse una sola autoridad.
8. La tesis no está en el repositorio, por lo que sus cifras no pudieron auditarse; este es el pendiente documental más importante antes de la defensa.
9. También siguen abiertos la licencia/procedencia completa del Excel, la aceptación con usuarios, la accesibilidad y el despliegue público.
