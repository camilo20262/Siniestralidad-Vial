"""Figuras locales de Plotly; el mapa no solicita teselas ni tokens externos."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.metrics import precision_recall_curve, roc_curve
from dashboard.data import DAYS, SLOTS

TEAL = '#137c78'
INK = '#172d3e'
GOLD = '#d7942d'
MAP_COLORS = [[0, '#eef5f2'], [.12, '#d5e8e3'], [.22, '#a9d0c8'],
              [.32, '#72b3aa'], [.42, '#378f88'], [.52, '#176762'],
              [.62, '#5f684b'], [.76, '#816923'], [.9, '#a8731d'], [1, '#9f6814']]
HEATMAP_COLORS = ['#edf7f5', '#d2ece8', '#a8d8d2', '#72bdb5', '#3b9b94', TEAL]
SLOT_COLORS = {
    'Madrugada': '#315d68',
    'Mañana': '#c08a34',
    'Tarde': '#3a9992',
    'Noche': INK,
}


def finish(fig, title=None, height=340):
    fig.update_layout(template='plotly_white', height=height, title=title,
                      font=dict(family='Arial, sans-serif', size=12, color=INK),
                      paper_bgcolor='white', plot_bgcolor='white',
                      margin=dict(l=45, r=22, t=35 if title else 20, b=45),
                      colorway=[TEAL, GOLD, '#7b90a0', '#a54d50'],
                      legend=dict(orientation='h', y=-.22, x=0), hoverlabel=dict(font_size=13))
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor='#edf1f2', zeroline=False)
    return fig


def empty(message='No hay registros para esta selección.'):
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, xref='paper', yref='paper', showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return finish(fig)


def line(frame, x, y, label='Siniestros registrados'):
    if frame.empty:
        return empty()
    fig = go.Figure(go.Scatter(x=frame[x], y=frame[y], mode='lines', line=dict(color=TEAL, width=2.5),
                              fill='tozeroy', fillcolor='rgba(19,124,120,.07)', name=label,
                              hovertemplate='%{x}<br>%{y:,.0f}<extra>'+label+'</extra>'))
    fig.update_yaxes(title=label)
    return finish(fig)


def bars(frame, x, y, horizontal=False, height=340):
    if frame.empty:
        return empty()
    colors = ([SLOT_COLORS.get(value, TEAL) for value in frame[x]]
              if x == 'Franja_Horaria' else TEAL)
    trace = go.Bar(x=frame[y] if horizontal else frame[x], y=frame[x] if horizontal else frame[y],
                   orientation='h' if horizontal else 'v', marker_color=colors,
                   hovertemplate=('%{y}: %{x:,.3f}' if horizontal else '%{x}: %{y:,.0f}')+'<extra></extra>')
    fig = go.Figure(trace)
    finish(fig, height=height)
    if horizontal:
        fig.update_yaxes(automargin=True, tickfont=dict(size=10))
        fig.update_layout(margin=dict(l=140))
    return fig


def map_figure(service, rows, selected, view):
    fig = go.Figure(go.Choroplethmap(
        geojson=service.geojson, featureidkey='properties.Localidad', locations=rows.Localidad,
        z=rows.Score_Priorizacion, zmin=0, zmax=1, colorscale=MAP_COLORS,
        marker_line_color='white', marker_line_width=1, marker_opacity=.9,
        customdata=np.column_stack([rows.Alerta_Modelo.map({0:'Baja',1:'Alta'}), rows.Umbral_Score]),
        hovertemplate='<b>%{location}</b><br>Score: %{z:.3f}<br>Priorización: %{customdata[0]}<br>Umbral: %{customdata[1]}<extra></extra>',
        colorbar=dict(title='Score', thickness=12, len=.62, tickformat='.1f')))
    chosen = rows[rows.Localidad.eq(selected)]
    if not chosen.empty:
        fig.add_trace(go.Choroplethmap(geojson=service.geojson, featureidkey='properties.Localidad',
            locations=chosen.Localidad, z=chosen.Score_Priorizacion, zmin=0, zmax=1,
            colorscale=MAP_COLORS, marker_line_color=INK, marker_line_width=3,
            showscale=False, hoverinfo='skip'))
    center, zoom = ({'lat':4.64,'lon':-74.11}, 10) if view=='urbana' else ({'lat':4.30,'lon':-74.20}, 8.6)
    if selected=='SUMAPAZ' and view=='urbana':
        center, zoom = {'lat':4.03,'lon':-74.27}, 9
    fig.update_layout(map=dict(style='white-bg', center=center, zoom=zoom), height=490,
                      margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor='#f3f6f4',
                      uirevision=f'{view}-{selected}', font=dict(family='Arial',color=INK))
    return fig


def detection_by_group(frame, group, height=460):
    """Comparación global: detección entre positivos, conservando tamaños de muestra."""
    ordered = frame.sort_values('Recall')
    fig = go.Figure()
    slot_breakdown = group == 'Franja_Horaria'
    for column, label, color in [('TP', 'Detectados', TEAL), ('FN', 'Omitidos', GOLD)]:
        fraction = ordered[column].div(ordered.Positivos.replace(0, np.nan))
        marker = dict(color=([SLOT_COLORS.get(value, TEAL) for value in ordered[group]]
                             if slot_breakdown else color))
        if slot_breakdown and column == 'FN':
            marker.update(opacity=.42, pattern_shape='/')
        fig.add_trace(go.Bar(x=fraction, y=ordered[group], orientation='h', name=label,
            marker=marker, customdata=np.column_stack([ordered[column], ordered.Positivos]),
            hovertemplate='%{y}<br>'+label+': %{customdata[0]:,}<br>Positivos: %{customdata[1]:,}<br>Proporción: %{x:.1%}<extra></extra>'))
    finish(fig, height=height)
    fig.update_layout(barmode='stack', margin=dict(l=145,b=80))
    fig.update_xaxes(range=[0,1], tickformat='.0%', title='Entre los casos positivos observados')
    fig.update_yaxes(automargin=True, tickfont=dict(size=10))
    return fig


def day_heatmap(grid):
    if grid.empty:
        return empty()
    # Un día aporta a cada franja seleccionada incluso cuando su conteo es cero.
    daily = grid.groupby(['Fecha_Acc','Dia_Num','Franja_Horaria'], observed=True).Siniestros.sum().reset_index()
    pivot = daily.groupby(['Dia_Num','Franja_Horaria']).Siniestros.mean().unstack().reindex(index=range(7),columns=SLOTS)
    values = pivot.to_numpy(dtype=float)
    finite = values[np.isfinite(values)]
    minimum = float(finite.min()) if finite.size else 0
    maximum = float(finite.max()) if finite.size else 0

    def cell_color(value):
        if pd.isna(value):
            return HEATMAP_COLORS[0]
        if maximum == minimum:
            position = 1 if maximum > 0 else 0
        else:
            position = (float(value)-minimum)/(maximum-minimum)
        index = min(int(position*len(HEATMAP_COLORS)), len(HEATMAP_COLORS)-1)
        return HEATMAP_COLORS[index]

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
    finish(fig)
    fig.update_xaxes(tickmode='array',tickvals=list(range(len(SLOTS))),ticktext=SLOTS,
                     range=[-.52,len(SLOTS)-.48],fixedrange=True)
    fig.update_yaxes(tickmode='array',tickvals=list(range(len(DAYS))),ticktext=DAYS,
                     range=[len(DAYS)-.48,-.52],fixedrange=True,showgrid=False)
    fig.update_layout(margin=dict(l=82,r=22,t=20,b=72),hovermode='closest')
    legend_start=.68
    for index,color in enumerate(HEATMAP_COLORS):
        x0=legend_start+index*.032
        fig.add_shape(type='rect',xref='paper',yref='paper',x0=x0,x1=x0+.022,
                      y0=-.25,y1=-.19,fillcolor=color,line=dict(color='#ffffff',width=1))
    fig.add_annotation(x=legend_start-.015,y=-.22,xref='paper',yref='paper',text='Menos',
                       showarrow=False,xanchor='right',font=dict(size=11,color=INK))
    fig.add_annotation(x=legend_start+len(HEATMAP_COLORS)*.032,y=-.22,xref='paper',yref='paper',
                       text='Más',showarrow=False,xanchor='left',font=dict(size=11,color=INK))
    return fig


def confusion(metrics):
    if metrics['Observaciones'] is None:
        return empty()
    z = [[metrics['TN'],metrics['FP']],[metrics['FN'],metrics['TP']]]
    labels = [['Negativos<br>correctos','Falsas<br>alertas'],['Positivos<br>omitidos','Positivos<br>detectados']]
    fig = go.Figure(go.Heatmap(x=['Sin alerta','Con alerta'],y=['Etiqueta 0','Etiqueta 1'],z=z,
        colorscale=MAP_COLORS, showscale=False, text=labels,
        texttemplate='%{text}<br><b>%{z:,}</b>', hovertemplate='%{text}: %{z:,}<extra></extra>'))
    fig.update_yaxes(autorange='reversed',title='Observado')
    fig.update_xaxes(title='Clasificación del modelo')
    return finish(fig)


def curves(rows):
    if rows.empty or rows.Alto_Riesgo.nunique()<2:
        return empty('ROC requiere ambas clases en la selección.'), empty('Curvas no comparables: solo una clase observada.')
    fpr,tpr,_ = roc_curve(rows.Alto_Riesgo,rows.Score)
    p,r,_ = precision_recall_curve(rows.Alto_Riesgo,rows.Score)
    def sample(x,y):
        idx=np.unique(np.linspace(0,len(x)-1,min(len(x),600)).astype(int))
        return x[idx],y[idx]
    x,y=sample(fpr,tpr)
    roc=go.Figure(go.Scatter(x=x,y=y,mode='lines',name='RF ajustado',line_color=TEAL))
    roc.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',name='Sin discriminación',line=dict(color='#9babb5',dash='dot')))
    roc.update_xaxes(title='Tasa de falsas alertas',range=[0,1]);roc.update_yaxes(title='Recall',range=[0,1])
    x,y=sample(r,p)
    pr=go.Figure(go.Scatter(x=x,y=y,mode='lines',name='RF ajustado',line_color=TEAL))
    pr.add_hline(y=float(rows.Alto_Riesgo.mean()),line_dash='dot',line_color=GOLD)
    pr.update_xaxes(title='Recall',range=[0,1]);pr.update_yaxes(title='Precisión',range=[0,1])
    return finish(roc),finish(pr)


def calibration(rows):
    if rows.empty:
        return empty()
    df=rows.copy()
    df['Grupo']=pd.cut(df.Score,bins=np.linspace(0,1,11),include_lowest=True)
    means=df.groupby('Grupo',observed=True).agg(Score=('Score','mean'),Frecuencia=('Alto_Riesgo','mean'),N=('Score','size'))
    fig=go.Figure(go.Scatter(x=means.Score,y=means.Frecuencia,mode='lines+markers',name='RF ajustado',
        customdata=means[['N']],hovertemplate='Score medio: %{x:.3f}<br>Frecuencia: %{y:.3f}<br>Casos: %{customdata[0]}<extra></extra>'))
    fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',name='Calibración ideal',line=dict(color='#9babb5',dash='dot')))
    fig.update_xaxes(title='Score medio · intervalos fijos de 0,1',range=[0,1])
    fig.update_yaxes(title='Frecuencia observada de la etiqueta',range=[0,1])
    return finish(fig)
