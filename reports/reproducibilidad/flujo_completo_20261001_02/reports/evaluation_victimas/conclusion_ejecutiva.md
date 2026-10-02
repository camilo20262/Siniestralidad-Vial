# Conclusión ejecutiva del escenario con víctimas — modelo ajustado

El Random Forest ajustado, seleccionado mediante la búsqueda temporal de 04C y umbral 0.52, obtiene retrospectivamente en 2023–2024 F1=0.4058, AUC-ROC=0.6933, Average Precision=0.3098, precisión=29.41% y recall=65.44%. Detecta 7,276 positivos, genera 17,467 falsas alertas y omite 3,842 positivos.

Frente al Random Forest base, cambia el F1 en +0.0076, el AUC-ROC en +0.0080, la Average Precision en +0.0060 y el recall en +6.67 puntos porcentuales. La mejora es modesta y debe leerse junto con el aumento de 2,299 falsas alertas.

El Brier del modelo ajustado es 0.2221, frente a 0.1544 de la constante basada en la prevalencia de entrenamiento. Aunque mejora respecto al modelo base (0.2304), sigue siendo peor que la línea base: los scores sirven para ranking y priorización, no como probabilidades literales.

El desempeño territorial no es uniforme: SANTA FE presenta el mayor F1 (0.4834) y CANDELARIA el menor (0.0000). Candelaria tiene 157 positivos, 0 detectados y recall 0.00% con el umbral global. El umbral específico analizado para Candelaria es retrospectivo y no debe adoptarse sin validación futura.

Por franja, Noche obtiene el mayor F1 (0.4306) y Madrugada el menor (0.3330). La correlación de Spearman entre volumen histórico y recall es -0.065; por tanto, el volumen no explica por sí solo las diferencias territoriales.

La etiqueta combina ocurrencia y superación de umbral según localidad y franja. Los resultados son retrospectivos, no causales ni confirmatorios. El sistema no está listo para producción sin evaluación futura independiente, calibración temporal y definición del costo operativo de falsas alertas y omisiones.

## Ampliación de 5.1: valor incremental frente a tasas históricas

La tasa por localidad–franja–día de semana, estimada solo con 2018–2022, alcanza
AP 0.3087, AUC 0.6931 y Brier 0.1438.
El RF ajustado obtiene AP 0.3098, AUC 0.6933 y Brier 0.2221.
La ventaja observada es +0.00118 en AP y +0.00021 en AUC.

En los tres cortes 2020–2022, recalculando etiquetas y tasas con el pasado de cada corte,
la AP media es 0.2503
para la referencia y 0.2552 para el RF.

El bootstrap temporal pareado de 300 réplicas tiene un intervalo percentil de
-0.00265 a 0.00477 para la diferencia de AP,
y de -0.00189 a 0.00259 para AUC.
Son intervalos exploratorios sobre modelos fijos, no evidencia confirmatoria ni prueba de equivalencia.
No se sostiene una superioridad concluyente del RF en ordenamiento frente a esta referencia.
El Brier de la referencia es menor, pero no demuestra calibración perfecta.

El modelo emite 33.85 alertas diarias en promedio
entre 80 combinaciones posibles. Una alerta acertada corresponde a una observación
localidad–franja–día positiva, no a un accidente individual evitado.

Se mantiene rf_victimas_bogota_v1.0 con umbral 0,52 como versión académica documentada,
sin sustituir el modelo ni adoptar nuevos umbrales territoriales. El aporte incremental
de su complejidad debe discutirse explícitamente. 2023–2024 ya había sido inspeccionado
durante el desarrollo; la evaluación continúa siendo retrospectiva.
