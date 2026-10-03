# Cierre de pendientes reales del repositorio

**Fecha:** 2 de octubre de 2026\
**Alcance:** escenario con víctimas, artefactos históricos, validación adicional,
procedencia y dashboard local.

## 1. Umbral 0,52 frente a 0,55

**Resultado:** implementado, con un TODO institucional que no puede resolverse
por código.

- [`docs/decisiones/umbral_modelo.md`](../../docs/decisiones/umbral_modelo.md)
  formaliza 0,52 como único umbral oficial del RF ajustado y 0,55 como umbral
  histórico del RF base.
- La comparación sobre las predicciones OOF 2020–2022 del RF ajustado da F1
  0,3577 y recall 0,6341 a 0,52, frente a F1 0,3553 y recall 0,5545 a 0,55.
- [`config/artefactos.json`](../../config/artefactos.json) asigna `vigente` o
  `historico` a cada modelo catalogado.
- Se actualizaron
  [`README.md`](../../README.md),
  [`docs/ESPECIFICACION_VIGENTE.md`](../../docs/ESPECIFICACION_VIGENTE.md),
  [`models/victimas/README.md`](../../models/victimas/README.md) y la
  [ficha técnica](../modelo_principal/ficha_tecnica_modelo.md).
- **TODO no inventado:** falta consignar nombre, rol, fecha y constancia del
  aprobador académico/institucional. El encargo formaliza la decisión técnica
  del repositorio, pero no identifica una autoridad nominal externa.

Prueba: `CatalogoTest.test_especificacion_vigente_distingue_umbral_principal_y_base`
contrasta registro, especificación, decisión y métricas fuente.

## 2. Separación vigente y legado

**Resultado:** implementado mediante portadas y catálogo, sin mover artefactos
cerrados.

- [`models/README.md`](../../models/README.md) declara que ningún `.pkl` de la
  raíz es vigente.
- [`legacy/README.md`](../../legacy/README.md) enumera notebooks, modelos y
  reportes históricos.
- 03, 04 y 05 tienen una portada `LEGADO` inequívoca. 04 conserva además la
  anulación de la validación aleatoria.
- No se trasladaron los binarios ni los notebooks porque sus rutas forman parte
  de salidas guardadas, pruebas y citas históricas. Trasladarlos rompería la
  trazabilidad y la regla de no reescribir el cierre. No cambió ningún `.pkl`.

Pruebas: `CatalogoTest.test_cada_modelo_tiene_estado_inequivoco`,
`test_portadas_de_legado_y_evidencia_ejecutada` y `ValidacionLegadoTest`.

## 3. Evidencia ejecutada de 03B y 04B

**Resultado:** implementada la opción (b).

Los notebooks oficiales permanecen sin salidas para no reentrenar ni reescribir
el cierre. Sus primeras celdas enlazan las copias ejecutadas exactas de
[`flujo_completo_20261001_02/notebooks/`](../reproducibilidad/flujo_completo_20261001_02/notebooks/):
03B registra 9/9 celdas y 04B 12/12, ambos con cero errores. El resultado de esa
ejecución registra coincidencia exacta del dataset y equivalencia de resultados.

Archivos modificados:
[`03B_Preparacion_Datos_Con_Victimas.ipynb`](../../notebooks/03B_Preparacion_Datos_Con_Victimas.ipynb)
y [`04B_Modelado_Con_Victimas.ipynb`](../../notebooks/04B_Modelado_Con_Victimas.ipynb).

## 4. EDA del escenario total

**Resultado:** no se amplió por decisión metodológica; se implementó la
alternativa documental solicitada.

02, 03, 04 y 05 explican desde la primera celda que el escenario total se
conserva como sensibilidad histórica y que no recibe un EDA equivalente debido
al cambio de cobertura de `Solo Daños`. El EDA canónico sigue siendo 02B.

## 5. Estimación temporal separada

**Resultado:** implementada y ejecutada sin cambiar el modelo oficial.

- [`src/validacion_independiente.py`](../../src/validacion_independiente.py)
  recalcula etiquetas por corte, compara las ocho configuraciones de 04C y
  garantiza que 2022 no participe en configuración ni umbral.
- [`scripts/generar_validacion_independiente.py`](../../scripts/generar_validacion_independiente.py)
  genera solo una carpeta nueva y rechaza sobrescrituras.
- La [evidencia](../validacion_independiente_victimas/conclusion_ejecutiva.md)
  selecciona el candidato 3 y umbral 0,54 con 2020–2021; al reajustar con
  2018–2021 obtiene en 2022 F1 0,4017, AP 0,3077, AUC-ROC 0,6959, recall 0,6096
  y Brier 0,2228.
- Es una separación procedimental adicional. 2022 ya había sido inspeccionado
  en el desarrollo histórico, por lo que no se presenta como prueba prospectiva
  o externa. El 0,54 experimental no sustituye el 0,52 oficial.

Pruebas nuevas: [`tests/test_validacion_independiente.py`](../../tests/test_validacion_independiente.py)
cubre la separación temporal, la etiqueta calculada solo con pasado, la selección
del umbral y el contrato de la evidencia congelada.

## 6. Procedencia y licencia

**Resultado:** pendiente institucional documentado, sin atribuir una licencia.

[`data/raw/procedencia_excel.json`](../../data/raw/procedencia_excel.json) contiene
literalmente `"licencia": "pendiente de confirmación institucional"` y conserva
el detalle de lo no verificado. README y
[`data/raw/README.md`](../../data/raw/README.md) muestran el TODO de redistribución.
[`scripts/verificar_fuente.py`](../../scripts/verificar_fuente.py) comprueba y
reporta ese estado.

## 7. Despliegue, aceptación y accesibilidad

**Resultado:** documentado como trabajo futuro, sin desplegar.

README y [`dashboard/README.md`](../../dashboard/README.md) declaran pendientes
el despliegue WSGI/HTTPS, aceptación formal con usuarios, pruebas de carga,
telemetría y auditoría exhaustiva de accesibilidad.

## Auditoría final ejecutada

| Comprobación | Resultado | Evidencia |
| --- | --- | --- |
| `python -m unittest discover -s tests -v` | Correcto: 77 pruebas en la corrida previa al informe; 0 fallos, 0 errores | Salida de consola; la corrida final posterior al informe vuelve a fijar el total |
| `scripts/verificar_codigo.py --integracion` | Correcto: dataset 204.560 × 16 exacto, 80 umbrales, 58.480 decisiones, 12 evidencias íntegras | [`verificacion_integracion_20261002.json`](verificacion_integracion_20261002.json) |
| `scripts/verificar_dashboard.py` | Correcto: cinco páginas, 20 localidades, 58.480 predicciones y conteos/metricas consistentes | [`verificacion_dashboard_20261002.json`](verificacion_dashboard_20261002.json) |
| Reconstrucción aislada | Correcto: cinco notebooks, 66 celdas, cero errores; 24 tablas EDA y 14 tablas de modelado/evaluación equivalentes; cuatro modelos con mismo esquema/parámetros | [`resultado.json`](../reproducibilidad/flujo_completo_20261002_cierre_pendientes/resultado.json) |
| Dashboard aislado por HTTP | Correcto: 23 peticiones HTTP, cinco páginas, tres consultas válidas, rechazo de futuro y cuatro descargas | [`verificacion_http.json`](../reproducibilidad/flujo_completo_20261002_cierre_pendientes/verificacion_http.json) |
| Integridad del repositorio durante la reproducción | Correcto: 265 archivos oficiales comprobados, ninguno modificado o creado por el ensayo | [`resultado.json`](../reproducibilidad/flujo_completo_20261002_cierre_pendientes/resultado.json) |

La nueva reproducción no incluyó revisión visual automatizada: el entorno de
esta sesión no expuso un navegador controlable. La comprobación HTTP/callbacks
sí fue nueva y completa; la revisión visual anterior se conserva en
[`flujo_completo_20261001_02/revision_visual/`](../reproducibilidad/flujo_completo_20261001_02/revision_visual/).
