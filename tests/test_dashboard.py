"""Pruebas con fixtures: se ejecutan también sin descargar el Excel LFS."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
import dashboard.app as app_module
import dashboard.data as data_module
from dashboard.data import (DashboardData, preparar_actores, preparar_base_historica,
                            resumen_metricas, normalize, KEYS, REPORTS, SLOTS)
from dashboard.app import (create_app, create_startup_error_app, query_result,
                           history_result, evaluation_result)
from dashboard.app import label_explanation, weakest_slot_warning
from plotly.utils import PlotlyJSONEncoder
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
    grid=preparar_base_historica(pd.DataFrame(rows))
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

    def callback_key(self,prefix):
        return next(key for key in self.app.callback_map if key.startswith(prefix))

    def assert_startup_error_visible(self,message):
        app=create_startup_error_app(message)
        client=app.server.test_client()
        layout=client.get('/_dash-layout')
        self.assertEqual(layout.status_code,200)
        body=json.dumps(layout.get_json(),ensure_ascii=False)
        self.assertIn(message,body)
        self.assertNotIn('Traceback',body)
        self.assertEqual(client.get('/healthz').status_code,503)

    def test_servidor_layout_salud_y_activos(self):
        for path in ['/','/_dash-layout','/_dash-dependencies','/healthz','/assets/dashboard.css']:
            self.assertEqual(self.client.get(path).status_code,200)
        self.assertEqual(self.client.get('/healthz').json['modelo'],REGISTRO['id_modelo'])

    def test_tema_local_bootstrap_y_callbacks_clientside(self):
        layout=json.dumps(self.client.get('/_dash-layout').get_json(),ensure_ascii=False)
        self.assertIn('theme-store',layout)
        self.assertIn('storage_type',layout)
        self.assertIn('local',layout)
        self.assertIn('"data": "dark"',layout)
        self.assertIn('theme-toggle',layout)
        self.assertIn('Cambiar a modo claro',layout)
        clientside=[item for item in self.app._callback_list if item.get('clientside_function')]
        self.assertEqual(len(clientside),2)
        self.assertTrue(any(item['output']=='theme-store.data' for item in clientside))
        self.assertTrue(any('theme-toggle.aria-label' in item['output'] for item in clientside))
        self.assertIn("localStorage.getItem('theme-store')",self.app.index_string)
        self.assertLess(self.app.index_string.index('theme-bootstrap'),
                        self.app.index_string.index('{%app_entry%}'))

    def test_cambio_tema_recolorea_mapa_sin_inferencia(self):
        key=self.callback_key('..query-map.figure')
        with patch.object(self.s.consulta.modelo,'predecir',wraps=self.s.consulta.modelo.predecir) as predict:
            result=self.call(key,['2023-01-01','Mañana','KENNEDY','urbana','dark'],
                             changed=['theme-store.data'])
        self.assertEqual(predict.call_count,0)
        figure=result['query-map']['figure']
        self.assertEqual(figure['layout']['paper_bgcolor'],charts.THEME_PALETTES['dark']['map-paper'])
        self.assertEqual(figure['data'][0]['colorscale'],charts.THEME_PALETTES['dark']['map_colors'])

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
        result=self.call(key,['2023-01-01','Mañana','KENNEDY','urbana','light'])
        self.assertEqual(result['query-error']['children'],'')
        self.assertEqual(result['query-map']['figure']['layout']['map']['style'],'white-bg')
        result=self.call(key,['2025-01-01','Mañana','KENNEDY','urbana','light'])
        self.assertTrue(result['query-error']['children'])
        self.assertEqual(result['query-detail']['children'],[])

    def test_query_result_valida_antes_de_iloc(self):
        with patch.object(self.s.consulta,'consultar',return_value=pd.DataFrame()):
            with self.assertRaisesRegex(ValueError,'no devolvió'):
                query_result(self.s,'2023-01-01','Mañana','KENNEDY','urbana')
        selected=self.s.consulta.consultar('2023-01-01','KENNEDY','Mañana')
        with patch.object(self.s.consulta,'consultar',return_value=selected), \
             patch.object(self.s,'map_rows',return_value=pd.DataFrame({'Localidad':['SUMAPAZ']})):
            with self.assertRaisesRegex(ValueError,'predicción congelada'):
                query_result(self.s,'2023-01-01','Mañana','KENNEDY','urbana')

    def test_cu01_ejecuta_una_sola_inferencia(self):
        with patch.object(self.s.consulta.modelo,'predecir',wraps=self.s.consulta.modelo.predecir) as predict:
            query_result(self.s,'2023-01-01','Mañana','KENNEDY','urbana')
        self.assertEqual(predict.call_count,1)

    def test_historia_usa_columnas_precalculadas_sin_reconvertir_fechas(self):
        before=self.s.consulta.datos.copy(deep=True)
        with patch.object(data_module.pd,'to_datetime',side_effect=AssertionError('reconversión')):
            result=self.s.history(2023,'KENNEDY','Mañana','Todos')
        self.assertFalse(result.empty)
        pd.testing.assert_frame_equal(self.s.consulta.datos,before)

    def test_click_mapa_selecciona_localidad(self):
        result=self.call('query-locality.value',[{'points':[{'location':'SUMAPAZ'}]}])
        self.assertEqual(result['query-locality']['value'],'SUMAPAZ')

    def test_callbacks_historia_y_evaluacion(self):
        for prefix,values,error in [('..history-kpis',[2023,'KENNEDY','Mañana','Peatón'],'history-error'),
                                     ('..eval-kpis',[2023,'KENNEDY','Mañana'],'eval-error')]:
            key=next(k for k in self.app.callback_map if k.startswith(prefix))
            response=self.call(key,[*values,'light'])
            self.assertEqual(response[error]['children'],'')
            self.assertTrue(any(name.endswith('-accessible') and value.get('aria-label')
                                for name,value in response.items()))

    def test_descargas_recalculadas_con_trazabilidad(self):
        result=self.call('download-query.data',[1],['2023-01-01','KENNEDY','Mañana'])
        row=json.loads(result['download-query']['data']['content'])[0]
        self.assertEqual(row['Id_Modelo'],REGISTRO['id_modelo'])
        for key,states,required in [('download-map.data',['2023-01-01','Mañana'],'Advertencia_Score'),
                                    ('download-history.data',[2023,'KENNEDY','Mañana','Peatón'],'Descriptivo'),
                                    ('download-eval.data',[2023,'KENNEDY','Mañana'],'Id_Modelo')]:
            result=self.call(key,[1],states)
            self.assertIn(required,result[key.split('.')[0]]['data']['content'])

    def test_descargas_invalidas_se_deshabilitan_con_mensaje(self):
        cases=[
            ('..download-query-button.disabled',['2025-01-01','KENNEDY','Mañana'],'download-query-button','download-query-status'),
            ('..download-map-button.disabled',['2023-01-01','ZZZ'],'download-map-button','download-map-status'),
            ('..download-history-button.disabled',[2025,'Todas','Todas','Todos'],'download-history-button','download-history-status'),
            ('..download-eval-button.disabled',[2022,'Todas','Todas'],'download-eval-button','download-eval-status'),
        ]
        for prefix,values,button,status in cases:
            with self.subTest(prefix=prefix):
                result=self.call(self.callback_key(prefix),values)
                self.assertTrue(result[button]['disabled'])
                self.assertIn('Descarga no disponible',result[status]['children'])
        enabled=self.call(self.callback_key('..download-query-button.disabled'),
                          ['2023-01-01','KENNEDY','Mañana'])
        self.assertFalse(enabled['download-query-button']['disabled'])
        self.assertEqual(enabled['download-query-status']['children'],'')

    def test_aria_live_y_descripciones_de_graficos(self):
        for page in ['query','history','evaluation']:
            body=json.dumps(self.call('page-content.children',[page]),ensure_ascii=False)
            self.assertIn('aria-live',body)
            self.assertIn('-accessible',body)
            self.assertIn('aria-label',body)
        key=self.callback_key('..query-map.figure')
        result=self.call(key,['2023-01-01','Mañana','KENNEDY','urbana','light'])
        label=result['query-map-accessible']['aria-label']
        self.assertIn('KENNEDY',label)
        self.assertIn('2023-01-01',label)
        self.assertEqual(label,result['query-map-summary']['children'])

    def test_color_de_foco_supera_contraste_tres_a_uno(self):
        def luminance(hex_color):
            values=[int(hex_color.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
            linear=[value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4 for value in values]
            return .2126*linear[0]+.7152*linear[1]+.0722*linear[2]
        def contrast(a,b):
            high,low=sorted([luminance(a),luminance(b)],reverse=True)
            return (high+.05)/(low+.05)
        for theme in ('light','dark'):
            colors=charts.THEME_PALETTES[theme]
            self.assertGreaterEqual(contrast(colors['focus'],colors['surface']),3)
            self.assertGreaterEqual(contrast(colors['focus'],colors['paper']),3)

    def test_validacion_independiente_opt_in_y_hash_separado(self):
        result=data_module.cargar_validacion_independiente()
        self.assertEqual(result['seleccion']['mejor_candidato'],3)
        self.assertAlmostEqual(result['seleccion']['umbral'],.54)
        with patch.object(data_module,'sha256_archivo',return_value='0'*64):
            with self.assertRaisesRegex(ValueError,'manifiesto complementario'):
                data_module.cargar_validacion_independiente()
        with patch.object(data_module,'MOSTRAR_VALIDACION_INDEPENDIENTE',True):
            loaded=data_module.load_data()
        self.assertEqual(loaded.reports['validacion_independiente']['seleccion']['mejor_candidato'],3)
        self.assertNotIn('validacion_independiente',self.s.reports)
        self.s.reports['validacion_independiente']=result
        with patch.object(data_module,'MOSTRAR_VALIDACION_INDEPENDIENTE',True):
            body=json.dumps(app_module.evaluation_page(self.s),cls=PlotlyJSONEncoder,ensure_ascii=False)
        self.assertIn('Estimación temporal adicional — experimental',body)
        self.assertIn('no sustituye el umbral 0,52 oficial',body.lower())
        self.assertIn('no es una prueba prospectiva ni externa',body)

    def test_contexto_consulta_opt_in_es_territorial_y_global(self):
        with patch.object(app_module,'MOSTRAR_CONTEXTO_LIMITACIONES_CONSULTA',True):
            for locality,required in [('CANDELARIA',['157 positivos globales','0 detectados']),
                                      ('SUMAPAZ',['solo 2 positivos globales','muestra es insuficiente'])]:
                body=json.dumps(query_result(self.s,'2023-01-01','Mañana',locality,'urbana'),
                                cls=PlotlyJSONEncoder,ensure_ascii=False)
                for text in [*required,'Brier','resultados globales de 2023–2024','Revisar la sección Evaluación']:
                    self.assertIn(text,body)

    def test_errores_de_carga_son_legibles_y_renderizables(self):
        errors=[]
        with patch.object(data_module,'_read_json',return_value={}):
            with self.assertRaisesRegex(ValueError,"objeto 'archivos'") as caught:
                data_module.load_data()
            errors.append(str(caught.exception))

        broken=fixture()
        broken.consulta.modelo.registro=copy.deepcopy(broken.registro)
        broken.consulta.modelo.registro['evidencias']=[]
        with patch.object(data_module,'cargar_consulta',return_value=broken.consulta):
            with self.assertRaisesRegex(ValueError,'evidencia única') as caught:
                data_module.load_data()
            errors.append(str(caught.exception))

        manifest=json.loads((ROOT/'data/dashboard/manifest.json').read_text())
        broken_geo={'type':'FeatureCollection','features':[{'type':'Feature','properties':{},
                    'geometry':{'type':'Point','coordinates':[0,0]}}]}
        with patch.object(data_module,'_read_json',side_effect=[manifest,broken_geo]):
            with self.assertRaisesRegex(ValueError,'localidad legible') as caught:
                data_module.load_data()
            errors.append(str(caught.exception))

        for message in errors:
            self.assert_startup_error_visible(message)

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

    def test_interpretacion_del_grupo_usa_solo_train(self):
        for threshold, text in [(0,'al menos un siniestro'),(1,'2 o más siniestros'),(2,'3 o más siniestros')]:
            with self.subTest(threshold=threshold):
                s=fixture()
                train=s.consulta.datos.Periodo.eq('train')
                s.consulta.datos.loc[train,'Num_Accidentes']=threshold
                s.consulta.datos.loc[~train,'Num_Accidentes']=999
                before=s.predictions.copy(deep=True)
                self.assertEqual(s.label_rule('KENNEDY','Mañana')['minimo_siniestros'],threshold+1)
                body=json.dumps(label_explanation(s,'KENNEDY','Mañana'),cls=PlotlyJSONEncoder,ensure_ascii=False)
                self.assertIn(text,body)
                self.assertIn('0,52',body)
                self.assertIn('no confirma',body)
                self.assertNotIn('999',body)
                pd.testing.assert_frame_equal(before,s.predictions)
        with self.assertRaises(ValueError):self.s.label_rule('INEXISTENTE','Mañana')

    def test_aviso_madrugada_deriva_del_reporte_y_declara_alcance(self):
        text=json.dumps(weakest_slot_warning(self.s),cls=PlotlyJSONEncoder,ensure_ascii=False)
        for value in ['Madrugada','39,43','914','2.318','1.404','no cambia con los filtros','no personas']:
            self.assertIn(value,text)
        frame=self.s.reports['metricas_random_forest_ajustado_por_franja']
        frame.loc[frame.Franja_Horaria.eq('Madrugada'),'Recall']=.1
        updated=json.dumps(weakest_slot_warning(self.s),cls=PlotlyJSONEncoder,ensure_ascii=False)
        self.assertIn('10,00',updated)
        self.assertNotIn('39,43',updated)

    def test_callback_consulta_incluye_significado_y_aviso_segun_franja(self):
        key=next(k for k in self.app.callback_map if k.startswith('..query-map'))
        for slot in ['Mañana','Madrugada']:
            response=self.call(key,['2023-01-01',slot,'KENNEDY','urbana','light'])
            body=json.dumps(response['query-detail']['children'],ensure_ascii=False)
            self.assertIn('¿Qué intenta identificar esta alerta?',body)
            self.assertIn('2 o más siniestros',body)
            self.assertEqual('menor recall global' in body,slot=='Madrugada')

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
