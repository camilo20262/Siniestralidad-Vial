"""Regresiones de la identidad visual teal/navy del dashboard."""
import json
import inspect
from pathlib import Path
import re
import unittest

import pandas as pd
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from dashboard import charts
from dashboard.app import graph, kpi, panel
from dashboard.data import DAYS, SLOTS
from src.rutas import ROOT


def _relative_luminance(color):
    rgb=[int(color[index:index+2],16)/255 for index in (1,3,5)]
    channels=[value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4
              for value in rgb]
    return .2126*channels[0]+.7152*channels[1]+.0722*channels[2]


def _contrast(first, second):
    light,dark=sorted((_relative_luminance(first),_relative_luminance(second)),reverse=True)
    return (light+.05)/(dark+.05)


class DashboardVisualTest(unittest.TestCase):
    def test_tema_claro_conserva_paleta_y_oscuro_es_explicito(self):
        light=charts.THEME_PALETTES['light']
        self.assertEqual({key:light[key] for key in ('ink','muted','teal','paper','line','gold','focus','alert-high','alert-high-bg')},{
            'ink':'#172d3e','muted':'#647580','teal':'#137c78','paper':'#f5f6f3',
            'line':'#e1e7e6','gold':'#d7942d','focus':'#b06f14',
            'alert-high':'#98463f','alert-high-bg':'#f8e9e6'})
        css=(Path(ROOT)/'dashboard/assets/dashboard.css').read_text(encoding='utf-8')
        self.assertIn(':root[data-theme="light"]',css)
        self.assertIn(':root[data-theme="dark"]',css)
        self.assertNotIn('prefers-color-scheme',css)

    def test_franjas_conservan_colores_consistentes(self):
        frame=pd.DataFrame({'Franja_Horaria':SLOTS,'Siniestros':[3,5,7,4]})
        figure=charts.bars(frame,'Franja_Horaria','Siniestros')
        self.assertEqual(list(figure.data[0].marker.color),
                         [charts.SLOT_COLORS[slot] for slot in SLOTS])

    def test_heatmap_usa_celdas_redondeadas_y_leyenda_simple(self):
        rows=[]
        for day_index,day in enumerate(DAYS):
            for slot_index,slot in enumerate(SLOTS):
                rows.append({'Fecha_Acc':pd.Timestamp('2024-01-01')+pd.Timedelta(days=day_index),
                             'Dia_Num':day_index,'Franja_Horaria':slot,
                             'Siniestros':day_index+slot_index})
        figure=charts.day_heatmap(pd.DataFrame(rows))
        paths=[shape for shape in figure.layout.shapes if shape.type == 'path']
        labels={annotation.text for annotation in figure.layout.annotations}
        self.assertEqual(len(paths),len(DAYS)*len(SLOTS))
        self.assertFalse(any(trace.type == 'heatmap' for trace in figure.data))
        self.assertTrue({'Menos','Más'}.issubset(labels))

    def test_mapa_y_matriz_comparten_escala_teal_navy(self):
        self.assertGreaterEqual(len(charts.MAP_COLORS),9)
        self.assertEqual(charts.confusion({'Observaciones':10,'TN':3,'FP':1,'FN':2,'TP':4}).data[0].colorscale,
                         tuple((position,color) for position,color in charts.MAP_COLORS))

    def test_tarjetas_paneles_y_graficos_exponen_identidad_accesible(self):
        components=[kpi('Siniestros registrados','10','Selección actual'),
                    panel('Mapa de priorización','Resultados por localidad','Contenido'),
                    graph('query-map')]
        rendered=json.dumps(components,cls=PlotlyJSONEncoder,ensure_ascii=False)
        self.assertIn('icon-badge',rendered)
        self.assertIn('data:image/svg+xml,',rendered)
        self.assertIn('graph-accessible',rendered)
        self.assertIn('Mapa de priorización por localidad',rendered)

    def test_alerta_alta_y_foco_tienen_contraste_suficiente(self):
        css=(Path(ROOT)/'dashboard/assets/dashboard.css').read_text(encoding='utf-8')
        self.assertIn('background:var(--alert-high-bg)',css)
        self.assertIn('color:var(--alert-high)',css)
        for colors in charts.THEME_PALETTES.values():
            self.assertGreaterEqual(_contrast(colors['alert-high'],colors['alert-high-bg']),4.5)
            self.assertGreaterEqual(_contrast(colors['focus'],colors['surface']),3)

    def test_contrastes_del_tema_oscuro(self):
        colors=charts.THEME_PALETTES['dark']
        normal=[('ink','paper'),('ink','surface'),('muted','paper'),('muted','surface'),
                ('teal','paper'),('teal','surface'),('header-tag-text','header-tag-bg'),
                ('pill-text','pill-bg'),('pill-neutral-text','pill-neutral-bg'),
                ('notice-text','notice-bg'),('warning-text','warning-bg'),
                ('low-text','low-bg'),('disabled-text','disabled-bg'),
                ('table-head-text','table-head-bg')]
        for foreground,background in normal:
            with self.subTest(pair=f'{foreground}/{background}'):
                self.assertGreaterEqual(_contrast(colors[foreground],colors[background]),4.5)
        for background in ('paper','surface'):
            self.assertGreaterEqual(_contrast(colors['focus'],colors[background]),3)
        self.assertGreaterEqual(_contrast(colors['on-accent'],colors['teal']),4.5)
        for color in colors['slot_colors'].values():
            self.assertGreaterEqual(_contrast(color,colors['surface']),3)
        for endpoint in ('map-0','map-9'):
            self.assertGreaterEqual(_contrast(colors[endpoint],colors['map-paper']),3)

    def test_controles_del_calendario_oscuro_son_legibles(self):
        colors=charts.THEME_PALETTES['dark']
        required=('Dash-Text-Primary','Dash-Fill-Primary-Hover',
                  'Dash-Fill-Primary-Active','Dash-Stroke-Weak')
        for token in required:
            self.assertIn(token,colors)
        self.assertGreaterEqual(
            _contrast(colors['Dash-Text-Primary'],colors['Dash-Fill-Inverse-Strong']),
            4.5)
        self.assertNotEqual(colors['Dash-Fill-Primary-Hover'],
                            colors['Dash-Fill-Inverse-Strong'])
        self.assertNotEqual(colors['Dash-Fill-Primary-Active'],
                            colors['Dash-Fill-Inverse-Strong'])

    def test_todas_las_figuras_aceptan_tema_y_recolorean_fondo(self):
        functions=[charts.finish,charts.empty,charts.line,charts.bars,charts.map_figure,
                   charts.detection_by_group,charts.day_heatmap,charts.confusion,
                   charts.curves,charts.calibration]
        for function in functions:
            self.assertIn('theme',inspect.signature(function).parameters,function.__name__)

        frame=pd.DataFrame({'x':[1,2],'y':[2,3]})
        for factory in (lambda theme:charts.finish(go.Figure(),theme=theme),
                        lambda theme:charts.empty(theme=theme),
                        lambda theme:charts.line(frame,'x','y',theme=theme),
                        lambda theme:charts.bars(frame,'x','y',theme=theme)):
            light=factory('light');dark=factory('dark')
            self.assertEqual(light.layout.paper_bgcolor,'#ffffff')
            self.assertEqual(dark.layout.paper_bgcolor,'#122630')
            self.assertNotEqual(light.layout.font.color,dark.layout.font.color)

        slots=pd.DataFrame({'Franja_Horaria':SLOTS,'Siniestros':[1,2,3,4]})
        dark=charts.bars(slots,'Franja_Horaria','Siniestros',theme='dark')
        self.assertEqual(list(dark.data[0].marker.color),
                         [charts.THEME_PALETTES['dark']['slot_colors'][slot] for slot in SLOTS])

        grid=pd.DataFrame([{'Fecha_Acc':pd.Timestamp('2024-01-01')+pd.Timedelta(days=day),
                            'Dia_Num':day,'Franja_Horaria':slot,'Siniestros':day+index}
                           for day in range(7) for index,slot in enumerate(SLOTS)])
        detection=pd.DataFrame({'Franja_Horaria':SLOTS,'Recall':[.2,.4,.6,.8],
                                'TP':[1,2,3,4],'FN':[4,3,2,1],'Positivos':[5]*4})
        metrics={'Observaciones':10,'TN':3,'FP':1,'FN':2,'TP':4}
        curve_rows=pd.DataFrame({'Alto_Riesgo':[0,1,0,1],'Score':[.1,.8,.3,.6]})
        class Service:
            geojson={'type':'FeatureCollection','features':[{'type':'Feature',
                'properties':{'Localidad':'KENNEDY'},'geometry':{'type':'Polygon',
                'coordinates':[[[-74.1,4.6],[-74.1,4.7],[-74.2,4.7],[-74.1,4.6]]]}}]}
        map_rows=pd.DataFrame({'Localidad':['KENNEDY'],'Score_Priorizacion':[.7],
                               'Alerta_Modelo':[1],'Umbral_Score':[.52]})
        pairs=[(charts.map_figure(Service(),map_rows,'KENNEDY','urbana','light'),
                charts.map_figure(Service(),map_rows,'KENNEDY','urbana','dark')),
               (charts.detection_by_group(detection,'Franja_Horaria',theme='light'),
                charts.detection_by_group(detection,'Franja_Horaria',theme='dark')),
               (charts.day_heatmap(grid,'light'),charts.day_heatmap(grid,'dark')),
               (charts.confusion(metrics,'light'),charts.confusion(metrics,'dark')),
               (charts.calibration(curve_rows,'light'),charts.calibration(curve_rows,'dark'))]
        light_curves=charts.curves(curve_rows,'light');dark_curves=charts.curves(curve_rows,'dark')
        pairs.extend(zip(light_curves,dark_curves))
        for light,dark in pairs:
            self.assertNotEqual(light.layout.paper_bgcolor,dark.layout.paper_bgcolor)
            self.assertNotEqual(light.layout.font.color,dark.layout.font.color)


if __name__ == '__main__':
    unittest.main()
