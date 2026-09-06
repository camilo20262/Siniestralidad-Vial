# Conclusión ejecutiva del escenario con víctimas

Random Forest, seleccionado con validación temporal 2018–2022 y umbral 0.55, obtiene en 2023–2024 F1=0.3982, AUC-ROC=0.6853, Average Precision=0.3038, precisión=30.11% y recall=58.77%. Detecta 6,534 positivos, genera 15,168 falsas alertas y omite 4,584 positivos.

El Brier de Random Forest es 0.2304, peor que 0.1544 de la constante basada en la prevalencia de entrenamiento. El modelo supera la referencia en discriminación y ranking, pero no en exactitud probabilística; sus scores no deben mostrarse como probabilidades literales.

El desempeño territorial no es uniforme: SANTA FE presenta el mayor F1 (0.4853) y CANDELARIA el menor (0.0000); estos valores deben leerse junto con prevalencia y cantidad de positivos. Por franja, Noche obtiene el mayor F1 (0.4254) y Madrugada el menor (0.2744).

Candelaria contiene 157 positivos, pero su score máximo es 0.3554, por debajo de 0,55 y también de 0,50. Este es un fallo territorial específico. La correlación de Spearman entre volumen histórico y recall es -0.049, por lo que no se puede generalizar que todas las localidades con bajo volumen tengan peor recall.

La madrugada presenta el menor volumen histórico, score medio y recall (23.47%). Esta coincidencia es descriptiva y compatible con menor señal histórica, pero no demuestra causalidad. La etiqueta combina ocurrencia y superación de umbral según localidad y franja. Los resultados son retrospectivos, no causales ni confirmatorios, y el sistema no se considera listo para producción sin una evaluación futura independiente y un criterio operativo para falsas alertas y omisiones.
