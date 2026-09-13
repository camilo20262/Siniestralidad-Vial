# Artefactos del escenario con víctimas

El modelo principal de la tesis se identifica en **[modelo_principal.json](modelo_principal.json)**. Su versión académica es `rf_victimas_bogota_v1.0`: Random Forest ajustado, umbral de score **0,52**. La [ficha técnica](../../reports/modelo_principal/ficha_tecnica_modelo.md) documenta datos, selección, resultados y límites.

| Archivo | Papel |
|---|---|
| `modelo_principal.json` | Registro oficial de la versión cerrada y sus huellas de integridad |
| `pipeline_random_forest_ajustado_victimas.pkl` | Pipeline principal: preprocesamiento y Random Forest ajustado por 04C |
| `metadata_random_forest_ajustado.json` | Salida original de entrenamiento de 04C; conserva la procedencia |
| `umbrales_etiqueta_principal.csv` | 80 umbrales históricos del conteo para construir la etiqueta; no son el punto de corte del score |
| `pipeline_random_forest_victimas.pkl` | Referencia base de 04B: 200 árboles, profundidad 12 y umbral 0,55 |
| `metadata_modelo.json` | Metadatos históricos de 04B; su selección y umbral corresponden al modelo base |
| `pipeline_modelo_seleccionado.pkl` | Alias histórico del modelo base de 04B; no identifica la versión principal actual |
| `pipeline_logistica_victimas.pkl`, `pipeline_xgboost_victimas.pkl` | Modelos comparativos de 04B |
| `modelo_*.pkl`, `preprocesador_*.pkl` | Componentes separados del entrenamiento original de 04B |

Para nuevas integraciones, importar `cargar_modelo_principal` desde `src.modelo_principal` y usar `modelo.predecir(datos_preparados)`. Devuelve `Score_Priorizacion` y `Alerta_Modelo`; la alerta aplica el umbral registrado 0,52. No combine el clasificador ajustado con otro preprocesador ni use el alias histórico para cargar el principal.

El cierre conserva los modelos base y sus metadatos. La ejecución de 04B puede recrear sus archivos históricos; no cambia el registro principal. La ejecución de 04C puede reemplazar el pipeline ajustado: si cambia su huella, se debe repetir la evaluación y versionar expresamente el cierre. Verificar desde la raíz con `.venv/bin/python scripts/verificar_modelo_principal.py`.
