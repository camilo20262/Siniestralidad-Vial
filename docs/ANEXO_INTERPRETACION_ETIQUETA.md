# Anexo — interpretación de la etiqueta en ambos escenarios

**Fecha de comprobación:** 1 de octubre de 2026. **Alcance:** documentación y
recálculo de solo lectura de los datasets congelados; sin reentrenamiento ni
modificación de etiquetas, modelos o resultados.

## Regla y periodo de cálculo

La unidad es **localidad × fecha × franja horaria**. La etiqueta se construye
comparando el conteo de siniestros de esa unidad con el cuantil **2/3** del
conteo de su grupo localidad–franja, calculado únicamente con entrenamiento:

`Alto_Riesgo = 1 si Num_Accidentes > Umbral_Etiqueta; 0 en otro caso.`

El cuantil utilizado es 2/3 (aproximadamente 66,67 %), no exactamente 0,66. La
comparación es estricta: igualar el umbral no produce una etiqueta positiva.
El entrenamiento final abarca 2018–2022: 146.080 observaciones, 20 localidades
y cuatro franjas. Los días sin eventos registrados también forman parte del
calendario y del cálculo del cuantil.

En los cortes de validación temporal se recalcula el umbral con el pasado de
cada corte. Los conteos de grupos de este anexo corresponden al entrenamiento
final 2018–2022, no necesariamente a cada corte interno.

## Distribución comprobada de los umbrales

| Umbral del conteo | Escenario original: todos los siniestros | Escenario principal: con víctimas | Etiqueta positiva cuando hay… |
| ---: | ---: | ---: | --- |
| 0 | **19** | **49** | Al menos 1 siniestro del universo correspondiente |
| 1 | 34 | 28 | 2 o más siniestros |
| 2 | 14 | 3 | 3 o más siniestros |
| 3 | 10 | 0 | 4 o más siniestros |
| 4 | 3 | 0 | 5 o más siniestros |
| **Total de grupos** | **80** | **80** | |

En el escenario original, **19/80 = 23,75 %** de los grupos tienen umbral cero.
En el escenario principal, **49/80 = 61,25 %** lo tienen. Son porcentajes de
**grupos localidad–franja**, no porcentajes de siniestros, personas, etiquetas
positivas ni alertas acertadas.

El escenario original incluye solo daños, heridos y fallecidos registrados.
El principal conserva únicamente las categorías Con Heridos y Con Muertos.
Una unidad positiva puede, por tanto, tener significado distinto entre ambos
escenarios aunque las columnas compartan el nombre `Alto_Riesgo`.

## Los 19 grupos con umbral cero del escenario original

| Localidad | Franjas con umbral cero | Número de grupos |
| --- | --- | ---: |
| Antonio Nariño | Madrugada | 1 |
| Barrios Unidos | Madrugada | 1 |
| Candelaria | Madrugada, Mañana, Tarde y Noche | 4 |
| Chapinero | Madrugada | 1 |
| Ciudad Bolívar | Madrugada | 1 |
| Los Mártires | Madrugada | 1 |
| Rafael Uribe Uribe | Madrugada | 1 |
| San Cristóbal | Madrugada | 1 |
| Santa Fe | Madrugada | 1 |
| Sumapaz | Madrugada, Mañana, Tarde y Noche | 4 |
| Teusaquillo | Madrugada | 1 |
| Tunjuelito | Madrugada | 1 |
| Usme | Madrugada | 1 |
| **Total** | **13 localidades; no las 20 completas** | **19** |

Por franja, son 13 grupos en Madrugada y dos en cada una de las otras franjas.
La lista se refiere al escenario original, no al universo actual del dashboard.

## Qué significa y qué no significa

Cuando el cuantil es cero, `Num_Accidentes > 0` equivale a **ocurrió al menos
un siniestro registrado** en ese día, localidad y franja. La tarea en esos
grupos es de ocurrencia; no debe presentarse como detección de una frecuencia
excepcional. Esto ya sucedía en 19 grupos del escenario original, no únicamente
en el escenario con víctimas.

Cuando el umbral es mayor que cero se exige un conteo superior al cuantil
histórico del grupo. Superar ese cuantil tampoco prueba que el caso sea un
valor atípico extremo. La etiqueta combina criterios de ocurrencia y frecuencia
según el grupo; no corresponde a una misma cantidad absoluta en toda Bogotá.

Ejemplos del escenario original:

- Umbral 0: conteo 0 → etiqueta 0; conteo 1 → etiqueta 1.
- Umbral 2: conteo 2 → etiqueta 0; conteo 3 → etiqueta 1.

La etiqueta no mide riesgo individual, gravedad personal ni tasas ajustadas
por exposición al tránsito. Una celda con cero registros tampoco demuestra
ausencia real de eventos. El cambio de universo y de cobertura del escenario
total limita la comparación directa de sus métricas con las del principal.

## Separación frente al umbral del modelo

Los valores 0, 1, 2, 3 y 4 anteriores son **umbrales de conteo para construir
la etiqueta observada**. No son puntuaciones ni probabilidades.

El **umbral de score 0,52** del RF ajustado principal determina si el modelo
emite una alerta: `Score_Priorizacion >= 0.52`. El 0,55 corresponde al RF base.
Ninguno sustituye el cuantil del conteo. Véase la
[especificación vigente](ESPECIFICACION_VIGENTE.md).

## Evidencia y reproducción de la comprobación

Se recalcularon los 80 umbrales de cada escenario y se reconstruyeron sus
etiquetas sobre las 204.560 filas de 2018–2024. Resultado: **cero diferencias
en cada dataset**. Las fuentes y sus huellas quedan en el
[registro de comprobación](../reports/correcciones/verificacion_umbrales_cero_20261001.json).

Para repetir la comprobación, ejecutar desde la raíz del repositorio con el
entorno del proyecto. Este código solo lee y muestra resultados:

```python
from pathlib import Path
import pandas as pd

for archivo in (
    'dataset_localidad_franja_fecha.parquet',
    'dataset_victimas_localidad_franja_fecha.parquet',
):
    datos = pd.read_parquet(Path('data/processed') / archivo)
    grupos = ['Localidad', 'Franja_Horaria']
    train = datos.loc[datos.Periodo.eq('train')]
    umbrales = train.groupby(grupos).Num_Accidentes.quantile(2 / 3)
    revision = datos.join(umbrales.rename('Umbral_Etiqueta'), on=grupos)
    assert revision.Umbral_Etiqueta.notna().all()
    etiqueta = revision.Num_Accidentes.gt(revision.Umbral_Etiqueta).astype(int)
    assert etiqueta.eq(revision.Alto_Riesgo).all()
    print(archivo)
    print(umbrales.value_counts().sort_index())
    print(umbrales.loc[umbrales.eq(0)])
```

Las salidas originales de 03, 04 y 05 se conservan como evidencia histórica.
Este anexo aclara su interpretación; no convierte el escenario total en el
principal ni recupera la validez de la validación aleatoria anulada de 04.
