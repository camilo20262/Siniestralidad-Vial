"""Figuras locales de Plotly; el mapa no solicita teselas ni tokens externos."""
from pathlib import Path
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.colors import sample_colorscale
from sklearn.metrics import precision_recall_curve, roc_curve
from dashboard.data import DAYS, SLOTS

CSS_PATH = Path(__file__).parent/'assets/dashboard.css'
MAP_STOPS = [0, .12, .22, .32, .42, .52, .62, .76, .9, 1]


def _css_theme_tokens(theme):
    """Carga la paleta desde CSS para mantener una sola fuente de verdad por tema."""
    css=CSS_PATH.read_text(encoding='utf-8')
    match=re.search(rf':root\[data-theme=["\']{theme}["\']\]\s*\{{(.*?)\}}',css,re.S)
    if not match:
        raise RuntimeError(f'No existe la paleta CSS del tema {theme}.')
    return dict(re.findall(r'--([\w-]+)\s*:\s*([^;\n]+)\s*;',match.group(1)))


def _palette(theme):
    tokens=_css_theme_tokens(theme)
    return {
        **tokens,
        'map_colors':[[stop,tokens[f'map-{index}']] for index,stop in enumerate(MAP_STOPS)],
        'heatmap_colors':[tokens[f'heat-{index}'] for index in range(6)],
        'slot_colors':{slot:tokens[key] for slot,key in zip(
            SLOTS,('slot-madrugada','slot-manana','slot-tarde','slot-noche'))},
    }


THEME_PALETTES={name:_palette(name) for name in ('light','dark')}


def normalize_theme(theme, fallback='light'):
    return theme if theme in THEME_PALETTES else fallback


def theme_palette(theme='light'):
    return THEME_PALETTES[normalize_theme(theme)]


# Alias claros conservados para compatibilidad con integraciones y pruebas existentes.
TEAL = THEME_PALETTES['light']['teal']
INK = THEME_PALETTES['light']['ink']
GOLD = THEME_PALETTES['light']['gold']
MAP_COLORS = THEME_PALETTES['light']['map_colors']
HEATMAP_COLORS = THEME_PALETTES['light']['heatmap_colors']
SLOT_COLORS = THEME_PALETTES['light']['slot_colors']


def finish(fig, title=None, height=340, theme='light'):
    colors=theme_palette(theme)
    hoverlabel=dict(font_size=13)
    if normalize_theme(theme)=='dark':
        hoverlabel.update(bgcolor=colors['surface'],font_color=colors['ink'],
                          bordercolor=colors['line'])
    fig.update_layout(template='plotly_white', height=height, title=title,
                      font=dict(family='Arial, sans-serif', size=12, color=colors['ink']),
                      paper_bgcolor=colors['surface'], plot_bgcolor=colors['surface'],
                      margin=dict(l=45, r=22, t=35 if title else 20, b=45),
                      colorway=[colors['teal'],colors['gold'],colors['chart-color-3'],colors['chart-color-4']],
                      legend=dict(orientation='h', y=-.22, x=0),
                      hoverlabel=hoverlabel)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor=colors['chart-grid'], zeroline=False)
    return fig


def empty(message='No hay registros para esta selección.', theme='light'):
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return finish(fig,theme=theme)


def line(frame, x, y, label='Siniestros registrados', theme='light'):
    colors=theme_palette(theme)
    if frame.empty:
        return empty(theme=theme)
    fig = go.Figure(go.Scatter(x=frame[x], y=frame[y], mode='lines', line=dict(color=colors['teal'], width=2.5),
                              fill='tozeroy', fillcolor=colors['chart-fill'], name=label,
                              hovertemplate='%{x}<br>%{y:,.0f}<extra>'+label+'</extra>'))
    fig.update_yaxes(title=label)
    finish(fig,theme=theme)
    values=frame[x].dropna()
    if not values.empty and pd.api.types.is_datetime64_any_dtype(values.dtype):
        start,end=values.min(),values.max()
        span=end-start
        padding=max(span*.025,pd.Timedelta(days=15))
        fig.update_xaxes(range=[start-padding,end+padding],automargin=True)
    else:
        fig.update_xaxes(automargin=True)
    return fig


def bars(frame, x, y, horizontal=False, height=340, theme='light', show_values=False):
    colors=theme_palette(theme)
    if frame.empty:
        return empty(theme=theme)
    marker_colors = ([colors['slot_colors'].get(value,colors['teal']) for value in frame[x]]
                     if x == 'Franja_Horaria' else colors['teal'])
    trace_options={
        'x':frame[y] if horizontal else frame[x],
        'y':frame[x] if horizontal else frame[y],
        'orientation':'h' if horizontal else 'v',
        'marker_color':marker_colors,
        'hovertemplate':('%{y}: %{x:,.0f}' if horizontal else '%{x}: %{y:,.0f}')+'<extra></extra>',
    }
    if horizontal and show_values:
        trace_options.update(
            text=[f'{value:,.0f}'.replace(',','.') for value in frame[y]],
            texttemplate='%{text}',textposition='outside',cliponaxis=False,
            textfont=dict(size=12,color=colors['ink']))
    trace = go.Bar(**trace_options)
    fig = go.Figure(trace)
    finish(fig,height=height,theme=theme)
    if horizontal:
        fig.update_yaxes(automargin=True, tickfont=dict(size=10))
        fig.update_layout(margin=dict(l=140,r=28))
        if show_values:
            maximum=pd.to_numeric(frame[y],errors='coerce').max()
            if pd.notna(maximum) and maximum>0:
                fig.update_xaxes(range=[0,float(maximum)*1.18])
    return fig


def _polygon_coordinates(geometry):
    """Convierte Polygon/MultiPolygon en segmentos cartesianos separados."""
    polygons=(geometry['coordinates'] if geometry['type']=='MultiPolygon'
              else [geometry['coordinates']])
    x_values=[]
    y_values=[]
    for polygon in polygons:
        for ring in polygon:
            x_values.extend(point[0] for point in ring)
            y_values.extend(point[1] for point in ring)
            x_values.append(None)
            y_values.append(None)
    return x_values,y_values


def _map_camera(selected, view):
    """Encuadres con proporción estable para el lienzo horizontal del panel."""
    if view!='urbana':
        return [-74.975,-73.425],[3.725,4.875],'district'
    if selected=='SUMAPAZ':
        return [-74.70,-73.84],[3.71,4.35],'sumapaz'
    return [-74.38,-73.84],[4.44,4.84],'urban'


def preserve_map_view(fig, relayout, selected, view):
    """Reaplica el encuadre manipulado por el usuario si pertenece a la misma vista."""
    if not isinstance(relayout,dict):
        return fig

    def axis_range(axis):
        values=relayout.get(f'{axis}.range')
        if not isinstance(values,(list,tuple)) or len(values)!=2:
            values=[relayout.get(f'{axis}.range[0]'),relayout.get(f'{axis}.range[1]')]
        return values if all(isinstance(value,(int,float)) for value in values) else None

    x_range=axis_range('xaxis')
    y_range=axis_range('yaxis')
    if x_range is None or y_range is None:
        return fig
    focus=_map_camera(selected,view)[2]
    latitude_center=sum(y_range)/2
    if (focus=='urban' and latitude_center<4.4) or (focus=='sumapaz' and latitude_center>=4.4):
        return fig
    fig.update_xaxes(range=x_range)
    fig.update_yaxes(range=y_range)
    return fig


def map_figure(service, rows, selected, view, theme='light'):
    colors=theme_palette(theme)
    features={feature['properties']['Localidad']:feature
              for feature in service.geojson['features']}
    fig=go.Figure()
    for row in rows.itertuples(index=False):
        feature=features.get(row.Localidad)
        if feature is None:
            continue
        x_values,y_values=_polygon_coordinates(feature['geometry'])
        priority='Alta' if row.Alerta_Modelo else 'Baja'
        metadata=[row.Localidad,float(row.Score_Priorizacion),priority,float(row.Umbral_Score)]
        hover_text=(f'<b>{row.Localidad}</b><br>Score: {metadata[1]:.3f}<br>'
                    f'Priorización: {priority}<br>Umbral: {metadata[3]:.2f}')
        fig.add_trace(go.Scatter(
            x=x_values,y=y_values,mode='lines',fill='toself',hoveron='points+fills',
            name=row.Localidad,uid=f'query-locality-{row.Localidad}',showlegend=False,
            fillcolor=sample_colorscale(colors['map_colors'],[metadata[1]])[0],opacity=.9,
            line=dict(color=colors['map-selected'] if row.Localidad==selected else colors['map-line'],
                      width=3 if row.Localidad==selected else 1),
            meta=metadata,text=hover_text,hoverinfo='text',
            customdata=[[row.Localidad]]*len(x_values),
            hovertemplate=None))
    fig.add_trace(go.Scatter(
        x=[None],y=[None],mode='markers',uid='query-map-colorbar',showlegend=False,
        hoverinfo='skip',marker=dict(color=[0],cmin=0,cmax=1,colorscale=colors['map_colors'],
                                    showscale=True,colorbar=dict(title='Score',thickness=12,
                                                                len=.62,tickformat='.1f'))))
    x_range,y_range,focus=_map_camera(selected,view)
    revision=f'query-map-{view}-{focus}'
    layout=dict(height=490,margin=dict(l=0,r=0,t=0,b=0),
                paper_bgcolor=colors['map-paper'],plot_bgcolor=colors['map-paper'],
                xaxis=dict(range=x_range,visible=False,showgrid=False,zeroline=False,
                           constrain='domain',fixedrange=False,uirevision=revision),
                yaxis=dict(range=y_range,visible=False,showgrid=False,zeroline=False,
                           scaleanchor='x',scaleratio=1,constrain='domain',fixedrange=False,
                           uirevision=revision),
                uirevision=revision,
                clickmode='event',clickanywhere=True,hovermode='closest',dragmode='pan',
                font=dict(family='Arial',color=colors['ink']),
                hoverlabel=dict(bgcolor=colors['surface'],font_color=colors['ink'],
                                bordercolor=colors['line'],font_size=13))
    fig.update_layout(**layout)
    return fig


def detection_by_group(frame, group, height=460, theme='light'):
    """Comparación global: detección entre positivos, conservando tamaños de muestra."""
    colors=theme_palette(theme)
    ordered = frame.sort_values('Recall')
    fig = go.Figure()
    slot_breakdown = group == 'Franja_Horaria'
    for column, label, color in [('TP','Detectados',colors['teal']),('FN','Omitidos',colors['gold'])]:
        fraction = ordered[column].div(ordered.Positivos.replace(0, np.nan))
        marker = dict(color=([colors['slot_colors'].get(value,colors['teal']) for value in ordered[group]]
                             if slot_breakdown else color))
        if slot_breakdown and column == 'FN':
            marker.update(opacity=.42, pattern_shape='/')
        fig.add_trace(go.Bar(x=fraction, y=ordered[group], orientation='h', name=label,
            marker=marker, customdata=np.column_stack([ordered[column], ordered.Positivos]),
            hovertemplate='%{y}<br>'+label+': %{customdata[0]:,}<br>Positivos: %{customdata[1]:,}<br>Proporción: %{x:.1%}<extra></extra>'))
    finish(fig,height=height,theme=theme)
    fig.update_layout(barmode='stack', margin=dict(l=145,b=80))
    fig.update_xaxes(range=[0,1], tickformat='.0%', title='Entre los casos positivos observados')
    fig.update_yaxes(automargin=True, tickfont=dict(size=10))
    return fig


def day_heatmap(grid, theme='light'):
    colors=theme_palette(theme)
    if grid.empty:
        return empty(theme=theme)
    # Un día aporta a cada franja seleccionada incluso cuando su conteo es cero.
    daily = grid.groupby(['Fecha_Acc','Dia_Num','Franja_Horaria'], observed=True).Siniestros.sum().reset_index()
    pivot = daily.groupby(['Dia_Num','Franja_Horaria']).Siniestros.mean().unstack().reindex(index=range(7),columns=SLOTS)
    values = pivot.to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    minimum = float(finite.min()) if finite.size else 0
    maximum = float(finite.max()) if finite.size else 0

    def cell_color(value):
        if pd.isna(value):
            return colors['heatmap_colors'][0]
        if maximum == minimum:
            position = 1 if maximum > 0 else 0
        else:
            position = (float(value)-minimum)/(maximum-minimum)
        index = min(int(position*len(colors['heatmap_colors'])),len(colors['heatmap_colors'])-1)
        return colors['heatmap_colors'][index]

    def rounded_cell(x, y, radius=.1):
        left,right,bottom,top=x-.41,x+.41,y-.4,y+.4
        return (f'M {left+radius},{bottom} L {right-radius},{bottom} '
                f'Q {right},{bottom} {right},{bottom+radius} L {right},{top-radius} '
                f'Q {right},{top} {right-radius},{top} L {left+radius},{top} '
                f'Q {left},{top} {left},{top-radius} L {left},{bottom+radius} '
                f'Q {left},{bottom} {left+radius},{bottom} Z')

    fig = go.Figure()
    hover_x=[];hover_y=[];hover=[]
    for day_index,day in enumerate(DAYS):
        for slot_index,slot in enumerate(SLOTS):
            value=values[day_index,slot_index]
            fig.add_shape(type='path',path=rounded_cell(slot_index,day_index),
                          fillcolor=cell_color(value),line=dict(width=0),layer='below')
            hover_x.append(slot_index);hover_y.append(day_index)
            hover.append(f'{day} · {slot}<br>Promedio: {value:.2f}' if pd.notna(value)
                         else f'{day} · {slot}<br>Sin datos')
    fig.add_trace(go.Scatter(x=hover_x,y=hover_y,mode='markers',showlegend=False,
        marker=dict(size=38,color='rgba(0,0,0,0)'),text=hover,
        hovertemplate='%{text}<extra></extra>'))
    finish(fig,theme=theme)
    fig.update_xaxes(tickmode='array',tickvals=list(range(len(SLOTS))),ticktext=SLOTS,
                     range=[-.52,len(SLOTS)-.48],fixedrange=True)
    fig.update_yaxes(tickmode='array',tickvals=list(range(len(DAYS))),ticktext=DAYS,
                     range=[len(DAYS)-.48,-.52],fixedrange=True,showgrid=False)
    fig.update_layout(margin=dict(l=82,r=22,t=20,b=72),hovermode='closest')
    legend_start=.68
    for index,color in enumerate(colors['heatmap_colors']):
        x0=legend_start+index*.032
        fig.add_shape(type='rect',xref='paper',yref='paper',x0=x0,x1=x0+.022,
                      y0=-.25,y1=-.19,fillcolor=color,line=dict(color=colors['surface'],width=1))
    fig.add_annotation(x=legend_start-.015,y=-.22,xref='paper',yref='paper',text='Menos',
                       showarrow=False,xanchor='right',font=dict(size=11,color=colors['ink']))
    fig.add_annotation(x=legend_start+len(colors['heatmap_colors'])*.032,y=-.22,xref='paper',yref='paper',
                       text='Más',showarrow=False,xanchor='left',font=dict(size=11,color=colors['ink']))
    return fig


def confusion(metrics, theme='light'):
    colors=theme_palette(theme)
    if metrics['Observaciones'] is None:
        return empty(theme=theme)
    z = [[metrics['TN'],metrics['FP']],[metrics['FN'],metrics['TP']]]
    labels = [['Negativos<br>correctos','Falsas<br>alertas'],['Positivos<br>omitidos','Positivos<br>detectados']]
    fig = go.Figure(go.Heatmap(x=['Sin alerta','Con alerta'],y=['Etiqueta 0','Etiqueta 1'],z=z,
        colorscale=colors['map_colors'], showscale=False, text=labels,
        texttemplate='%{text}<br><b>%{z:,}</b>', hovertemplate='%{text}: %{z:,}<extra></extra>'))
    fig.update_yaxes(autorange='reversed',title='Observado')
    fig.update_xaxes(title='Clasificación del modelo')
    return finish(fig,theme=theme)


def curves(rows, theme='light'):
    colors=theme_palette(theme)
    if rows.empty or rows.Alto_Riesgo.nunique()<2:
        return (empty('ROC requiere ambas clases en la selección.',theme),
                empty('Curvas no comparables: solo una clase observada.',theme))
    fpr,tpr,_ = roc_curve(rows.Alto_Riesgo,rows.Score)
    p,r,_ = precision_recall_curve(rows.Alto_Riesgo,rows.Score)
    def sample(x,y):
        idx=np.unique(np.linspace(0,len(x)-1,min(len(x),600)).astype(int))
        return x[idx],y[idx]
    x,y=sample(fpr,tpr)
    roc=go.Figure(go.Scatter(x=x,y=y,mode='lines',name='RF ajustado',line_color=colors['teal']))
    roc.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',name='Sin discriminación',line=dict(color=colors['chart-baseline'],dash='dot')))
    roc.update_xaxes(title='Tasa de falsas alertas',range=[0,1]);roc.update_yaxes(title='Recall',range=[0,1])
    x,y=sample(r,p)
    pr=go.Figure(go.Scatter(x=x,y=y,mode='lines',name='RF ajustado',line_color=colors['teal']))
    pr.add_hline(y=float(rows.Alto_Riesgo.mean()),line_dash='dot',line_color=colors['gold'])
    pr.update_xaxes(title='Recall',range=[0,1]);pr.update_yaxes(title='Precisión',range=[0,1])
    return finish(roc,theme=theme),finish(pr,theme=theme)


def calibration(rows, theme='light'):
    colors=theme_palette(theme)
    if rows.empty:
        return empty(theme=theme)
    df=rows.copy()
    df['Grupo']=pd.cut(df.Score,bins=np.linspace(0,1,11),include_lowest=True)
    means=df.groupby('Grupo',observed=True).agg(Score=('Score','mean'),Frecuencia=('Alto_Riesgo','mean'),N=('Score','size'))
    fig=go.Figure(go.Scatter(x=means.Score,y=means.Frecuencia,mode='lines+markers',name='RF ajustado',
        line=dict(color=colors['teal']),marker=dict(color=colors['teal']),
        customdata=means[['N']],hovertemplate='Score medio: %{x:.3f}<br>Frecuencia: %{y:.3f}<br>Casos: %{customdata[0]}<extra></extra>'))
    fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',name='Calibración ideal',line=dict(color=colors['chart-baseline'],dash='dot')))
    fig.update_xaxes(title='Score medio · intervalos fijos de 0,1',range=[0,1])
    fig.update_yaxes(title='Frecuencia observada de la etiqueta',range=[0,1])
    return finish(fig,theme=theme)
