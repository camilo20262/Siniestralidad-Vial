# Artefactos del escenario con víctimas

La [especificación vigente ESP-MODELO-01](../../docs/ESPECIFICACION_VIGENTE.md)
formaliza la sustitución del requisito antiguo RF/0,55 por RF ajustado/0,52 para
el producto actual. Los artefactos y metadatos históricos del base no se modifican.
La [decisión DEC-UMB-01](../../docs/decisiones/umbral_modelo.md) conserva la
comparación numérica de ambos puntos de corte y el pendiente de aprobación nominal.

El modelo principal de la tesis se identifica en **[modelo_principal.json](modelo_principal.json)**. Su versión académica es `rf_victimas_bogota_v1.0`: Random Forest ajustado, umbral de score **0,52**. La [ficha técnica](../../reports/modelo_principal/ficha_tecnica_modelo.md) documenta datos, selección, resultados y límites.

| Archivo | Estado | Papel |
|---|---|---|
| `modelo_principal.json` | Vigente | Registro oficial de la versión cerrada y sus huellas de integridad |
| `pipeline_random_forest_ajustado_victimas.pkl` | **Vigente** | Pipeline principal: preprocesamiento y Random Forest ajustado por 04C |
| `metadata_random_forest_ajustado.json` | Vigente / procedencia | Salida original de entrenamiento de 04C; conserva la procedencia |
| `umbrales_etiqueta_principal.csv` | Vigente / datos | 80 umbrales históricos del conteo para construir la etiqueta; no son el punto de corte del score |
| `pipeline_random_forest_victimas.pkl` | Histórico | Referencia base de 04B: 200 árboles, profundidad 12 y umbral 0,55 |
| `metadata_modelo.json` | Histórico | Metadatos de 04B; su selección y umbral corresponden al modelo base |
| `pipeline_modelo_seleccionado.pkl` | Histórico | Alias del modelo base de 04B; no identifica la versión principal actual |
| `pipeline_logistica_victimas.pkl`, `pipeline_xgboost_victimas.pkl` | Histórico | Modelos comparativos de 04B |
| `modelo_*.pkl`, `preprocesador_*.pkl` | Histórico | Componentes separados del entrenamiento original de 04B |

Para nuevas integraciones, importar `cargar_modelo_principal` desde `src.modelo_principal` y usar `modelo.predecir(datos_preparados)`. Devuelve `Score_Priorizacion` y `Alerta_Modelo`; la alerta aplica el umbral registrado 0,52. No combine el clasificador ajustado con otro preprocesador ni use el alias histórico para cargar el principal.

El cierre conserva los modelos base y sus metadatos. La ejecución de 04B puede recrear sus archivos históricos; no cambia el registro principal. La ejecución de 04C puede reemplazar el pipeline ajustado: si cambia su huella, se debe repetir la evaluación y versionar expresamente el cierre. Verificar desde la raíz con `.venv/bin/python scripts/verificar_modelo_principal.py`.

## Entornos históricos y reproducción

`metadata_modelo.json` declara Python **3.14.5** para el base de 04B. El modelo
ajustado y la reproducción aislada registran **3.12.14**, versión fijada para el
proyecto actual. No se debe editar el metadato histórico para igualarlo al entorno
actual: forma parte de las evidencias congeladas del cierre. La
[nota de procedencia](../../docs/PROCEDENCIA_ENTORNOS_MODELOS.md) distingue la
declaración histórica de la ejecución comprobada y documenta sus limitaciones.
