# Verificación integral del proyecto: EDA → modelos → dashboard

Ejecución automática: **1 de octubre de 2026**. Revisión visual y cierre del
informe: **2 de octubre de 2026**.

## Resultado

**Recorrido integral verificado en una copia aislada.** Se ejecutaron los cinco
notebooks desde el Excel original y la cartografía local verificada. Después se
regeneraron los agregados del dashboard y se probó una aplicación local que
consumía los modelos, datos y reportes reconstruidos en este ensayo.

Se conservaron intactos los **248 archivos oficiales** comprobados antes y
después de la ejecución. No se promovió un modelo nuevo ni se modificó el cierre
`rf_victimas_bogota_v1.0`. La revisión visual posterior tampoco cambió esos archivos.

## Ejecución de notebooks

| Etapa | Celdas de código ejecutadas | Errores | Segundos |
| --- | ---: | ---: | ---: |
| 02B — EDA temporal, territorial y actores | 12 | 0 | 96,89 |
| 03B — Preparación | 9 | 0 | 21,03 |
| 04B — Comparación inicial de modelos | 12 | 0 | 32,44 |
| 04C — Ajuste y selección | 6 | 0 | 113,23 |
| 05B — Evaluación | 27 | 0 | 26,78 |
| **Total** | **66** | **0** | **290,37** |

Estos tiempos no incluyen instalación, preparación del dashboard, comparación
de archivos ni revisión en navegador. Las copias ejecutadas conservan sus salidas
en `notebooks/`; los notebooks oficiales no se reescribieron.

## Comparación con el cierre

- **EDA:** 24 tablas equivalentes; mismos controles y conclusión ejecutiva;
  10 figuras generadas. No se exigió identidad de píxeles entre figuras.
- **Dataset:** igualdad exacta de las 204.560 filas y 16 columnas.
- **Modelado/evaluación:** 14 tablas equivalentes, con tolerancia absoluta
  prefijada `1e-10` y relativa cero. Misma selección de familia, configuración y
  umbrales (0,55 para el base y 0,52 para el ajustado).
- **Predicciones finales:** las 58.480 etiquetas y decisiones coinciden.
  Diferencia máxima de score: `3,885780586188048e-16`.
- **Modelo principal reconstruido:** mismo esquema e hiperparámetros; su archivo
  serializado también coincide en SHA-256. No se exige identidad binaria de todos
  los modelos base para declarar equivalencia de resultados.
- **Dashboard:** agregados de participación de actores equivalentes, conteos
  consistentes con el EDA y métricas consistentes con 05B.

Se reproducen F1 **0,405789**, AUC-ROC **0,693324**, Average Precision **0,309838**
y Brier **0,222088**. No es una mejora del desempeño ni una evaluación nueva.

## Pruebas de aplicación

El verificador de datos y vistas comprobó las cinco secciones, 20 localidades,
conteos de actores y métricas. Luego se arrancó un servidor real en `127.0.0.1`
con puerto asignado por el sistema, distinto del dashboard del usuario.

La prueba HTTP completó **23 peticiones satisfactorias**, incluyendo:

- Salud del servidor, página inicial, estructura de Dash, callbacks y CSS.
- Navegación por las cinco secciones.
- Consultas para Kennedy, Candelaria y Sumapaz; rechazo de una fecha de 2025.
- Selección de localidad desde el mapa y filtros de historia/evaluación.
- Cuatro descargas: consulta JSON, 20 localidades CSV, historia mensual CSV y
  métricas CSV. Se verificó contenido y trazabilidad cuando corresponde al modelo.

El proceso temporal se detuvo al terminar. La prueba HTTP no ejecuta JavaScript;
por eso se añadió una revisión separada en el navegador integrado el 2 de octubre.
En esa revisión se recorrieron las cinco secciones, se comprobó el mapa de
Kennedy, el cambio Mañana → Madrugada, la explicación contextual de la etiqueta,
el aviso 39,43 %, la trazabilidad del ensayo, las métricas y la metodología.
No se observaron errores en los registros de consola consultados. Se conservaron
cinco capturas de ventana; las capturas de página completa se descartaron como
evidencia final por artefactos de composición del capturador.

Identificador observado en la trazabilidad y metodología:
`reproduccion_aislada_flujo_completo_20261001_02`. El texto general RF v1.0 describe
el contrato reproducido, no una promoción de este ensayo a modelo oficial.
El servidor adicional de revisión visual también se detuvo al concluir.

## Procedencia y alcance

- Código ejecutado: commit `fe9e048e0f572d3029b0e9e749d3318604f42edf`.
- Entorno nuevo: Python 3.12.14, sin `system-site-packages`; dependencias
  instaladas independientemente y `pip check` correcto.
- Se conservaron el estado de trabajo y las huellas del código copiado. El
  cambio previo del usuario en `AUDITORIA_PROYECTO.md` no se modificó ni se incluyó
  en este cierre.
- Las entradas científicas fueron el Excel y los polígonos congelados, no una
  descarga nueva. Los datos procesados, modelos y reportes usados por la cadena
  se reconstruyeron. La copia de `dashboard/` incluye su maqueta estática antigua,
  pero esta no alimenta los notebooks ni el servidor Dash verificado.
- El primer intento, `flujo_completo_20261001`, falló durante la preparación de
  la copia, antes de ejecutar notebooks. Se corrigió el ejecutor y se añadió una
  prueba de regresión; ese intento no se presenta como exitoso ni se sobrescribió.
- **70 pruebas unitarias** pasan tras la corrección del ejecutor.

Queda cubierto el pendiente técnico del recorrido integral para esta versión.
No queda acreditada aceptación por usuarios, accesibilidad exhaustiva, desempeño
bajo carga, compatibilidad con todos los navegadores ni despliegue público.
Tampoco se resuelven la licencia del Excel, la calibración del modelo o la falta
de validación prospectiva. Esas cuestiones son independientes.

## Evidencias y repetición

- [Resultado automático](resultado.json).
- [Comparación EDA](comparacion_eda.json).
- [Notebooks ejecutados](ejecuciones_notebooks.json).
- [Comprobación de datos y vistas](verificacion_dashboard.json).
- [Prueba HTTP real](verificacion_http.json).
- [Revisión visual](revision_visual/resultado.json).
- [Pruebas unitarias del cierre](verificacion_codigo_cierre.json).
- [Procedencia](procedencia.json), [entorno](entorno.json) y
  [dependencias resueltas](dependencias_congeladas.txt).

Para realizar **otro** ensayo, desde la raíz del repositorio:

```sh
.venv/bin/python scripts/verificar_flujo_completo.py
```

Se crea una carpeta nueva. No reutilice esta carpeta ni ejecute entrenamientos
directamente sobre los artefactos oficiales. La revisión visual sigue siendo un
paso separado del comando automático.
