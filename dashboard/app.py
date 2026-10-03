"""Aplicación local: python -m dashboard.app. Sin escrituras ni entrenamiento."""
import argparse
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
from dash import Dash, Input, Output, State, dcc, html, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go

from dashboard import charts
from dashboard.data import load_data, resumen_metricas, SLOTS, DAYS, FLAGS

CONFIG = {'displaylogo': False, 'scrollZoom': False,
          'modeBarButtonsToRemove': ['lasso2d', 'select2d', 'sendChartToCloud'],
          'toImageButtonOptions': {'format': 'png', 'filename': 'siniestralidad_bogota'}}

GRAPH_DESCRIPTIONS = {
    'overview-series': 'Serie mensual de siniestros con víctimas entre 2018 y 2024.',
    'overview-localities': 'Comparación de las siete localidades con mayor conteo registrado.',
    'query-map': 'Mapa de priorización por localidad para la selección actual.',
    'history-series': 'Serie mensual de siniestros para los filtros históricos actuales.',
    'history-localities': 'Comparación de localidades para los filtros históricos actuales.',
    'history-heat': 'Mapa de calor por día de semana y franja para los filtros actuales.',
    'history-slots': 'Comparación de franjas horarias para los filtros históricos actuales.',
    'eval-confusion': 'Matriz de clasificación para los filtros de evaluación actuales.',
    'eval-calibration': 'Relación entre score medio y frecuencia observada para la selección.',
    'eval-roc': 'Curva ROC para los filtros de evaluación actuales.',
    'eval-pr': 'Curva de precisión y recall para los filtros de evaluación actuales.',
    'eval-territory-detection': 'Proporción de positivos detectados y omitidos por localidad.',
    'eval-slot-detection': 'Proporción de positivos detectados y omitidos por franja.',
    'eval-importance': 'Importancia por permutación de las variables del modelo principal.',
}

ICON_PATHS = {
    'activity': '<path d="M3 12h4l2-7 4 14 2-7h6"/>',
    'calendar': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/>',
    'chart': '<path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/>',
    'clock': '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    'info': '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    'layers': '<path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 12 9 5 9-5M3 16l9 5 9-5"/>',
    'map': '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Z"/><path d="M9 3v15M15 6v15"/>',
}


def _icon_name(text):
    value=text.lower()
    if any(word in value for word in ('mapa','localidad','territorio','geogr')):
        return 'map'
    if any(word in value for word in ('franja','mes','temporal','calendario','historia')):
        return 'calendar'
    if any(word in value for word in ('tiempo','promedio diario')):
        return 'clock'
    if any(word in value for word in ('modelo','f1','auc','precisión','recall','evaluación',
                                       'aciertos','errores','calibración','curva','compar',
                                       'resultado','detección','importancia')):
        return 'chart'
    if any(word in value for word in ('siniestro','casos','universo')):
        return 'activity'
    if any(word in value for word in ('unidad','variables','identidad','validación')):
        return 'layers'
    return 'info'


def icon(text):
    name=_icon_name(text)
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" '
         f'viewBox="0 0 24 24" fill="none" stroke="#137c78" stroke-width="1.8" '
         f'stroke-linecap="round" stroke-linejoin="round">{ICON_PATHS[name]}</svg>')
    return html.Span(html.Img(src='data:image/svg+xml,'+quote(svg),alt=''),
                     className='icon-badge',**{'aria-hidden':'true'})


def number(value, decimals=0):
    if value is None or pd.isna(value):
        return '—'
    return f'{value:,.{decimals}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def kpi(label, value, note, accent=False):
    return html.Div([html.Div([icon(label),html.Span(label,className='kpi-label')],className='kpi-heading'),
                     html.Strong(value),html.Small(note)],
                    className='kpi accent' if accent else 'kpi')


def intro(kicker, title, description):
    return html.Div([html.P(kicker, className='eyebrow'), html.H1(title), html.P(description, className='lede')],className='page-intro')


def graph(id, figure=None, description=None):
    description=description or GRAPH_DESCRIPTIONS.get(id,'Visualización interactiva del dashboard.')
    component=dcc.Graph(id=id, figure=figure if figure is not None else charts.empty('Cargando selección…'),
                        config=CONFIG, responsive=True,
                        style={'height': 490 if id=='query-map' else (figure.layout.height if figure is not None else 340)})
    return html.Div([component,html.Span(description,id=id+'-summary',className='sr-only')],
                    id=id+'-accessible',className='graph-accessible',role='group',tabIndex=0,
                    title=description,**{'aria-label':description})


def panel(title, subtitle, content, extra=None):
    children = content if isinstance(content,list) else [content]
    heading=html.Div([icon(title),html.Div([html.H2(title),html.P(subtitle)])],className='panel-title')
    return html.Section([html.Div([heading,extra],className='panel-head'),*children],className='panel')


def table(df, labels=None):
    labels = labels or {}
    def cell(value):
        if isinstance(value,(float,np.floating)):
            return number(value,4)
        if isinstance(value,(int,np.integer)):
            return number(value)
        return str(value) if pd.notna(value) else '—'
    return html.Div(html.Table([
        html.Thead(html.Tr([html.Th(labels.get(c,c.replace('_',' ')),scope='col') for c in df.columns])),
        html.Tbody([html.Tr([html.Td(cell(v)) for v in row]) for row in df.itertuples(index=False,name=None)])
    ]),className='table-wrap',tabIndex=0)


def dropdown(id,label,options,value):
    return html.Div([html.Label(label,id=id+'-label',htmlFor=id),
        dcc.Dropdown(id=id,options=options,value=value,clearable=False,persistence=True,persistence_type='session')],
        className='field',role='group',**{'aria-labelledby':id+'-label'})


def notice(text, warning=False):
    return html.Div(text,className='notice warning' if warning else 'notice',role='note')


def label_explanation(s, locality, slot):
    rule=s.label_rule(locality,slot)
    minimum=rule['minimo_siniestros']
    target='al menos un siniestro con víctimas' if minimum==1 else f'{minimum} o más siniestros con víctimas'
    meaning=('Aquí la etiqueta describe ocurrencia, no una frecuencia excepcional.' if minimum==1
             else 'Aquí la etiqueta exige superar el umbral histórico de conteo del grupo.')
    return html.Div([
        html.H3('¿Qué intenta identificar esta alerta?'),
        html.P(['En esta localidad y franja, la etiqueta observada Alto_Riesgo = 1 significa ',html.Strong(target),' en ese día.']),
        html.P(meaning),
        html.P(f"Umbral del conteo: {number(rule['umbral_conteo'],2)}; se exige superarlo, no igualarlo. Se calcula solo con 2018–2022.",className='footnote'),
        html.P(f"Es distinto del umbral del score ({number(s.registro['decision']['umbral_score'],2)}). La alerta es la clasificación del modelo: no confirma que ese número de siniestros haya ocurrido ni indica cuántos ocurrirán.",className='footnote'),
    ],className='label-explanation')


def weakest_slot_warning(s):
    rows=s.reports['metricas_random_forest_ajustado_por_franja']
    valid=rows[rows.Positivos.gt(0) & rows.Recall.notna()]
    if valid.empty:
        return notice('No hay positivos suficientes para comparar el recall por franja.')
    row=valid.loc[valid.Recall.idxmin()]
    return notice([
        html.Strong(f'{row.Franja_Horaria}: menor recall global ({number(row.Recall*100,2)} %)'),
        html.P(f"El modelo detectó {number(row.TP)} de {number(row.Positivos)} casos con etiqueta positiva y omitió {number(row.FN)}. Son casos localidad × fecha × franja, no personas ni siniestros individuales."),
        html.P('Resultado global 2023–2024 para todas las localidades; no cambia con los filtros. No significa que esta franja tenga menor siniestralidad ni explica la causa de las omisiones.'),
    ],True)


def overview(s):
    grid=s.history()
    monthly=grid.groupby('Mes',as_index=False).Siniestros.sum()
    top=grid.groupby('Localidad',as_index=False).Siniestros.sum().nlargest(7,'Siniestros').sort_values('Siniestros')
    return html.Div([
        html.Div([html.Div([html.P('BOGOTÁ D.C. / DATOS QUE CUENTAN',className='eyebrow'),
            html.H1(['Entender el pasado.',html.Br(),html.Span('Explorar las señales.',className='text-teal')]),
            html.P('Siniestros con víctimas, territorio y tiempo. Una herramienta académica para explorar los registros de Bogotá y los resultados de un modelo de priorización.',className='lede'),
            html.Div([html.Span('●  Datos verificados',className='pill'),html.Span('Solo lectura',className='pill neutral')],className='pills')]),
            html.Div([html.Span('VENTANA DEL ESTUDIO',className='eyebrow'),html.Strong('2018 — 2024'),
                      html.P('7 años · 20 localidades · 4 franjas'),html.Hr(),html.Small('Consulta del modelo'),html.B('2023 — 2024'),
                      html.Small('Evaluación retrospectiva, no pronóstico en tiempo real.')],className='hero-aside')],className='hero'),
        html.Div([kpi('Siniestros con víctimas',number(grid.Siniestros.sum()),'Eventos, no número de personas',True),
                  kpi('Localidades','20','Resolución territorial del modelo'),kpi('Casos evaluados','58.480','Localidad × fecha × franja'),
                  kpi('Modelo principal','Random Forest','Versión 1.0 · umbral 0,52')],className='kpi-grid'),
        html.Div([panel('La historia, mes a mes','Siniestros con heridos o fallecidos · 2018–2024',graph('overview-series',charts.line(monthly,'Mes','Siniestros'))),
                  panel('Dónde se concentran los registros','Siete localidades con mayor conteo · no ajustado por exposición',graph('overview-localities',charts.bars(top,'Localidad','Siniestros',True)))],className='two-columns wide-left'),
        html.Div([panel('Explorar no es pronosticar','Cómo leer esta herramienta',html.P('La consulta reproduce casos de 2023–2024 con antecedentes históricos. El score ordena casos; no expresa la probabilidad de sufrir un accidente.')),
                  panel('Un universo definido','Siniestros con víctimas',html.P('Se excluyen los eventos de solo daños. Las franjas dividen cada día en cuatro intervalos de seis horas. El tipo de actor vial se usa únicamente para describir los registros.')),
                  panel('Resultados con contexto','Una evaluación que muestra sus límites',html.P('La tasa histórica sencilla obtiene un desempeño de ordenamiento similar al modelo. Consulta la evaluación, las falsas alertas y los errores por territorio.'))],className='three-columns'),
    ])


def query_page(s):
    ev=s.registro['datos']['evaluacion']
    return html.Div([intro('01 / CONSULTA RETROSPECTIVA','Un día, una franja, una localidad.',
        'Explora la puntuación del modelo y los antecedentes que acompañan a cada caso. Selecciona una localidad en el mapa o en el filtro.'),
        html.Div([html.Div([html.Label('Fecha evaluada',htmlFor='query-date'),dcc.DatePickerSingle(
            id='query-date',date=ev['desde'],min_date_allowed=ev['desde'],max_date_allowed=ev['hasta'],
            display_format='DD/MM/YYYY',first_day_of_week=1)],className='field'),
            dropdown('query-slot','Franja horaria',[{'label':f'{x} · {a}','value':x} for x,a in zip(SLOTS,['00–06 h','06–12 h','12–18 h','18–24 h'])],'Mañana'),
            dropdown('query-locality','Localidad',s.localidades,'KENNEDY'),
            dropdown('query-view','Encuadre del mapa',[{'label':'Área urbana','value':'urbana'},{'label':'Distrito completo','value':'distrito'}],'urbana')],className='filters'),
        notice('El score es una puntuación de priorización, NO una probabilidad calibrada. Una alerta baja no garantiza ausencia de siniestros.'),
        html.Div(id='query-error',role='alert'),
        html.Div([panel('Mapa de priorización','Las 20 localidades tienen resultado. El encuadre urbano se acerca a Sumapaz al seleccionarla.',
                        [graph('query-map'),html.P('Cartografía: SDP / Catastro. Instantánea de referencia, no límites históricos certificados. Fondo local sin teselas.',className='footnote')]),
                  html.Div(id='query-detail',className='case-panel',**{'aria-live':'polite'})],className='two-columns map-layout'),
        html.Div([html.Button('Descargar consulta JSON',id='download-query-button',className='button'),
                  html.Button('Descargar las 20 localidades CSV',id='download-map-button',className='button secondary')],className='actions'),
        panel('Comparación del día','Ordenada por score para la fecha y franja seleccionadas. El umbral es fijo: 0,52.',html.Div(id='query-ranking'))])


def query_result(s,fecha,slot,locality,view):
    if view not in ['urbana','distrito']:
        raise ValueError('Encuadre no válido.')
    row=s.consulta.consultar(fecha,locality,slot).iloc[0]
    rows=s.map_rows(fecha,slot)
    frozen=rows[rows.Localidad.eq(locality)].iloc[0]
    if not np.isclose(row.Score_Priorizacion,frozen.Score_Priorizacion,atol=1e-12,rtol=0) or row.Alerta_Modelo!=frozen.Alerta_Modelo:
        raise ValueError('La consulta no coincide con la evaluación congelada.')
    histories=[('Promedio previo de 7 días',number(row.Accidentes_Prom_7d,2)),
               ('Promedio previo de 30 días',number(row.Accidentes_Prom_30d,2)),
               ('Siniestros de siete días antes',number(row.Accidentes_Semana_Anterior))]
    trace=html.Dl([item for name,value in [('Modelo',row.Id_Modelo),('Versión',row.Version_Modelo),('Umbral',number(row.Umbral_Score,2)),
        ('Evaluación',f'{row.Evaluacion_Desde} → {row.Evaluacion_Hasta}'),('Alcance',row.Alcance_Consulta)] for item in [html.Dt(name),html.Dd(value)]],className='trace')
    detail=[html.P('CASO SELECCIONADO',className='eyebrow'),html.H2(locality.title()),
            html.P(f'{pd.Timestamp(fecha):%d/%m/%Y} · {slot}',className='muted'),
            html.Div([html.Strong(number(row.Score_Priorizacion,3)),html.Span('Score de priorización')],className='score-value'),
            html.Div('Priorización alta' if row.Alerta_Modelo else 'Priorización baja',className='badge high' if row.Alerta_Modelo else 'badge low'),
            html.P('Alerta cuando el score es mayor o igual a 0,52. No equivale a una probabilidad.',className='footnote'),
            label_explanation(s,locality,slot),
            html.H3('Antecedentes del caso'),html.Dl([item for n,v in histories for item in [html.Dt(n),html.Dd(v)]],className='antecedents'),
            html.P('No incluyen los siniestros del propio día.',className='footnote'),
            html.Details([html.Summary('Ver trazabilidad e interpretación'),trace,html.P(row.Advertencia_Score)])]
    if slot=='Madrugada':
        detail.append(weakest_slot_warning(s))
    ranking=rows[['Localidad','Score_Priorizacion','Alerta_Modelo']].copy()
    ranking['Alerta_Modelo']=ranking.Alerta_Modelo.map({0:'Baja',1:'Alta'})
    return charts.map_figure(s,rows,locality,view), detail, table(ranking,{'Alerta_Modelo':'Priorización','Score_Priorizacion':'Score'})


def history_page(s):
    return html.Div([intro('02 / ANÁLISIS DESCRIPTIVO','Los registros, desde distintas perspectivas.',
        'Explora 2018–2024. Los filtros de esta sección describen siniestros registrados y no modifican el modelo.'),
        html.Div([dropdown('history-year','Año',['Todos',*range(2018,2025)],'Todos'),
                  dropdown('history-locality','Localidad',['Todas',*s.localidades],'Todas'),
                  dropdown('history-slot','Franja',['Todas',*SLOTS],'Todas'),
                  dropdown('history-actor','Participación de actor',['Todos',*FLAGS],'Todos')],className='filters'),
        notice('Se cuentan siniestros, no personas. Un mismo siniestro puede involucrar varios tipos de actor; sus categorías no deben sumarse. Solo se incluyen indicadores de participación afirmativos.'),
        html.Div(id='history-error',role='alert'),html.Div(id='history-kpis',className='kpi-grid',**{'aria-live':'polite'}),
        html.Div([panel('Evolución mensual','Incluye meses y días con cero registros.',graph('history-series')),
                  panel('Localidades','Conteos registrados; no tasas de exposición al tránsito.',graph('history-localities'))],className='two-columns'),
        html.Div([panel('Día de semana × franja','Promedio por día del calendario, incluida la ausencia de registros.',graph('history-heat')),
                  panel('Franjas horarias','Los filtros de año, territorio y actor se aplican a todos los gráficos.',graph('history-slots'))],className='two-columns'),
        html.Button('Descargar resumen mensual CSV',id='download-history-button',className='button secondary')])


def history_result(s,year,locality,slot,actor):
    df=s.history(year,locality,slot,actor)
    total=int(df.Siniestros.sum()); days=df.Fecha_Acc.nunique()
    monthly=df.groupby('Mes',as_index=False).Siniestros.sum()
    territory=df.groupby('Localidad',as_index=False).Siniestros.sum().sort_values('Siniestros')
    slots=df.groupby('Franja_Horaria').Siniestros.sum().reindex(SLOTS).dropna().reset_index()
    cards=[kpi('Siniestros registrados',number(total),'Con víctimas · selección actual',True),kpi('Promedio diario',number(total/days if days else 0,2),f'{number(days)} días del calendario'),
           kpi('Localidades incluidas',number(df.Localidad.nunique()),'Según los filtros seleccionados'),kpi('Participación de actor',actor,'Filtro descriptivo, no predictor')]
    figs=[charts.line(monthly,'Mes','Siniestros'),charts.bars(territory,'Localidad','Siniestros',True,450),
          charts.day_heatmap(df),charts.bars(slots,'Franja_Horaria','Siniestros')]
    if not total:
        figs=[charts.empty('Cero siniestros registrados para esta selección.') for _ in range(4)]
    return cards,*figs


def evaluation_page(s):
    refs=s.reports['comparacion_referencias_historicas'][['Metodo','Average_Precision','AUC_ROC','Brier']]
    configs=s.reports['metricas_globales'][['Modelo','Umbral','F1','AUC_ROC','Average_Precision','Precision','Recall']]
    boot=s.reports['bootstrap_rf_vs_referencia_resumen'][['Metrica','Diferencia_A_Menos_B','P025','P975']]
    territory=s.reports['metricas_random_forest_ajustado_por_localidad']
    slots=s.reports['metricas_random_forest_ajustado_por_franja']
    error_columns=['Observaciones','Positivos','TP','FN','FP','Precision','Recall','F1']
    error_labels={'TP':'Detectados','FN':'Omitidos','FP':'Falsas alertas','Franja_Horaria':'Franja'}
    imp=s.reports['importancia_permutacion_random_forest_ajustado'].sort_values('Caida_AP_Media')
    short=imp.Variable.str.replace('Sin_Historial_Accidentes_','Sin historial ',regex=False).str.replace('Accidentes_Prom_','Promedio ',regex=False).str.replace('Accidentes_Semana_Anterior','Hace 7 días',regex=False).str.replace('_',' ',regex=False)
    fig=go.Figure(go.Bar(x=imp.Caida_AP_Media,y=short,orientation='h',marker_color=charts.TEAL,
        error_x=dict(type='data',array=imp.Desviacion),customdata=imp[['Variable']],
        hovertemplate='%{customdata[0]}<br>Caída AP: %{x:.4f}<extra></extra>'))
    fig=charts.finish(fig,height=420);fig.update_layout(margin=dict(l=180));fig.update_yaxes(tickfont=dict(size=10))
    return html.Div([intro('03 / EVALUACIÓN DEL MODELO','El desempeño también tiene límites.',
        'Random Forest ajustado · umbral fijo 0,52. Las métricas filtradas se recalculan sobre las predicciones conservadas de 2023–2024.'),
        html.Div([dropdown('eval-year','Año de evaluación',['Todos',2023,2024],'Todos'),
                  dropdown('eval-locality','Localidad',['Todas',*s.localidades],'Todas'),
                  dropdown('eval-slot','Franja',['Todas',*SLOTS],'Todas')],className='filters three'),
        html.Div(id='eval-error',role='alert'),html.Div(id='eval-kpis',className='kpi-grid',**{'aria-live':'polite'}),html.Div(id='eval-note',**{'aria-live':'polite'}),
        html.Div([panel('Aciertos y errores','Etiqueta observada frente a alerta del modelo.',graph('eval-confusion')),
                  panel('Calibración','La diagonal es la referencia ideal, no el comportamiento esperado del modelo.',graph('eval-calibration'))],className='two-columns'),
        html.Div([panel('Curva ROC','Ordenamiento de casos a distintos umbrales.',graph('eval-roc')),
                  panel('Precisión y recall','Línea punteada: prevalencia de la selección. Curvas simplificadas solo para dibujar.',graph('eval-pr'))],className='two-columns'),
        html.Button('Descargar métricas filtradas CSV',id='download-eval-button',className='button secondary'),
        html.H2('Comparaciones del estudio completo',className='section-title'),
        notice('Las siguientes tablas e importancia de variables corresponden al conjunto completo 2023–2024; no cambian con los filtros superiores.'),
        weakest_slot_warning(s),
        html.Div([
            panel('Detección por localidad','Proporción de positivos detectados y omitidos. Pase sobre las barras para ver los conteos.',
                  graph('eval-territory-detection',charts.detection_by_group(territory,'Localidad',560))),
            panel('Detección por franja','Comparación global 2023–2024; no son probabilidades de sufrir un siniestro.',
                  graph('eval-slot-detection',charts.detection_by_group(slots,'Franja_Horaria',560)))],className='two-columns'),
        notice('Las proporciones no reflejan por sí solas el tamaño de muestra: Sumapaz solo tiene dos positivos. Estas diferencias son descriptivas y no demuestran una causa.'),
        panel('Errores por territorio y horario','Conteos absolutos para contextualizar recall y F1. Precisión, recall y F1 están en escala 0–1.',[
            html.Details([html.Summary('Ver las 20 localidades'),table(territory[['Localidad',*error_columns]],error_labels)]),
            html.Details([html.Summary('Ver las cuatro franjas'),table(slots[['Franja_Horaria',*error_columns]],error_labels)])]),
        panel('Modelos comparados','Resultados finales de 05B; el modelo principal no se cambia desde la interfaz.',table(configs)),
        panel('¿Qué aporta frente a una referencia sencilla?','AP y AUC: mayor es mejor. Brier: menor es mejor.',table(refs)),
        notice('El RF no muestra superioridad concluyente frente a la tasa histórica localidad–franja–día. Su Brier global de 0,2221 es peor que el 0,1544 de la constante de entrenamiento.',True),
        panel('Incertidumbre de la comparación','RF menos tasa localidad–franja–día. Bootstrap exploratorio pareado: 300 réplicas, bloques de 7 días.',table(boot)),
        panel('Importancia por permutación','Caída de Average Precision. Barras de error: desviación entre repeticiones, no intervalo de confianza. No implica causalidad.',graph('eval-importance',fig)),
        html.Div([panel('Candelaria','Un caso que la métrica global no resume',html.P('157 positivos y ninguno detectado con el umbral 0,52. El score máximo de 0,3227 no alcanza el umbral.')),
                  panel('Sumapaz','Una muestra pequeña',html.P('Solo dos positivos en la evaluación. Evita extraer conclusiones territoriales firmes a partir de este grupo.'))],className='two-columns')])


def evaluation_result(s,year,locality,slot):
    df=s.evaluation(year,locality,slot);m=resumen_metricas(df)
    cards=[kpi('F1',number(m['F1'],4),'Equilibrio entre precisión y recall',True),kpi('AUC-ROC',number(m['AUC_ROC'],4),'Capacidad de ordenamiento'),
           kpi('Precisión',number(m['Precision']*100,2)+' %' if m['Precision'] is not None else '—','Alertas que corresponden a positivos'),
           kpi('Recall',number(m['Recall']*100,2)+' %' if m['Recall'] is not None else '—','Positivos que el modelo detecta')]
    text=f"{number(m['Observaciones'])} observaciones · {number(m['Positivos'])} positivos · Average Precision: {number(m['Average_Precision'],4)} · Brier: {number(m['Brier'],4)}."
    if df.Alto_Riesgo.nunique()<2:
        text+=' La selección no contiene ambas clases; algunas métricas no son interpretables y se muestran como —.'
    roc,pr=charts.curves(df)
    return cards,notice(text),charts.confusion(m),charts.calibration(df),roc,pr


def about_page(s):
    reg=s.registro
    steps=[('2018–2019 → 2020','Primer corte temporal'),('2018–2020 → 2021','Segundo corte temporal'),('2018–2021 → 2022','Tercer corte temporal'),('2018–2022 → 2023–2024','Entrenamiento final y evaluación retrospectiva')]
    return html.Div([intro('04 / METODOLOGÍA Y ALCANCE','Lo que estos resultados representan.',
        'Una referencia transparente para interpretar la fuente, la etiqueta y el proceso de evaluación.'),
        panel('Identidad del modelo','La aplicación utiliza una versión congelada, de solo lectura.',
            table(pd.DataFrame([{'Modelo':reg['nombre'],'Versión':reg['version'],'Identificador':reg['id_modelo'],'Umbral':reg['decision']['umbral_score']}]))),
        html.Div([panel('Unidad de análisis','Localidad × fecha × franja',html.P('Cada caso agrupa siniestros con víctimas. Las cuatro franjas son Madrugada (00–06), Mañana (06–12), Tarde (12–18) y Noche (18–24).')),
                  panel('Doce variables','Calendario, territorio y antecedentes',html.P('Localidad, franja, día semanal, mes, fin de semana, festivo, promedios de 7 y 30 días, conteo de siete días antes y tres indicadores de ausencia de historial.'))],className='two-columns'),
        panel('Dos umbrales distintos','La etiqueta observada no es la decisión del clasificador.',[
            html.P('Alto_Riesgo = 1 cuando el conteo del día supera estrictamente el cuantil 2/3 de su localidad y franja, calculado en entrenamiento.'),
            table(pd.DataFrame({'Umbral del conteo':[0,1,2],'Grupos':[49,28,3],'Etiqueta positiva':['Al menos 1 siniestro','Al menos 2 siniestros','Al menos 3 siniestros']})),
            html.P('En 49 de 80 grupos se detecta ocurrencia, no una frecuencia excepcional. Por separado, el modelo emite una alerta cuando su score alcanza 0,52.')]),
        panel('Validación temporal','El pasado se usa para evaluar periodos posteriores.',html.Div([
            html.Div([html.Strong(a),html.Small(b)],className='timeline-step') for a,b in steps],className='timeline')),
        notice('La configuración y el umbral reutilizan las validaciones de 2020–2022. El periodo 2023–2024 ya fue inspeccionado durante el desarrollo: no es una prueba prospectiva independiente.',True),
        panel('Limitaciones de uso','Antes de interpretar una alerta',html.Ul([
            html.Li('El score no es una probabilidad calibrada ni el riesgo individual de una persona.'),
            html.Li('No se predicen fechas nuevas, calles, coordenadas ni resultados por tipo de actor vial.'),
            html.Li('No se incorporan clima, tráfico en tiempo real ni exposición al tránsito.'),
            html.Li('Los históricos presuponen que los conteos de días anteriores ya están disponibles.'),
            html.Li('Una fila con cero registros no garantiza ausencia real de siniestros.'),
            html.Li('La importancia predictiva no demuestra causalidad. No se recomienda asignar recursos institucionales con este prototipo.') ])),
        panel('Fuentes y reproducibilidad','Datos locales y evidencia conservada.',[
            html.P('Excel: Base del Anuario de Siniestralidad Vial de Bogotá 2024, Secretaría Distrital de Movilidad. Universo principal: Con Heridos y Con Muertos, 2018–2024.'),
            html.P('Cartografía: Secretaría Distrital de Planeación / Catastro, instantánea del 13/09/2026. No certifica límites históricos de todo el periodo.'),
            html.P('La fecha original de descarga del Excel es desconocida y su licencia específica sigue pendiente de confirmación. Esta aplicación no publica microdatos ni identificadores de personas.'),
            html.P('Al iniciar se verifican el modelo, el dataset, las predicciones y los recursos del dashboard. Los filtros no escriben archivos. Las descargas se generan en memoria.'),
            html.Details([html.Summary('Huella del modelo y dataset'),html.Pre(f"Modelo SHA-256\n{reg['artefacto']['sha256']}\n\nDataset SHA-256\n{reg['datos']['sha256']}")]),
            html.A('Consultar repositorio y documentación ↗',href='https://github.com/camilo20262/Siniestralidad-Vial',target='_blank',rel='noopener noreferrer')]),
        panel('Guía rápida','Cómo recorrer el dashboard',html.Ol([
            html.Li('Resumen: conoce el universo y sus conteos.'),html.Li('Consulta y mapa: selecciona una fecha, franja y localidad; revisa antecedentes y trazabilidad.'),
            html.Li('Análisis histórico: filtra los registros. El actor solo afecta esta vista descriptiva.'),
            html.Li('Evaluación: revisa aciertos, falsas alertas, omisiones y referencias. Los filtros superiores no cambian las comparaciones globales.'),
            html.Li('Descarga: exporta consultas o resúmenes con su contexto para revisión académica.')]))])


def create_app(service=None):
    s=service if service is not None else load_data()
    app=Dash(__name__,assets_folder=str(Path(__file__).parent/'assets'),
             title='Siniestralidad · Bogotá',update_title='Actualizando…',suppress_callback_exceptions=True,
             meta_tags=[{'name':'viewport','content':'width=device-width, initial-scale=1'},
                        {'name':'description','content':'Exploración académica de siniestros con víctimas en Bogotá. Evaluación retrospectiva.'}])
    app.index_string=app.index_string.replace('<html>','<html lang="es">')
    app.layout=html.Div([
        html.A('Saltar al contenido',href='#main-content',className='skip-link'),
        html.Header([html.Div([html.Span('SV',className='brand-symbol'),html.Div([html.Strong('Siniestralidad vial'),html.Small('BOGOTÁ · OBSERVACIÓN Y ANÁLISIS')])],className='brand'),
                     html.Div([html.Span('Prototipo académico',className='header-tag'),html.Span('2018 — 2024',className='header-period')],className='header-right')],className='topbar'),
        html.Nav(dcc.RadioItems(id='navigation',value='overview',options=[{'label':label,'value':value}
            for value,label in [('overview','Resumen'),('query','Consulta y mapa'),('history','Análisis histórico'),('evaluation','Evaluación'),('about','Metodología')]],
            inline=True,className='navigation',labelClassName='nav-tab',inputClassName='nav-radio'),**{'aria-label':'Secciones del dashboard'}),
        html.Main(dcc.Loading(html.Div(id='page-content'),type='circle',color=charts.TEAL,delay_show=250),id='main-content',className='container'),
        dcc.Download(id='download-query'),dcc.Download(id='download-map'),dcc.Download(id='download-history'),dcc.Download(id='download-eval'),
        html.Footer([html.Span('Siniestros con víctimas · Bogotá D.C.'),html.Span('RF v1.0 · Solo lectura · Sin validación prospectiva')],className='footer')])

    @app.callback(Output('page-content','children'),Input('navigation','value'))
    def render_page(value):
        return {'overview':overview,'query':query_page,'history':history_page,'evaluation':evaluation_page,'about':about_page}.get(value,overview)(s)

    @app.callback(Output('query-map','figure'),Output('query-detail','children'),Output('query-ranking','children'),Output('query-error','children'),
                  Input('query-date','date'),Input('query-slot','value'),Input('query-locality','value'),Input('query-view','value'))
    def update_query(fecha,slot,locality,view):
        try:
            return (*query_result(s,fecha,slot,locality,view), '')
        except (ValueError,TypeError) as exc:
            return charts.empty('Consulta no disponible.'),[],[],notice(str(exc),True)

    @app.callback(Output('query-locality','value'),Input('query-map','clickData'),prevent_initial_call=True)
    def choose_locality(click):
        if click and click.get('points'):
            value=click['points'][0].get('location')
            if value in s.localidades:
                return value
        return no_update

    @app.callback(Output('history-kpis','children'),Output('history-series','figure'),Output('history-localities','figure'),
                  Output('history-heat','figure'),Output('history-slots','figure'),Output('history-error','children'),
                  Input('history-year','value'),Input('history-locality','value'),Input('history-slot','value'),Input('history-actor','value'))
    def update_history(year,locality,slot,actor):
        try:
            return (*history_result(s,year,locality,slot,actor),'')
        except (ValueError,TypeError) as exc:
            return [],*[charts.empty() for _ in range(4)],notice(str(exc),True)

    @app.callback(Output('eval-kpis','children'),Output('eval-note','children'),Output('eval-confusion','figure'),
                  Output('eval-calibration','figure'),Output('eval-roc','figure'),Output('eval-pr','figure'),Output('eval-error','children'),
                  Input('eval-year','value'),Input('eval-locality','value'),Input('eval-slot','value'))
    def update_eval(year,locality,slot):
        try:
            return (*evaluation_result(s,year,locality,slot),'')
        except (ValueError,TypeError) as exc:
            return [],'',*[charts.empty() for _ in range(4)],notice(str(exc),True)

    @app.callback(Output('download-query','data'),Input('download-query-button','n_clicks'),
                  State('query-date','date'),State('query-locality','value'),State('query-slot','value'),prevent_initial_call=True)
    def download_query(n,fecha,locality,slot):
        if not n:
            raise PreventUpdate
        try:
            frame=s.consulta.consultar(fecha,locality,slot)
        except (ValueError,TypeError):
            raise PreventUpdate
        return dict(content=frame.to_json(orient='records',force_ascii=False,indent=2),filename=f'consulta_{fecha}.json',type='application/json')

    @app.callback(Output('download-map','data'),Input('download-map-button','n_clicks'),
                  State('query-date','date'),State('query-slot','value'),prevent_initial_call=True)
    def download_map(n,fecha,slot):
        if not n:
            raise PreventUpdate
        try:
            frame=s.map_rows(fecha,slot)
        except (ValueError,TypeError):
            raise PreventUpdate
        return dcc.send_data_frame(frame.to_csv,f'localidades_{fecha}.csv',index=False)

    @app.callback(Output('download-history','data'),Input('download-history-button','n_clicks'),
                  State('history-year','value'),State('history-locality','value'),State('history-slot','value'),State('history-actor','value'),prevent_initial_call=True)
    def download_history(n,year,locality,slot,actor):
        if not n:
            raise PreventUpdate
        try:
            df=s.history(year,locality,slot,actor).groupby('Mes',as_index=False).Siniestros.sum()
        except (ValueError,TypeError):
            raise PreventUpdate
        df=df.assign(Localidad=locality,Franja=slot,Actor=actor,Unidad='Siniestros con víctimas; participación no excluyente',Alcance='Descriptivo, no predicción')
        return dcc.send_data_frame(df.to_csv,'historia_mensual.csv',index=False)

    @app.callback(Output('download-eval','data'),Input('download-eval-button','n_clicks'),
                  State('eval-year','value'),State('eval-locality','value'),State('eval-slot','value'),prevent_initial_call=True)
    def download_eval(n,year,locality,slot):
        if not n:
            raise PreventUpdate
        try:
            df=pd.DataFrame([resumen_metricas(s.evaluation(year,locality,slot))])
        except (ValueError,TypeError):
            raise PreventUpdate
        df=s.attach_trace(df.assign(Anio=year,Localidad=locality,Franja=slot))
        return dcc.send_data_frame(df.to_csv,'metricas_filtradas.csv',index=False)

    @app.server.get('/healthz')
    def health():
        return {'status':'ok','modelo':s.registro['id_modelo'],'alcance':'retrospectivo'}

    return app


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8050)
    args=parser.parse_args()
    try:
        app=create_app()
    except (FileNotFoundError,ValueError,RuntimeError) as exc:
        parser.exit(1,f'No se pudo iniciar el dashboard: {exc}\nRevise Git LFS y el manual dashboard/README.md.\n')
    app.run(host='127.0.0.1',port=args.port,debug=False)


if __name__=='__main__':
    main()
