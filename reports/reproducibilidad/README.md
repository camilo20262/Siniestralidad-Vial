# Reproducción aislada de la cadena de víctimas

[Inicio del proyecto](../../README.md) · [Índice de reportes](../README.md) · [Modelo principal](../../models/victimas/modelo_principal.json)

## Consultar las evidencias existentes

Leer los informes, JSON y salidas guardadas de los notebooks no requiere ejecutar
modelos. Las carpetas siguientes conservan la evidencia de ensayos anteriores,
no copias completas listas para ejecutarse. Los [notebooks originales](../../notebooks/)
y el registro oficial permanecen separados de sus copias ejecutadas.

| Ensayo | Estado registrado | Evidencias de entrada |
|---|---|---|
| `ejecucion_20260913` | Cadena 03B → 04B → 04C → 05B equivalente | [Informe](ejecucion_20260913/INFORME.md), [resultado](ejecucion_20260913/resultado.json) y [notebooks ejecutados](ejecucion_20260913/notebooks/) |
| `flujo_completo_20261001` | Intento fallido; no acredita una reproducción completa | [Resultado y error conservados](flujo_completo_20261001/resultado.json) |
| `flujo_completo_20261001_02` | Flujo integral verificado, con revisión visual posterior | [Informe](flujo_completo_20261001_02/INFORME.md), [resultado](flujo_completo_20261001_02/resultado.json), [notebooks ejecutados](flujo_completo_20261001_02/notebooks/) y [revisión visual](flujo_completo_20261001_02/revision_visual/resultado.json) |
| `flujo_completo_20261002_cierre_pendientes` | Flujo integral verificado | [Resultado](flujo_completo_20261002_cierre_pendientes/resultado.json) y [registro de celdas](flujo_completo_20261002_cierre_pendientes/ejecuciones_notebooks.json); sus copias de notebooks están en el respaldo externo |

La ejecución [ejecucion_20260913](ejecucion_20260913/INFORME.md) reconstruyó y
comparó 03B → 04B → 04C → 05B en un entorno virtual nuevo, partiendo del Excel.
Los ensayos conservan sus resultados y evidencias disponibles; el intento fallido
se identifica expresamente en la tabla. Las copias de datos, modelos binarios y
entornos virtuales de esos ensayos se retiraron del proyecto durante la limpieza
del 9 de noviembre de 2026. Los notebooks y artefactos oficiales no se modificaron.

La [nota de procedencia de entornos](../../docs/PROCEDENCIA_ENTORNOS_MODELOS.md)
aclara por qué el metadato base declara Python 3.14.5 mientras este ensayo y el
modelo ajustado registran 3.12.14. Los campos `python_oficial` del resultado leen
los metadatos conservados; no verifican independientemente el intérprete original.
El registro de ejecución del ensayo es `entorno.json`. No se reescribe la evidencia
histórica para hacer coincidir versiones.

## Repetir la prueba

### Recorrido integral con EDA y dashboard

**Ensayo completado:** [flujo_completo_20261001_02/INFORME.md](flujo_completo_20261001_02/INFORME.md).
66 celdas ejecutadas sin errores, 24 tablas EDA y 14 de modelado/evaluación
equivalentes; dashboard reconstruido, HTTP real y revisión visual registrada.
Ejecución automática del 1 de octubre; revisión visual del 2 de octubre de 2026.

Desde la raíz, con Python 3.12.14 y las dependencias instaladas:

```sh
.venv/bin/python scripts/verificar_flujo_completo.py
```

Este comando **sí reentrena, pero únicamente en una copia aislada nueva**. Ejecuta
02B → 03B → 04B → 04C → 05B, reconstruye los agregados descriptivos del dashboard
y comprueba su funcionamiento con las salidas reconstruidas. No modifica ni
promueve el modelo oficial. `--run-name nombre_nuevo` permite identificar el
ensayo; una carpeta existente se rechaza, no se reutiliza.

Entradas: Excel original, su ficha de procedencia y la instantánea local de
cartografía con su hash. No descarga nuevos polígonos ni precarga datasets,
modelos, agregados o reportes oficiales como resultados del ensayo. La instalación
del entorno virtual nuevo sí puede requerir Internet. Conserva commit, estado de
trabajo, hashes del código copiado, versiones y salidas de los cinco notebooks.

Comprobaciones adicionales respecto a la cadena 03B–05B:

- Igualdad de las tablas EDA y controles; generación de sus figuras y conclusión.
- Dataset exacto y equivalencia de las 14 tablas de modelado/evaluación.
- Agregados por actor reconstruidos y contrastados con el EDA y la copia oficial.
- Cinco secciones, mapa, métricas y filtros mediante el verificador del dashboard.
- Arranque real de un servidor en **127.0.0.1 con puerto temporal**: salud, activos,
  cinco páginas, consultas, rechazo de una fecha futura, filtros y cuatro descargas.
  El proceso temporal se detiene al terminar; no interviene el puerto 8050 del usuario.
- Huellas de archivos oficiales antes/después; una diferencia o fallo devuelve
  un estado de error y conserva la evidencia, sin intentar reparar el cierre.

`resultado.json` reúne el recorrido; `comparacion_eda.json`,
`verificacion_dashboard.json` y `verificacion_http.json` detallan cada control.
La prueba HTTP ejercita callbacks reales pero **no ejecuta JavaScript ni acredita
el diseño visual o la usabilidad**. La revisión en navegador del mismo ensayo se
debe registrar aparte; tampoco equivale a aceptación por usuarios o despliegue.

Las mediciones de tiempo son locales y no constituyen una prueba de carga.

### Cadena de modelado sin EDA ni dashboard

Desde la raíz del proyecto, con las dependencias de `requirements-dev.txt`
instaladas en el entorno que inicia el proceso:

```sh
.venv/bin/python scripts/reproducir_cadena_aislada.py
```

El script crea una carpeta con fecha y hora dentro de `reports/reproducibilidad`.
Opcionalmente puede usarse `--run-name nombre_nuevo`. Rechaza carpetas existentes.
Se necesita espacio para una copia del Excel, los modelos, resultados y un
entorno virtual independiente. La instalación puede requerir acceso a Internet.

Dentro del ensayo se copian únicamente el Excel, el código y los requisitos.
Los datos procesados, modelos y reportes se reconstruyen; no se precargan las
salidas oficiales. Los cuatro notebooks mantienen su código original. 05B
requiere un registro del modelo: el script crea un contrato local con los hashes,
parámetros y resultados recién obtenidos, marcado como ensayo no oficial.

La comparación final lee los artefactos oficiales por separado. Exige identidad
exacta del dataset, coincidencia de selección y parámetros, y equivalencia de
14 tablas con tolerancia absoluta prefijada de `1e-10`, sin tolerancia relativa.
Las diferencias binarias entre archivos de modelos no implican por sí mismas
diferencias predictivas. `NaN` en el parámetro `missing` de XGBoost se compara
como el mismo valor especial, no como un cambio de configuración.

Para solicitar solamente la comparación de una ejecución de la cadena de cuatro
notebooks, primero restaure desde los respaldos externos sus carpetas `data/`,
`models/` y `reports/` en las rutas originales del ensayo. Las copias de datos y
binarios se retiraron el 9 de noviembre; los metadatos locales y reportes
reconstruidos se retiraron el 11 de noviembre de 2026. La comparación necesita
además las dependencias del ensayo y un cierre oficial compatible; no basta con
los informes conservados.
Una vez restauradas esas entradas, el comando es:

```sh
.venv/bin/python scripts/reproducir_cadena_aislada.py --run-name ejecucion_20260913 --compare-only
```

Esta opción comprueba los hashes de los notebooks ejecutados, conserva una copia
del resultado anterior y recalcula las comparaciones sin volver a entrenar.
Lee los reportes, metadatos y cuatro pipelines del ensayo, y deserializa los
pipelines usando el entorno que inicia el comando (`.venv/` de la raíz en el
ejemplo). No utiliza el `.venv/` histórico del ensayo. Escribe un nuevo
`resultado.json` y `estado.json`: no es una consulta de solo lectura.

**Límite de la comparación histórica:** la comprobación final contrasta archivos
oficiales con `integridad_oficial_antes.json` del ensayo. El cierre ha evolucionado
desde septiembre: en la revisión del 13 de octubre se encontraron 12 diferencias
de huella ya existentes antes de la limpieza documental. Por ello, el ejemplo
puede terminar con `error_integridad_oficial` aunque no se reentrene ni se
modifiquen modelos. La limpieza autorizada de temporales retiró además
`data/.DS_Store`, `data/processed/.DS_Store` y `reports/.DS_Store`, que ese
manifiesto también registra: ahora son 15 discrepancias en total, tres de ellas
por temporales respaldados. Una comparación literal del estado antiguo requiere
restaurar también esos archivos desde el respaldo, dentro de una copia de trabajo
histórica; los manifiestos originales se conservan intactos.

Para revisar el resultado histórico, consulte el JSON
conservado; para reconstruir la versión actual, use una carpeta nueva. No altere
el manifiesto histórico para hacer pasar esta comprobación. La opción exige la
lista exacta de cuatro notebooks; no admite los ensayos integrales de cinco.

## Evidencias conservadas

- `notebooks/`: cuatro copias ejecutadas de septiembre y cinco del flujo integral `flujo_completo_20261001_02`, con sus salidas. Las cinco copias del ensayo del 2 de octubre se archivaron fuera del proyecto; sus celdas de código coinciden con las del flujo integral conservado.
- `resultado.json`, comparaciones y verificaciones JSON: resultados, controles y estado de cada ejecución.
- `ejecuciones_notebooks.json`: celdas ejecutadas, tiempos y hashes.
- `procedencia.json`, `integridad_oficial_antes.json`: origen y huellas iniciales.
- `entorno.json`, `dependencias_congeladas.txt`, requisitos y versión de Python: plataforma y dependencias históricas.
- Informes, adaptación del registro y revisión visual: interpretación y evidencia del ensayo, sin promover sus artefactos al cierre oficial.

El 11 de noviembre de 2026 se retiraron las copias de `dashboard/`, `src/`,
`scripts/`, `reports/`, los metadatos de `models/`, `runtime/` y los archivos
`.log` de estos ensayos. Eran archivos de trabajo históricos, no entradas del
dashboard vigente. Todos quedaron respaldados fuera del proyecto. Los datos,
modelos binarios y entornos virtuales de ensayo ya se habían retirado a un
respaldo anterior. Los artefactos oficiales permanecen en las carpetas de la raíz.

Los informes describen lo ocurrido en la fecha del ensayo. Sus menciones a
archivos retirados no indican que esas copias sigan disponibles en este paquete.
Los resultados y huellas permanecen sin reescribirlos. Las copias ejecutadas
conservadas en el proyecto y las archivadas externamente mantienen su contenido
original; el registro de cada ejecución permite distinguir sus fechas y salidas.

## Consultar, reproducir y recomparar

| Operación | Requisitos |
|---|---|
| Leer los resultados históricos | Informes, JSON y notebooks ejecutados conservados; no necesita cargar modelos. |
| Reconstruir la versión actual | Scripts de la raíz, fuente y cartografía originales, dependencias actuales y una carpeta de ensayo nueva. |
| Recomprobar un ensayo antiguo con `--compare-only` | Restaurar sus datos, modelos, metadatos y reportes desde los respaldos, junto con un entorno y cierre oficial compatibles. |

Las pruebas del catálogo leen `ejecucion_20260913/resultado.json` y
`entorno.json` en sus rutas actuales. Estas evidencias se conservan, al igual
que los notebooks ejecutados de octubre citados desde los originales.

Para reconstruir un entorno histórico hacen falta la versión de Python y la
plataforma registradas, las dependencias congeladas y paquetes todavía
disponibles. Instalar únicamente los requisitos actuales no acredita una réplica
del entorno anterior ni garantiza modelos binariamente idénticos.

Una reproducción exitosa acredita la reconstrucción de los resultados actuales;
no constituye una nueva evaluación sobre datos nunca observados ni elimina las
limitaciones metodológicas o de calibración documentadas.

## Segunda depuración del 11 de noviembre de 2026

Se archivaron externamente las cinco copias de notebooks del ensayo del 2 de
octubre. No se necesitan para abrir ni ejecutar el dashboard, y repiten el código
de los cinco notebooks ejecutados del 1 de octubre que enlazan las portadas
oficiales. Los JSON de ambos ensayos, sus tiempos, hashes, entornos y resultados
se mantienen; una ejecución no se presenta como evidencia de la otra.

Se retiraron también dos reglas de exclusión de las copias de trabajo eliminadas
y los requisitos y versión de Python del intento fallido. Su diagnóstico, estado
y manifiesto de integridad siguen disponibles. Para restaurar exactamente un
ensayo histórico se necesitan también los archivos del respaldo externo.
