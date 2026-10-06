# Dashboard de siniestralidad con víctimas

Aplicación en Python Dash de solo lectura. Reutiliza el modelo académico
`rf_victimas_bogota_v1.0`, umbral 0,52. No entrena ni modifica los datos oficiales.
La maqueta anterior se conserva en `dist/`; no es la aplicación vigente.

La [especificación vigente ESP-MODELO-01](../docs/ESPECIFICACION_VIGENTE.md)
establece RF ajustado con umbral 0,52 para esta interfaz. El requisito anterior
de 0,55 queda sustituido: ese valor corresponde únicamente a la referencia base
mostrada en las comparaciones. La autoridad ejecutable sigue siendo el registro
del modelo; no se ofrece un cambio de umbral desde el dashboard.

## Instalación e inicio

Desde la raíz del repositorio, con Python 3.12.14 y Git LFS. Compruebe que
`python3 --version` indique 3.12.14 antes de crear el entorno:

```sh
git lfs pull
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m dashboard.app
```

Abra **http://127.0.0.1:8050**. Para otro puerto:

```sh
python -m dashboard.app --port 8051
```

Detenga la aplicación con Ctrl+C. Este comando escucha solo en la dirección
local y se ejecuta sin modo de depuración. El servidor de desarrollo no debe
exponerse directamente a Internet.

## Despliegue público académico

El despliegue público principal, validado con el estado actual del repositorio,
está disponible en Railway:
**https://siniestralidad-vial-production.up.railway.app**. Usa `wsgi.py` como
entrada WSGI y sirve la aplicación Flask/Dash mediante Gunicorn:

```sh
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
```

El endpoint `/healthz` permite comprobar la disponibilidad del servicio. Tanto
la consulta como la evaluación tienen alcance retrospectivo 2023–2024. La URL
pública facilita la revisión del prototipo académico; no representa un sistema
institucional en producción ni una autorización para uso operativo.

El repositorio mantiene `vercel.json` y la entrada WSGI como alternativa
compatible y evaluada para Vercel. No se considera el despliegue público
principal mientras su deployment actual permanezca obsoleto y protegido.

Los agregados `data/dashboard/` se incluyen en el repositorio. Si se trabaja con
una copia en la que todavía no existen, se pueden construir una vez:

```sh
python scripts/preparar_dashboard.py
```

Este comando necesita el Excel original de Git LFS. Contrasta sus huellas y los
conteos contra el dataset y el EDA, genera únicamente los archivos nuevos de
`data/dashboard/` y rechaza sobrescribir archivos existentes. No volver a
ejecutarlo sobre un directorio ya preparado ni borrar evidencias para forzarlo.
Para ejecutar este generador y los verificadores instale `requirements-dev.txt`;
`requirements.txt` cubre el dashboard con artefactos ya preparados.

## Guía de uso

1. **Resumen:** universo del estudio, evolución mensual y localidades con mayor
   conteo de registros. Todos los conteos se refieren a siniestros, no a personas.
2. **Consulta y mapa:** elija una fecha de 2023–2024, franja y localidad. El mapa
   muestra scores para las 20 localidades y permite seleccionarlas haciendo clic.
   El encuadre urbano no cubre todo Sumapaz; seleccionarla acerca el mapa a esa
   localidad. «Distrito completo» muestra el conjunto. La tabla contiene siempre
   las 20 localidades, también si no están visibles en el encuadre.
   El detalle explica si la etiqueta del grupo significa uno, dos o tres
   siniestros con víctimas, usando solo el histórico de entrenamiento. No
   muestra el conteo observado del día como si fuera la predicción.
3. **Análisis histórico:** filtros combinables por año, localidad, franja y
   participación de motocicleta, peatón o bicicleta. Son categorías no
   excluyentes: no sumar sus conteos. El filtro usa indicadores afirmativos de
   la hoja Siniestros, no predicciones ni conteos de personas.
4. **Evaluación:** métricas recalculadas para la intersección de año, localidad y
   franja. Las tablas comparativas y la importancia de variables situadas debajo
   corresponden al conjunto completo y están identificadas como globales.
   Incluye barras de detección y omisión por localidad y franja, con tablas de
   conteos para no interpretar porcentajes sin conocer el tamaño de muestra.
   AUC se omite si no hay ambas clases; AP y recall se omiten sin positivos.
   Un aviso destaca Madrugada: recall global de 39,43 % (914 de 2.318 positivos
   detectados y 1.404 omitidos). Se deriva del reporte conservado, no de una
   cifra introducida manualmente. También aparece al consultar Madrugada y
   siempre aclara que describe el conjunto completo 2023–2024, no el caso individual.
5. **Metodología:** definición de etiqueta, separación temporal, identidad del
   modelo, procedencia, interpretación, limitaciones y guía de navegación.

### Funciones opt-in pendientes de aprobación textual

Dos bloques están implementados y probados, pero permanecen ocultos por defecto:

- `MOSTRAR_VALIDACION_INDEPENDIENTE = False`, en `dashboard/data.py`, controla
  una tarjeta con el experimento temporal separado de 2022. Su JSON se lee en
  modo de solo lectura y se verifica contra
  `dashboard/validacion_independiente_manifest.json`, separado del manifiesto
  oficial del dashboard.
- `MOSTRAR_CONTEXTO_LIMITACIONES_CONSULTA = False`, en `dashboard/app.py`,
  controla el bloque contextual de Brier, comparación histórica y advertencias
  de Candelaria/Sumapaz junto al resultado individual.

Activarlos requiere aprobar primero el texto académico. Ninguna bandera cambia
el modelo, el dataset, las predicciones congeladas ni el umbral oficial 0,52.

### Interpretación y descargas

- El score no es una probabilidad calibrada. Una alerta baja no garantiza la
  ausencia de accidentes. El umbral fijo 0,52 no se modifica en la interfaz.
- La consulta individual calcula el score con el pipeline registrado y lo
  contrasta con las predicciones congeladas. El mapa utiliza esas predicciones
  precalculadas, después de verificar su integridad y correspondencia con el
  dataset. No se utilizan etiquetas observadas como entradas del modelo.
- JSON de consulta y CSV del mapa incluyen versión, identificador, umbral,
  periodo de evaluación y advertencias. El CSV histórico incluye sus filtros y
  unidad de conteo. El CSV de métricas incluye filtros y trazabilidad del modelo.
- Las descargas se generan en memoria y se guardan en el equipo del usuario;
  no alteran los archivos oficiales del proyecto.
- No se generan fechas futuras, predicciones por actor ni resolución por calle.

## Arquitectura y datos

| Archivo | Responsabilidad |
| --- | --- |
| `app.py` | Componentes, callbacks, filtros y descargas |
| `data.py` | Carga verificada, selección de casos y métricas |
| `charts.py` | Figuras Plotly, mapa local y estados sin datos |
| `assets/dashboard.css` | Presentación adaptable y estilos de foco |
| `../src/consulta_retrospectiva.py` | Consulta y trazabilidad del modelo principal |
| `../scripts/preparar_dashboard.py` | Agregados descriptivos nuevos y manifiesto |
| `../scripts/verificar_dashboard.py` | Integración con datos reales y comprobación de tiempos |
| `../tests/test_dashboard.py` | Pruebas con fixtures, callbacks, filtros y descargas |

Una instancia de datos se carga por proceso, con comprobaciones de integridad
antes de habilitar las consultas. Los callbacks leen esa instancia y devuelven
copias o resúmenes; no tienen rutas de actualización de datos ni entrenamiento.
La fecha, el año, el mes y el día semanal del análisis descriptivo se preparan
una sola vez al iniciar. La consulta individual ejecuta una sola inferencia: el
mapa valida el alcance temporal de forma independiente y utiliza las
predicciones congeladas verificadas.
No hay telemetría ni mapas de terceros. La cartografía se simplifica únicamente
en memoria para dibujar; el GeoJSON original permanece intacto. El botón de
compartir gráficos con servicios externos está deshabilitado.

Los eventos con participación de actor se agrupan por fecha, localidad y franja;
el nuevo archivo no contiene nombres, identificadores personales ni códigos de
accidente. El manifiesto registra la fuente y las huellas de recursos utilizados.

Los errores estructurales del manifiesto, registro o GeoJSON se convierten en
mensajes de contrato legibles. Si impiden el arranque local, se muestra una
pantalla de diagnóstico en lugar de un traceback. Los botones de descarga se
deshabilitan con una explicación cuando sus filtros no son exportables.

Los resultados dinámicos de consulta, historia y evaluación usan regiones
`aria-live`; cada gráfico tiene un contenedor enfocable con nombre y resumen
textual. El indicador de foco usa `#b06f14`, con contraste aproximado 4,09:1
sobre blanco y 3,77:1 sobre `#f5f6f3`. Son mejoras acotadas con WCAG 2.2 AA
como referencia, no sustituyen la auditoría exhaustiva pendiente.

## Pruebas y diagnóstico

```sh
python scripts/verificar_codigo.py
python scripts/verificar_dashboard.py
python scripts/verificar_codigo.py --integracion
```

La prueba habitual usa fixtures y no requiere descargar el Excel. La integración
completa sí requiere los artefactos reales. `verificar_dashboard.py` compara
métricas con 05B, conteos por actor con el EDA, consultas en distintas fechas,
renderizado de las cinco páginas y preservación de evidencias. Los tiempos que
reporta son del servidor local, no de una conexión remota ni del navegador.

| Situación | Acción |
| --- | --- |
| No se encuentra `dash` | Active `.venv` e instale `requirements.txt` |
| Punteros LFS o archivos incompletos | Ejecute `git lfs pull` y los verificadores |
| Falta `manifest.json` | Recupere `data/dashboard/` de Git o genere los agregados en una copia aún no preparada |
| Falla una huella de integridad | No desactive la validación; recupere la versión correcta del artefacto y compruebe el registro |
| Puerto ocupado | Use `--port 8051` o detenga su instancia anterior |
| Consulta no disponible | Revise fecha 2023–2024, localidad y franja; no admite futuro |
| No hay registros históricos | La aplicación muestra cero siniestros; no lo confunde con probabilidades ni resultados del modelo |
| Mapa no visible | Compruebe soporte WebGL del navegador; la tabla de 20 localidades sigue disponible |

## Alcance de la entrega

Versión funcional para revisión académica, disponible tanto localmente como en
el despliegue público principal de Railway. Permanecen como pendientes
independientes la aceptación formal por usuarios, las pruebas de carga, la
telemetría y una auditoría exhaustiva de accesibilidad (teclado, lector de
pantalla, contraste y pruebas con usuarios). También falta revisar las
condiciones de reutilización del Excel. La licencia específica de la fuente sigue
pendiente de confirmación; la disponibilidad pública no convierte esta entrega
en un sistema institucional ni constituye autorización para redistribuir
microdatos o usar el prototipo operativamente.

Documentación técnica consultada: [callbacks de Dash](https://dash.plotly.com/basic-callbacks)
y [mapas coropléticos de Plotly](https://plotly.com/python/tile-county-choropleth/).
