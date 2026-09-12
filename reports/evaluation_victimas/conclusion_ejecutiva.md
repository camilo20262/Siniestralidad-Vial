# Conclusión ejecutiva del escenario con víctimas — modelo ajustado

El Random Forest ajustado, seleccionado exclusivamente con validación temporal 2020–2022 y umbral 0.52, obtiene retrospectivamente en 2023–2024 F1=0.4058, AUC-ROC=0.6933, Average Precision=0.3098, precisión=29.41% y recall=65.44%. Detecta 7,276 positivos, genera 17,467 falsas alertas y omite 3,842 positivos.

Frente al Random Forest base, cambia el F1 en +0.0076, el AUC-ROC en +0.0080, la Average Precision en +0.0060 y el recall en +6.67%. La mejora es modesta y debe leerse junto con el aumento de 2,299 falsas alertas.

El Brier del modelo ajustado es 0.2221, frente a 0.1544 de la constante basada en la prevalencia de entrenamiento. Aunque mejora respecto al modelo base (0.2304), sigue siendo peor que la línea base: los scores sirven para ranking y priorización, no como probabilidades literales.

El desempeño territorial no es uniforme: SANTA FE presenta el mayor F1 (0.4834) y CANDELARIA el menor (0.0000). Candelaria tiene 157 positivos, 0 detectados y recall 0.00% con el umbral global. El umbral específico analizado para Candelaria es retrospectivo y no debe adoptarse sin validación futura.

Por franja, Noche obtiene el mayor F1 (0.4306) y Madrugada el menor (0.3330). La correlación de Spearman entre volumen histórico y recall es -0.065; por tanto, el volumen no explica por sí solo las diferencias territoriales.

La etiqueta combina ocurrencia y superación de umbral según localidad y franja. Los resultados son retrospectivos, no causales ni confirmatorios. El sistema no está listo para producción sin evaluación futura independiente, calibración temporal y definición del costo operativo de falsas alertas y omisiones.
