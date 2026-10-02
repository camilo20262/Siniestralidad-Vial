# Dashboard local de siniestralidad con víctimas

Aplicación en Python Dash de solo lectura. Reutiliza el modelo académico
`rf_victimas_bogota_v1.0`, umbral 0,52. No entrena ni modifica los datos oficiales.
La maqueta anterior se conserva en `dist/`; no es la aplicación vigente.

La [especificación vigente ESP-MODELO-01](../docs/ESPECIFICACION_VIGENTE.md)
establece RF ajustado con umbral 0,52 para esta interfaz. El requisito anterior
de 0,55 queda sustituido: ese valor corresponde únicamente a la referencia base
mostrada en las comparaciones. La autoridad ejecutable sigue siendo el registro
del modelo; no se ofrece un cambio de umbral desde el dashboard.

## Instalación e inicio

Desde la raíz del repositorio, con Python 3.12 y Git LFS:

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

Detenga la aplicación con Ctrl+C. El servicio se limita a la dirección local y
se ejecuta sin modo de depuración. No se ha realizado un despliegue público;
el servidor de desarrollo no debe exponerse directamente a Internet.

Los agregados `data/dashboard/` se incluyen en el repositorio. Si se trabaja con
una copia en la que todavía no existen, se pueden construir una vez:

```sh
python scripts/preparar_dashboard.py
```

Este comando necesita el Excel original de Git LFS. Contrasta sus huellas y los
conteos contra el dataset y el EDA, genera únicamente los archivos nuevos de
`data/dashboard/` y rechaza sobrescribir archivos existentes. No volver a
ejecutarlo sobre un directorio ya preparado ni borrar evidencias para forzarlo.

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
No hay telemetría ni mapas de terceros. La cartografía se simplifica únicamente
en memoria para dibujar; el GeoJSON original permanece intacto. El botón de
compartir gráficos con servicios externos está deshabilitado.

Los eventos con participación de actor se agrupan por fecha, localidad y franja;
el nuevo archivo no contiene nombres, identificadores personales ni códigos de
accidente. El manifiesto registra la fuente y las huellas de recursos utilizados.

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

Versión local funcional para revisión académica. Pendientes independientes:
aceptación por usuarios, despliegue público con configuración WSGI/HTTPS y revisión
de condiciones de reutilización del Excel. La licencia específica de la fuente
sigue pendiente de confirmación; no se presenta esta entrega como autorización
para redistribuir microdatos ni como validación para uso operativo.

Documentación técnica consultada: [callbacks de Dash](https://dash.plotly.com/basic-callbacks)
y [mapas coropléticos de Plotly](https://plotly.com/python/tile-county-choropleth/).
