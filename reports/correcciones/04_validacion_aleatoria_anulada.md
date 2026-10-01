# Anulación de la validación aleatoria del escenario total

Fecha: 1 de octubre de 2026. Notebook: `notebooks/04_Modelado.ipynb`.

## Decisión

Se anulan la validación aleatoria de la sección 10 y sus conclusiones como
evidencia de estabilidad o generalización temporal. No se anula todo el
experimento original ni la línea principal con víctimas. Se retiraron del
notebook los imports, las llamadas y las salidas de esa validación, además de
corregir las afirmaciones de test intacto y el resumen de decisiones.

Motivos: mezcla de fechas con `StratifiedKFold(shuffle=True)`, preprocesamiento
ajustado sobre todo el train antes de los folds y etiqueta sin recalcular con
el pasado de cada corte. La estratificación no resuelve estos problemas.

## Trazabilidad y recuperación

La versión anterior se conserva en el commit
[`c0a18ce68c759031472d9dbe9a81cf6798aec5d5`](https://github.com/camilo20262/Siniestralidad-Vial/blob/c0a18ce68c759031472d9dbe9a81cf6798aec5d5/notebooks/04_Modelado.ipynb).
Las celdas 28–33 (índices desde cero) contenían la sección retirada; también
había referencias en la portada, los imports y el resumen final.

Sus medias de F1 (RL: 0,3807; RF: 0,3987; XGBoost: 0,3981) quedan registradas
aquí **solo para identificar los resultados anulados**, no para seleccionarlos,
compararlos como evidencia válida ni reutilizarlos en la tesis.

Las salidas de entrenamiento y comparación retrospectiva ajenas a esa sección
permanecen históricas e intactas. La celda de imports editada se dejó sin marca
de ejecución para no atribuirle una ejecución nueva. Esta corrección no ejecutó
el notebook completo: ello reentrenaría y escribiría artefactos del escenario
original. Para reproducirlo debe utilizarse una copia aislada.

## Evidencia temporal de referencia

La sección 20 de `05_Evaluacion.ipynb` ya contiene los cortes
2018–2019→2020, 2018–2020→2021 y 2018–2021→2022 del escenario total. Ajusta
etiqueta, preprocesador y modelo con el pasado de cada corte y recalcula la
ponderación de XGBoost. La nueva sección 10 de 04 enlaza sus CSV, predicciones y
gráfica conservados en `reports/evaluation/`. No se regeneraron ni se atribuyen
a una nueva ejecución de 04.

El periodo 2023–2024 sigue siendo evaluación retrospectiva previamente
inspeccionada. Esta anulación no lo convierte en holdout independiente. La
autoridad del modelo principal permanece en `models/victimas/modelo_principal.json`
(RF ajustado, umbral 0,52); no se modificó.

## Alcance de los controles

Se añadieron pruebas para impedir que 04 vuelva a incorporar validadores
aleatorios ejecutables, comprobar su compilación y verificar las referencias
temporales. La comprobación de integración se conserva en
`validacion_04_20261001.json`. Los controles no constituyen un nuevo entrenamiento
ni una auditoría completa de todo el escenario legado.

Se compararon huellas SHA-256 antes y después de 103 archivos en `models/`,
`data/processed/`, `reports/evaluation/` y `reports/evaluation_victimas/`: cero
cambios. También se compararon las 13 celdas históricas restantes con salidas:
su contenido y resultados permanecen idénticos. La auditoría general del
proyecto tenía cambios previos del usuario y no se editó como parte de este trabajo.
