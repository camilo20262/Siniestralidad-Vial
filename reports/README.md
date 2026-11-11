# Índice de resultados y evidencias

[Inicio del proyecto](../README.md) · [Especificación vigente](../docs/ESPECIFICACION_VIGENTE.md) · [Reproducibilidad](reproducibilidad/README.md) · [Dashboard](../dashboard/README.md)

El modelo principal es **Random Forest ajustado**, versión
`rf_victimas_bogota_v1.0`, con umbral **0,52**. El
[registro oficial](../models/victimas/modelo_principal.json) identifica sus
artefactos y huellas; la [ficha técnica](modelo_principal/ficha_tecnica_modelo.md)
explica su alcance. La evaluación es retrospectiva sobre **2023–2024**.

## Resultados del cierre vigente

| Tema | Evidencia de referencia | Cómo leerla |
|---|---|---|
| Métricas definitivas | [Métricas globales](evaluation_victimas/metricas_globales.csv) | Comparación del RF ajustado con los modelos de referencia. |
| Desempeño por subgrupo | [Localidad](evaluation_victimas/metricas_random_forest_ajustado_por_localidad.csv) y [franja](evaluation_victimas/metricas_random_forest_ajustado_por_franja.csv) | Desagregación del modelo principal; acompaña las métricas globales. |
| Evaluación e interpretación | [Conclusión de 05B](evaluation_victimas/conclusion_ejecutiva.md) y [carpeta de evaluación](evaluation_victimas/) | Errores, calibración, importancia de variables y límites del resultado. |
| Referencias e incertidumbre | [Comparación de tasas históricas](evaluation_victimas/comparacion_referencias_historicas.csv) y [bootstrap resumido](evaluation_victimas/bootstrap_rf_vs_referencia_resumen.csv) | Evidencia necesaria para valorar las diferencias; no acredita superioridad concluyente del RF. |
| Optimización y selección | [Búsqueda temporal](tuning_victimas/busqueda_temporal_resumen.csv), [selección de umbral](tuning_victimas/seleccion_umbral.csv) y [conclusión de 04C](tuning_victimas/conclusion_ejecutiva.md) | Configuración y umbral seleccionados con validaciones 2020–2022. |
| Modelado de referencia | [Resultados de 04B](modeling_victimas/) | Modelos base y validaciones temporales; el alias `pipeline_modelo_seleccionado.pkl` corresponde al RF base. |
| Comprensión y preparación | [Conclusión del EDA](eda_victimas/conclusion_ejecutiva.md), [tablas y figuras del EDA](eda_victimas/) y [calidad de datos](data_quality/) | Cobertura, distribuciones, análisis espacial y controles de preparación. |
| Cierre del modelo | [Ficha técnica](modelo_principal/ficha_tecnica_modelo.md) y [verificación conservada](modelo_principal/verificacion_cierre.json) | Contrato académico y evidencia de la comprobación realizada. |

La [validación temporal adicional sobre 2022](validacion_independiente_victimas/conclusion_ejecutiva.md)
es evidencia complementaria. No reemplaza el modelo principal ni constituye
una prueba prospectiva con datos nunca observados.

## Notebooks del escenario principal

Los originales se conservan en [notebooks/](../notebooks/). Para seguir el
desarrollo del escenario con víctimas:

1. [02B — EDA y análisis espacial](../notebooks/02B_EDA_y_Analisis_Espacial_Con_Victimas.ipynb).
2. [03B — Preparación](../notebooks/03B_Preparacion_Datos_Con_Victimas.ipynb).
3. [04B — Modelado base](../notebooks/04B_Modelado_Con_Victimas.ipynb).
4. [04C — Ajuste de hiperparámetros](../notebooks/04C_Ajuste_Hiperparametros_Con_Victimas.ipynb).
5. [05B — Evaluación](../notebooks/05B_Evaluacion_Con_Victimas.ipynb).

Los notebooks 01 y 02 aportan el contexto del negocio y de los datos.
Los originales 03, 04 y 05 del escenario con todos los siniestros se conservan
como legado, identificado en sus portadas y en el [catálogo](../legacy/README.md).

Para consultar salidas de una reconstrucción ya realizada, use las
[copias ejecutadas de octubre](reproducibilidad/flujo_completo_20261001_02/notebooks/)
y su [informe](reproducibilidad/flujo_completo_20261001_02/INFORME.md).
Para una ejecución nueva, siga la [guía de reproducción aislada](reproducibilidad/README.md).
Reejecutar 04C sobre el cierre oficial puede sobrescribir su pipeline.

## Evidencias históricas

Estos documentos conservan observaciones y resultados de su fecha. Sus
diagnósticos o pendientes deben interpretarse junto con la documentación vigente.

| Evidencia | Contenido |
|---|---|
| [Auditoría técnica conservada](auditoria_proyecto/AUDITORIA_TECNICA_2026-10-02.md) | Revisión del 2 de octubre de 2026. Las auditorías anteriores quedaron en el respaldo externo de la limpieza. |
| [Cierre técnico del 26 de septiembre](cierre_tecnico/INFORME_20260926.md) | Verificaciones, integridad y notebook ejecutado conservados en [cierre_tecnico/](cierre_tecnico/). |
| [Correcciones y aclaraciones](correcciones/) | Evidencias de las revisiones del entorno, especificación, etiquetas y notebooks. |
| [Cierre de pendientes del 2 de octubre](cierre_pendientes/CIERRE_PENDIENTES_2026-10-02.md) | Informe y comprobaciones de integración y dashboard de esa revisión. |
| [Ejecuciones de reproducibilidad](reproducibilidad/README.md) | Ensayos completados e intento fallido, con estados, procedencia, salidas y entornos registrados. |
| [Entrega del dashboard del 1 de octubre](dashboard/ENTREGA_20261001.md) | Verificaciones y capturas de esa entrega. Para uso actual, consulte la [guía del dashboard](../dashboard/README.md). |
| [Evaluación del escenario original](evaluation/) | Resultados históricos con todos los siniestros; su alcance se distingue del escenario principal con víctimas. |

Las referencias a archivos de trabajo dentro de informes históricos describen
el estado de cada ensayo. Sus copias de código, reportes reconstruidos, kernels
y registros de instalación se retiraron del paquete de entrega el 11 de noviembre
de 2026 y se conservaron en un respaldo externo. Los resultados y los notebooks ejecutados de septiembre y del flujo integral
del 1 de octubre permanecen en sus rutas. Las cinco copias del ensayo del 2 de
octubre se archivaron externamente en una segunda depuración: repiten las celdas
de código del flujo integral conservado. También se archivaron dos comprobaciones
intermedias de especificación e interpretación y una captura auxiliar sin
consumidores; se conservan el cierre posterior y la revisión visual integral.
Los manifiestos históricos mantienen sus hashes originales, incluso para los
archivos archivados; consultarlos no equivale a recomprobar el estado antiguo.

## Reproducibilidad y dashboard

- [Guía de reproducción y mapa de ensayos](reproducibilidad/README.md): distingue consulta de evidencias, comparación y reconstrucción con entrenamiento.
- [Procedencia de entornos y modelos](../docs/PROCEDENCIA_ENTORNOS_MODELOS.md): diferencia las versiones declaradas en los metadatos y las observadas en los ensayos.
- [Pruebas automatizadas](../tests/) y [comando de verificación](../scripts/verificar_codigo.py): alcance explicado en el [README principal](../README.md#verificación-del-código-sin-reentrenar).
- [Guía del dashboard](../dashboard/README.md), [agregados descriptivos](../data/dashboard/) y [manifiesto](../data/dashboard/manifest.json): la aplicación también consume los reportes de `evaluation_victimas/`; esos CSV forman parte de sus entradas.

La guía de reproducibilidad distingue la evidencia conservada de los componentes
retirados. Para recomparar una ejecución antigua hay que restaurar sus archivos
desde el respaldo; una ejecución nueva reconstruye sus propias salidas.
