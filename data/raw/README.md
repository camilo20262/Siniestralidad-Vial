# Fuente congelada del modelo

La fuente es el Excel del [Anuario 2024 publicado por la Secretaría Distrital de
Movilidad](https://observatorio.movilidadbogota.gov.co/node/79). Su URL de descarga,
hash SHA-256, tamaño, hojas y usos se documentan en `procedencia_excel.json`.

La copia local contiene 2015–2024; el modelo utiliza 2018–2024. La fecha de corte
analítico (2024-12-31) no equivale a una fecha certificada de extracción de SIGAT.
No se conserva la fecha de descarga original: se registra como desconocida.
La consulta de la publicación se realizó el 26 de septiembre de 2026.

## Recuperar y verificar

Desde un clon del repositorio:

```sh
git lfs pull
python scripts/verificar_fuente.py
```

El verificador detecta punteros LFS sin descargar, comprueba el hash de la copia
congelada y las dimensiones de las cuatro hojas. No descarga ni modifica datos.
La URL pública puede actualizar su contenido: no reemplazar el Excel oficial sin
comparar su hash, revisar el cambio y versionar explícitamente un nuevo escenario.

## Uso de las hojas

`Siniestros` contiene eventos y alimenta el modelo principal. `Vehiculos` y
`Actor_vial` contienen varios registros por siniestro y se usan en exploración;
actor vial no es una variable del clasificador. `Diccionario` documenta campos.
La relación por `Codigo_Accidente` no autoriza a sumar filas después de una unión
uno-a-muchos: antes hay que validar la cardinalidad y la unidad de conteo.

## Condiciones todavía por confirmar

No se verificó una licencia específica para este Excel en la página consultada.
Su disponibilidad pública no basta para asignarle una licencia. Ese punto de
procedencia sigue abierto; no se inventó una fecha ni un permiso de reutilización.
El metadato lo expresa literalmente como
`"licencia": "pendiente de confirmación institucional"`.
