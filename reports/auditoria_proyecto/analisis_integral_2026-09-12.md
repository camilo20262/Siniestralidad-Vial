# Análisis integral del proyecto de siniestralidad vial

Fecha de revisión: 12 de septiembre de 2026. Escenario principal: siniestros con víctimas. Modelo registrado: `rf_victimas_bogota_v1.0`.

## 1. Dictamen general

El proyecto tiene una base experimental sustancial y verificable: datos preparados, comparación temporal de modelos, ajuste de Random Forest, evaluación detallada y una versión principal documentada. Su mayor avance reciente es la coherencia entre el modelo registrado, sus predicciones y la ficha técnica. No es únicamente una colección de entrenamientos exploratorios.

Todavía no constituye un sistema predictivo integrado y terminado. La interfaz presenta fallos reproducibles, el objetivo de visualizar predicciones georreferenciadas no está implementado y falta demostrar con suficiente exigencia el valor adicional del modelo frente a una referencia histórica sencilla.

La fase 5.1 está desarrollada y ejecutada en 05B; requiere una ampliación puntual y una actualización de conclusiones, no reconstruir toda la evaluación. El cierre académico de una versión no equivale a demostrar superioridad estadística, utilidad operativa o cumplimiento de todos los objetivos de la tesis.

## 2. Alcance y evidencia de la revisión

Se inspeccionaron los diez notebooks, sus salidas guardadas, los componentes de carga y verificación, los metadatos y reportes de ambos escenarios, la preparación de datos, las dependencias y el dashboard local. Se contrastó la formulación de 01 con lo implementado. Se consultaron fuentes oficiales para verificar el cambio de registro y cifras del anuario.

Se realizaron diagnósticos de lectura: comprobación del archivo original, integridad de la cuadrícula, reconstrucción de variables históricas y calendario, reproducción de predicciones con el artefacto cerrado, referencias históricas adicionales y pruebas de interfaz. No se reentrenaron los modelos ni se ejecutaron secuencialmente todos los notebooks desde cero. No se editaron los archivos existentes como parte de esta auditoría.

La verificación del cierre terminó correctamente: 58.480 predicciones, 80 umbrales de etiqueta, 12 evidencias íntegras y cuatro casos de entradas inválidas comprobados. Las métricas coinciden con 05B. Esto verifica la versión congelada, no sustituye una prueba completa desde el Excel hasta el dashboard en un entorno limpio.

El alcance documental corresponde a los archivos del repositorio. No se certifica el estado del documento Word de tesis almacenado fuera de esta carpeta, ni se realizó una revisión exhaustiva de todas las referencias del estado del arte. Tampoco se verificó una versión pública desplegada del dashboard.

Los cálculos adicionales quedan en [diagnosticos_2026-09-12.json](diagnosticos_2026-09-12.json). Son evidencia de auditoría, no una nueva versión del modelo ni resultados incorporados automáticamente a 05B.

## 3. Qué hace realmente el proyecto

El sistema transforma registros individuales de siniestros en observaciones de localidad × franja horaria × fecha. Para cada observación calcula si el número de siniestros con víctimas supera un umbral histórico del grupo. El modelo intenta anticipar esa etiqueta a partir de calendario, ubicación y conteos anteriores.

No predice quién se accidentará, el número de personas heridas, una calle específica, la gravedad individual del próximo siniestro ni el efecto de una intervención. Tampoco calcula tasas ajustadas por población, viajes, kilómetros recorridos o flujo vehicular.

### Dos escenarios, con funciones diferentes

- El escenario original incluye todos los siniestros y conserva valor como experimento inicial y análisis del cambio de cobertura. Sus resultados no deben mezclarse con los del escenario principal.
- El escenario principal incluye `Con Heridos` y `Con Muertos` según `Gravedad_Indicador_Tradicional`. Es la base del Random Forest ajustado y de 05B.

La Secretaría Distrital de Movilidad confirma que, desde julio de 2022, los IPAT no deben ser diligenciados por las autoridades para accidentes de solo daños materiales, conforme al artículo 16 de la Ley 2251 de 2022. Esto respalda documentalmente un cambio del mecanismo de registro, no una redefinición de que esos choques sean o no siniestros. [Fuente oficial SDM](https://www.movilidadbogota.gov.co/preguntas-frecuentes/donde-se-consultan-los-reportes-oficiales-de-accidentes-de-transito-en-los-que).

La estabilidad del escenario con víctimas es evidencia favorable de mayor comparabilidad, pero no una prueba de cobertura perfecta ni de invariancia completa de la distribución. No demuestra que la norma explique cada diferencia por localidad o franja, ni que ningún modelo pudiera generalizar en el escenario anterior. Esas afirmaciones excederían la evidencia.

## 4. Datos y definición de la etiqueta

### Dimensiones comprobadas

| Elemento | Resultado |
|---|---:|
| Siniestros del Excel original, 2015–2024 | 278.614 |
| Siniestros de cualquier gravedad, 2018–2024 | 177.099 |
| Siniestros con víctimas, indicador tradicional | 85.199 |
| Filas de la cuadrícula preparada | 204.560 |
| Localidades × franjas × días | 20 × 4 × 2.557 |
| Variables predictoras | 12 |

No encontré identificadores de siniestro duplicados en la comprobación del original, discordancia entre año y fecha, horas fuera de rango, duplicados de localidad–franja–fecha ni nulos en el dataset preparado. Cada grupo tiene los 2.557 días esperados. La ausencia de nulos después de imputar no demuestra ausencia de problemas en la fuente original.

| Periodo | Observaciones | Siniestros | Etiquetas positivas | Prevalencia |
|---|---:|---:|---:|---:|
| 2018–2022 | 146.080 | 59.288 | 24.907 | 17,05 % |
| 2023–2024 | 58.480 | 25.911 | 11.118 | 19,01 % |

Estas observaciones no son 204.560 accidentes ni 204.560 casos estadísticamente independientes: comparten territorios, fechas y ventanas históricas. Incluir días sin registros es necesario para representar ausencia de siniestros registrados, pero presupone que un cero no corresponde a una interrupción de cobertura.

### Dos umbrales que no deben confundirse

El umbral de etiqueta es el cuantil 2/3 del conteo diario en entrenamiento para cada localidad–franja. Se usa una comparación estricta: conteo > umbral. El umbral de decisión del modelo es distinto: score >= 0,52.

| Umbral histórico del conteo | Grupos | Qué significa una etiqueta positiva |
|---|---:|---|
| 0 | 49 | Ocurrió al menos un siniestro con víctima |
| 1 | 28 | Ocurrieron dos o más |
| 2 | 3 | Ocurrieron tres o más |

En el 61,25 % de los grupos la tarea es detección de ocurrencia. En los otros grupos se exige superar un conteo mayor. Tampoco sería preciso decir que únicamente los tres grupos con umbral 2 conservan una condición de frecuencia elevada: los 28 grupos con umbral 1 también la exigen. Debido a los empates y ceros, un cuantil 2/3 no implica que un tercio de las filas resulte positivo.

### Variables históricas: comprobación favorable con una condición de uso

Se reconstruyeron los promedios de siete y treinta días, el conteo de siete días antes, sus indicadores de ausencia, el mes, fin de semana, día de semana y calendario de festivos. Coinciden con el dataset. Los promedios excluyen el día que se intenta predecir y el conteo contemporáneo no entra al modelo.

Esto permite una evaluación retrospectiva de un paso adelante bajo la hipótesis de que los conteos anteriores ya están disponibles. No demuestra que los datos oficiales lleguen diariamente con esa oportunidad. Pronosticar una semana completa sin actualizar históricos sería otro problema y no está evaluado.

### Gravedad tradicional y a treinta días no son intercambiables

El archivo también contiene `Gravedad_indicador_30d`. Su filtro de víctimas produce 85.143 registros frente a los 85.199 del indicador tradicional: al cambiar el filtro salen 77 filas y entran 21. Entre los 77 excluidos hay 16 con indicador a treinta días faltante. La pertenencia cambia en 98 filas, no solo en la diferencia neta de 56.

No invalida el dataset actual: la ficha ya identifica la columna utilizada. Sí obliga a justificar la elección y a conservar esa definición al comparar con estadísticas oficiales. Cambiarla exigiría una sensibilidad explícita y una nueva versión, no una sustitución silenciosa.

## 5. Función y estado de los archivos principales

| Archivo o componente | Función y estado observado |
|---|---|
| `01_Comprension_del_Negocio.ipynb` | Objetivos, problema, pregunta y alcance. Requiere alinearse con el escenario con víctimas, la unidad diaria, la validación temporal y la interfaz realmente construida. |
| `02_Comprension_de_los_Datos.ipynb` | Exploración de estructura y calidad de las hojas originales. Sus 25 celdas de código tienen ejecución guardada. |
| `02B_EDA_y_Analisis_Espacial_Con_Victimas.ipynb` | Cobertura de coordenadas, distribución territorial anual, densidad puntual y concentraciones. Sus seis celdas de código están ejecutadas. El EDA temporal y de actores todavía es limitado. |
| `03_Preparacion_de_los_Datos (3).ipynb` | Preparación del escenario original. Sus 28 celdas de código están ejecutadas. El sufijo del nombre dificulta identificar una versión canónica. |
| `03B_Preparacion_Datos_Con_Victimas.ipynb` | Prepara el escenario principal y la etiqueta histórica. Existen sus artefactos, pero las nueve celdas de código no conservan ejecución ni salidas. |
| `04_Modelado.ipynb` | Comparación inicial del escenario total. Conserva validación aleatoria; no debe presentarse como el protocolo temporal definitivo. Sus 16 celdas de código tienen ejecución guardada. |
| `04B_Modelado_Con_Victimas.ipynb` | Compara familias mediante validación temporal y selecciona RF base y umbral 0,55. Existen modelos y reportes, pero las 12 celdas no conservan ejecución ni salidas. |
| `04C_Ajuste_Hiperparametros_Con_Victimas.ipynb` | Evalúa ocho configuraciones de RF, selecciona la ajustada y umbral 0,52. Seis celdas de código ejecutadas. |
| `05_Evaluacion.ipynb` | Evaluación y sensibilidades del escenario original, incluidas comprobaciones temporales posteriores. 36 de 37 celdas de código con ejecución guardada. |
| `05B_Evaluacion_Con_Victimas.ipynb` | Evaluación principal del RF ajustado y comparación con referencias anteriores. 22 de 22 celdas de código con ejecución guardada. |
| `data/raw/` y `data/processed/` | Fuente original y datasets derivados. Deben conservarse separados y con procedencia trazable. |
| `models/victimas/` | Pipelines base y ajustado, metadatos, registro principal y umbrales. El catálogo reciente reduce el riesgo de confusión. |
| `reports/` | Tablas, gráficas, predicciones y conclusiones de cada etapa. Hay resultados antiguos y nuevos en algunos mismos directorios. |
| `src/modelo_principal.py` | Carga el modelo registrado, valida entradas y aplica el umbral 0,52. Requiere variables ya preparadas; no crea históricos desde una fecha. |
| `scripts/verificar_modelo_principal.py` | Reproduce el cierre sin entrenar. Pasó la auditoría. |
| Otros scripts | Generan notebooks o actualizan celdas. No son una ejecución integral automatizada y sus posiciones de celdas son frágiles ante cambios estructurales. |
| `dashboard/dist/` | Visor web estático de métricas retrospectivas, con fallos funcionales comprobados. No realiza inferencia. |
| `README.md` y `requirements.txt` | Guía actualizada y versiones directas fijadas. Falta demostrar reproducción desde una instalación limpia y consolidar documentación de uso. |

Un contador de ejecución vacío no demuestra que un notebook nunca se ejecutó. Significa que el archivo actual no conserva esa evidencia. No se encontraron salidas de error guardadas en los notebooks inspeccionados; esto tampoco certifica que todos se ejecuten de principio a fin en su estado actual.

## 6. Modelado y ajuste: qué se sostiene metodológicamente

El escenario principal utiliza tres cortes expansivos: entrenar hasta 2019 y validar 2020; hasta 2020 y validar 2021; hasta 2021 y validar 2022. Dentro de cada corte se reconstruyen etiqueta y preprocesamiento con el pasado disponible. Este diseño es más adecuado al problema que mezclar fechas aleatoriamente.

04B selecciona la familia. 04C ajusta únicamente Random Forest mediante ocho candidatos. La configuración principal usa 300 árboles, profundidad sin límite explícito, mínimo 20 observaciones por hoja, selección `sqrt` de variables, pesos `balanced`, muestreo bootstrap y semilla 42.

La configuración se escoge por Average Precision media; después se selecciona el umbral que maximiza F1 agregado en las predicciones fuera de muestra de 2020–2022. Finalmente se entrena con 2018–2022 y se evalúa retrospectivamente con 2023–2024.

Los límites del protocolo están bien reconocidos en la ficha reciente, pero deben quedar homogéneos en todos los documentos:

- Ocho candidatos de RF no son una búsqueda exhaustiva ni un ajuste equivalente de las tres familias.
- La misma validación participa en selección de configuración y umbral. Sus métricas no son una estimación independiente de la selección.
- 2023–2024 no alimenta el cálculo de la búsqueda, pero ya había sido examinado durante el desarrollo. No es un test futuro intacto.
- El F1 seleccionado no incorpora costos institucionales ni capacidad real de atender alertas.
- La variación entre 2020, 2021 y 2022 incluye cambios de prevalencia y el periodo pandémico; no debe interpretarse como mejora progresiva del algoritmo.

No es necesario descartar la experimentación existente. Es necesario describirla como una comparación retrospectiva con selección temporal acotada.

## 7. Fase 5.1: evaluación y selección del modelo

**Estado: desarrollada, ejecutada y reproducida para la versión principal; pendiente de una ampliación de referencia y cierre interpretativo.**

05B ya contiene matrices de confusión, ROC y precisión–recall, calibración y Brier, comparación base–ajustado, resultados anuales, errores territoriales y horarios, métricas macro, análisis de Candelaria, diagnósticos de scores e importancia interna y por permutación. No se puede describir como una fase que todavía no se ha hecho.

### Resultados globales verificados

| Métrica | RF base, 0,55 | RF ajustado, 0,52 |
|---|---:|---:|
| F1 | 0,3982 | 0,4058 |
| AUC-ROC | 0,6853 | 0,6933 |
| Average Precision | 0,3038 | 0,3098 |
| Precisión | 30,11 % | 29,41 % |
| Recall | 58,77 % | 65,44 % |
| Brier, menor es mejor | 0,2304 | 0,2221 |

Con el modelo ajustado se detectan 7.276 positivos, se omiten 3.842 y se generan 17.467 falsas alertas. Los negativos correctos son 29.895. Aproximadamente 29 de cada 100 alertas son aciertos respecto a la etiqueta y se detectan 65 de cada 100 positivos; esto no significa detectar el 65 % de los accidentes individuales.

El sistema alerta sobre el 42,31 % de las combinaciones del test: unas 34 de las 80 combinaciones localidad–franja por día. Esta carga debe acompañar cualquier argumento de priorización. Frente al base hay 742 positivos adicionales detectados y 2.299 falsas alertas adicionales: 3,10 falsas alertas adicionales por cada detección adicional.

La diferencia combina cambios de configuración y umbral. Como diagnóstico, a umbral común 0,52 el F1 es 0,3973 en el base y 0,4058 en el ajustado. A 0,55 es 0,3982 y 0,4002. No se adoptaron nuevos umbrales ni se optimizó la decisión sobre test.

### Calibración y desigualdad territorial

La constante de prevalencia de entrenamiento tiene Brier 0,1544, mejor que 0,2221 del modelo. Debe mantenerse el lenguaje de score o puntuación relativa, no probabilidad literal. Un AUC de 0,6933 no significa 69,33 % de exactitud ni una probabilidad de accidente.

El F1 macro por localidad es 0,3474, frente al global 0,4058; el recall macro es 55,83 %. Candelaria sigue con 157 positivos, cero detectados y score máximo 0,3227, inferior a 0,52. Sumapaz tiene dos positivos, también sin detecciones, pero su tamaño no permite conclusiones equivalentes a las de Candelaria.

Madrugada tiene recall 39,43 %; Noche 74,42 %, Mañana 74,80 % y Tarde 66,87 %. Los valores anteriores de Madrugada de alrededor de 23 % corresponden al modelo base, no al principal actual.

La correlación de Spearman entre volumen histórico territorial y recall es aproximadamente -0,065. Por tanto, no está respaldada una explicación general de que el modelo omite localidades simplemente por tener poco volumen. En Candelaria sí está comprobado el mecanismo inmediato: los scores no alcanzan el umbral. La causa de esa distribución de scores necesita análisis adicional.

Localidad, franja, día de semana y promedio de treinta días dominan la importancia por permutación. Esto mide dependencia predictiva del modelo, no factores causales; utiliza una muestra de 5.000 filas y tres repeticiones. Que la localidad sea importante no prueba que se haya aprendido una dinámica temporal compleja.

## 8. Hallazgo nuevo central: una referencia histórica casi iguala el ordenamiento

Se calculó una referencia sencilla: para cada localidad–franja–día de semana, asignar la proporción histórica de etiquetas positivas observada exclusivamente en entrenamiento. No se utilizaron etiquetas de test para estimar esas tasas ni se eligió un umbral nuevo.

Por ejemplo, todas las observaciones de una determinada localidad, en madrugada y lunes, reciben su tasa histórica de positivos de 2018–2022. Son 560 grupos y no requieren un bosque de árboles ni ventanas móviles.

| Método, test 2023–2024 | Average Precision | AUC-ROC | Brier ↓ |
|---|---:|---:|---:|
| Constante de prevalencia de train | 0,1901 | 0,5000 | 0,1544 |
| Tasa por localidad | 0,2440 | 0,6219 | 0,1495 |
| Tasa por localidad y franja | 0,2964 | 0,6809 | 0,1450 |
| Tasa por localidad, franja y día de semana | 0,3087 | 0,6931 | 0,1438 |
| RF ajustado | 0,3098 | 0,6933 | 0,2221 |

La ventaja del RF sobre la referencia más exigente es 0,00118 en AP y 0,00021 en AUC. En Brier la referencia histórica es sustancialmente mejor. Esto sugiere que una parte importante del ordenamiento global puede explicarse por patrones territoriales y semanales estables.

Se comprobó también en los tres cortes temporales, recalculando umbrales de etiqueta y tasas únicamente con el entrenamiento de cada corte. La AP media de la referencia fue 0,2503 y la del RF ajustado 0,2552. El RF tiene una ventaja media pequeña; no se demuestra una ganancia sustancial generalizada.

Como diagnóstico de incertidumbre se realizó un bootstrap pareado de 300 repeticiones, semilla 42, remuestreando 105 bloques consecutivos no solapados de hasta siete días, manteniendo juntas todas sus localidades y franjas. Los intervalos percentiles de la diferencia RF menos referencia fueron:

| Diferencia | Estimación | Percentiles 2,5 % y 97,5 % |
|---|---:|---:|
| AP | +0,00118 | -0,00265 a +0,00477 |
| AUC | +0,00021 | -0,00189 a +0,00259 |
| Brier | +0,07832 | +0,07580 a +0,08045 |

Los intervalos de AP y AUC incluyen cero. Es un análisis exploratorio condicionado a los artefactos y periodos actuales: no incorpora toda la incertidumbre de reentrenamiento y selección, ni sustituye evaluación independiente. No prueba equivalencia, pero desaconseja afirmar superioridad concluyente del RF sobre esta referencia.

Este hallazgo no elimina el mérito de la tesis y no autoriza cambiar automáticamente el modelo cerrado. Sí es la ampliación prioritaria de 5.1: incluir esta referencia formalmente y discutir qué aporta la complejidad del modelo. La tesis puede obtener un resultado valioso incluso si concluye que una solución simple compite con modelos más complejos.

## 9. Fase 3.1: EDA espacial y temporal

Hay avances reales: cobertura de coordenadas, distribución anual por localidad, densidades de siniestros con heridos y muertos, centros medianos y celdas de concentración. Kennedy concentra 11.879 registros, 13,94 % del escenario principal, seguida por Engativá y Suba. Esto describe volumen registrado, no riesgo ajustado por exposición.

La cobertura espacial mejora de alrededor de 91 % en 2018 a casi 100 % desde 2021; esa diferencia puede afectar comparaciones de mapas. El indicador denominado `Coordenada_Valida_Bogota` usa un rectángulo aproximado, no el límite oficial distrital. Encontré nueve registros con coordenadas completas excluidos por ese rectángulo, incluidos registros de Sumapaz. Estar fuera de ese rectángulo no basta para declarar una coordenada inválida.

Hay dos ajustes semánticos importantes:

- La columna `Fallecidos` de los resúmenes cuenta siniestros clasificados `Con Muertos`, no personas fallecidas. Debe identificarse como siniestros con fallecidos o calcular personas con la hoja apropiada.
- Los centros mostrados son medianas de coordenadas de eventos, no centroides administrativos. Las cuadrículas por redondeo son concentración descriptiva, no delimitación oficial de zonas críticas.

Los conteos `Con_Moto`, `Con_Peaton` y `Con_Bicicleta` representan participación en siniestros, pueden solaparse y no son cantidades de víctimas de cada actor. Los campos ausentes no deben interpretarse automáticamente como negativos confirmados sin revisar el diccionario.

Faltan cruces más explícitos de día de semana × franja × actor, comportamiento mensual, festivos frente a no festivos con denominadores comparables y discusión del periodo pandémico. El notebook crea la franja, pero sus salidas principales no desarrollan esos cruces. Por eso 3.1 está avanzada, no completamente agotada frente al objetivo específico de 01.

## 10. Dashboard: estado real comprobado

Existe una interfaz con mensajes adecuados sobre calibración y alcance retrospectivo. Los CSV contienen métricas del modelo ajustado. Sin embargo, la versión local no puede considerarse funcionalmente cerrada.

### Fallo de carga global

En `dashboard/dist/app.js`, línea 5, se busca una fila cuyo modelo sea exactamente `Random Forest`. El CSV actualizado identifica `Random Forest ajustado` y `Random Forest base`. No hay coincidencia; la vista global queda sin fila y falla al leer sus métricas.

La apertura mediante servidor local reproduce el mensaje «No fue posible cargar los datos» y deja los indicadores globales vacíos. No es un problema de abrir el archivo sin servidor; el mensaje mostrado atribuye la causa incorrectamente.

### Los filtros no se cruzan

En la línea 8, una localidad seleccionada tiene prioridad sobre la franja. Seleccionar Candelaria y Madrugada conserva los 157 omitidos de Candelaria en todas las franjas. La nota de alcance lo dice, pero la interfaz permite dos selecciones que parecen combinables. Las tablas disponibles son marginales, no contienen el cruce necesario.

### Barras sin dimensión visible

Los elementos `.fill` de las barras horizontales se crean como elementos en línea. En la comprobación de navegador, tres barras inspeccionadas tuvieron ancho y alto cero. Los valores textuales aparecen al seleccionar una localidad, pero las barras no representan visualmente los valores como se espera.

### Distancia frente al objetivo original

El dashboard consume cuatro CSV estáticos de métricas. No carga el pipeline ni el módulo de inferencia, no permite seleccionar fechas para ver predicciones y no incluye mapas georreferenciados. Ordenar localidades por F1 muestra dónde funciona mejor el modelo, no cuáles son las zonas con mayor riesgo predicho. Esa diferencia debe quedar clara en títulos y demostración.

La existencia de configuración de alojamiento no demuestra que una versión pública esté desplegada y funcione. Esta revisión verificó solamente la copia local.

## 11. Ingeniería, reproducibilidad y documentación

### Mejoras recientes bien resueltas

El registro principal explicita identidad, parámetros, columnas, umbral y huellas de integridad. El cargador valida el esquema, categorías y valores; aplica 0,52 expresamente, evitando depender de la regla interna de `predict()`. El verificador enlaza los artefactos con las predicciones de 05B. La ficha técnica separa cierre académico de preparación para producción.

El modelo base no fue sustituido y su alias histórico `pipeline_modelo_seleccionado.pkl` está advertido en el catálogo. Conservarlo permite comparaciones y evita perder el experimento anterior.

### Deuda pendiente

1. No hay ejecución integral automatizada y comprobada desde fuente cruda hasta visor. El código de preparación, evaluación y selección sigue repartido y parcialmente duplicado en notebooks.
2. Los reportes base y ajustado comparten directorios y algunos nombres genéricos. Se necesitan versiones o subdirectorios de ejecución y un catálogo de salidas actuales para evitar usar gráficos antiguos en la tesis.
3. Las copias de CSV del dashboard se pueden desincronizar de 05B. El error de nombre del modelo es evidencia concreta de esa separación.
4. Faltan pruebas automáticas de la interfaz y pruebas más amplias de preparación, actualización de históricos y consistencia de entradas. La verificación existente es útil pero no cubre todo el sistema.
5. Las dependencias directas están fijadas; falta una prueba desde instalación limpia y, si se busca reproducibilidad más estricta, registrar dependencias transitivas y entorno completo.
6. Al revisar Git había cambios de cierre aún sin incorporar al historial, entre ellos registro, ficha, cargador y verificador. Están presentes localmente, pero no debe asumirse que otra copia del repositorio ya los tiene.
7. No encontré manual técnico y manual de usuario completos dentro de la carpeta. El README y la ficha ayudan, pero no sustituyen instalación detallada, uso, interpretación, resolución de errores y límites de cada filtro.

### Alineación de la tesis

01 todavía habla de k-fold genérico, omite fecha en la granularidad y contiene promesas de actores como entradas y mapas predictivos que no corresponden plenamente a la implementación. Debe actualizarse sin atribuir al modelo entradas que no utiliza ni beneficios preventivos que no se midieron.

La cifra de 4.902 lesionados en 2024 atribuida al anuario necesita corrección o una fuente y universo diferentes: el resumen oficial del Anuario 2024 informa 22.593 lesionados y 565 fallecidos, y diferencia personas de siniestros. No deben intercambiarse estadísticas de registros policiales, forenses u otras coberturas. [Anuario oficial, resumen ejecutivo](https://observatorio.movilidadbogota.gov.co/sites/default/files/2025-09/ANUARIO%20SINIESTRALIDAD%20VIAL%202024-Digital-1_0.pdf).

Las afirmaciones sobre ausencia de sistemas predictivos previos, conducta reactiva institucional y originalidad del trabajo requieren revisión bibliográfica propia; el código no demuestra esas afirmaciones.

## 12. Estado frente al cronograma

| Actividad | Estado basado en evidencia | Qué falta para cerrar |
|---|---|---|
| 1.1 Revisión bibliográfica | No certificable como completa con esta auditoría de código | Actualizar fuentes, cifras y antecedentes; revisar el documento de tesis. |
| 1.2 Comprensión del problema | Desarrollada; desalineaciones con cambios recientes | Actualizar escenario, unidad diaria, objetivo y beneficios demostrables. |
| 2.1 Adquisición e integración | Fuente principal disponible y utilizada | Documentar procedencia y decisión tradicional/30 días; delimitar uso de otras hojas. |
| 2.2 Preparación | Desarrollada; variables comprobadas | Conservar evidencia ejecutada de 03B y probar reproducción desde fuente. |
| 3.1 EDA y espacial | Avanzada, con resultados ejecutados | Completar cruces temporales y de actores, corregir unidades y límites espaciales. |
| 4.1 Entrenamiento | Desarrollado, con artefactos y resultados | Conservar ejecución de 04B y delimitar el protocolo original frente al principal. |
| 4.2 Hiperparámetros | Desarrollado para RF mediante ocho candidatos | Documentar alcance acotado; no afirmar ajuste exhaustivo de las tres familias. |
| 5.1 Evaluación y selección | 05B ejecutado y modelo principal reproducido | Incorporar referencia histórica exigente, incertidumbre y conclusiones actualizadas. |
| 6.1 Dashboard | Implementación parcial con fallos reproducibles | Corregir carga, filtros y barras; definir e implementar visualización de predicciones acorde al alcance. |
| 6.2 Manuales | No completos en la carpeta | Manual técnico y de usuario, incluida interpretación de limitaciones. |
| Documento final | Reportes técnicos disponibles; Word no certificado | Integrar método, resultados, discusión y correspondencia con objetivos. |
| Sustentación | No certificable como preparada | Demostración funcional, diapositivas, guion y respuestas a preguntas metodológicas. |

Por entregables estás en consolidación de 5.1 y desarrollo/corrección de 6.1, con pendientes de 3.1 y documentación. No es posible afirmar adelanto o atraso calendario sin fecha de inicio y seguimiento real. Tampoco sería riguroso asignar un porcentaje de avance arbitrario.

## 13. Prioridades recomendadas, sin implementarlas en esta revisión

### Prioridad inmediata: validez de lo que se presenta

1. Ampliar 05B con la tasa histórica localidad–franja–día de semana como referencia, mantener la constante y el RF base, y discutir el valor incremental. No cambiar automáticamente el modelo principal ni volver a elegir umbral sobre test.
2. Corregir los fallos reproducibles del dashboard y agregar pruebas de carga global, selección individual, combinación de filtros y coincidencia con las tablas fuente.
3. Corregir unidades de fallecidos, cifra de lesionados, definición de gravedad y afirmaciones de causalidad o cobertura perfecta. Actualizar conclusiones sin borrar el historial experimental.

### Prioridad de cumplimiento académico

4. Completar los cruces de 3.1 y la discusión espacial; distinguir concentración de eventos, desempeño territorial y predicción agregada de riesgo.
5. Acordar el producto de 6.1: un visor retrospectivo de evaluación no cumple por sí solo el objetivo de mapas de predicciones. Si se mantiene este objetivo, implementar vista geográfica a la resolución realmente modelada y una dimensión de fecha. No presentar precisión de calle a partir de un modelo por localidad.
6. Guardar evidencia ejecutada de los notebooks principales, sincronizar reportes con dashboard, verificar desde un entorno limpio y consolidar versiones en el control de cambios.
7. Completar manuales y documento final con trazabilidad entre cada objetivo, resultado, limitación y evidencia.

### Futuro trabajo, no requisito para ocultar limitaciones actuales

Explorar calibración con separación temporal adecuada, alternativas de pesos de clase, objetivos de conteo u ocurrencia homogénea, alertas limitadas por capacidad diaria y datos de exposición u otras covariables disponibles antes de predecir. Estas serían nuevas hipótesis y versiones, no mejoras garantizadas. La evaluación futura deberá respetar la fecha real de disponibilidad de los datos.

## 14. Conclusión para el autor

Tienes un prototipo académico con resultados concretos y una evaluación mucho más madura que la experimentación inicial. La selección del escenario con víctimas, el control temporal y el cierre verificable son contribuciones importantes.

Lo que todavía necesita fortalecerse es la distancia entre un modelo que produce resultados, un modelo que aporta valor frente a alternativas simples y un producto que cumple los objetivos de visualización. La nueva referencia histórica hace especialmente importante esa distinción.

La conclusión defendible hoy no es «el sistema predice con alta precisión dónde ocurrirán accidentes». Es: «se desarrolló y evaluó retrospectivamente un prototipo de clasificación de ocurrencia o frecuencia elevada de siniestros con víctimas a escala localidad–franja–día; se identificaron limitaciones de cobertura, calibración y desempeño territorial, y el valor incremental frente a patrones históricos simples todavía debe justificarse».

La fase 5.1 sí existe y funciona. Su siguiente avance es incorporar esa comparación exigente y ajustar las conclusiones; en paralelo, la fase 6.1 necesita corrección funcional e integración para que la demostración sea coherente con la tesis.
