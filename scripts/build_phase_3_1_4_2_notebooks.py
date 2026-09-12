from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / 'notebooks'

def md(text): return nbf.v4.new_markdown_cell(text)
def code(text): return nbf.v4.new_code_cell(text)

eda_cells = [
md("""# 02B · EDA y análisis espacial de siniestros con víctimas
## Actividad 3.1 del cronograma

Este notebook caracteriza la distribución temporal, territorial y puntual de los siniestros con personas heridas o fallecidas entre 2018 y 2024. El análisis es descriptivo: identifica concentración espacial, no causalidad ni riesgo individual. Las coordenadas se usan como puntos; no se asignan polígonos administrativos."""),
md("## 1. Configuración y carga"),
code("""from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use('seaborn-v0_8-whitegrid')
pd.set_option('display.max_columns', 50)
RAW_FILE = Path('../data/raw/base-anuario-de-siniestralidad-2024.xlsx')
REPORTS_PATH = Path('../reports/eda_victimas')
REPORTS_PATH.mkdir(parents=True, exist_ok=True)
COLS = ['Codigo_Accidente','Longitud','Latitud','Fecha_Acc','AA_Acc','Hora_Acc',
        'Localidad','Gravedad_Indicador_Tradicional','Con_Bicicleta','Con_Moto','Con_Peaton']
siniestros = pd.read_excel(RAW_FILE, sheet_name='Siniestros', usecols=COLS)
siniestros['Fecha_Acc'] = pd.to_datetime(siniestros['Fecha_Acc'])
victimas = siniestros[
    siniestros.AA_Acc.between(2018, 2024) &
    siniestros.Gravedad_Indicador_Tradicional.isin(['Con Heridos','Con Muertos'])
].copy()
assert victimas.Codigo_Accidente.is_unique
print(f'Siniestros con víctimas: {len(victimas):,}')
display(victimas.head())"""),
md("## 2. Calidad y cobertura de coordenadas"),
code("""victimas['Coordenada_Completa'] = victimas[['Longitud','Latitud']].notna().all(axis=1)
victimas['Coordenada_Valida_Bogota'] = (
    victimas.Coordenada_Completa & victimas.Longitud.between(-74.30,-73.90) &
    victimas.Latitud.between(4.40,4.90)
)
coverage = (victimas.groupby('AA_Acc').agg(
    Siniestros=('Codigo_Accidente','size'),
    Coordenadas_Completas=('Coordenada_Completa','sum'),
    Coordenadas_Validas=('Coordenada_Valida_Bogota','sum'))
    .rename_axis('Anio').reset_index())
coverage['Cobertura_Valida'] = coverage.Coordenadas_Validas / coverage.Siniestros
coverage.to_csv(REPORTS_PATH/'cobertura_coordenadas.csv', index=False, encoding='utf-8-sig')
display(coverage)
ax=coverage.plot(x='Anio',y='Cobertura_Valida',marker='o',legend=False,figsize=(9,4),color='#0C6E8A')
ax.set(title='Cobertura anual de coordenadas válidas — siniestros con víctimas',ylabel='Proporción',xlabel='Año',ylim=(0,1.02))
ax.yaxis.set_major_formatter(lambda x,pos:f'{x:.0%}')
plt.tight_layout(); plt.savefig(REPORTS_PATH/'01_cobertura_coordenadas.png',dpi=170,bbox_inches='tight'); plt.show()"""),
md("## 3. Distribución temporal y territorial"),
code("""victimas['Franja_Horaria'] = pd.cut(victimas.Hora_Acc, bins=[-1,5,11,17,23],
    labels=['Madrugada','Mañana','Tarde','Noche'])
annual_locality = victimas.groupby(['Localidad','AA_Acc']).size().unstack(fill_value=0)
summary = victimas.groupby('Localidad').agg(
    Siniestros=('Codigo_Accidente','size'),
    Fallecidos=('Gravedad_Indicador_Tradicional',lambda s:(s=='Con Muertos').sum()),
    Con_Peaton=('Con_Peaton',lambda s:(s=='SI').sum()),
    Con_Moto=('Con_Moto',lambda s:(s=='SI').sum()),
    Con_Bicicleta=('Con_Bicicleta',lambda s:(s=='SI').sum()),
    Cobertura_Coordenadas=('Coordenada_Valida_Bogota','mean')).sort_values('Siniestros',ascending=False)
summary['Participacion_Ciudad'] = summary.Siniestros / summary.Siniestros.sum()
summary.to_csv(REPORTS_PATH/'resumen_localidades.csv',encoding='utf-8-sig')
display(summary.round(4))
plt.figure(figsize=(11,8)); sns.heatmap(annual_locality.div(annual_locality.sum(axis=0),axis=1),cmap='YlGnBu',fmt='.1%',annot=True)
plt.title('Participación de cada localidad en los siniestros con víctimas por año'); plt.xlabel('Año'); plt.ylabel('Localidad')
plt.tight_layout(); plt.savefig(REPORTS_PATH/'02_distribucion_anual_localidad.png',dpi=170,bbox_inches='tight'); plt.show()"""),
md("## 4. Densidad espacial puntual"),
code("""geo=victimas[victimas.Coordenada_Valida_Bogota].copy()
fig,axes=plt.subplots(1,2,figsize=(14,7),sharex=True,sharey=True)
for ax,(label,part) in zip(axes,[('Con heridos',geo[geo.Gravedad_Indicador_Tradicional=='Con Heridos']),('Con muertos',geo[geo.Gravedad_Indicador_Tradicional=='Con Muertos'])]):
    hb=ax.hexbin(part.Longitud,part.Latitud,gridsize=52,mincnt=1,cmap='magma',bins='log')
    ax.set(title=f'{label} · densidad logarítmica',xlabel='Longitud',ylabel='Latitud',aspect='equal')
    fig.colorbar(hb,ax=ax,label='log10 del conteo')
plt.suptitle('Concentración puntual de siniestros con víctimas en Bogotá',y=1.01)
plt.tight_layout(); plt.savefig(REPORTS_PATH/'03_densidad_espacial_victimas.png',dpi=180,bbox_inches='tight'); plt.show()"""),
md("## 5. Centros espaciales y cuadrículas de concentración"),
code("""centroids=(geo.groupby('Localidad').agg(Longitud=('Longitud','median'),Latitud=('Latitud','median'),Siniestros=('Codigo_Accidente','size')).reset_index())
fig,ax=plt.subplots(figsize=(10,9)); ax.scatter(centroids.Longitud,centroids.Latitud,s=30+500*centroids.Siniestros/centroids.Siniestros.max(),c=centroids.Siniestros,cmap='viridis',alpha=.82,edgecolor='white')
for _,r in centroids.iterrows(): ax.annotate(r.Localidad.title(),(r.Longitud,r.Latitud),xytext=(4,4),textcoords='offset points',fontsize=8)
ax.set(title='Centro mediano y volumen de siniestros con víctimas por localidad',xlabel='Longitud',ylabel='Latitud',aspect='equal')
plt.tight_layout(); plt.savefig(REPORTS_PATH/'04_centros_localidad.png',dpi=180,bbox_inches='tight'); plt.show()

geo['Lon_Celda']=geo.Longitud.round(3); geo['Lat_Celda']=geo.Latitud.round(3)
hotspots=(geo.groupby(['Lon_Celda','Lat_Celda']).agg(Siniestros=('Codigo_Accidente','size'),Localidad_Dominante=('Localidad',lambda s:s.mode().iat[0]),Fallecidos=('Gravedad_Indicador_Tradicional',lambda s:(s=='Con Muertos').sum())).reset_index().sort_values('Siniestros',ascending=False).head(25))
hotspots.to_csv(REPORTS_PATH/'top25_celdas_concentracion.csv',index=False,encoding='utf-8-sig')
display(hotspots)"""),
md("## 6. Estabilidad 2018–2022 frente a 2023–2024"),
code("""period = victimas.assign(Periodo=np.where(victimas.AA_Acc<=2022,'2018–2022','2023–2024'))
rates=(period.groupby(['Localidad','Periodo']).size().unstack(fill_value=0))
rates['Promedio_Anual_2018_2022']=rates['2018–2022']/5
rates['Promedio_Anual_2023_2024']=rates['2023–2024']/2
rates['Ratio_Post_Pre']=rates.Promedio_Anual_2023_2024/rates.Promedio_Anual_2018_2022
rates.sort_values('Ratio_Post_Pre').to_csv(REPORTS_PATH/'estabilidad_territorial_periodos.csv',encoding='utf-8-sig')
display(rates.sort_values('Ratio_Post_Pre').round(3))
print('Ratio ciudad:',round((rates['2023–2024'].sum()/2)/(rates['2018–2022'].sum()/5),3))"""),
md("""## Conclusión

El análisis completa el componente espacial de la actividad 3.1 mediante control de coordenadas, distribución anual por localidad, densidad puntual, centros territoriales y cuadrículas de concentración. Las concentraciones son descriptivas y no deben interpretarse como efectos causales. La comparación territorial de periodos permite verificar si el universo con víctimas conserva una cobertura espacial razonablemente estable después de 2022.""")
]

tune_cells = [
md("""# 04C · Ajuste de hiperparámetros con validación temporal
## Actividad 4.2 del cronograma

Se optimiza Random Forest exclusivamente con cortes temporales dentro de 2018–2022. **2023–2024 no participa en la selección** y se usa solo para confirmación retrospectiva. El criterio principal es Average Precision media; el umbral se selecciona después con predicciones fuera de muestra de 2020–2022."""),
md("## 1. Configuración, datos y funciones"),
code("""from pathlib import Path
import json, platform, time
import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score,roc_auc_score,f1_score,precision_score,recall_score,balanced_accuracy_score,confusion_matrix,brier_score_loss

plt.style.use('seaborn-v0_8-whitegrid'); RANDOM_STATE=42
DATA_FILE=Path('../data/processed/dataset_victimas_localidad_franja_fecha.parquet')
MODELS_PATH=Path('../models/victimas'); REPORTS_PATH=Path('../reports/tuning_victimas')
MODELS_PATH.mkdir(parents=True,exist_ok=True); REPORTS_PATH.mkdir(parents=True,exist_ok=True)
dataset=pd.read_parquet(DATA_FILE); dataset['Fecha_Acc']=pd.to_datetime(dataset.Fecha_Acc)
cat_cols=['Localidad','Franja_Horaria','Dia_Semana']
num_cols=['Mes','Es_Fin_de_Semana','Es_Festivo','Accidentes_Prom_7d','Accidentes_Prom_30d','Accidentes_Semana_Anterior','Sin_Historial_Accidentes_Prom_7d','Sin_Historial_Accidentes_Prom_30d','Sin_Historial_Accidentes_Semana_Anterior']
feature_cols=cat_cols+num_cols; group_cols=['Localidad','Franja_Horaria']

def label_from_past(train,val):
    th=train.groupby(group_cols,observed=True).Num_Accidentes.quantile(2/3).rename('Umbral').reset_index()
    a=train.merge(th,on=group_cols,how='left'); b=val.merge(th,on=group_cols,how='left')
    return a,b,(a.Num_Accidentes>a.Umbral).astype(int),(b.Num_Accidentes>b.Umbral).astype(int)
def pipeline(params):
    prep=ColumnTransformer([('cat',OneHotEncoder(handle_unknown='ignore'),cat_cols)],remainder='passthrough')
    return Pipeline([('preprocesador',prep),('modelo',RandomForestClassifier(random_state=RANDOM_STATE,n_jobs=-1,**params))])
def calc(y,p,s):
    tn,fp,fn,tp=confusion_matrix(y,p,labels=[0,1]).ravel()
    return dict(Average_Precision=average_precision_score(y,s),AUC_ROC=roc_auc_score(y,s),F1=f1_score(y,p,zero_division=0),Precision=precision_score(y,p,zero_division=0),Recall=recall_score(y,p,zero_division=0),Balanced_Accuracy=balanced_accuracy_score(y,p),Brier=brier_score_loss(y,s),TN=tn,FP=fp,FN=fn,TP=tp)
print(dataset.shape, dataset.Fecha_Acc.min(), dataset.Fecha_Acc.max())"""),
md("## 2. Espacio de búsqueda acotado y justificable"),
code("""candidates=[
 {'n_estimators':200,'max_depth':12,'min_samples_leaf':20,'max_features':'sqrt','class_weight':'balanced'},
 {'n_estimators':300,'max_depth':8,'min_samples_leaf':20,'max_features':'sqrt','class_weight':'balanced'},
 {'n_estimators':300,'max_depth':16,'min_samples_leaf':20,'max_features':'sqrt','class_weight':'balanced'},
 {'n_estimators':300,'max_depth':None,'min_samples_leaf':20,'max_features':'sqrt','class_weight':'balanced'},
 {'n_estimators':300,'max_depth':12,'min_samples_leaf':10,'max_features':'sqrt','class_weight':'balanced'},
 {'n_estimators':300,'max_depth':12,'min_samples_leaf':40,'max_features':'sqrt','class_weight':'balanced'},
 {'n_estimators':300,'max_depth':12,'min_samples_leaf':20,'max_features':0.5,'class_weight':'balanced'},
 {'n_estimators':300,'max_depth':12,'min_samples_leaf':20,'max_features':'sqrt','class_weight':'balanced_subsample'},
]
param_table=pd.DataFrame(candidates); param_table.index.name='Candidato'; display(param_table)"""),
md("## 3. Búsqueda con cortes expansivos"),
code("""folds=[(2019,2020),(2020,2021),(2021,2022)]; rows=[]
start=time.time()
for cid,params in enumerate(candidates):
    for train_end,val_year in folds:
        train=dataset[dataset.Fecha_Acc.dt.year<=train_end].copy(); val=dataset[dataset.Fecha_Acc.dt.year==val_year].copy()
        train,val,ytr,yv=label_from_past(train,val)
        model=pipeline(params); model.fit(train[feature_cols],ytr)
        score=model.predict_proba(val[feature_cols])[:,1]; pred=(score>=.5).astype(int)
        rows.append({'Candidato':cid,'Train_Hasta':train_end,'Validacion':val_year,**params,**calc(yv,pred,score)})
    print(f'Candidato {cid+1}/{len(candidates)} terminado')
results=pd.DataFrame(rows); results.to_csv(REPORTS_PATH/'busqueda_temporal_detalle.csv',index=False,encoding='utf-8-sig')
summary=(results.groupby('Candidato').agg(AP_Media=('Average_Precision','mean'),AP_Std=('Average_Precision','std'),AUC_Media=('AUC_ROC','mean'),F1_Medio=('F1','mean'),Recall_Medio=('Recall','mean'),Brier_Medio=('Brier','mean')).join(param_table))
summary=summary.sort_values(['AP_Media','AP_Std'],ascending=[False,True]); summary.to_csv(REPORTS_PATH/'busqueda_temporal_resumen.csv',encoding='utf-8-sig')
best_id=int(summary.index[0]); best_params=candidates[best_id]
print(f'Duración: {(time.time()-start)/60:.1f} min | Mejor candidato: {best_id}'); display(summary.round(4))"""),
md("## 4. Comparación y estabilidad del ajuste"),
code("""fig,axes=plt.subplots(1,2,figsize=(14,5))
plot=results.pivot(index='Validacion',columns='Candidato',values='Average_Precision')
plot.plot(marker='o',ax=axes[0]); axes[0].set(title='Average Precision por corte',ylabel='Average Precision',xticks=[2020,2021,2022])
axes[1].bar(summary.index.astype(str),summary.AP_Media,yerr=summary.AP_Std,color=['#0C6E8A' if i==best_id else '#A8C5D1' for i in summary.index],capsize=4)
axes[1].set(title='Promedio y variación temporal',xlabel='Candidato',ylabel='Average Precision')
plt.tight_layout(); plt.savefig(REPORTS_PATH/'01_busqueda_hiperparametros.png',dpi=170,bbox_inches='tight'); plt.show()"""),
md("## 5. Predicciones fuera de muestra y selección del umbral"),
code("""oof=[]
for train_end,val_year in folds:
    train=dataset[dataset.Fecha_Acc.dt.year<=train_end].copy(); val=dataset[dataset.Fecha_Acc.dt.year==val_year].copy()
    train,val,ytr,yv=label_from_past(train,val); model=pipeline(best_params); model.fit(train[feature_cols],ytr)
    score=model.predict_proba(val[feature_cols])[:,1]
    oof.append(pd.DataFrame({'Fecha_Acc':val.Fecha_Acc.to_numpy(),'Localidad':val.Localidad.to_numpy(),'Franja_Horaria':val.Franja_Horaria.to_numpy(),'Alto_Riesgo':yv.to_numpy(),'Score':score}))
oof=pd.concat(oof,ignore_index=True); threshold_rows=[]
for threshold in np.linspace(.05,.95,181): threshold_rows.append({'Umbral':threshold,**calc(oof.Alto_Riesgo,(oof.Score>=threshold).astype(int),oof.Score)})
thresholds=pd.DataFrame(threshold_rows); best_threshold=float(thresholds.loc[thresholds.F1.idxmax(),'Umbral'])
oof.to_parquet(REPORTS_PATH/'predicciones_oof_mejor_configuracion.parquet',index=False); thresholds.to_csv(REPORTS_PATH/'seleccion_umbral.csv',index=False,encoding='utf-8-sig')
print('Umbral temporal seleccionado:',best_threshold); display(thresholds.loc[(thresholds.Umbral-best_threshold).abs().nsmallest(5).index].round(4))
plt.figure(figsize=(9,5));
for metric in ['F1','Precision','Recall']: plt.plot(thresholds.Umbral,thresholds[metric],label=metric)
plt.axvline(best_threshold,color='black',ls='--',label=f'Seleccionado {best_threshold:.3f}'); plt.xlabel('Umbral'); plt.ylabel('Métrica'); plt.legend(); plt.tight_layout()
plt.savefig(REPORTS_PATH/'02_seleccion_umbral.png',dpi=170,bbox_inches='tight'); plt.show()"""),
md("## 6. Entrenamiento final y confirmación retrospectiva"),
code("""train=dataset[dataset.Periodo=='train'].copy(); test=dataset[dataset.Periodo=='test'].copy()
final_model=pipeline(best_params); final_model.fit(train[feature_cols],train.Alto_Riesgo.astype(int))
test_score=final_model.predict_proba(test[feature_cols])[:,1]; test_pred=(test_score>=best_threshold).astype(int)
test_metrics=pd.DataFrame([{'Modelo':'Random Forest ajustado','Umbral':best_threshold,**calc(test.Alto_Riesgo,test_pred,test_score)}])
test_metrics.to_csv(REPORTS_PATH/'confirmacion_retrospectiva_2023_2024.csv',index=False,encoding='utf-8-sig'); display(test_metrics.round(4))
joblib.dump(final_model,MODELS_PATH/'pipeline_random_forest_ajustado_victimas.pkl')
metadata={'seleccion_sin_test':True,'criterio':'Mayor Average Precision media 2020–2022','mejor_candidato':best_id,'hiperparametros':best_params,'umbral_temporal':best_threshold,'metricas_test_retro':test_metrics.iloc[0].to_dict(),'version_python':platform.python_version(),'version_sklearn':sklearn.__version__}
(MODELS_PATH/'metadata_random_forest_ajustado.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
print('Modelo ajustado guardado sin reemplazar el pipeline anterior.')"""),
md("""## Conclusión

La configuración se eligió exclusivamente con validación temporal 2020–2022. El resultado 2023–2024 es una confirmación retrospectiva y no interviene en la selección. Debe compararse el incremento de Average Precision frente al candidato base con su variación entre años: una diferencia mínima no justifica afirmar superioridad concluyente.""")
]

for name,cells in [('02B_EDA_y_Analisis_Espacial_Con_Victimas.ipynb',eda_cells),('04C_Ajuste_Hiperparametros_Con_Victimas.ipynb',tune_cells)]:
    nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.12'}})
    nbf.write(nb,NB/name)
    print('Creado',NB/name)
