# Conclusión ejecutiva del escenario con víctimas

Random Forest, seleccionado con validación temporal 2018–2022 y umbral 0.55, obtiene en 2023–2024 F1=0.3982, AUC-ROC=0.6853, Average Precision=0.3038, precisión=30.11% y recall=58.77%. Detecta 6,534 positivos, genera 15,168 falsas alertas y omite 4,584 positivos.

El desempeño territorial no es uniforme: SANTA FE presenta el mayor F1 (0.4853) y CANDELARIA el menor (0.0000); estos valores deben leerse junto con prevalencia y cantidad de positivos. Por franja, Noche obtiene el mayor F1 (0.4254) y Madrugada el menor (0.2744).

Las probabilidades requieren revisar la curva de calibración antes de mostrarse literalmente. La etiqueta combina ocurrencia y superación de umbral según la localidad y franja. Los resultados son retrospectivos, no causales ni confirmatorios, y el sistema no se considera listo para producción sin una evaluación futura independiente y un criterio operativo para falsas alertas y omisiones.
