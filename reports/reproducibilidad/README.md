# Reproducción aislada de la cadena de víctimas

La ejecución [ejecucion_20260913](ejecucion_20260913/INFORME.md) reconstruyó y
comparó 03B → 04B → 04C → 05B en un entorno virtual nuevo, partiendo del Excel.
Las cuatro copias conservan sus salidas; los notebooks y artefactos oficiales
no se sobrescribieron.

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

Desde la raíz del proyecto, con las dependencias de `requirements.txt`
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

Para repetir solamente la comparación de una ejecución completa:

```sh
.venv/bin/python scripts/reproducir_cadena_aislada.py --run-name ejecucion_20260913 --compare-only
```

Esta opción comprueba los hashes de los notebooks ejecutados, conserva una copia
del resultado anterior y recalcula las comparaciones sin volver a entrenar.

## Evidencias conservadas

- `notebooks/`: cuatro notebooks ejecutados con sus salidas.
- `reports/`: reportes y predicciones reconstruidos.
- `resultado.json`: comparaciones e integridad de los archivos oficiales.
- `comparacion_dataset.json`: comprobación exacta del dataset.
- `ejecuciones_notebooks.json`: celdas ejecutadas, tiempos y hashes.
- `procedencia.json`, `integridad_oficial_antes.json`: origen y huellas iniciales.
- `entorno.json`, `dependencias_congeladas.txt`, `instalacion.log`: entorno y dependencias.
- `adaptacion_registro_local.json`: alcance del registro local usado por 05B.

Las copias de datos, modelos binarios, entorno y configuración del kernel se
conservan localmente, pero se excluyen de Git para evitar duplicados voluminosos.
No se eliminan archivos oficiales ni resultados de ejecuciones anteriores.

Una reproducción exitosa acredita la reconstrucción de los resultados actuales;
no constituye una nueva evaluación sobre datos nunca observados ni elimina las
limitaciones metodológicas o de calibración documentadas.
