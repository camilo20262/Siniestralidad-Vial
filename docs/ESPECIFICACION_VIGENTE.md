# Especificación vigente del modelo y sus consultas

**Identificador documental:** ESP-MODELO-01 · **Revisión:** 1 · **Fecha:** 01/10/2026.

## Decisión de alcance

El requisito vigente del prototipo es **Random Forest ajustado con umbral de
score 0,52**, identificado como `rf_victimas_bogota_v1.0`.

Esta especificación sustituye, para la aplicación y las consultas vigentes, la
formulación anterior «RF víctimas, umbral 0,55». El valor **0,55** sigue siendo
correcto exclusivamente para el **Random Forest base de referencia**. No hay
dos umbrales alternativos del modelo principal ni un selector entre ellos.

Se formaliza una decisión ya implementada y evaluada; no se selecciona un nuevo
umbral usando 2023–2024, no se reentrena y no cambia la versión del modelo.
La revisión de este documento es independiente de la versión del artefacto.

La única autoridad ejecutable para identidad, pipeline, parámetros, esquema y
umbral es el [registro oficial](../models/victimas/modelo_principal.json).
Este documento especifica su uso; no crea un archivo de configuración paralelo.

## Identidades que no deben confundirse

| Papel | Artefacto | Configuración distintiva | Umbral del score |
| --- | --- | --- | --- |
| Principal vigente | `models/victimas/pipeline_random_forest_ajustado_victimas.pkl` | 300 árboles; profundidad sin límite explícito; mínimo 20 por hoja | **0,52** |
| Referencia base de 04B | `models/victimas/pipeline_random_forest_victimas.pkl` | 200 árboles; profundidad máxima 12; mínimo 20 por hoja | **0,55** |
| Alias histórico del base | `models/victimas/pipeline_modelo_seleccionado.pkl` | No es el modelo principal, pese al nombre del archivo | **0,55**, solo en su experimento histórico |

`metadata_modelo.json` pertenece al base y conserva su umbral candidato histórico.
`metadata_random_forest_ajustado.json` conserva la salida de entrenamiento de
04C. Las representaciones decimales largas de esos metadatos no redefinen el
umbral cerrado del registro. No se reescriben para aparentar que el experimento
base utilizó 0,52.

## Requisitos de aceptación

| ID | Requisito vigente | Evidencia o control |
| --- | --- | --- |
| MOD-01 | Cargar el pipeline ajustado registrado, con su preprocesador, y verificar su integridad antes de usarlo. No cargar el alias histórico como principal. | `src/modelo_principal.py`, catálogo y pruebas de carga/integridad |
| UMB-01 | Emitir `Alerta_Modelo = 1` si y solo si `Score_Priorizacion >= 0.52`; en otro caso, emitir 0. Comparar el score sin redondearlo previamente. | Método `ModeloPrincipal.predecir`; prueba de frontera del umbral |
| UMB-02 | Mostrar 0,52 como umbral principal en consulta, dashboard y exportaciones. 0,55 solo puede aparecer identificado como comparación del modelo base. | Registro, guía del dashboard y pruebas de trazabilidad/descarga |
| ETQ-01 | Mantener separada la etiqueta observada: `Num_Accidentes > cuantil 2/3` del conteo por localidad–franja calculado con entrenamiento. No aplicar 0,52 ni 0,55 al conteo. | Preparación, 80 umbrales de etiqueta y verificador del modelo |
| ALC-01 | Consultar exclusivamente casos preparados de 2023–2024 del universo con heridos o fallecidos. El histórico descriptivo abarca 2018–2024. | Validaciones de fechas, unidad localidad × fecha × franja y filtros de la interfaz |
| INT-01 | Comunicar el score como puntuación no calibrada; no como probabilidad individual, pronóstico futuro ni recomendación operativa. | Advertencias de consulta, dashboard y exportaciones |
| TRA-01 | Conservar identificador, versión, umbral, periodo y advertencias en las salidas del modelo. El filtro descriptivo de actor no modifica el clasificador. | Pruebas de consulta y dashboard |
| HIS-01 | Preservar los modelos, umbrales y métricas históricos con sus identidades originales. No reemplazar globalmente 0,55 por 0,52 en reportes ni metadatos. | Catálogo y comparación principal/base |

La frontera principal exige alerta 0 para un score de 0,5199 y alerta 1 para
0,52 y 0,54. Este último caso permite detectar una sustitución indebida del
umbral principal por el 0,55 del modelo base.

## Fundamento y límites

04B seleccionó la familia y el punto de corte del modelo base con validación
temporal de 2020–2022. 04C ajustó ocho configuraciones RF y seleccionó el umbral
0,52 con las predicciones fuera de muestra de esos años. Las validaciones se
reutilizan para configuración y umbral: son resultados de selección, no una
estimación independiente. La evaluación de 2023–2024 es retrospectiva y el
periodo ya fue inspeccionado durante el desarrollo.

El cierre conserva RF ajustado como referencia académica. No implica superioridad
concluyente frente a la tasa histórica localidad–franja–día ni probabilidades
calibradas. Véanse la [ficha técnica](../reports/modelo_principal/ficha_tecnica_modelo.md)
y la [evaluación](../reports/evaluation_victimas/conclusion_ejecutiva.md).

## Control de cambios y verificación

Cualquier cambio real de pipeline, etiqueta, datos o umbral exige evaluación,
versionado explícito y actualización coordinada del registro y sus documentos;
no basta con editar una etiqueta en la interfaz. No se promueve el modelo base
por interpretar el requisito antiguo como vigente.

Desde la raíz del repositorio:

```sh
python scripts/verificar_codigo.py
python scripts/verificar_codigo.py --integracion
```

El segundo comando requiere los artefactos reales de Git LFS y no reentrena.
La aprobación académica externa o las correcciones del manuscrito Word no se
presuponen: esta revisión formaliza la especificación del repositorio y sus
consumidores actuales. Las auditorías anteriores se conservan como evidencia
de los hallazgos, no como configuración del modelo.
