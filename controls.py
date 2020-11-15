import json

import dash_table.FormatTemplate as FormatTemplate
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pandas.tseries.offsets import DateOffset
from plotly.subplots import make_subplots
from sqlalchemy import create_engine

import settings

# create database connection
engine = create_engine(settings.DATABASE['CONNECTION'], max_overflow=20)

# Table section
limit = 100000
table_df = pd.read_sql(
    f'''
    SELECT v.*, procesado, municipioejecuta, municipioentrega, c.fechacargasecop, g.grupoid, procesoid
    FROM secop1validacion v, secop1contrato c, secop1general g, doc_contrato dc 
    WHERE v.uuid = c.uuid and g.uuid = v.uuid and dc.uuid  = v.uuid and dc.document_type = '13'
    ''', engine)

# get dates range
min_date_cargue = table_df['fechacargasecop'].min()
max_date_cargue = table_df['fechacargasecop'].max()

dates_range = pd.date_range(start=min_date_cargue,
                            end=max_date_cargue, freq='M')
dates_amount = len(dates_range)
dlist = pd.DatetimeIndex(dates_range).normalize()
tags = {}
datevalues = {}
x = 1
for i in dlist:
    tags[x] = (i + DateOffset(months=1)).strftime('%b')
    datevalues[x] = i
    x = x + 1

# get periods for groups
table_df['period'] = pd.to_datetime(
    table_df['fechacargasecop']).dt.to_period("M")
table_df['period'] = table_df['period'].astype(str)

# define some formats
format_fields = {
    'money': ['contratocuantia', 'contratoconadicionesvalor'],
    'datetime': ['fechacargasecop', 'firmacontratofecha', 'period'],
    'numeric': []
}

formats = {
    'money': {'type': 'numeric', 'format': FormatTemplate.money(0)},
    'datetime': {'type': 'datetime'},
    'numeric': {'type': 'numeric'},
    'text': {'type': 'text'}
}


def get_field_info(column: str, format_fields: dict):
    result = {"name": column, "id": column}

    final_format = 'text'
    for f, fields in format_fields.items():
        if column in fields:
            final_format = f
            break

    format_dict = formats.get(final_format)
    result.update(format_dict)
    return result


table_columns = [get_field_info(c, format_fields) for c in table_df.columns]


# PDF pikles
filename_files = 'data/df_files4B_pandas.pickle'
df_files = pd.read_pickle(filename_files)

# define dict and options for "grupo"
grupos = table_df['grupoid'].unique()
grupo_df = pd.read_sql_table('secop1grupo', engine)
grupo_dict = dict(zip(grupo_df['grupoid'], grupo_df['nombregrupo']))
grupo_options = [{"label": v, "value": k}
                 for k, v in grupo_dict.items() if k in grupos]

# TODO: create "estado_proceso" table
estado_proceso_dict = {e: e for e in sorted(
    table_df['procesoestatus'].unique())}
estado_proceso_options = [{"label": v, "value": k}
                          for k, v in estado_proceso_dict.items()]

# define dict and options for "tipo de proceso"
procesos = table_df['procesoid'].unique()
tipo_proceso_df = pd.read_sql_table('secop1proceso', engine)
tipo_proceso_dict = dict(
    zip(tipo_proceso_df['procesoid'], tipo_proceso_df['procesotipo']))
tipo_proceso_options = [{"label": v, "value": k}
                        for k, v in tipo_proceso_dict.items() if k in procesos]


# define Municipio options
municipios_dict = {
    'municipioobtencion': 'Municipio Obtención',
    'municipioejecuta': 'Municipio Ejecuta',
    'municipioentrega': 'Municipio Entrega',
}
municipios_options = [{"label": v, "value": k}
                      for k, v in municipios_dict.items()]


# TODO: Files (pending)
def get_pivot_heatmap(df, values, margins):
    df_pivot = pd.pivot_table(data=df,
                              index='document_type_nombre',
                              columns='process_name',
                              values=values,
                              aggfunc='sum',
                              margins=margins)
    return df_pivot


def df_to_plotly(df):
    return {'z': df.values.tolist(),
            'x': df.columns.tolist(),
            'y': df.index.tolist()}


def plot_pages(df):
    df_pivot = get_pivot_heatmap(df, 'pages', margins=False)
    data = df_to_plotly(df_pivot)
    fig = go.Figure(data=go.Heatmap(z=data['z'],
                                    x=data['x'],
                                    y=data['y'],
                                    colorscale='Viridis',
                                    ))

    fig.update_layout(
        title="Quantity of pages by document' type and process' type",
        height=750,
        margin={'b': 300, 'l': 100}
    )
    return fig


def plot_size(df):
    df_pivot = get_pivot_heatmap(df, 'file_size_MB', margins=False)
    data = df_to_plotly(df_pivot)
    fig = go.Figure(data=go.Heatmap(z=data['z'],
                                    x=data['x'],
                                    y=data['y'],
                                    colorscale='Viridis',
                                    ))

    fig.update_layout(
        title="Storage size in MB by document' type and process' type",
        height=750,
        margin={'b': 300, 'l': 100}
    )
    return fig


quantity_files_fig = plot_pages(df_files)
size_files_fig = plot_size(df_files)

# VALIDATION SECTION
validados_count = pd.read_sql(
    '''select count(distinct uuid)
from doc_validados dv ''', engine)
validados_count = int(validados_count.iloc[0, 0])

availables_count = pd.read_sql(
    '''select count(distinct uuid)
from doc_contrato dc
where document_type = '13' ''', engine)
availables_count = int(availables_count.iloc[0, 0])

validation_state = f'{validados_count} / {availables_count}'

# define dict and options for "tipocampo"
tipo_campo_df = pd.read_sql_table('tipocampo', engine)
tipo_campo_dict = dict(zip(tipo_campo_df['id'], tipo_campo_df['nombreCampo']))
tipo_campo_options = [{"label": v, "value": k}
                      for k, v in tipo_proceso_dict.items()]


# GENERAL
df_x = pd.read_sql(
    '''
    SELECT procesoestatus, g.grupoid,  entidadnombre,
        sum(contratocuantia) contratocuantia, sum(contratoconadicionesvalor) contratoconadicionesvalor,
    round(avg(coincidencia),3) coincidencia, 
    case when round(avg(coincidencia),3) < 0.8 then 'RED'
    when round(avg(coincidencia),3) between 0.800001 and 0.98 then 'YELLOW'
    when round(avg(coincidencia),3) > 0.98 then 'GREEN'
    else '?'
    end  gravedad,
    count(1) cantidad
    FROM public.doc_validados d, public.secop1validacion s, secop1general g 
    where d.uuid = s.uuid and s.uuid = g.uuid
    group by procesoestatus, g.grupoid, entidadnombre
    ORDER BY 6
    ''', engine)


# MAPA
geo_df = pd.read_sql_table('dash_geografico', engine)
with open('data/colombia.json') as f:
    geo_json = json.load(f)

for i in range(0, 33):
    geo_json["features"][i]['id'] = str(i)


# INCONSISTENCIAS
df1 = pd.read_sql(
    '''
    SELECT entidadnombre,  
        sum(contratocuantia+contratoconadicionesvalor) contratocuantia,
        round(avg(coincidencia),3) coincidencia
    FROM public.doc_validados d, public.secop1validacion s, secop1general g 
    where d.uuid = s.uuid and s.uuid = g.uuid
    group by entidadnombre
    having round(avg(coincidencia),3) > 0.98 
    order by 3 
    limit 20
    ''', engine)


def contratistas_top_good_fig(df1):
    y_saving = df1['coincidencia']*100
    y_net_worth = df1['contratocuantia']
    x = df1['entidadnombre']

    # Creating two subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=True,
                        shared_yaxes=False, vertical_spacing=0.001)

    fig.append_trace(go.Bar(
        x=y_saving,
        y=x,
        marker=dict(
            color='rgba(50, 171, 96, 0.6)',
            line=dict(
                color='rgba(50, 171, 96, 1.0)',
                width=1),
        ),
        name='Porcentaje de coincidencia',
        orientation='h',
    ), 1, 1)

    fig.append_trace(go.Scatter(
        x=y_net_worth, y=x,
        mode='lines+markers',
        line_color='rgb(128, 0, 128)',
        name='Cantidad total del valor contrato',
    ), 1, 2)

    fig.update_layout(
        title='Entidades con mayor porcentaje de similitud',
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 0.85],
        ),
        yaxis2=dict(
            showgrid=False,
            showline=True,
            showticklabels=False,
            linecolor='rgba(102, 102, 102, 0.8)',
            linewidth=2,
            domain=[0, 0.85],
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.1, 0.42],
        ),
        xaxis2=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.47, 1],
            side='top',

        ),
        legend=dict(x=0.029, y=1.038, font_size=10),
        margin=dict(l=100, r=20, t=70, b=70),
        paper_bgcolor='rgb(248, 248, 255)',
        plot_bgcolor='rgb(248, 248, 255)',
    )

    annotations = []

    y_s = np.round(y_saving, decimals=2)
    y_nw = np.rint(y_net_worth)

    # Adding labels
    for ydn, yd, xd in zip(y_nw, y_s, x):
        # labeling the scatter savings
        annotations.append(dict(xref='x2', yref='y2',
                                y=xd, x=ydn - 20000,
                                text='$'+'{:,}'.format(ydn),
                                font=dict(family='Arial', size=12,
                                          color='rgb(128, 0, 128)'),
                                showarrow=False))
        # labeling the bar net worth
        annotations.append(dict(xref='x1', yref='y1',
                                y=xd, x=yd + 20,
                                text=str(yd) + '%',
                                font=dict(family='Arial', size=12,
                                          color='rgb(50, 171, 96)'),
                                showarrow=False))
    # Source
    annotations.append(dict(xref='paper', yref='paper',
                            x=0, y=-0.109,
                            text='Compra eficiente ' +
                                 '(2020), Team #34 DS4A, ',
                            font=dict(family='Arial', size=10,
                                      color='rgb(150,150,150)'),
                            showarrow=False))

    fig.update_layout(annotations=annotations)

    return fig


fig_top_contratistas_good = contratistas_top_good_fig(df1)

df2 = pd.read_sql(
    '''
    SELECT entidadnombre,  
        sum(contratocuantia+contratoconadicionesvalor) contratocuantia,
        round(avg(coincidencia),3) coincidencia
    FROM public.doc_validados d, public.secop1validacion s, secop1general g 
    where d.uuid = s.uuid and s.uuid = g.uuid
    group by entidadnombre
    having round(avg(coincidencia),3) < 0.8 
    order by 3 
    limit 20
    ''', engine)


def contratistas_top_bad_fig(df2):
    entidad = 'entidadnombre'
    # entidad = 'contratistarazsocial'

    y_saving = df2['coincidencia']*100
    y_net_worth =df2['contratocuantia']
    x = df2[entidad]

    # Creating two subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{}, {}]], shared_xaxes=True,
                        shared_yaxes=False, vertical_spacing=0.001)

    fig.append_trace(go.Bar(
        x=y_saving,
        y=x,
        marker=dict(
            color='rgba(50, 171, 96, 0.6)',
            line=dict(
                color='rgba(50, 171, 96, 1.0)',
                width=1),
        ),
        name='Porcentaje de coincidencia',
        orientation='h',
    ), 1, 1)

    fig.append_trace(go.Scatter(
        x=y_net_worth, y=x,
        mode='lines+markers',
        line_color='rgb(128, 0, 128)',
        name='Cantidad total del valor contrato',
    ), 1, 2)

    fig.update_layout(
        title='Entidades con menor porcentaje de similitud',
        yaxis=dict(
            showgrid=False,
            showline=False,
            showticklabels=True,
            domain=[0, 0.85],
        ),
        yaxis2=dict(
            showgrid=False,
            showline=True,
            showticklabels=False,
            linecolor='rgba(102, 102, 102, 0.8)',
            linewidth=2,
            domain=[0, 0.85],
        ),
        xaxis=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.2, 0.42],
        ),
        xaxis2=dict(
            zeroline=False,
            showline=False,
            showticklabels=True,
            showgrid=True,
            domain=[0.47, 1],
            side='top',

        ),
        legend=dict(x=0.029, y=1.038, font_size=10),
        margin=dict(l=100, r=20, t=70, b=70),
        paper_bgcolor='rgb(248, 248, 255)',
        plot_bgcolor='rgb(248, 248, 255)',
    )

    annotations = []

    y_s = np.round(y_saving, decimals=2)
    y_nw = np.rint(y_net_worth)

    # Adding labels
    for ydn, yd, xd in zip(y_nw, y_s, x):
        # labeling the scatter savings
        annotations.append(dict(xref='x2', yref='y2',
                                y=xd, x=ydn - 20000,
                                text='$'+'{:,}'.format(ydn) ,
                                font=dict(family='Arial', size=12,
                                        color='rgb(128, 0, 128)'),
                                showarrow=False))
        # labeling the bar net worth
        annotations.append(dict(xref='x1', yref='y1',
                                y=xd, x=yd +5,
                                text=str(yd) + '%',
                                font=dict(family='Arial', size=12,
                                        color='rgb(50, 171, 96)'),
                                showarrow=False))
    # Source
    annotations.append(dict(xref='paper', yref='paper',
                            x=0, y=-0.109,
                            text='Compra eficiente ' +
                                '(2020), Team #34 DS4A, ',
                            font=dict(family='Arial', size=10, color='rgb(150,150,150)'),
                            showarrow=False))

    fig.update_layout(annotations=annotations)

    return fig


fig_top_contratistas_bad = contratistas_top_bad_fig(df2)


# INSPECTION BY SPECIFIC CONTRACT
format_fields = {
    'money': [],
    'datetime': [],
    'numeric': ['coincidencia']
}

val_column_representations = {
    'nombreCampo': 'Nombre del campo',
    'valorbd': 'Valor registrado',
    'valordoc': 'Valor en documento',
    'coincidencia': 'Similitud'
}


def get_val_field_info(column: str, name: str, format_fields: dict):
    result = {"name": name, "id": column}

    final_format = 'text'
    for f, fields in format_fields.items():
        if column in fields:
            final_format = f
            break

    format_dict = formats.get(final_format)
    result.update(format_dict)
    return result


val_columns = [get_val_field_info(c, n, format_fields)
               for c, n in val_column_representations.items()]
