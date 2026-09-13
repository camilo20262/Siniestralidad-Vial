# Auditoría integral del proyecto de tesis

**Fecha de auditoría:** 13 de septiembre de 2026
**Semana declarada del cronograma:** 8
**Sustentación prevista:** 30 de noviembre de 2026
**Alcance:** estado del repositorio y del árbol de trabajo; no se reentrenaron modelos ni se ejecutaron notebooks completos durante esta auditoría.

## 1. Resumen ejecutivo

El proyecto tiene un núcleo experimental serio y reproducible, pero **no está listo para sustentar como sistema terminado**.
**Avance global ponderado estimado: 60 %**; modelado/evaluación están adelantados, mientras producto y documentación están incompletos.
Problema grave 1: el dashboard falla en la vista global por una clave de modelo inexistente y no implementa mapa, fecha, inferencia ni filtro de actor vial (`dashboard/dist/app.js:5-9`).
Problema grave 2: no se encontró documento final de tesis, manual técnico ni manual de usuario; el README y la ficha del modelo no los sustituyen.
Problema grave 3: el alcance declarado no es homogéneo: `01_Comprension_del_Negocio.ipynb` promete k-fold, actor vial como entrada y mapas predictivos, pero la línea vigente usa cortes temporales manuales, no modela actor y muestra métricas retrospectivas.
Fortaleza 1: etiqueta, históricos, preprocesamiento y selección respetan el pasado en la línea vigente (`03B`, celdas 16 y 18; `04B`, celdas 8 y 12; `04C`, celdas 7 y 11).
Fortaleza 2: tres familias se comparan, RF se ajusta sin usar 2023–2024 y se reportan AP, AUC, F1, precisión, recall, Brier y matrices (`reports/evaluation_victimas/metricas_globales.csv`).
Fortaleza 3: el modelo cerrado reproduce 58.480 decisiones y sus métricas; además existe una ejecución aislada completa equivalente, aunque todavía no está versionada (`reports/reproducibilidad/ejecucion_20260913/INFORME.md:5-48`).
El modelo principal actual es **RF ajustado, umbral 0,52, F1 0,4058 y AUC 0,6933**; la afirmación RF 0,55/F1 0,398/AUC 0,685 corresponde ya al modelo base histórico.
La contribución incremental frente a una tasa histórica localidad–franja–día es mínima y no concluyente en AP/AUC; esto debe discutirse, no ocultarse.
Dictamen: **apto para continuar a cierre, no apto todavía para entrega a jurado**.

## 2. Inventario de archivos

### 2.1 Criterios del inventario

- Los tamaños son los observados el 13/09/2026. Se excluyen dependencias instaladas en `.venv/`.
- Los PNG de una misma fase y las tablas homogéneas se agrupan en una fila, pero se enumeran todos sus nombres.
- “Completo” significa que cumple su función técnica acotada, no que cierre por sí solo el objetivo de tesis.
- El bloque `reports/reproducibilidad/` y `scripts/reproducir_cadena_aislada.py` estaba **sin seguimiento Git**. No cuenta como evidencia disponible para quien clone `main` hasta versionarlo o publicarlo como anexo.

### 2.2 Raíz, datos y configuración

| Ruta | Contenido/función | Actividad / objetivo | Estado | Problemas y decisión de entrega |
|---|---|---|---|---|
| `README.md` (9,7 KB) | Presenta escenario de víctimas, modelo, resultados, ejecución y estructura. | 1.2, 6.2 / Obj. 1–6 | parcial | Bien actualizado al RF 0,52 (`README.md:13-29`), pero llama “dashboard” a un visor con fallo y no da URL pública (`README.md:109-115`). Consolidar con manuales, no eliminar. |
| `requirements.txt` (239 B) | Fija 15 dependencias directas con versión exacta. | 2.2–5.1 / Obj. 1–4 | completo | La reproducción aislada acredita una instalación concreta; no fija Python/plataforma ni transitivas en el archivo raíz. |
| `.gitignore` | Ignora `.DS_Store`, `__pycache__`, entornos y secretos. | Estructura / transversal | completo | Los archivos ya rastreados no se dejan de versionar por agregarlos aquí. |
| `.gitattributes` | Declara el Excel crudo en Git LFS. | 2.1 / Obj. 1 | completo | Solo cubre `data/raw/*.xlsx`; verificar disponibilidad LFS antes de entregar. |
| `.DS_Store`; `dashboard/.DS_Store`; `data/.DS_Store`; `data/processed/.DS_Store`; `reports/.DS_Store` | Metadatos de Finder sin valor académico. | Ninguna | basura o duplicado | **Eliminar del índice Git** antes de entregar. Recuperables desde el sistema; no contienen evidencia. |
| `data/raw/base-anuario-de-siniestralidad-2024.xlsx` (126,58 MB) | Fuente con hojas Siniestros (278.614×40), Vehículos (523.168×32), Actor_vial (608.155×44) y Diccionario (110×3). | 2.1 / Obj. 1–2 | completo | Binario LFS; no hay script de descarga ni manifiesto de origen/fecha/licencia junto al archivo. El repositorio enlaza fuentes, pero falta ficha de procedencia del Excel. |
| `data/processed/dataset_localidad_franja_fecha.parquet` (683 KB) | Cuadrícula histórica de todos los siniestros: 204.560×16. | 2.2, 4.1 / sensibilidad | obsoleto | Escenario anterior afectado por “Solo daños”. **Mover a `legacy/` o rotularlo de forma inequívoca**; no mezclar con resultados principales. |
| `data/processed/dataset_victimas_localidad_franja_fecha.parquet` (577 KB) | Dataset principal: 20 localidades×4 franjas×2.557 días, 204.560×16, construido con 85.199 siniestros con víctimas. | 2.2–5.1 / Obj. 1, 3, 4 | completo | La cifra 85.199 es el número de siniestros agregados, no el número de filas del dataset. Debe explicarse siempre. |
| `data/reference/localidades_sdp_referencia.geojson` (2,36 MB) | 20 polígonos oficiales de referencia en EPSG:4326. | 3.1 / Obj. 2 | completo | Instantánea actual, no límites históricos; no se usa en el modelo (`data/reference/README.md:7-9`). |
| `data/reference/localidades_sdp_referencia_metadata.json`; `data/reference/README.md` | URL, atribución, fecha, CRS, SHA-256 y límites de uso de la cartografía. | 2.1, 3.1 / Obj. 1–2 | completo | Buena trazabilidad; fecha de consulta 13/09/2026 (`metadata:2-8`). |

### 2.3 Notebooks

| Ruta | Contenido/función | Actividad / objetivo | Estado | Problemas y decisión de entrega |
|---|---|---|---|---|
| `notebooks/01_Comprension_del_Negocio.ipynb` | Objetivos, problema, pregunta y beneficios; 7 celdas markdown. | 1.1–1.2 / transversal | borrador | Declara k-fold (celda 2), granularidad sin fecha (celda 5), actor como entrada y mapas predictivos (celdas 5–6); contradice el sistema vigente. También conserva cifras bibliográficas que el repo no permite verificar. Actualizar, no eliminar. |
| `notebooks/02_Comprension_de_los_Datos.ipynb` | Inspecciona Siniestros, Vehículos y Actor_vial; 25/25 celdas de código con ejecución, sin errores guardados. | 2.1 / Obj. 1 | completo | Resultados exploratorios no equivalen a un pipeline de descarga/integración automatizado. |
| `notebooks/02B_EDA_y_Analisis_Espacial_Con_Victimas.ipynb` | EDA temporal, festivos, actores, cobertura, polígonos, celdas de 100 m y sensibilidad a 2020; 12/12 celdas ejecutadas, 0 errores. | 3.1 / Obj. 2 | completo | Descarga cartografía si falta (celda 17), por lo que una ejecución limpia necesita red; documenta bien CRS y no reasigna localidades. |
| `notebooks/03_Preparacion_de_los_Datos (3).ipynb` | Prepara escenario original con todos los siniestros; 28/28 celdas ejecutadas. | 2.2 / sensibilidad | obsoleto | Nombre con sufijo `(3)` y salida canónica antigua inducen confusión. **Mover a `notebooks/legacy/` y renombrar**, no borrar la evidencia histórica. |
| `notebooks/03B_Preparacion_Datos_Con_Victimas.ipynb` | Filtra víctimas, crea cuadrícula, calendario, lags y etiqueta; 9 celdas de código sin ejecución guardada en la copia raíz. | 2.2 / Obj. 1 | completo | Rutas `../` dependen de ejecutar desde `notebooks/` (celda 4). La copia ejecutada solo existe en el bloque no versionado de reproducibilidad. |
| `notebooks/04_Modelado.ipynb` | Modelado del escenario original; 16/16 celdas ejecutadas. | 4.1 / sensibilidad | obsoleto | Contiene `StratifiedKFold` y validación aleatoria (celdas 29–32). **Archivar como legado** para que no contradiga el protocolo principal. |
| `notebooks/04B_Modelado_Con_Victimas.ipynb` | Compara RL, RF y XGBoost en tres cortes expansivos; selecciona familia y umbral base 0,55; 12 celdas sin ejecución guardada en raíz. | 4.1 / Obj. 3–4 | completo | No usa la clase `TimeSeriesSplit`; implementa cortes manuales (celda 12). `pipeline_modelo_seleccionado.pkl` que genera es hoy un alias histórico (celda 25). |
| `notebooks/04C_Ajuste_Hiperparametros_Con_Victimas.ipynb` | Evalúa ocho configuraciones RF, elige candidato 3 y umbral 0,52; 6/6 celdas ejecutadas, sin errores. | 4.2 / Obj. 4 | completo | Búsqueda acotada solo a RF; configuración y umbral usan las mismas OOF 2020–2022, sin validación anidada (celdas 7 y 11). |
| `notebooks/05_Evaluacion.ipynb` | Evaluación extensa del escenario antiguo; 36/37 celdas ejecutadas, 0 errores guardados. | 5.1 / sensibilidad | obsoleto | Incluye selección diagnóstica sobre 2023 y nombres “Probabilidad”; resultados no son los del modelo principal. **Archivar junto con `reports/evaluation/`**. |
| `notebooks/05B_Evaluacion_Con_Victimas.ipynb` | Evaluación principal: métricas, curvas, calibración, subgrupos, Candelaria, referencias y bootstrap; 27/27 celdas ejecutadas. | 5.1 / Obj. 4 | completo | Usa “score” correctamente en la línea vigente; el diagnóstico de umbral de Candelaria se calcula en test pero se marca explícitamente como no adoptable (celdas 39–41). |

### 2.4 Modelos, código y pruebas

| Ruta | Contenido/función | Actividad / objetivo | Estado | Problemas y decisión de entrega |
|---|---|---|---|---|
| `models/modelo_logistica.pkl`; `modelo_random_forest.pkl`; `modelo_xgboost.pkl`; `preprocesador_arboles.pkl`; `preprocesador_logistica.pkl` | Modelos/componentes del escenario total antiguo. | 4.1 / sensibilidad | obsoleto | **Mover como conjunto a `models/legacy/`**; hoy duplican nombres del escenario vigente y el RF antiguo ocupa 15,4 MB. |
| `models/victimas/pipeline_logistica_victimas.pkl`; `pipeline_random_forest_victimas.pkl`; `pipeline_xgboost_victimas.pkl` | Pipelines comparativos del 04B. | 4.1 / Obj. 3 | completo | Correctamente separados; conservar para reproducir la comparación. |
| `models/victimas/pipeline_random_forest_ajustado_victimas.pkl` (87,77 MB) | Pipeline principal cerrado. | 4.2–6.1 / Obj. 4–5 | completo | Archivo grande; integridad controlada por registro. No está consumido por el dashboard web. |
| `models/victimas/pipeline_modelo_seleccionado.pkl` | Alias histórico del RF base 0,55. | 4.1 / legado | obsoleto | Nombre engañoso pese a advertencia en `models/victimas/README.md:11-17`. **Renombrar/retirar en próxima versión**, preservando hash del cierre actual. |
| `models/victimas/modelo_logistica.pkl`; `modelo_random_forest.pkl`; `modelo_xgboost.pkl`; `preprocesador_logistica.pkl`; `preprocesador_arboles.pkl` | Componentes separados generados por 04B. | 4.1 / Obj. 3 | parcial | Duplican lo contenido en pipelines; conservar solo si existe consumidor documentado. **Candidatos a consolidación**. |
| `models/victimas/metadata_modelo.json` | Metadatos históricos de la selección base RF 0,55. | 4.1 / Obj. 3–4 | obsoleto | Es requerido por 05B para variables/umbral base, pero el nombre genérico confunde. Renombrar en una versión futura. |
| `models/victimas/metadata_random_forest_ajustado.json` | Parámetros, criterio, umbral y métricas del RF ajustado. | 4.2–5.1 / Obj. 4 | completo | Declara selección sin test; consistente con 04C (`metadata:2-29`). |
| `models/victimas/modelo_principal.json` | Registro oficial con versión, esquema, hashes y evidencias. | 5.1, 6.2 / Obj. 4, 6 | completo | Es la autoridad actual; contradice la decisión 0,55 incluida en el encargo, que quedó histórica. |
| `models/victimas/umbrales_etiqueta_principal.csv` | 80 cuantiles históricos localidad–franja. | 2.2, 5.1 / Obj. 1, 4 | completo | Debe distinguirse del umbral de decisión del modelo. |
| `models/victimas/README.md` | Catálogo que distingue principal, base y componentes. | 6.2 / Obj. 6 | completo | Mitiga, pero no elimina, la confusión causada por nombres históricos. |
| `src/__init__.py` | Declara paquete. | Ingeniería / transversal | completo | Sin problema material. |
| `src/modelo_principal.py` | Carga registro/pipeline, valida entradas y devuelve score/alerta. | 6.1 / Obj. 5 | completo | Requiere 12 variables ya preparadas; no construye históricos ni obtiene datos para una fecha. Es servicio de inferencia incompleto, no sistema extremo a extremo. |
| `src/evaluacion_referencias.py` | Etiquetado temporal, tasas históricas, métricas y bootstrap pareado. | 5.1 / Obj. 4 | completo | Buen código reusable; cubierto por seis pruebas. |
| `tests/test_evaluacion_referencias.py` | Prueba orden, corte temporal, cuantil, grupos nuevos, scores y bootstrap. | 5.1 / Obj. 4 | completo | 6/6 pasan. Faltan pruebas de preparación, cargador y dashboard. |
| `scripts/verificar_modelo_principal.py` | Verifica hashes, etiqueta, 58.480 predicciones y métricas sin entrenar. | 5.1 / Obj. 4 | completo | Ejecutado en esta auditoría con resultado correcto. |
| `scripts/build_phase_3_1_4_2_notebooks.py` | Generador histórico de notebooks 02B/04C. | 3.1, 4.2 / soporte | obsoleto | Manipular notebooks por posiciones es frágil; el propio README indica protecciones contra sobrescritura. **Retirar o archivar tras consolidar código fuente**. |
| `scripts/update_05b_for_tuned_model.py` | Generador/actualizador histórico de 05B. | 5.1 / soporte | obsoleto | Código duplicado y acoplado a estructura de celdas. **Archivar** cuando el notebook quede estable. |
| `scripts/reproducir_cadena_aislada.py` | Crea entorno/copia aislada, ejecuta 03B→05B y compara artefactos. | Reproducibilidad / Obj. 1–4 | completo, no versionado | Evidencia valiosa, pero `git status` lo mostraba `??`. Versionar tras revisar tamaño y política de artefactos. |
| `src/__pycache__/*`; `scripts/__pycache__/*`; `tests/__pycache__/*` | Bytecode local Python. | Ninguna | basura o duplicado | **Eliminar del índice y del paquete de entrega**; regenerable. |

### 2.5 Reportes vigentes

| Ruta(s) | Contenido/función | Actividad / objetivo | Estado | Problemas y decisión de entrega |
|---|---|---|---|---|
| `reports/data_quality/comparacion_cobertura_por_gravedad.csv` | Conteos 2018–2024; evidencia caída de Solo daños 12.557→1.115 en 2023 y estabilidad de víctimas. | 2.1–2.2 / Obj. 1 | completo | Respalda el quiebre observado; por sí solo no prueba causalidad legal. |
| `reports/eda_victimas/01_cobertura_coordenadas.png`; `02_distribucion_anual_localidad.png`; `03_densidad_espacial_victimas.png`; `04_centros_localidad.png`; `05_serie_temporal_mensual.png`; `06_dia_franja_y_mes.png`; `07_festivos_denominadores.png`; `08_actores_dia_franja.png`; `09_mapa_localidades_oficial.png`; `10_estabilidad_sensibilidad_2020.png` | Diez visualizaciones ejecutadas de EDA espacial, temporal, actores y sensibilidad. | 3.1 / Obj. 2 | completo | Son descriptivas, no mapas de predicción ni tasas ajustadas por exposición. |
| `reports/eda_victimas/actores_dia_semana_franja.csv`; `actores_por_localidad.csv`; `calidad_indicadores_actores.csv`; `registros_actor_condicion_dia_franja.csv`; `registros_actor_por_condicion_gravedad.csv`; `integridad_hoja_actores.csv`; `resumen_picos_actores.csv` | Evidencia tabular de actores desde indicadores de siniestro y hoja Actor_vial. | 3.1 / Obj. 2 | completo | Participaciones se solapan; registros de actores no son siniestros ni personas únicas necesariamente (`conclusion_ejecutiva.md:17-22`). |
| `reports/eda_victimas/cobertura_coordenadas.csv`; `coordenadas_para_revision.csv`; `control_poligonos_y_rectangulo.csv`; `centros_medianos_siniestros.csv`; `top25_celdas_concentracion.csv`; `resumen_localidades.csv`; `estabilidad_territorial_periodos.csv` | Controles y agregaciones espaciales. | 3.1 / Obj. 2 | completo | Hay 5.782 discrepancias localidad declarada/polígono para revisar; no se corrigen automáticamente (`conclusion_ejecutiva.md:24-39`). |
| `reports/eda_victimas/dia_semana_franja.csv`; `estacionalidad_mes.csv`; `festivos_comparacion_dias_equivalentes.csv`; `festivos_estandarizados_dia_semana.csv`; `festivos_por_anio.csv`; `serie_diaria_calendario.csv`; `serie_mensual.csv`; `resumen_anual.csv`; `sensibilidad_universo_gravedad.csv`; `comparacion_indicadores_gravedad.csv` | Agregaciones temporales, festivos, pandemia y sensibilidad del indicador de gravedad. | 3.1 / Obj. 2 | completo | Descriptivas; no controlan exposición al tránsito. |
| `reports/eda_victimas/conclusion_ejecutiva.md`; `verificacion_actividad_3_1.json` | Síntesis y controles de integridad de 85.199 siniestros, 20 polígonos y 84 cruces actor–día–franja. | 3.1 / Obj. 2 | completo | Buena delimitación de inferencias (`conclusion:41-49`). |
| `reports/modeling_victimas/validacion_temporal_detalle.csv`; `validacion_temporal_resumen.csv`; `predicciones_oof_2020_2022.parquet`; `01_validacion_temporal_modelos.png` | Comparación temporal de tres familias. | 4.1 / Obj. 3–4 | completo | Predicciones se llaman `Probabilidad` aunque no están calibradas. Conviene renombrar a `Score`. |
| `reports/modeling_victimas/seleccion_umbral_2020_2022.csv`; `02_seleccion_umbral.png`; `confirmacion_retrospectiva_2023_2024.csv`; `predicciones_2023_2024.parquet` | Selección RF base 0,55 y evaluación histórica. | 4.1 / Obj. 3–4 | obsoleto como resultado principal | Conservar como comparación base, rotulado como tal. |
| `reports/tuning_victimas/busqueda_temporal_detalle.csv`; `busqueda_temporal_resumen.csv`; `01_busqueda_hiperparametros.png` | Ocho configuraciones×tres cortes; el candidato 3 gana por AP media. | 4.2 / Obj. 4 | completo | Búsqueda no exhaustiva y solo RF. |
| `reports/tuning_victimas/seleccion_umbral.csv`; `02_seleccion_umbral.png`; `predicciones_oof_mejor_configuracion.parquet` | Selección del 0,52 sobre OOF 2020–2022. | 4.2 / Obj. 4 | completo | Mismas OOF usadas para escoger configuración y umbral. |
| `reports/tuning_victimas/confirmacion_retrospectiva_2023_2024.csv`; `conclusion_ejecutiva.md` | Resultado RF ajustado y síntesis. | 4.2–5.1 / Obj. 4 | completo | Llamar siempre retrospectiva, no test futuro intacto. |
| `reports/evaluation_victimas/01_matrices_confusion.png`; `02_curvas_roc_pr.png`; `03_calibracion.png`; `04_metricas_por_anio.png`; `05_errores_territoriales_temporales.png`; `06_importancia_interna_random_forest.png`; `06_importancia_interna_random_forest_ajustado.png`; `07_importancia_permutacion.png`; `08_volumen_prevalencia_recall.png`; `09_bootstrap_referencia_historica.png`; `10_curvas_referencia_historica.png` | Gráficas de evaluación principal, base, subgrupos, calibración y referencia. | 5.1 / Obj. 4 | completo | Mantener ambas gráficas `06_*` rotuladas base/ajustado; no confundir importancia con causalidad. |
| `reports/evaluation_victimas/metricas_globales.csv`; `metricas_por_anio.csv`; `metricas_macro_localidad.csv`; `metricas_random_forest_por_localidad.csv`; `metricas_random_forest_por_franja.csv`; `metricas_random_forest_ajustado_por_localidad.csv`; `metricas_random_forest_ajustado_por_franja.csv` | Métricas globales, anuales y de subgrupos para base y principal. | 5.1 / Obj. 4 | completo | Buen conjunto; falta intervalo de incertidumbre de métricas finales por subgrupo. |
| `reports/evaluation_victimas/predicciones_random_forest_2023_2024.parquet`; `predicciones_random_forest_ajustado_2023_2024.parquet`; `predicciones_referencias_historicas_2023_2024.parquet` | Evidencia fila a fila para base, ajustado y referencias. | 5.1 / Obj. 4 | completo | Datos retrospectivos, no pronósticos publicados para fechas futuras. |
| `reports/evaluation_victimas/calibracion_por_deciles.csv`; `calibracion_por_localidad.csv`; `comparacion_brier_lineas_base.csv` | Diagnóstico de calibración y Brier. | 5.1 / Obj. 4 | completo | Confirma que score no es probabilidad; Brier RF 0,2221 vs constante train 0,1544. |
| `reports/evaluation_victimas/diagnostico_scores_localidad.csv`; `diagnostico_umbral_candelaria.csv`; `impacto_umbral_candelaria.csv`; `resumen_candelaria.csv`; `diagnostico_volumen_franja.csv`; `correlaciones_spearman_localidad.csv` | Fallos territoriales/horarios y análisis de umbral. | 5.1 / Obj. 4 | completo | Umbral específico de Candelaria usa test solo como diagnóstico; no adoptarlo. Spearman prevalencia–recall 0,911 y volumen–recall −0,065. |
| `reports/evaluation_victimas/importancia_interna_random_forest.csv`; `importancia_interna_random_forest_ajustado.csv`; `importancia_permutacion_random_forest.csv`; `importancia_permutacion_random_forest_ajustado.csv` | Importancias base/ajustada. | 5.1 / Obj. 4 | completo | Permutación usa muestra de 5.000 y tres repeticiones; no causal. |
| `reports/evaluation_victimas/tasas_train_1_claves.csv`; `tasas_train_2_claves.csv`; `tasas_train_3_claves.csv`; `comparacion_referencias_historicas.csv`; `referencias_validacion_temporal_detalle.csv`; `referencias_validacion_temporal_resumen.csv`; `referencias_por_anio.csv` | Referencias históricas calculadas solo con pasado. | 5.1 / Obj. 4 | completo | La tasa de tres claves prácticamente iguala al RF en AP/AUC y lo supera en Brier; hallazgo central, no accesorio. |
| `reports/evaluation_victimas/bootstrap_rf_vs_referencia_replicas.csv`; `bootstrap_rf_vs_referencia_resumen.csv` | 300 réplicas pareadas por bloques semanales. | 5.1 / Obj. 4 | completo | Intervalos exploratorios; no incluyen incertidumbre de reentrenamiento/selección. |
| `reports/evaluation_victimas/comparacion_random_forest_ajustado_vs_base.csv`; `carga_alertas_modelo_principal.csv` | Efecto del ajuste y carga de 33,85 alertas/día. | 5.1 / Obj. 4–5 | completo | La carga operativa no está conectada con capacidad institucional ni costos. |
| `reports/evaluation_victimas/conclusion_ejecutiva.md`; `verificacion_ampliacion_05b.json` | Síntesis actual y verificación de cierre. | 5.1 / Obj. 4 | completo | Correctamente prudente; debe integrarse al documento final. |
| `reports/modelo_principal/ficha_tecnica_modelo.md`; `verificacion_cierre.json` | Model card académica y resultado del verificador. | 5.1, 6.2 / Obj. 4, 6 | completo | Excelente evidencia técnica; no sustituye manual ni capítulo metodológico. |
| `reports/auditoria_proyecto/analisis_integral_2026-09-12.md`; `diagnosticos_2026-09-12.json` | Auditoría previa y datos diagnósticos. | Gestión / transversal | parcial | Parte del diagnóstico quedó superada por ampliaciones posteriores de 02B/05B y reproducción del 13/09. **Conservar como histórico fechado**, no presentarlo como estado vigente. |

### 2.6 Artefactos antiguos, dashboard y reproducibilidad

| Ruta(s) | Contenido/función | Actividad / objetivo | Estado | Problemas y decisión de entrega |
|---|---|---|---|---|
| `reports/evaluation/` completo: 11 PNG; 19 CSV; 2 Parquet; `conclusion_ejecutiva.md` | Evaluación del escenario antiguo con todos los siniestros/XGBoost. | 5.1 / sensibilidad | obsoleto | **Mover el directorio completo a `reports/legacy/evaluation_todos_los_siniestros/`**. Contiene ajuste diagnóstico con 2023 y lenguaje de probabilidad; no mezclar con el principal. |
| `dashboard/dist/index.html`; `styles.css`; `app.js`; `favicon.svg` | Visor web estático de métricas retrospectivas. | 6.1 / Obj. 5 | parcial | Falla vista global (`app.js:5`), filtros no se cruzan (`app.js:8`), barras `<i>` carecen de `display:block`, y no hay mapa/fecha/actor/inferencia (`index.html:31-39,70-85`). |
| `dashboard/dist/data/metricas_globales.csv`; `metricas_por_localidad.csv`; `metricas_por_franja.csv`; `importancia.csv` | Copias de resultados para el frontend. | 6.1 / Obj. 5 | parcial | Son marginales y estáticas; no permiten localidad×franja ni alertas por fecha. Riesgo de desincronización manual. |
| `dashboard/.openai/hosting.json` | Identificador y directorio de alojamiento estático. | 6.1 / Obj. 5 | parcial | No contiene URL pública ni prueba de disponibilidad. La configuración no demuestra despliegue público. |
| `reports/reproducibilidad/README.md`; `.gitignore` | Explica el ensayo aislado y exclusiones. | Reproducibilidad / Obj. 1–4 | completo, no versionado | Versionar al menos instrucciones y manifiestos. |
| `reports/reproducibilidad/ejecucion_20260913/INFORME.md`; `estado.json`; `resultado.json`; `resultado_previo_20260913_072310.json`; `comparacion_dataset.json`; `ejecuciones_notebooks.json`; `entorno.json`; `procedencia.json`; `adaptacion_registro_local.json`; `integridad_oficial_antes.json`; `dependencias_congeladas.txt`; `instalacion.log`; `requirements.txt`; `runtime/kernels/repro/kernel.json` | Manifiestos, entorno, tiempos y comparación de una ejecución limpia. | Reproducibilidad / Obj. 1–4 | completo, no versionado | Evidencia fuerte, pero incluye un resultado previo fallido que debe rotularse/archivarse y datos de entorno potencialmente locales. Revisar antes de publicar. |
| `reports/reproducibilidad/ejecucion_20260913/notebooks/{03B,04B,04C,05B}*.ipynb` | Copias ejecutadas, 54 celdas, 0 errores. | 2.2–5.1 / Obj. 1–4 | completo, no versionado | Útiles como evidencia ejecutada; son copias. Elegir entre promover salidas a notebooks canónicos o conservarlas como artefacto de corrida, no ambas sin catálogo. |
| `reports/reproducibilidad/ejecucion_20260913/data/**`; `models/**`; `reports/**`; `src/**`; `scripts/**` | Copia aislada de fuente, dataset, modelos, código y 57 salidas. | Reproducibilidad / Obj. 1–4 | basura o duplicado para entrega Git | Duplica >250 MB, incluido el Excel y modelos. **No versionar la copia completa**; conservar manifiestos, notebooks ejecutados y hashes en un release/almacenamiento apropiado. |
| `reports/reproducibilidad/ejecucion_20260913/.venv/**`; `__pycache__/**` | Entorno virtual y bytecode de la reproducción. | Ninguna | basura o duplicado | **Excluir de cualquier entrega**; no es portable y se reconstruye con requisitos. |

### 2.7 Archivos no encontrados

| Entregable esperado | Resultado de búsqueda | Estado |
|---|---|---|
| Documento final de tesis `.docx`, `.pdf` o `.md` | No encontrado fuera de reportes técnicos. | no evidenciado |
| Manual técnico independiente | No encontrado. | no evidenciado |
| Manual de usuario independiente | No encontrado. | no evidenciado |
| Presentación/diapositivas o guion de sustentación | No encontrado. | no evidenciado |
| URL pública verificable del dashboard | No encontrada en README/configuración. | no evidenciado |
| CI (`.github/workflows`, similar) | No encontrado. | no evidenciado |

## 3. Auditoría metodológica

### 3.1 Fuga de información

**Hallazgo.** No se encontró fuga directa en el pipeline vigente. El cuantil 2/3 final se calcula solo con filas `train` hasta 2022; los lags excluyen el día actual; en cada corte se recalcula la etiqueta y el preprocesamiento se ajusta dentro de un `Pipeline`. La evaluación supone predicción diaria a un paso con históricos observados hasta el día anterior: no valida pronóstico de todo un horizonte sin actualizar datos.

**Evidencia.** `notebooks/03B_Preparacion_Datos_Con_Victimas.ipynb`, celda 16, líneas 1–17 (`shift(1)`, `shift(7)`); celda 18, líneas 1–17 (train y cuantil); `04B`, celda 8, líneas 5–21 y celda 12, líneas 5–23; `04C`, celda 3, líneas 45–57.

**Severidad:** baja para leakage; media para la condición operativa no validada.

**Corrección recomendada.** Declarar explícitamente “pronóstico diario de un paso con actualización de conteos” y probar disponibilidad/latencia de SIGAT. Si el caso de uso exige varios días futuros, construir y evaluar ese horizonte sin usar observaciones intermedias reales.

### 3.2 Validación temporal

**Hallazgo.** La línea vigente respeta el tiempo mediante tres ventanas expansivas manuales: hasta 2019→2020, hasta 2020→2021 y hasta 2021→2022. **No se usa literalmente `TimeSeriesSplit`**. Además, `04_Modelado.ipynb` conserva `StratifiedKFold` aleatorio, aunque README lo presenta como escenario histórico.

**Evidencia.** `04B`, celda 12, líneas 1–23; `04C`, celda 7, líneas 1–17; `04_Modelado.ipynb`, celdas 29–32; `README.md:19,97`.

**Severidad:** alta por contradicción documental y riesgo de que el jurado abra el notebook equivocado; baja para la validez de los cortes manuales en sí.

**Corrección recomendada.** Elegir una de dos rutas: (a) describir honestamente “cortes anuales expansivos manuales”, preferible por claridad; o (b) implementar un splitter temporal equivalente y demostrar las mismas fronteras. Archivar notebooks antiguos y añadir una tabla canónica de experimentos.

### 3.3 Reproducibilidad

**Hallazgo.** Hay semillas fijas (`42`), dependencias directas fijadas, hashes, un verificador de no reentrenamiento y una reproducción aislada completa equivalente. La debilidad es de entrega: 03B/04B raíz no guardan salidas y toda la evidencia limpia del 13/09 está sin seguimiento Git.

**Evidencia.** `04B`, celda 4, línea 47; `04C`, celda 3, línea 27; `requirements.txt:1-15`; `reports/modelo_principal/verificacion_cierre.json:1-24`; `reports/reproducibilidad/ejecucion_20260913/INFORME.md:5-48`; `git status` mostró `?? reports/reproducibilidad/` y `?? scripts/reproducir_cadena_aislada.py`.

**Severidad:** media.

**Corrección recomendada.** Versionar el script y manifiestos ligeros; conservar notebooks ejecutados o publicar un release de corrida; añadir versión de Python y comando único al README/CI. No subir `.venv`, Excel duplicado ni copias de modelos sin política LFS.

### 3.4 Coherencia dataset ↔ documento

**Hallazgo.** El modelo principal sí usa exclusivamente `Con Heridos`/`Con Muertos`: 85.199 siniestros se agregan a 204.560 filas localidad–franja–día. Persisten dataset, notebooks, modelos y reportes del escenario total. El README los rotula como sensibilidad, pero sus nombres genéricos siguen siendo peligrosos.

**Evidencia.** `03B`, celdas 10, 12, 14 y 21; `reports/data_quality/comparacion_cobertura_por_gravedad.csv:2-8`; `reports/modelo_principal/ficha_tecnica_modelo.md:20-42`; `README.md:19,27`.

**Severidad:** media.

**Corrección recomendada.** Crear `legacy/todos_los_siniestros/`, un manifiesto de artefactos y una única ruta `current`. En el texto diferenciar siempre “85.199 siniestros fuente” de “204.560 observaciones modeladas”.

### 3.5 Umbral de decisión

**Hallazgo.** El umbral vigente no es 0,55 sino **0,52**. Se elige maximizando F1 agregado en las OOF 2020–2022 del RF ajustado; no usa 2023–2024. El 0,55 corresponde al RF base. Las mismas OOF se usan para escoger hiperparámetros y umbral, por lo que la estimación de selección es optimista y no anidada.

**Evidencia.** `04C`, celda 11, líneas 1–21; celda 13, líneas 1–15; `models/victimas/metadata_random_forest_ajustado.json:2-18`; `models/victimas/README.md:3-13`.

**Severidad:** alta si el documento final aún afirma 0,55; media metodológicamente.

**Corrección recomendada.** Actualizar todas las afirmaciones al modelo 0,52 o declarar explícitamente base vs. principal. Justificar F1 frente a una función de costos/capacidad; para una estimación menos sesgada, separar selección de configuración y umbral o usar validación temporal anidada.

### 3.6 Métricas y desbalance

**Hallazgo.** Se reportan F1, AUC-ROC, Average Precision/PR, precisión, recall, especificidad, balanced accuracy, Brier y matriz de confusión. Son adecuadas para desbalance. Falta una explicación canónica y explícita de por qué accuracy simple no basta; además, el criterio operativo no está conectado con costos.

**Evidencia.** `04B`, celda 8, líneas 25–47; `reports/evaluation_victimas/metricas_globales.csv`; `dashboard/dist/index.html:42-66`; `reports/evaluation_victimas/carga_alertas_modelo_principal.csv`.

**Severidad:** baja por cobertura métrica; media por criterio operativo.

**Corrección recomendada.** Añadir en tesis una subsección de desbalance, prevalencia y costo. Mostrar AP frente a prevalencia, F1 macro territorial y carga de 33,85 alertas/día; no usar accuracy como argumento principal.

### 3.7 Calibración

**Hallazgo.** El Brier se compara contra constantes de prevalencia y el producto vigente dice correctamente que el score no es probabilidad. Persisten nombres `Probabilidad` y el título “Calibración de probabilidades” en artefactos antiguos y OOF base; pueden inducir una cita errónea si no se archivan.

**Evidencia.** `reports/evaluation_victimas/comparacion_brier_lineas_base.csv`; `05B`, celdas 14–16 y 31–33; `dashboard/dist/index.html:60-66`; `reports/modeling_victimas/predicciones_oof_2020_2022.parquet`; `05_Evaluacion.ipynb`, celdas 22–24.

**Severidad:** baja en la línea vigente; media por legado ambiguo.

**Corrección recomendada.** Renombrar campos futuros a `Score_Priorizacion`; rotular material heredado; si se requiere probabilidad, calibrar con un bloque temporal independiente y reevaluar Brier/calibration slope.

### 3.8 Análisis espacial

**Hallazgo.** Sí existe EDA espacial real: polígonos GeoJSON, reproyección, cobertura, `point-in-polygon`, mapa administrativo, densidad, centros medianos y cuadrícula métrica. Es descriptivo y no forma parte del modelo/dashboard predictivo.

**Evidencia.** `02B`, celdas 17–23; `data/reference/README.md:1-9`; `reports/eda_victimas/verificacion_actividad_3_1.json:2-10`; `reports/eda_victimas/conclusion_ejecutiva.md:24-39`.

**Severidad:** baja para EDA; alta para la brecha con el objetivo de dashboard georreferenciado.

**Corrección recomendada.** Mantener la distinción concentración observada vs. score/predicción. Integrar un mapa por localidad al dashboard solo con la resolución que el modelo soporta; no insinuar riesgo de calle.

### 3.9 Actor vial

**Hallazgo.** Actor vial está bien trabajado en el EDA, incluyendo la hoja `Actor_vial`, pero **no está entre las 12 variables del modelo ni existe como filtro del dashboard**. Por tanto, se cumple el objetivo 2 de análisis, no el requisito de filtro del objetivo 5 ni la afirmación de 01 de que el modelo usa actor.

**Evidencia.** `02B`, celdas 13–15; `reports/eda_victimas/conclusion_ejecutiva.md:17-22`; `models/victimas/metadata_modelo.json:9-22`; `dashboard/dist/index.html:31-39`; `01_Comprension_del_Negocio.ipynb`, celdas 5–6.

**Severidad:** alta.

**Corrección recomendada.** Decidir y documentar: (a) actor es solo dimensión descriptiva del EDA y se modifica el objetivo 5; o (b) se construyen resultados/filtros válidos por actor, aclarando que no son predicciones actor-específicas si el modelo no incluye esa variable. No añadir un selector decorativo sin datos cruzados.

### 3.10 Hallazgo adicional: valor incremental

**Hallazgo.** El RF ajustado casi empata a la tasa histórica localidad–franja–día: AP 0,30984 vs. 0,30866; AUC 0,69332 vs. 0,69311. Los intervalos pareados de AP/AUC incluyen cero y la referencia tiene Brier mucho mejor (0,14377 vs. 0,22209).

**Evidencia.** `reports/evaluation_victimas/comparacion_referencias_historicas.csv`; `bootstrap_rf_vs_referencia_resumen.csv`; `conclusion_ejecutiva.md`.

**Severidad:** alta para las conclusiones de aporte; no invalida el trabajo experimental.

**Corrección recomendada.** Convertirlo en resultado de tesis: el ML complejo no demuestra ventaja concluyente frente a una referencia histórica fuerte bajo este diseño. Explicar qué señal añaden o no añaden los lags y qué futuras variables de exposición podrían aportar.

## 4. Pros y contras por componente

| Componente | Fortalezas con evidencia | Debilidades con evidencia | Veredicto para sustentar hoy |
|---|---|---|---|
| Adquisición de datos | Excel oficial completo y hojas relacionadas (`data/raw/...xlsx`); LFS (`.gitattributes:1`); cartografía con URL/hash (`data/reference/*`). | No hay script/manifiesto de descarga del Excel ni licencia/fecha de corte local; se “integra” poco de Vehículos/Actor_vial al modelado. | **Casi listo**, falta procedencia formal. |
| Preprocesamiento | Universo comparable de víctimas, grid completo, lags desplazados, etiqueta train-only y asserts (`03B`, celdas 10–21). | Notebook raíz sin salidas; rutas relativas; etiqueta significa ocurrencia en 49/80 grupos, no siempre “frecuencia alta” (`ficha:31-42`). | **Listo con correcciones documentales**. |
| EDA | Temporal, espacial, festivos, actores, pandemia, CRS y controles; 12 celdas ejecutadas (`02B`; `reports/eda_victimas/`). | Sin denominadores de exposición; 5.782 discrepancias espaciales; mapas son observados, no predictivos (`conclusion EDA:24-46`). | **Listo como EDA descriptivo**, no como mapa de riesgo operativo. |
| Modelado | RL, RF y XGB; pipelines y semillas; selección temporal (`04B`, celdas 10–17). | Cortes manuales, no `TimeSeriesSplit`; legado aleatorio; tuning solo RF y sin anidación. | **Listo para defensa metodológica prudente**. |
| Evaluación | Métricas apropiadas, subgrupos, calibración, referencias fuertes, bootstrap y verificación (`05B`; `reports/evaluation_victimas/`). | Holdout ya inspeccionado durante desarrollo; ventaja vs. referencia no concluyente; falta costo institucional y prospectiva. | **Listo como evaluación retrospectiva**, no como validación operativa. |
| Dashboard | Mensajes correctos sobre score/calibración y CSV actuales (`index.html:27-29,60-66`). | Vista global rota; filtros marginales; sin actor, mapa, fecha, predicciones, inferencia o URL pública (`app.js:5-9`). | **No listo**. |
| Documentación | README, ficha técnica, catálogo de modelos y auditoría previa son sólidos (`README`; `reports/modelo_principal/`; `models/victimas/README.md`). | No hay tesis final ni manuales; 01 está desactualizado; no puede contrastarse documento↔código. | **No listo**. |
| Estructura del repo | Separación raw/processed/models/reports; registro con hashes; pruebas y verificador. | Legado mezclado, nombres engañosos, archivos de sistema/bytecode y reproducción duplicada no versionada; sin CI. | **Parcial; requiere limpieza controlada**. |

## 5. Trazabilidad de objetivos

| Objetivo específico | Actividades | Evidencia principal | Cumplimiento | Qué falta |
|---|---|---|---|---|
| 1. Descargar, integrar y limpiar datos 2018–2024 | 2.1, 2.2 | `data/raw/...xlsx`; `02_Comprension...`; `03B`; `data/processed/dataset_victimas...`; `reports/data_quality/...csv` | parcial | Automatizar/documentar descarga y procedencia; guardar evidencia canónica ejecutada; explicar integración de hojas y gravedad elegida. |
| 2. EDA espacial por localidad, franja y actor | 3.1 | `02B`; `reports/eda_victimas/*`; `data/reference/*` | cumplido | Incorporar al documento y mantener límites: sin exposición, causalidad ni mapas predictivos. |
| 3. Entrenar y comparar RL, RF y XGBoost | 4.1 | `04B`; `reports/modeling_victimas/*`; pipelines comparativos | cumplido | Archivar experimento aleatorio anterior y conservar ejecución canónica visible. |
| 4. Seleccionar con validación temporal y métricas de desbalance | 4.1, 4.2, 5.1 | `04B`; `04C`; `05B`; `reports/tuning_victimas/*`; `reports/evaluation_victimas/*` | cumplido | Alinear “TimeSeriesSplit” con cortes manuales; justificar costo/umbral y carácter retrospectivo; discutir baseline casi equivalente. |
| 5. Dashboard interactivo con modelo, filtros localidad/horario/actor y acceso público | 6.1 | `dashboard/dist/*`; `dashboard/.openai/hosting.json` | parcial | Corregir carga, cruzar filtros, añadir actor, mapa y fecha, integrar predicciones/inferencia, probar y aportar URL pública. |
| 6. Manual técnico/usuario y documento final | 6.2, Docs | `README.md`; `models/victimas/README.md`; `reports/modelo_principal/ficha_tecnica_modelo.md` | no evidenciado | Crear ambos manuales y tesis final; actualizar objetivos, cifras, método, resultados, discusión y referencias. |

## 6. Avance frente al cronograma

### 6.1 Ponderación

Se asigna 20 % a datos/EDA (2.1=5, 2.2=7, 3.1=8), 35 % a modelado/evaluación (4.1=12, 4.2=10, 5.1=13), 20 % al dashboard, 20 % a documentación académica (1.1=5, 1.2=3, documento final=12) y 5 % a manuales/sustentación (6.2=3, sustentación=2). La ponderación penaliza que una tesis técnicamente avanzada aún no tenga producto demostrable ni documento entregable.

| Actividad | Peso | Avance | Evidencia y faltante | Semana planificada vs. semana 8 | Bloqueo |
|---|---:|---:|---|---|---|
| 1.1 Revisión bibliográfica | 5 % | 20 % | Solo formulación en `01`; no hay matriz bibliográfica ni capítulo/referencias verificable. | atrasada 4 semanas; seguimiento debe continuar | Documento/fuentes no están en repo. |
| 1.2 Comprensión y especificación | 3 % | 55 % | Problema/objetivos existen, pero hablan de k-fold, actor/modelo y dashboard no implementado. | atrasada 6 semanas | Falta congelar alcance coherente. |
| 2.1 Descarga e integración | 5 % | 90 % | Fuente completa y cartografía trazable; falta automatización/procedencia formal del Excel. | atrasada 3 semanas | Origen/licencia/fecha y script de adquisición. |
| 2.2 Limpieza, preprocesamiento y features | 7 % | 95 % | Dataset y controles completos; raíz sin salidas ejecutadas y rutas dependientes del cwd. | atrasada 2 semanas | Promover evidencia reproducible al estado versionado. |
| 3.1 EDA y espacial | 8 % | 90 % | EDA amplio y ejecutado; falta integración narrativa y exposición. | a tiempo | Documento final y denominadores externos. |
| 4.1 Entrenamiento RL/RF/XGB | 12 % | 100 % | Tres familias, pipelines y comparación temporal existen. | adelantada | Ninguno técnico; limpiar legado. |
| 4.2 Hiperparámetros | 10 % | 90 % | Ocho candidatos RF y selección temporal; búsqueda acotada/no anidada. | adelantada | Justificar alcance y evitar afirmar óptimo global. |
| 5.1 Evaluación/selección | 13 % | 95 % | Métricas, subgrupos, baseline, bootstrap y verificador completos. | adelantada | Integrar discusión de valor incremental/costos. |
| 6.1 Dashboard | 20 % | 25 % | Existe maqueta estática, pero la vista global falla y faltan funciones nucleares. | adelantada en inicio, no en cierre | Datos cruzados, diseño funcional, integración y despliegue. |
| 6.2 Manuales | 3 % | 0 % | No encontrados. | a tiempo: plan S13, pero sin inicio evidenciado | Dashboard y flujo final no están cerrados. |
| Documento final | 12 % | 5 % | Solo reportes parciales; no hay manuscrito. | atrasada 4 semanas respecto al inicio S4 | Falta ensamblar capítulos y referencias. |
| Sustentación | 2 % | 0 % | No hay diapositivas, guion ni ensayo. | a tiempo: inicia S13 | Depende de producto/documento cerrados. |

**Cálculo:** `5×0,20 + 3×0,55 + 5×0,90 + 7×0,95 + 8×0,90 + 12×1,00 + 10×0,90 + 13×0,95 + 20×0,25 + 3×0 + 12×0,05 + 2×0 = 59,95 %`, redondeado a **60 %**.

**Inferencia de calendario.** Al no existir fecha de inicio ni bitácora semanal en el repo, “atrasada N semanas” se mide contra el fin/inicio comprometido de cada actividad y la semana declarada, no contra horas realmente trabajadas.

## 7. Riesgos de sustentación

| Pregunta incómoda del jurado | ¿Hay respuesta sólida hoy? | Respuesta/evidencia disponible y riesgo |
|---|---|---|
| “¿Por qué llaman alto riesgo a cualquier día con un siniestro en 49 de 80 grupos?” | Parcial | La ficha lo reconoce (`ficha:31-42`), pero obliga a moderar el título y explicar etiqueta heterogénea. |
| “¿Dónde está `TimeSeriesSplit` si ustedes afirman usarlo?” | No, literalmente | Hay cortes expansivos válidos pero manuales (`04B`, celda 12). Corregir afirmación o implementación. |
| “¿Por qué un RF si una tabla histórica lo iguala en AP/AUC y lo supera en Brier?” | Sí, si se asume el resultado | `comparacion_referencias_historicas.csv` y bootstrap permiten una respuesta honesta; no existe superioridad concluyente. |
| “¿El 0,52 fue escogido mirando 2023–2024?” | Sí | No: se obtiene de OOF 2020–2022 (`04C`, celda 11). Aclarar que configuración y umbral comparten OOF. |
| “¿Este score es una probabilidad de accidente?” | Sí | No; Brier peor que constante y dashboard/ficha lo advierten. Evitar abrir artefactos antiguos sin contexto. |
| “¿Por qué Candelaria tiene recall cero?” | Parcial | Su score máximo 0,3227 no llega a 0,52; prevalencia se asocia con recall. La causa del patrón de scores no está explicada causalmente. |
| “Muéstreme ahora el dashboard con filtros combinados y mapa.” | No | La vista global falla; no hay cruce, mapa, actor, fecha ni inferencia. Riesgo alto de demostración fallida. |
| “¿Dónde interviene actor vial en el modelo y el dashboard?” | No | Solo aparece en EDA. Las 12 variables del modelo y los dos filtros lo excluyen. |
| “¿Cómo reproduzco todo desde el Excel en un clon de `main`?” | Parcial | Existe ensayo exitoso, pero script/reportes están sin versionar y 03B/04B canónicos no guardan outputs. |
| “¿Dónde están la tesis final, manuales y bibliografía?” | No | No encontrados. Es el mayor riesgo formal de entrega. |

## 8. Plan de cierre

Las horas son estimaciones de trabajo efectivo y no incluyen tiempos de aprobación institucional ni búsqueda de nuevos datos.

### A. Correcciones obligatorias de metodología y coherencia

| Prioridad | Acción | Horas | Criterio de terminado |
|---:|---|---:|---|
| 1 | Congelar alcance canónico: RF ajustado 0,52; cortes expansivos manuales; unidad localidad×franja×día; actor solo EDA salvo rediseño. | 4–6 | README, 01, ficha, tesis y dashboard dicen lo mismo. |
| 2 | Escribir la discusión del baseline fuerte y reformular la contribución sin afirmar superioridad concluyente. | 6–8 | Tabla RF vs. tasa histórica, intervalos y limitación integrados en resultados/discusión. |
| 3 | Documentar etiqueta heterogénea (49 umbrales cero), horizonte a un paso, disponibilidad de históricos y holdout retrospectivo ya inspeccionado. | 5–7 | Sección metodológica revisable por jurado con ejemplos. |
| 4 | Justificar el umbral por objetivo/capacidad o declarar F1 como criterio académico exploratorio; incluir 33,85 alertas/día y costos. | 4–6 | Criterio operativo explícito, sin reajustar sobre 2023–2024. |
| 5 | Versionar la reproducción ligera y añadir una prueba automatizada de preparación/cargador; no incluir `.venv` ni copias masivas. | 6–10 | Clon limpio ejecuta pruebas/verificador y encuentra manifiestos de reproducción. |

### B. Entregables pendientes

| Prioridad | Acción | Horas | Criterio de terminado |
|---:|---|---:|---|
| 1 | Reparar dashboard global y barras; crear datos cruzados localidad×franja y pruebas funcionales mínimas. | 8–12 | Carga sin errores; selecciones simples/combinadas verificadas. |
| 2 | Implementar mapa por localidad, fecha/periodo y vista de alertas/scores; integrar inferencia o redefinir formalmente como visor retrospectivo. | 24–40 | Cumple alcance acordado, sin precisión geográfica falsa. |
| 3 | Resolver actor vial: filtro descriptivo con datos válidos o cambio aprobado del objetivo. | 8–16 | Selector tiene semántica y tablas cruzadas documentadas. |
| 4 | Desplegar y registrar URL pública, versión/fecha y prueba desde sesión anónima. | 3–6 | Enlace estable en README y manual. |
| 5 | Redactar documento final con bibliografía, método, resultados, discusión, amenazas a validez y trazabilidad. | 45–70 | Manuscrito completo revisado contra evidencia del repo. |
| 6 | Crear manual técnico y manual de usuario. | 12–18 | Instalación, reproducción, inferencia, dashboard, errores, interpretación y límites. |
| 7 | Preparar diapositivas, demo de respaldo, guion y dos ensayos con preguntas de §7. | 12–18 | Sustentación cronometrada y demo offline reproducible. |

### C. Limpieza del repositorio

| Prioridad | Acción | Horas | Criterio de terminado |
|---:|---|---:|---|
| 1 | Mover escenario total a `legacy/` y crear manifiesto `current` vs. `legacy`. | 3–5 | Ningún archivo antiguo parece principal. |
| 2 | Retirar `.DS_Store`, `__pycache__` y entorno virtual/copia masiva de reproducción del paquete de entrega. | 1–2 | `git ls-files` no contiene basura regenerable. |
| 3 | Renombrar en una nueva versión alias/metadatos ambiguos y campos `Probabilidad` a `Score`, respetando hashes del cierre v1.0. | 3–5 | Catálogo y consumidores actualizados; cierre anterior preservado. |
| 4 | Consolidar scripts generadores de notebooks en módulos `src/` o archivarlos. | 4–8 | No hay dos fuentes activas para la misma lógica. |

### D. Mejoras deseables si sobra tiempo

| Prioridad | Acción | Horas | Valor |
|---:|---|---:|---|
| 1 | Validación temporal anidada o bloque separado para configuración/umbral. | 12–20 | Reduce optimismo de selección. |
| 2 | Intervalos por localidad/franja y análisis de estabilidad adicional. | 8–12 | Mejora defensa de heterogeneidad. |
| 3 | Estudiar objetivo homogéneo de ocurrencia/conteo y variables de exposición disponibles antes de predecir. | 20–40 | Aumenta validez sustantiva; constituye nueva versión, no parche. |
| 4 | Calibración con periodo temporal separado y evaluación prospectiva futura. | 12–20 + espera | Solo necesaria si se comunicarán probabilidades. |

**Estimación obligatoria total (A+B+C, sin mejoras deseables): 148–237 horas.** La mayor variación depende de si el dashboard se convierte en sistema predictivo integrado o se renegocia como visor retrospectivo.

## 9. Anexo: comandos ejecutados y salidas resumidas

| Comando/inspección | Salida resumida |
|---|---|
| `find . -type f ...`, `git ls-files`, `stat`, `find ... -type d` | 193 archivos versionados; estructura completa inventariada; reproducción y script adicionales sin seguimiento. |
| `git status --short`, `git log --oneline -15` | `main` en `bae352e`; `reports/reproducibilidad/` y `scripts/reproducir_cadena_aislada.py` aparecían `??`. |
| `jq` sobre los diez `.ipynb` | 03B y 04B raíz sin ejecución guardada; 02, 02B, 03 antiguo, 04 antiguo, 04C y 05B ejecutados; ningún error guardado. |
| Extracción de celdas con `jq` y numeración con `nl` | Verificados cuantil train-only, `shift`, pipelines, cortes manuales, selección de modelo/umbral, calibración, actores y EDA espacial. |
| Lectura con pandas de Excel/Parquet | Excel: 278.614/523.168/608.155/110 filas por hoja; dataset principal 204.560×16, 20 localidades, cuatro franjas, 2.557 días, cero nulos. |
| Lectura JSON/GeoJSON | 20 polígonos; metadatos con URL, EPSG:4326, fecha y SHA-256. |
| `python -m unittest discover -s tests -v` | 6 pruebas ejecutadas, 6 correctas, 0 fallos (0,109 s). |
| `.venv/bin/python scripts/verificar_modelo_principal.py` | Correcto: 58.480 observaciones, 80 umbrales, 12 evidencias, F1 0,405789, AUC 0,693324, umbral 0,52; sin reentrenar. |
| `python3 -m http.server 8765 --directory dashboard/dist`; `curl -I` y CSV | Servidor/archivos responden HTTP 200; el CSV confirma que no existe una fila `Random Forest`, solo `Random Forest ajustado` y `Random Forest base`. |
| Inspección estática `index.html`, `app.js`, `styles.css` | Confirmado fallo de clave global, filtros no combinados, barras sin bloque y ausencia de mapa/actor/fecha/inferencia. No había navegador CUA disponible para repetir la prueba visual; la auditoría previa versionada documenta ese fallo visual (`reports/auditoria_proyecto/analisis_integral_2026-09-12.md:209-231`). |
| `rg` de `TimeSeriesSplit`, `StratifiedKFold`, actor, probabilidad, dashboard y manuales | No aparece `TimeSeriesSplit` en la línea vigente; sí `StratifiedKFold` en el legado; actor solo en EDA/formulación; manuales y URL pública no encontrados. |
| Búsqueda de `*.docx`, `*.pdf`, `*.md` excluyendo entornos | No se encontró tesis final ni manuales; solo README, fichas, conclusiones e informes técnicos. |

### Hechos verificados frente a inferencias

- **Verificado:** resultados, estructuras, código, hashes, pruebas y estados de Git citados arriba.
- **Inferencia:** porcentajes de avance, horas del plan y clasificación de atraso; se basan en entregables observables y semana 8, no en una bitácora de dedicación.
- **No verificable con el repositorio:** coherencia con un manuscrito externo, calidad/cobertura de toda la revisión bibliográfica, disponibilidad pública del dashboard y fecha real de inicio del cronograma.
