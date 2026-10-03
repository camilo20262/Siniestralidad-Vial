# Decisión de umbral del modelo principal

**Registro:** DEC-UMB-01\
**Fecha:** 2 de octubre de 2026\
**Estado técnico:** vigente en el repositorio\
**Modelo:** `rf_victimas_bogota_v1.0`

## Decisión

El umbral oficial del score es **0,52** y se aplica al Random Forest ajustado
producido por 04C. El valor **0,55** pertenece exclusivamente al Random Forest
base de 04B y se conserva como resultado histórico versionado aparte. No son dos
alternativas vigentes del mismo modelo.

La autoridad ejecutable es
[`models/victimas/modelo_principal.json`](../../models/victimas/modelo_principal.json):
`Alerta_Modelo = 1` si y solo si `Score_Priorizacion >= 0.52`, sin redondear el
score antes de compararlo.

## Justificación numérica

La comparación usa el **mismo RF ajustado** y las mismas predicciones fuera de
muestra de 2020–2022 de 04C. No usa 2023–2024 para escoger el punto de corte.

| Métrica de selección 2020–2022 | Umbral 0,52 | Umbral 0,55 | Cambio 0,52 menos 0,55 |
| --- | ---: | ---: | ---: |
| F1 | 0,3577 | 0,3553 | +0,0024 |
| Precisión | 0,2491 | 0,2614 | -0,0123 |
| Recall | 0,6341 | 0,5545 | +0,0796 |
| Balanced accuracy | 0,6483 | 0,6389 | +0,0094 |
| Verdaderos positivos | 8.343 | 7.296 | +1.047 |
| Falsos negativos | 4.815 | 5.862 | -1.047 |
| Falsos positivos | 25.146 | 20.613 | +4.533 |

Average Precision (0,2647), AUC-ROC (0,7002) y Brier (0,2181) no cambian al
mover el punto de corte porque se calculan a partir del score continuo. El 0,52
maximiza F1 en la grilla evaluada y prioriza mayor cobertura a costa de más
falsas alertas. Esta elección sigue siendo académica: no incorpora costos
operativos acordados con usuarios.

Fuentes numéricas: [`seleccion_umbral.csv`](../../reports/tuning_victimas/seleccion_umbral.csv)
y [`modelo_principal.json`](../../models/victimas/modelo_principal.json).

## Aprobación y límites

- **Aprobación técnica del repositorio:** formalizada por el encargo de cierre
  del responsable del repositorio recibido el 2 de octubre de 2026.
- **TODO institucional:** consignar nombre, rol, fecha y constancia de la
  aprobación académica/institucional. Los artefactos disponibles no identifican
  a una persona autorizada para otorgarla y no se inventa esa atribución.
- No existe aprobación para operación, asignación de recursos ni despliegue
  público. Cualquier cambio de umbral exige una nueva versión evaluada.

La estimación temporal complementaria que reserva 2022 selecciona 0,54 dentro
de su propio protocolo 2020–2021. Se conserva como análisis de sensibilidad y
no reabre esta decisión ni cambia el 0,52 oficial.
