"""Verificación del dashboard con artefactos reales, sin servidor ni entrenamiento."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from dashboard.data import load_data, resumen_metricas, FLAGS
from dashboard.app import create_app, query_result, history_result, evaluation_result
from src.rutas import ROOT, sha256_archivo


def verificar():
    start=perf_counter()
    s=load_data()
    protected=[ROOT/e['ruta'] for e in s.registro['evidencias']]
    hashes={str(p):sha256_archivo(p) for p in protected}
    measured={}
    metrics=resumen_metricas(s.predictions)
    for name in ['F1','Precision','Recall','AUC_ROC','Average_Precision','Brier','TN','FP','FN','TP']:
        np.testing.assert_allclose(metrics[name],s.registro['evaluacion']['metricas'][name],atol=1e-12,rtol=0)
    refs=pd.read_csv(ROOT/'reports/eda_victimas/actores_por_localidad.csv')
    for actor in FLAGS:
        df=s.history(actor=actor)
        actual=df.groupby('Localidad').Siniestros.sum().reindex(refs.Localidad)
        np.testing.assert_array_equal(actual.to_numpy(),refs[actor].to_numpy())
    if int(s.history().Siniestros.sum())!=s.registro['datos']['siniestros']:
        raise ValueError('El histórico no coincide con el universo del modelo.')
    for date,slot,loc in [('2023-01-01','Mañana','KENNEDY'),('2024-02-29','Noche','CANDELARIA'),('2024-12-31','Madrugada','SUMAPAZ')]:
        t=perf_counter()
        result=query_result(s,date,slot,loc,'distrito')
        measured[f'consulta_{date}_{loc}']=round(perf_counter()-t,4)
        if len(result[0].data[0].locations)!=20:
            raise ValueError('El mapa no contiene las veinte localidades.')
    for label,fn,args in [('historia_completa',history_result,('Todos','Todas','Todas','Todos')),
                          ('historia_filtrada',history_result,(2024,'KENNEDY','Noche','Peatón')),
                          ('evaluacion_global',evaluation_result,('Todos','Todas','Todas')),
                          ('evaluacion_filtrada',evaluation_result,(2023,'SUMAPAZ','Madrugada'))]:
        t=perf_counter();fn(s,*args);measured[label]=round(perf_counter()-t,4)
    app=create_app(s)
    client=app.server.test_client()
    for path in ['/','/healthz','/_dash-layout','/_dash-dependencies','/assets/dashboard.css']:
        if client.get(path).status_code!=200:
            raise ValueError(f'Fallo HTTP en {path}')
    layout=json.dumps(client.get('/_dash-layout').get_json(),ensure_ascii=False)
    pages=['overview','query','history','evaluation','about']
    if any(f'page-{page}' not in layout for page in pages):
        raise ValueError('El layout no contiene las cinco vistas montadas.')
    if any(sha256_archivo(Path(p))!=h for p,h in hashes.items()):
        raise ValueError('Se modificó una evidencia oficial durante la verificación.')
    return {'resultado':'correcto','modelo':s.registro['id_modelo'],'paginas_verificadas':pages,
            'predicciones':len(s.predictions),'localidades_mapa':len(s.geojson['features']),
            'conteos_actores_coinciden_con_eda':True,'metricas_globales_coinciden_con_05B':True,
            'evidencias_oficiales_intactas':len(hashes),'tiempos_servidor_segundos':measured,
            'operaciones_medidas_menores_5s':all(t<5 for t in measured.values()),
            'nota_rendimiento':'Medición local del cálculo de vista; no incluye navegador, arranque ni red.',
            'duracion_total_segundos':round(perf_counter()-start,3),'modelos_reentrenados':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--salida',type=Path)
    args=parser.parse_args()
    if args.salida and args.salida.exists():
        parser.error('El informe ya existe. Elija otro nombre.')
    result={'fecha_utc':datetime.now(timezone.utc).isoformat(),**verificar()}
    if args.salida:
        args.salida.parent.mkdir(parents=True,exist_ok=True)
        with args.salida.open('x',encoding='utf-8') as stream:
            json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False,indent=2))
