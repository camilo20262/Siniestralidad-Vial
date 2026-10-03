# Separación de modelos vigentes e históricos

> **PORTADA DE LEGADO.** Ningún archivo `.pkl` situado directamente en
> `models/` es un modelo vigente ni alimenta el dashboard. Son componentes del
> escenario histórico de todos los siniestros y su estado es **histórico**.

El único pipeline vigente es
`models/victimas/pipeline_random_forest_ajustado_victimas.pkl`, identificado por
`models/victimas/modelo_principal.json` y con umbral oficial 0,52.

Los binarios de la raíz no se trasladaron a `legacy/` porque los notebooks 04 y
05 cerrados, sus salidas guardadas y citas históricas dependen de esas rutas.
Moverlos haría que la evidencia dejara de ser autocontenida. La separación se
implementa mediante esta portada y los estados explícitos de
`config/artefactos.json`; no se alteraron los bytes de los modelos.

El manifiesto de la decisión está en [`legacy/README.md`](../legacy/README.md).
