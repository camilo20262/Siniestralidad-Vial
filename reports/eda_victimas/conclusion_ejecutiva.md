# Conclusión ejecutiva — actividad 3.1

Se analizaron 85,199 siniestros con víctimas del indicador tradicional, en 2.557 días de 2018–2024.
Se mantuvo intacto el dataset del modelo. Las observaciones son siniestros registrados, no personas ni tasas de riesgo individual.

## Patrones temporales

La combinación de mayor promedio diario es Martes–Mañana: 12.19 siniestros por día de ese tipo.
La serie mensual utiliza días calendario como denominador. En 2020 el promedio diario equivale a
0.686 veces el de 2018–2019.
La sensibilidad sin 2020 muestra cuánto influye ese año en la comparación de periodos; no estima un efecto causal.

En festivos, el cociente de siniestros observados frente a los esperados según días no festivos del mismo año
y día de semana es 0.622. Es una comparación descriptiva ajustada por esa composición,
no por exposición al tránsito ni otras variables.

## Actores

Se exportaron cruces de participación registrada de motocicleta, peatón y bicicleta por día, franja y localidad.
Las categorías se solapan y los campos vacíos no son ausencias confirmadas.
También se cruzó la hoja Actor_vial: 203,548 registros asociados,
separando registros de actores de siniestros distintos. Su integridad se informa en una tabla específica.

## Territorio y coordenadas

KENNEDY concentra 11,879 siniestros (13.94%).
La cobertura de coordenadas completas es 91.00% en 2018 y
100.00% en 2024.
Se usaron veinte polígonos oficiales de referencia SDP/Catastro. Hay
9 puntos dentro del distrito pero fuera del antiguo rectángulo urbano;
no se excluyen por ese rectángulo.
Se identifican 18 puntos fuera del distrito de referencia y
5782 dentro del distrito cuya localidad declarada no coincide con el polígono.
Se exportan para revisión; no se corrigen automáticamente ni se reasignan registros.
La cartografía actual no certifica los límites históricos ni elimina la incertidumbre de geocodificación.

Se corrigió Fallecidos por Siniestros_Con_Muertos. Los centros son medianas de eventos, no centroides administrativos.
Las concentraciones puntuales usan celdas de 100 × 100 m en EPSG:9377 y mapas con escala de conteo explícita.
El mapa administrativo usa los conteos por localidad declarada, no scores del modelo.

## Alcance

El cambio de indicador tradicional a treinta días modifica la pertenencia de
98 registros.
La definición del modelo se conserva. No se demuestra cobertura perfecta, causalidad,
riesgo por persona ni eficacia de intervenciones. Las diferencias por exposición requieren denominadores adicionales.

Fuente cartográfica: https://sig.catastrobogota.gov.co/arcgis/rest/services/ordenamientoterritorial/localidad/MapServer/0
Instantánea y procedencia: data/reference/localidades_sdp_referencia_metadata.json.
