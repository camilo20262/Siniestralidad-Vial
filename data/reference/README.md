# Cartografía de referencia para 02B

`localidades_sdp_referencia.geojson` es una instantánea del servicio oficial de localidades de Catastro Bogotá, atribuido a la Secretaría Distrital de Planeación (SDP):

[Servicio Localidad](https://sig.catastrobogota.gov.co/arcgis/rest/services/ordenamientoterritorial/localidad/MapServer/0).

`localidades_sdp_referencia_metadata.json` registra la URL exacta de consulta, fecha UTC, atribución, CRS y SHA-256. El notebook 02B verifica la copia local antes de usarla y no vuelve a descargarla mientras exista. Si se desea actualizarla, debe conservarse o versionarse la instantánea anterior y revisar los resultados espaciales; no debe sustituirse silenciosamente.

La capa contiene veinte localidades en EPSG:4326. Se usa para mapas descriptivos y diagnóstico de concordancia de coordenadas, no para certificar límites históricos, reasignar localidades de los siniestros ni modificar las entradas del modelo. Los puntos originales se interpretan en EPSG:4686 según el diccionario del Excel; la cuadrícula de 100 m se construye en EPSG:9377.
