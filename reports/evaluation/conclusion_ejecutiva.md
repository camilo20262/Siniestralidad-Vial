**Resultado relativo.** XGBoost obtiene la mayor Average Precision. XGBoost alcanza F1=0.1973, AUC-ROC=0.7053 y AP=0.1329, frente a AP=0.0631 de la línea base. Presenta discriminación moderada, sin demostrar utilidad operativa suficiente.

**Validación temporal 2018–2022.** Al ajustar desde cero cada corte expansivo, Random Forest obtiene la mayor AP promedio (0.2245 ± 0.0505), frente a XGBoost (0.2179 ± 0.0597) y Regresión Logística (0.2103 ± 0.0550). El umbral candidato seleccionado solo con predicciones fuera de muestra de 2020–2022 es 0.525. Este resultado cambia la selección preliminar: XGBoost domina la comparación retrospectiva 2023–2024, pero Random Forest muestra la mejor generalización temporal interna promedio.

**Alertas y omisiones.** Con umbral 0,5, la precisión es 14.76% y el recall 29.72%: 1,096 verdaderos positivos, 6,328 falsas alertas y 2,592 positivos omitidos.

**Calibración.** El score medio de XGBoost es 29.23%, frente a prevalencia observada 6.31%. Su Brier=0.1264, frente a 0.0726 de la constante de entrenamiento, evidencia junto con la curva limitaciones de calibración. La línea base también está afectada por el cambio de prevalencia.

**Estabilidad.** El F1 anual de XGBoost es {2023: 0.19350232059978578, 2024: 0.20108892921960073}. El F1 territorial varía entre 0.0000 y 0.2872; el macro es 0.1524. En noche se omiten 689 de 765 positivos (recall=9.93%). Los grupos tienen prevalencias diferentes y algunos muy pocos positivos; esto no mide peligrosidad.

**Sensibilidad territorial.** Excluir Sumapaz de la evaluación cambia AUC de 0.7053 a 0.6891; su importancia puede reflejar un grupo casi siempre negativo. Sin Localidad explícita, el modelo experimental obtiene AUC=0.5887, AP=0.0798, F1=0.1347. La comparación muestra sensibilidad territorial, no causalidad; persiste información geográfica indirecta.

**Umbral.** Pasar de 0,5 a 0,455 en 2024 agrega 176 positivos detectados y 1523 falsas alertas, 8.65 por positivo adicional. El 0,455 es exploratorio y no definitivo.

**Alcance.** La validación temporal expansiva ya ajusta umbrales de etiqueta, preprocesamiento y entrenamiento dentro del pasado permitido de cada corte. Aun así, 2023–2024 ya se utilizó para comparar algoritmos, por lo que la confirmación sobre esos años sigue siendo retrospectiva y no independiente. Los históricos de prueba suponen disponibilidad diaria de accidentes pasados: esta evaluación no valida pronósticos de múltiples días sin actualizar historial.

**Dashboard.** XGBoost funciona mejor como herramienta exploratoria de priorización relativa que como generador de probabilidades confiables. Mostrar puntuaciones relativas con sus limitaciones, no probabilidades literales. No se considera listo para producción; se requieren un criterio operativo y una evaluación posterior independiente.
