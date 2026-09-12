# Conclusión ejecutiva — ajuste de hiperparámetros

Se compararon ocho configuraciones de Random Forest mediante tres cortes temporales expansivos: validación en 2020, 2021 y 2022. El periodo 2023–2024 no participó en la selección.

La mejor configuración utiliza 300 árboles, profundidad sin límite, mínimo 20 observaciones por hoja, `max_features='sqrt'` y pesos balanceados. Su Average Precision media fue 0,2552, frente a 0,2493 del candidato base. La mejora es modesta y menor que la variación entre años (desviación 0,0653), por lo que no constituye evidencia de superioridad estadística concluyente.

El umbral elegido con predicciones fuera de muestra de 2020–2022 fue 0,52. En la confirmación retrospectiva 2023–2024 logró F1 0,4058, AUC-ROC 0,6933, Average Precision 0,3098, precisión 0,2941 y recall 0,6544. Frente al modelo base aumenta la detección, pero también las falsas alertas.

El Brier mejora a 0,2221, aunque continúa peor que la línea base histórica 0,1544. En consecuencia, las salidas deben seguir comunicándose como puntuaciones de priorización y no como probabilidades calibradas.
