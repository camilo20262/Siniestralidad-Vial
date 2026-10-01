"""Pruebas con fixtures: se ejecutan también sin descargar el Excel LFS."""
import copy
import json
from pathlib import Path
import unittest

import pandas as pd
from dashboard.data import DashboardData, preparar_actores, resumen_metricas, normalize, KEYS, REPORTS, SLOTS
from dashboard.app import create_app, query_result, history_result, evaluation_result
from dashboard import charts
from src.consulta_retrospectiva import ConsultaRetrospectiva
from src.modelo_principal import ModeloPrincipal
from src.rutas import ROOT
from test_modelo_principal import PipelineFalso, REGISTRO


def fixture():
    reg=copy.deepcopy(REGISTRO)
    rows=[]
    for loc in reg['categorias']['Localidad']:
        for date in ['2018-01-01','2023-01-01','2023-01-02','2024-02-29']:
            for slot in SLOTS:
                row=dict.fromkeys(reg['variables'],0)
                row.update(Localidad=loc,Franja_Horaria=slot,Dia_Semana='Monday',Mes=1,
                           Fecha_Acc=date,Periodo='train' if date.startswith('2018') else 'test',
                           Num_Accidentes=1,Alto_Riesgo=int(slot=='Mañana'))
                rows.append(row)
    grid=pd.DataFrame(rows)
    model=ModeloPrincipal(PipelineFalso(),reg)
    pred=grid[grid.Periodo.eq('test')][KEYS+['Alto_Riesgo']].copy()
    pred['Score']=.5199
    pred['Prediccion']=0
    pred['Fecha_Acc']=pd.to_datetime(pred.Fecha_Acc)
    actors=grid[(grid.Localidad=='KENNEDY') & (grid.Franja_Horaria=='Mañana')][KEYS].copy()
    actors['Fecha_Acc']=pd.to_datetime(actors.Fecha_Acc)
    actors=actors.assign(Siniestros=1,Actor='Peatón')
    geo={'type':'FeatureCollection','features':[{'type':'Feature','properties':{'Localidad':loc},
          'geometry':{'type':'Polygon','coordinates':[[[-74.1,4.6],[-74.1,4.7],[-74.2,4.7],[-74.1,4.6]]]}}
          for loc in reg['categorias']['Localidad']]}
    reports={name:pd.read_csv(ROOT/f'reports/evaluation_victimas/{name}.csv') for name in REPORTS}
    return DashboardData(ConsultaRetrospectiva(model,grid),pred,actors,geo,reports,{})


class DashboardTest(unittest.TestCase):
    def setUp(self):
        self.s=fixture()
        self.app=create_app(self.s)
        self.client=self.app.server.test_client()

    def call(self,key,inputs,states=None,changed=None):
        callback=self.app.callback_map[key]
        outputs=callback['output']
        outputs=[{'id':o.component_id,'property':o.component_property} for o in outputs] if isinstance(outputs,list) else {'id':outputs.component_id,'property':outputs.component_property}
        result=self.client.post('/_dash-update-component',json={'output':key,'outputs':outputs,
            'inputs':[dict(spec,value=value) for spec,value in zip(callback['inputs'],inputs)],
            'state':[dict(spec,value=value) for spec,value in zip(callback['state'],states or [])],
            'changedPropIds':changed or [f"{callback['inputs'][0]['id']}.{callback['inputs'][0]['property']}"]})
        self.assertEqual(result.status_code,200,result.data[:500])
        return result.json['response']

    def test_servidor_layout_salud_y_activos(self):
        for path in ['/','/_dash-layout','/_dash-dependencies','/healthz','/assets/dashboard.css']:
            self.assertEqual(self.client.get(path).status_code,200)
        self.assertEqual(self.client.get('/healthz').json['modelo'],REGISTRO['id_modelo'])

    def test_cinco_paginas_serializan_sin_listas_anidadas(self):
        def walk(value):
            if isinstance(value,dict):
                children=value.get('props',{}).get('children')
                if isinstance(children,list):
                    self.assertFalse(any(isinstance(x,list) for x in children))
                for v in value.values():walk(v)
            elif isinstance(value,list):
                for v in value:walk(v)
        for page in ['overview','query','history','evaluation','about']:
            with self.subTest(page=page):
                walk(self.call('page-content.children',[page]))

    def test_mapa_20_localidades_sin_etiquetas_observadas(self):
        result=self.s.map_rows('2023-01-01','Mañana')
        self.assertEqual(len(result),20)
        self.assertNotIn('Alto_Riesgo',result)
        self.assertEqual(result.Id_Modelo.nunique(),1)
        self.assertTrue(result.Advertencia_Score.str.contains('no una probabilidad calibrada').all())
        self.assertTrue(result.Alerta_Modelo.eq(0).all())

    def test_fechas_y_filtros_invalidos(self):
        for date in ['2022-12-31','2025-01-01','no-fecha',None]:
            with self.subTest(date=date),self.assertRaises(ValueError):self.s.map_rows(date,'Noche')
        for args in [(2025,'Todas','Todas','Todos'),('Todos','ZZZ','Todas','Todos'),('Todos','Todas','Todas','ZZZ')]:
            with self.subTest(args=args),self.assertRaises(ValueError):self.s.history(*args)
        with self.assertRaises(ValueError):self.s.evaluation(2022)

    def test_historico_actor_no_altera_modelo(self):
        before=self.s.predictions.copy(deep=True)
        h=self.s.history(2023,'KENNEDY','Mañana','Peatón')
        self.assertEqual(h.Siniestros.sum(),2)
        self.assertEqual(h.Fecha_Acc.nunique(),2)
        self.assertEqual(self.s.history(2023,'SUMAPAZ','Mañana','Peatón').Siniestros.sum(),0)
        pd.testing.assert_frame_equal(before,self.s.predictions)

    def test_filtro_combinado_evaluacion(self):
        df=self.s.evaluation(2023,'CANDELARIA','Mañana')
        self.assertEqual(len(df),2)
        m=resumen_metricas(df)
        self.assertEqual(m['FN'],2)
        self.assertEqual(m['Recall'],0)
        self.assertIsNone(m['AUC_ROC'])

    def test_metricas_sin_positivos_y_vacias(self):
        m=resumen_metricas(self.s.evaluation(2023,'CANDELARIA','Noche'))
        self.assertIsNone(m['Recall'])
        self.assertIsNone(m['Average_Precision'])
        self.assertIsNone(m['AUC_ROC'])
        self.assertIsNone(resumen_metricas(self.s.predictions.iloc[:0])['F1'])

    def test_callbacks_consulta_y_error(self):
        key=next(k for k in self.app.callback_map if k.startswith('..query-map'))
        result=self.call(key,['2023-01-01','Mañana','KENNEDY','urbana'])
        self.assertEqual(result['query-error']['children'],'')
        self.assertEqual(result['query-map']['figure']['layout']['map']['style'],'white-bg')
        result=self.call(key,['2025-01-01','Mañana','KENNEDY','urbana'])
        self.assertTrue(result['query-error']['children'])
        self.assertEqual(result['query-detail']['children'],[])

    def test_click_mapa_selecciona_localidad(self):
        result=self.call('query-locality.value',[{'points':[{'location':'SUMAPAZ'}]}])
        self.assertEqual(result['query-locality']['value'],'SUMAPAZ')

    def test_callbacks_historia_y_evaluacion(self):
        for prefix,values,error in [('..history-kpis',[2023,'KENNEDY','Mañana','Peatón'],'history-error'),
                                     ('..eval-kpis',[2023,'KENNEDY','Mañana'],'eval-error')]:
            key=next(k for k in self.app.callback_map if k.startswith(prefix))
            self.assertEqual(self.call(key,values)[error]['children'],'')

    def test_descargas_recalculadas_con_trazabilidad(self):
        result=self.call('download-query.data',[1],['2023-01-01','KENNEDY','Mañana'])
        row=json.loads(result['download-query']['data']['content'])[0]
        self.assertEqual(row['Id_Modelo'],REGISTRO['id_modelo'])
        for key,states,required in [('download-map.data',['2023-01-01','Mañana'],'Advertencia_Score'),
                                    ('download-history.data',[2023,'KENNEDY','Mañana','Peatón'],'Descriptivo'),
                                    ('download-eval.data',[2023,'KENNEDY','Mañana'],'Id_Modelo')]:
            result=self.call(key,[1],states)
            self.assertIn(required,result[key.split('.')[0]]['data']['content'])

    def test_conteos_actores_no_excluyentes(self):
        raw=pd.DataFrame({'Codigo_Accidente':[1,2,3],'Fecha_Acc':pd.to_datetime(['2023-01-01']*3),
            'AA_Acc':[2023]*3,'MM_Acc':[1]*3,'Hora_Acc':[7]*3,'Localidad':['KENNEDY']*3,
            'Gravedad_Indicador_Tradicional':['Con Heridos','Con Muertos','Solo Daños'],
            'Con_Moto':['SI','NO','SI'],'Con_Peaton':['SI','SI','NO'],'Con_Bicicleta':['NO','NO','SI']})
        result,events=preparar_actores(raw)
        self.assertEqual(len(events),2)
        self.assertEqual(result.groupby('Actor').Siniestros.sum().to_dict(),{'Motocicleta':1,'Peatón':2})

    def test_normalizacion_tildes(self):
        self.assertEqual(normalize('SAN CRISTÓBAL'),normalize('San Cristobal'))

    def test_deteccion_por_grupo_preserva_conteos(self):
        report=self.s.reports['metricas_random_forest_ajustado_por_localidad']
        fig=charts.detection_by_group(report,'Localidad')
        self.assertEqual(len(fig.data),2)
        self.assertEqual(len(fig.data[0].y),20)
        idx=list(fig.data[0].y).index('CANDELARIA')
        self.assertEqual(fig.data[0].x[idx],0)
        self.assertEqual(fig.data[1].x[idx],1)
        self.assertEqual(fig.data[1].customdata[idx][0],157)
        for a,b in zip(fig.data[0].x,fig.data[1].x):
            self.assertAlmostEqual(a+b,1)

    def test_sumapaz_y_estados_vacios_serializan(self):
        fig,*_=query_result(self.s,'2023-01-01','Noche','SUMAPAZ','urbana')
        self.assertEqual(fig.layout.map.center.lat,4.03)
        result=history_result(self.s,2023,'SUMAPAZ','Noche','Peatón')
        for fig in result[1:]:self.assertIn('Cero siniestros',fig.layout.annotations[0].text)
