from pathlib import Path
import nbformat

root = Path(__file__).resolve().parents[1]
path = root / 'notebooks' / '05B_Evaluacion_Con_Victimas.ipynb'
nb = nbformat.read(path, as_version=4)

nb.cells[0].source = """# 05B · Evaluación del escenario de siniestros con víctimas
### Fase 5 de CRISP-DM · modelo ajustado

Este notebook evalúa el **Random Forest ajustado** mediante validación temporal en 2018–2022 y confirmado retrospectivamente en 2023–2024. El umbral 0,52 se seleccionó con predicciones fuera de muestra de 2020–2022. Se conserva el Random Forest base como referencia y no se reentrena ni sobrescribe ningún modelo."""

nb.cells[5].source = """dataset = pd.read_parquet(DATA_FILE)
dataset['Fecha_Acc'] = pd.to_datetime(dataset['Fecha_Acc'])
base_metadata = json.loads((MODELS_PATH / 'metadata_modelo.json').read_text(encoding='utf-8'))
tuned_metadata = json.loads((MODELS_PATH / 'metadata_random_forest_ajustado.json').read_text(encoding='utf-8'))
feature_cols = base_metadata['variables']
selected_model = 'Random Forest ajustado'
selected_threshold = float(tuned_metadata['umbral_temporal'])
base_threshold = float(base_metadata['umbral_candidato'])
pipelines = {
    'Regresión Logística': joblib.load(MODELS_PATH / 'pipeline_logistica_victimas.pkl'),
    'Random Forest base': joblib.load(MODELS_PATH / 'pipeline_random_forest_victimas.pkl'),
    'Random Forest ajustado': joblib.load(MODELS_PATH / 'pipeline_random_forest_ajustado_victimas.pkl'),
    'XGBoost': joblib.load(MODELS_PATH / 'pipeline_xgboost_victimas.pkl'),
}
required = feature_cols + ['Fecha_Acc', 'Localidad', 'Franja_Horaria', 'Periodo', 'Alto_Riesgo']
assert dataset[required].isna().sum().sum() == 0
assert tuned_metadata['seleccion_sin_test'] is True
print('Modelo evaluado:', selected_model, '| Umbral temporal:', selected_threshold)
print('Hiperparámetros:', tuned_metadata['hiperparametros'])
print('Dataset:', dataset.shape)"""

nb.cells[6].source = """test = dataset[dataset.Periodo.eq('test')].copy()
test['Anio'] = test.Fecha_Acc.dt.year
X_test, y_test = test[feature_cols], test.Alto_Riesgo.astype(int)
scores = {name: pipeline.predict_proba(X_test)[:, 1] for name, pipeline in pipelines.items()}
thresholds = {
    'Regresión Logística': 0.5,
    'Random Forest base': base_threshold,
    'Random Forest ajustado': selected_threshold,
    'XGBoost': 0.5,
}
predictions = {name: (scores[name] >= thresholds[name]).astype(int) for name in pipelines}
print(f'Test: {len(test):,} observaciones; prevalencia={y_test.mean():.2%}')"""

nb.cells[8].source = """def classification_metrics(y_true, y_pred, y_score):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        'F1': f1_score(y_true, y_pred, zero_division=0),
        'AUC_ROC': roc_auc_score(y_true, y_score),
        'Average_Precision': average_precision_score(y_true, y_score),
        'Precision': precision_score(y_true, y_pred, zero_division=0),
        'Recall': recall_score(y_true, y_pred, zero_division=0),
        'Especificidad': tn / (tn + fp),
        'Balanced_Accuracy': balanced_accuracy_score(y_true, y_pred),
        'Brier': brier_score_loss(y_true, y_score),
        'Tasa_Predicha_Positiva': np.mean(y_pred),
        'TN': tn, 'FP': fp, 'FN': fn, 'TP': tp
    }

global_metrics = pd.DataFrame([
    {'Modelo': name, 'Umbral': thresholds[name],
     **classification_metrics(y_test, predictions[name], scores[name])}
    for name in pipelines
]).sort_values('Average_Precision', ascending=False)
global_metrics.to_csv(REPORTS_PATH / 'metricas_globales.csv', index=False, encoding='utf-8-sig')

rf_comparison = global_metrics[global_metrics.Modelo.isin(['Random Forest base', selected_model])].set_index('Modelo')
rf_delta = (rf_comparison.loc[selected_model] - rf_comparison.loc['Random Forest base']).rename('Cambio_Ajustado_Menos_Base')
rf_delta.to_frame().to_csv(REPORTS_PATH / 'comparacion_random_forest_ajustado_vs_base.csv', encoding='utf-8-sig')
display(global_metrics.round(4))
display(rf_delta[['F1','AUC_ROC','Average_Precision','Precision','Recall','Brier','FP','FN','TP']].to_frame().T.round(4))"""

nb.cells[10].source = """model_names = list(pipelines)
fig, axes = plt.subplots(1, len(model_names), figsize=(5 * len(model_names), 4))
for ax, name in zip(axes, model_names):
    cm = confusion_matrix(y_test, predictions[name], labels=[0, 1])
    ax.imshow(cm, cmap='Blues')
    for row in range(2):
        for col in range(2):
            ax.text(col, row, f'{cm[row, col]:,}', ha='center', va='center',
                    color='white' if cm[row, col] > cm.max()/2 else 'black')
    ax.set(title=f'{name} (u={thresholds[name]:.2f})', xlabel='Predicción', ylabel='Valor real')
    ax.set_xticks([0, 1], ['No alto', 'Alto']); ax.set_yticks([0, 1], ['No alto', 'Alto'])
plt.suptitle('Matrices de confusión — escenario con víctimas', y=1.03)
plt.tight_layout(); plt.savefig(REPORTS_PATH / '01_matrices_confusion.png', dpi=160, bbox_inches='tight')
plt.show()"""

nb.cells[12].source = nb.cells[12].source.replace(
    "colors = {'Regresión Logística': '#4472C4', 'Random Forest': '#70AD47', 'XGBoost': '#ED7D31'}",
    "colors = {'Regresión Logística': '#4472C4', 'Random Forest base': '#9BBB59', 'Random Forest ajustado': '#008C95', 'XGBoost': '#ED7D31'}"
)

nb.cells[19].source = "## 8. Errores del Random Forest ajustado por localidad y franja"
nb.cells[20].source = nb.cells[20].source.replace("metricas_random_forest_por_localidad.csv", "metricas_random_forest_ajustado_por_localidad.csv").replace("metricas_random_forest_por_franja.csv", "metricas_random_forest_ajustado_por_franja.csv")
nb.cells[21].source = nb.cells[21].source.replace("color='#70AD47'", "color='#008C95'")
nb.cells[25].source = "## 10. Importancia interna del Random Forest ajustado"
nb.cells[26].source = nb.cells[26].source.replace("importancia_interna_random_forest.csv", "importancia_interna_random_forest_ajustado.csv").replace("Importancia interna de Random Forest", "Importancia interna del Random Forest ajustado").replace("color='#70AD47'", "color='#008C95'").replace("06_importancia_interna_random_forest.png", "06_importancia_interna_random_forest_ajustado.png")
nb.cells[28].source = nb.cells[28].source.replace("importancia_permutacion_random_forest.csv", "importancia_permutacion_random_forest_ajustado.csv")
nb.cells[31].source = nb.cells[31].source.replace("'Random Forest'", "selected_model")

nb.cells[34].source = """train = dataset[dataset.Periodo.eq('train')].copy()
historical_volume = train.groupby('Localidad').Num_Accidentes.sum().rename('Volumen_Historico_2018_2022')
score_summary = (rf_eval.groupby('Localidad').Score
                 .agg(Score_Min='min', Score_Medio='mean', Score_Mediana='median',
                      Score_P95=lambda x: x.quantile(.95), Score_Max='max').reset_index())
score_summary['Alertas_Umbral_Seleccionado'] = rf_eval.groupby('Localidad').Prediccion.sum().values
locality_diagnostic = (by_locality.merge(score_summary, on='Localidad')
                       .merge(historical_volume.reset_index(), on='Localidad'))
locality_diagnostic.to_csv(REPORTS_PATH / 'diagnostico_scores_localidad.csv', index=False, encoding='utf-8-sig')
locality_diagnostic.sort_values('Score_Max').round(4)"""

nb.cells[38].source = """candelaria = rf_eval[rf_eval.Localidad.eq('CANDELARIA')].copy()
candelaria_summary = pd.DataFrame([{
    'Observaciones': len(candelaria), 'Positivos': int(candelaria.Alto_Riesgo.sum()),
    'Prevalencia': candelaria.Alto_Riesgo.mean(), 'Score_Medio': candelaria.Score.mean(),
    'Score_Mediana': candelaria.Score.median(), 'Score_P95': candelaria.Score.quantile(.95),
    'Score_Max': candelaria.Score.max(),
    'Umbral_Global': selected_threshold, 'Alertas': int(candelaria.Prediccion.sum()),
    'TP': int(((candelaria.Alto_Riesgo == 1) & (candelaria.Prediccion == 1)).sum()),
    'Recall': recall_score(candelaria.Alto_Riesgo, candelaria.Prediccion, zero_division=0)
}])
candelaria_summary.to_csv(REPORTS_PATH / 'resumen_candelaria.csv', index=False, encoding='utf-8-sig')
candelaria_summary.round(4)"""

nb.cells[39].source = """candelaria_threshold_rows = []
for threshold in np.linspace(0.05, selected_threshold, 95):
    pred = (candelaria.Score.to_numpy() >= threshold).astype(int)
    candelaria_threshold_rows.append({'Umbral': threshold,
        **classification_metrics(candelaria.Alto_Riesgo, pred, candelaria.Score)})
candelaria_thresholds = pd.DataFrame(candelaria_threshold_rows)
candelaria_best_threshold = float(candelaria_thresholds.loc[candelaria_thresholds.F1.idxmax(), 'Umbral'])
candelaria_thresholds.to_csv(REPORTS_PATH / 'diagnostico_umbral_candelaria.csv', index=False, encoding='utf-8-sig')

global_default = classification_metrics(y_test, predictions[selected_model], scores[selected_model])
global_low_pred = (scores[selected_model] >= candelaria_best_threshold).astype(int)
global_low = classification_metrics(y_test, global_low_pred, scores[selected_model])
targeted_pred = predictions[selected_model].copy()
cand_mask = test.Localidad.eq('CANDELARIA').to_numpy()
targeted_pred[cand_mask] = (scores[selected_model][cand_mask] >= candelaria_best_threshold).astype(int)
targeted = classification_metrics(y_test, targeted_pred, scores[selected_model])
threshold_impact = pd.DataFrame({
    f'Umbral global {selected_threshold:.2f}': global_default,
    f'Umbral global {candelaria_best_threshold:.3f}': global_low,
    f'Umbral {candelaria_best_threshold:.3f} solo Candelaria': targeted
}).T
threshold_impact.to_csv(REPORTS_PATH / 'impacto_umbral_candelaria.csv', encoding='utf-8-sig')
print(f'Umbral que maximiza F1 en Candelaria, calculado retrospectivamente: {candelaria_best_threshold:.3f}')
display(threshold_impact[['F1','Precision','Recall','FP','FN','TP','TN']].round(4))"""

nb.cells[47].source = """rf_eval.to_parquet(REPORTS_PATH / 'predicciones_random_forest_ajustado_2023_2024.parquet', index=False)
rf = global_metrics.set_index('Modelo').loc[selected_model]
rf_base = global_metrics.set_index('Modelo').loc['Random Forest base']
best_loc, worst_loc = by_locality.iloc[0], by_locality.iloc[-1]
best_slot, worst_slot = by_slot.iloc[0], by_slot.iloc[-1]
cand = by_locality.set_index('Localidad').loc['CANDELARIA']
executive = f\"\"\"# Conclusión ejecutiva del escenario con víctimas — modelo ajustado

El Random Forest ajustado, seleccionado exclusivamente con validación temporal 2020–2022 y umbral {selected_threshold:.2f}, obtiene retrospectivamente en 2023–2024 F1={rf.F1:.4f}, AUC-ROC={rf.AUC_ROC:.4f}, Average Precision={rf.Average_Precision:.4f}, precisión={rf.Precision:.2%} y recall={rf.Recall:.2%}. Detecta {int(rf.TP):,} positivos, genera {int(rf.FP):,} falsas alertas y omite {int(rf.FN):,} positivos.

Frente al Random Forest base, cambia el F1 en {rf.F1-rf_base.F1:+.4f}, el AUC-ROC en {rf.AUC_ROC-rf_base.AUC_ROC:+.4f}, la Average Precision en {rf.Average_Precision-rf_base.Average_Precision:+.4f} y el recall en {rf.Recall-rf_base.Recall:+.2%}. La mejora es modesta y debe leerse junto con el aumento de {int(rf.FP-rf_base.FP):,} falsas alertas.

El Brier del modelo ajustado es {rf.Brier:.4f}, frente a {brier_comparison.iloc[1].Brier:.4f} de la constante basada en la prevalencia de entrenamiento. Aunque mejora respecto al modelo base ({rf_base.Brier:.4f}), sigue siendo peor que la línea base: los scores sirven para ranking y priorización, no como probabilidades literales.

El desempeño territorial no es uniforme: {best_loc.Localidad} presenta el mayor F1 ({best_loc.F1:.4f}) y {worst_loc.Localidad} el menor ({worst_loc.F1:.4f}). Candelaria tiene {int(cand.Positivos)} positivos, {int(cand.TP)} detectados y recall {cand.Recall:.2%} con el umbral global. El umbral específico analizado para Candelaria es retrospectivo y no debe adoptarse sin validación futura.

Por franja, {best_slot.Franja_Horaria} obtiene el mayor F1 ({best_slot.F1:.4f}) y {worst_slot.Franja_Horaria} el menor ({worst_slot.F1:.4f}). La correlación de Spearman entre volumen histórico y recall es {locality_correlations.loc['Volumen_Historico_2018_2022','Recall']:.3f}; por tanto, el volumen no explica por sí solo las diferencias territoriales.

La etiqueta combina ocurrencia y superación de umbral según localidad y franja. Los resultados son retrospectivos, no causales ni confirmatorios. El sistema no está listo para producción sin evaluación futura independiente, calibración temporal y definición del costo operativo de falsas alertas y omisiones.
\"\"\"
(REPORTS_PATH / 'conclusion_ejecutiva.md').write_text(executive, encoding='utf-8')
print(executive)
print('Reportes guardados en:', REPORTS_PATH.resolve())"""

nbformat.write(nb, path)
print('Actualizado:', path)
