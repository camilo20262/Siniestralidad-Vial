# Reproducción aislada de la cadena de víctimas

La ejecución [ejecucion_20260913](ejecucion_20260913/INFORME.md) reconstruyó y
comparó 03B → 04B → 04C → 05B en un entorno virtual nuevo, partiendo del Excel.
Las cuatro copias conservan sus salidas; los notebooks y artefactos oficiales
no se sobrescribieron.

## Repetir la prueba

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
