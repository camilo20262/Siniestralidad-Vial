# Procedencia de los entornos de modelos

Fecha de aclaración: 1 de octubre de 2026.

## Qué significa la discrepancia

**Python 3.14.5 corresponde a la declaración histórica del modelo base de 04B;
Python 3.12.14 es el entorno registrado del modelo ajustado y de la reproducción
aislada.** No son dos requisitos simultáneos para ejecutar el producto actual.
La versión fijada para reproducir el proyecto es **3.12.14**, según
[.python-version](../.python-version).

| Evidencia | Python | Alcance de la evidencia |
| --- | --- | --- |
| [Metadatos base de 04B](../models/victimas/metadata_modelo.json) | 3.14.5 | Declaración histórica asociada al RF base, umbral 0,55; no es la configuración del principal |
| [Metadatos ajustados de 04C](../models/victimas/metadata_random_forest_ajustado.json) | 3.12.14 | Declaración del entrenamiento del RF ajustado, umbral 0,52 |
| [Registro principal](../models/victimas/modelo_principal.json), sección `versiones` | 3.12.14 | Versiones declaradas del entrenamiento y del entorno de verificación del cierre |
| [Entorno del ensayo del 13 de septiembre](../reports/reproducibilidad/ejecucion_20260913/entorno.json) | 3.12.14 | Registro de la ejecución aislada: versión completa, ejecutable, plataforma, paquetes y comprobación de dependencias |
| [Comparación del ensayo](../reports/reproducibilidad/ejecucion_20260913/resultado.json), sección `seleccion` | Base: 3.14.5 → 3.12.14; ajustado: 3.12.14 → 3.12.14 | Contraste entre metadatos oficiales conservados y metadatos reconstruidos |

04B genera el campo `version_python` mediante `platform.python_version()`.
Sin embargo, el valor del archivo histórico no constituye por sí solo una
verificación independiente del entorno que produjo los modelos originales.
No se dispone aquí de una captura equivalente a `entorno.json` que permita
certificar retrospectivamente ese entorno original de 04B. No se afirma que
3.14.5 sea un error tipográfico ni se inventa una fecha o motivo de migración.

En el comparador, `python_oficial` significa **versión leída de los metadatos
oficiales**, no versión del intérprete que está ejecutando la comprobación.
`python_reproduccion` se obtiene de los metadatos generados en el ensayo; el
archivo `entorno.json` aporta el registro adicional de su intérprete.

## Qué se pudo reproducir

El [informe del ensayo](../reports/reproducibilidad/ejecucion_20260913/INFORME.md)
documenta la cadena 03B → 04B → 04C → 05B en un entorno nuevo con Python 3.12.14:

- Dataset idéntico: 204.560 filas y 16 columnas.
- Misma selección base y ajustada, variables, hiperparámetros y umbrales.
- 14 tablas equivalentes, con tolerancia absoluta `1e-10` y relativa cero.
- Las 58.480 decisiones finales coinciden; diferencia máxima de score
  `4,440892098500626e-16`.
- Los tres pipelines base no coinciden en bytes; el pipeline ajustado sí.
  Equivalencia de resultados no significa identidad de todos los archivos.

Esta evidencia corresponde al ensayo conservado del **13 de septiembre**;
la presente aclaración no es un nuevo entrenamiento ni una nueva ejecución
integral de los notebooks. Acredita esa reproducción concreta, no compatibilidad
general entre versiones de Python, plataformas o dependencias. Tampoco explica
por sí sola las diferencias de desempeño entre el modelo base y el ajustado.

## Decisión de conservación y uso

1. Mantener sin editar `metadata_modelo.json`, los modelos, los resultados del
   ensayo y `modelo_principal.json`. El metadato base participa en las huellas de
   integridad del cierre; cambiar su versión borraría procedencia histórica.
2. Para nuevas ejecuciones, usar Python 3.12.14 y las dependencias del proyecto.
   La lista histórica de paquetes del ensayo está en
   [dependencias_congeladas.txt](../reports/reproducibilidad/ejecucion_20260913/dependencias_congeladas.txt).
   Consultar las [instrucciones de reproducción aislada](../reports/reproducibilidad/README.md)
   antes de entrenar, para no sobrescribir el cierre oficial.
3. Para el producto, cargar el RF ajustado mediante el registro principal:
   `rf_victimas_bogota_v1.0`, umbral 0,52. El RF base/0,55 sigue siendo referencia.
4. En futuros ensayos, conservar el registro del intérprete y sus dependencias
   junto con los resultados; no sustituir evidencias antiguas por las nuevas.

La discrepancia queda **aclarada documentalmente**, sin certificar de manera
independiente el entorno original de 04B ni modificar resultados científicos.
