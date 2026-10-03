"""Regresiones de la identidad visual teal/navy del dashboard."""
import json
from pathlib import Path
import re
import unittest

import pandas as pd
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
        variables=dict(re.findall(r'--([\w-]+):\s*(#[0-9a-fA-F]{6})',css))
        self.assertIn('background:var(--alert-high-bg)',css)
        self.assertIn('color:var(--alert-high)',css)
        self.assertGreaterEqual(_contrast(variables['alert-high'],variables['alert-high-bg']),4.5)
        self.assertGreaterEqual(_contrast(variables['focus'],'#ffffff'),3)


if __name__ == '__main__':
    unittest.main()
