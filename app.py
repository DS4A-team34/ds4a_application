# Import required libraries
import copy
import datetime as dt
import math
import os
import glob
import uuid as u
import pathlib
import pickle
import urllib.request

import boto3
import botocore
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import pandas as pd
import plotly.express as px
from dash.dependencies import ClientsideFunction, Input, Output, State
from sqlalchemy import create_engine

import settings
from components import header
from controls import table_df, tipo_proceso_dict, datevalues, grupo_dict, municipios_dict, engine, df_x, geo_df, geo_json
from dash.exceptions import PreventUpdate
from layouts import data, files, graphs, inspect, inconsistencias
from flask import Flask, render_template, request
from common6 import NER_contrato_textract

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
)
# app.config['suppress_callback_exceptions'] = True
server = app.server

# Create global chart template
mapbox_access_token = "pk.eyJ1IjoicGxvdGx5bWFwYm94IiwiYSI6ImNrOWJqb2F4djBnMjEzbG50amg0dnJieG4ifQ.Zme1-Uzoi75IaFbieBDl3A"

layout = dict(
    autosize=True,
    automargin=True,
    margin=dict(l=30, r=30, b=20, t=40),
    hovermode="closest",
    plot_bgcolor="#F9F9F9",
    paper_bgcolor="#F9F9F9",
    legend=dict(font=dict(size=10), orientation="h"),
    title="Satellite Overview",
    mapbox=dict(
        accesstoken=mapbox_access_token,
        style="light",
        center=dict(lon=-78.05, lat=42.54),
        zoom=7,
    ),
)


app.title = 'DS4A 3.0 - Team #34'

# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),

        dcc.Location(id='url', refresh=False),

        # header
        header.component,

        dcc.Tabs(id='tabs-control', value='graphs', children=[
            dcc.Tab(label='Explorar', value='graphs'),
            dcc.Tab(label='Procesar', value='contracts'),
            dcc.Tab(label='Validar', value='inspect'),
            dcc.Tab(label='Identificar Inconsistencias', value='inconsistencias'),
            # dcc.Tab(label='Gestor de documentos', value='files'),
        ]),

        # content will be rendered in this element
        html.Div(id='tab-content')

    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)

# Create callbacks
app.clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="resize"),
    Output("output-clientside", "children"),
    [Input("grupos_contratos_grapsh", "figure")],
)


@app.callback(
    Output('tab-content', 'children'),
    [
        Input('tabs-control', 'value'), 
        # Input('button-inspect', 'n_clicks'),
    ]
)
def update_content(value):
    content_dict = {
        'files': files.layout,
        'contracts': data.layout,
        'inspect': inspect.layout,
        'inconsistencias': inconsistencias.layout
    }
    
    return content_dict.get(value, graphs.layout)


def filter_dataframe(df, year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list) -> pd.DataFrame:
    min_date = datevalues.get(year_slider[0])
    max_date = datevalues.get(year_slider[-1])

    dff = df[
        (df["fechacargasecop"] >= min_date)
        & (df["fechacargasecop"] <= max_date)
        & (df["grupoid"].isin(grupo_dropdown))
        & (df["procesoestatus"].isin(estado_proceso_dropdown))
    ].copy()
    return dff


@app.callback(
    Output('date_range_text', 'children'),
    [Input('year_slider', 'value'),]
)
def update_date_range(value: list):
    return f"Rango de fechas: {value[0]} - {value[-1]}"


@app.callback(
    Output('contracts_deparment_plot', 'figure'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
        Input('tipo_municipio_dropdown', 'value'),
    ]
)
def update_municipio_estado_graph(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list, tipo_municipio_dropdown: str):
    variable = tipo_municipio_dropdown
    variable_readable = municipios_dict.get(variable)

    dff = filter_dataframe(table_df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    dff = dff[~(dff[variable].isna()) & ~(dff[variable] == 'No definido')].copy()

    dff = dff.groupby([variable, 'procesoestatus'])['uuid'].count().reset_index()
    dff.rename(columns={'uuid': 'count'}, inplace=True)
    dff.sort_values(by='count', ascending=False, inplace=True)

    title = f'Concentración de contratos por "{variable_readable}" y estado del proceso'

    return px.treemap(dff.head(10), path=[variable, 'procesoestatus'], values='count',
                      title=title)


def get_filters_string(dropdown: list) -> str:
    return str(dropdown).replace('[', '').replace(']', '')


@app.callback(
    Output('count_contratos_graph', 'figure'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_contratos_graph(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):    
    dff = filter_dataframe(table_df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    dff = dff.groupby('fechacargasecop')['uuid'].count().reset_index()
    dff.rename(columns={'uuid': 'count'}, inplace=True)

    fig = px.line(dff, x="fechacargasecop", y="count", title='Cantidad de contratos cargados a SECOP I', labels={
                  'count': 'Cantidad', 'fechacargasecop': 'Año'})

    return fig


@app.callback(
    Output('grupos_contratos_grapsh', 'figure'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_grupos_contratos(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    dff = filter_dataframe(table_df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    dff = dff.groupby(['period', 'grupoid'])['uuid'].count().reset_index()
    dff.rename(columns={'uuid': 'count'}, inplace=True)
    dff['nombregrupo'] = dff['grupoid'].map(grupo_dict)

    fig = px.bar(dff, y="count", x="period", color='nombregrupo',
                 title='Grupos más frecuentes por periodo',
                 labels={'count': 'Cantidad', 'period': 'Periodo'}).update_layout(legend_title_text='Nombre grupo')

    return fig


# MAPA PLOT
def filter_geo_dataframe(df, grupo_dropdown: list, estado_proceso_dropdown: list) -> pd.DataFrame:
    dff = df[
        (df["grupoid"].isin(grupo_dropdown))
        & (df["procesostatus"].isin(estado_proceso_dropdown))
    ].copy()
    return dff


@app.callback(
    [
        Output('contracts_map_plot', 'figure'),
        Output('map-title', 'children')
    ],
    [
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
        Input('map-variable', 'value'),
    ]
)
def update_map_plot(grupo_dropdown: list, estado_proceso_dropdown: list, variable: str):
    title = f'Concentración de {variable} por departamento'

    dff = filter_geo_dataframe(geo_df, grupo_dropdown, estado_proceso_dropdown)

    dff = dff.groupby(by=['dpto', 'id'])[variable].sum().reset_index()

    fig = px.choropleth_mapbox(dff, geojson=geo_json, locations='id', color=variable,
                           color_continuous_scale="Viridis",
                           range_color=(0, dff[variable].max()),
                           mapbox_style="carto-positron",
                           zoom=4.5, center = {"lat": 4.60971, "lon": -74.08175},
                           hover_name='dpto',
                           opacity=0.5,
                           title=title
                          ).update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    return fig, title

# AUDITORÍA 
operators = [['ge ', '>='],
             ['le ', '<='],
             ['lt ', '<'],
             ['gt ', '>'],
             ['ne ', '!='],
             ['eq ', '='],
             ['contains '],
             ['datestartswith ']]


def split_filter_part(filter_part):
    for operator_type in operators:
        for operator in operator_type:
            if operator in filter_part:
                name_part, value_part = filter_part.split(operator, 1)
                name = name_part[name_part.find('{') + 1: name_part.rfind('}')]

                value_part = value_part.strip()
                v0 = value_part[0]
                if (v0 == value_part[-1] and v0 in ("'", '"', '`')):
                    value = value_part[1: -1].replace('\\' + v0, v0)
                else:
                    try:
                        value = float(value_part)
                    except ValueError:
                        value = value_part

                # word operators need spaces after them in the filter string,
                # but we don't want these later
                return name, operator_type[0].strip(), value

    return [None] * 3


@app.callback(
    [Output('contracts-table', "data"),
     Output('contracts-table', 'tooltip_data')],
    [Input('contracts-table', "filter_query")])
def update_table(filter):
    try:
        filtering_expressions = filter.split(' && ')
        dff = table_df
        for filter_part in filtering_expressions:
            col_name, operator, filter_value = split_filter_part(filter_part)

            if operator in ('eq', 'ne', 'lt', 'le', 'gt', 'ge'):
                # these operators match pandas series operator method names
                dff = dff.loc[getattr(dff[col_name], operator)(filter_value)]
            elif operator == 'contains':
                dff = dff.loc[dff[col_name].str.contains(filter_value)]
            elif operator == 'datestartswith':
                # this is a simplification of the front-end filtering logic,
                # only works with complete fields in standard format
                dff = dff.loc[dff[col_name].str.startswith(filter_value)]
        
        data = dff.to_dict('records')
        tooltip = [{
            column: {'value': str(value), 'type': 'markdown'}
            for column, value in row.items()
        } for row in data]
        
        return data, tooltip
    except AttributeError:
        raise PreventUpdate


# AUDITORÍA

@app.callback(
    Output('selected-rows', 'children'),
    [Input('contracts-table', 'selected_rows'),]
)
def update_selected_rows(selected_rows):
    return selected_rows


@app.callback(
    Output('selected-contracts-text', 'children'),
    [Input('selected-rows', 'children'),]
)
def update_selected_contracts_text(selected_rows):
    return len(selected_rows)


# @app.callback(
#     Output('process-dialog', 'message'),
#     [Input('selected-rows', 'children'),]
# )
def update_dialog_text_selected_rows(selected_rows):
    # uuid_selected = table_df.iloc[selected_columns]['uuid']
    dialog = f"Selected rows: {selected_rows}"
    return dialog


@app.callback([Output('process-dialog', 'displayed'),
               Output('process-dialog', 'message')],
              [Input('button-process', 'n_clicks')],
              [State('selected-rows', 'children'),
              State('contracts-table', 'data')])
def display_confirm(n_clicks, rows: list, data):
    if not rows:
        return False, None
    
    show = True
    dff = pd.DataFrame(data)
    for r in rows:
        try:
            contract_df = dff.iloc[r].copy()
            uuid = contract_df['uuid']

            document = get_contract_document_info(uuid)
            full_path = f"{document['folder_original']}/{document['file_basename_original']}"

            validation_score = NER_contrato_textract(contract_df, full_path)
        except Exception as e:
            print(e)
            message = f'Error inesperado procesando {uuid}'
        else:
            message = f'Procesamiento exitoso para {uuid}. \
                Validation score: {round(validation_score * 100, 3)}%. Puede dirigirse a la pestaña de Inspección.'
    
    return show, message


def get_boto3_client() -> boto3.client:
    client = boto3.client('s3',
                          aws_access_key_id=settings.AWS['ACCESS_KEY_ID'], 
                          aws_secret_access_key=settings.AWS['SECRET_ACCESS_KEY'])
    return client


def get_boto3_resource() -> boto3.resource:
    resource = boto3.resource('s3',
                          aws_access_key_id=settings.AWS['ACCESS_KEY_ID'], 
                          aws_secret_access_key=settings.AWS['SECRET_ACCESS_KEY'])
    return resource


def get_contract_document_info(uuid: str):
    document_df = pd.read_sql(
        f'''
        SELECT folder_original, file_basename_original, file_extension, pages, document_type
        FROM doc_contrato
        WHERE uuid = '{uuid}'
        ''', engine)
    
    return document_df.iloc[0].to_dict() if not document_df.empty else {}


@app.callback([Output('inspect-dialog', 'displayed'),
               Output('inspect-dialog', 'message'),
               Output('iframe-contract-file', 'data'),
               Output('iframe-contract-extracted', 'src'),
               Output('validation-table', 'data'),
               Output('validation-score', 'children'),
               Output('validation-score-card', 'style')],
              [Input('button-inspect', 'n_clicks')],
              [State('input-uuid', 'value')],
            )
def update_inspect_dialog(n_clicks, uuid: str):
    # ideal scenario won't show message
    show = False
    message = ''

    # define deafult values
    local_pdf = None
    html_url = None
    data = None
    val_score = 0
    style = None

    # initial state
    if not uuid:
        return show, message, local_pdf, html_url, data, val_score, style

    # get document info
    document = get_contract_document_info(uuid)
    if not document:
        show = True
        message = f'No se registran documentos en el sistema para {uuid}'

        return show, message, local_pdf, html_url, data, val_score, style
    
    for file in glob.glob('assets/*.pdf'):
        os.remove(file)
    
    # retrieve validation data
    validation_df = pd.read_sql(
        f'''
        select c."nombreCampo", valorbd, valordoc, coincidencia 
        from doc_validados v
        join tipocampo c on c.id = v.tipocampo 
        where uuid = '{uuid}'
        ''', engine)
    
    if not validation_df.empty:
        val_score = validation_df['coincidencia'].mean()
        style = {'background-color': 'red'}
        if val_score >= 0.9:
            style = {'background-color': 'green'}
        elif 0.6 < val_score < 0.9:
            style = {'background-color': 'yellow'}
        
        val_score = f'{round(val_score * 100, 3)}%'
        
        data = validation_df.to_dict('records')
    else:
        show = True
        message = f'El registro {uuid} no ha sido procesado. Dirígase al módulo de auditoría.'
    
    s3_resource = get_boto3_resource()
    s3_client = get_boto3_client()
    
    # compute files paths 
    fullname_pdf = f"{document['folder_original']}/{document['file_basename_original']}"
    fullname = fullname_pdf.replace(document['file_extension'], '')

    # first pdf file
    local_pdf = f"assets/{u.uuid4()}.pdf"
    try:
        s3_client.download_file(settings.AWS['BUCKET_NAME'], fullname_pdf, local_pdf)
    except Exception as e:
        print(e)
        show = True
        local_pdf = None
        message = f'No es posible encontrar el documento del contrato {uuid}'

        return show, message, local_pdf, html_url, data, val_score, style
    
    # now html file
    fullname_html = fullname + '.html'
    
    try:
        s3_resource.Object(settings.AWS['BUCKET_NAME'], fullname_html).load()
    except botocore.exceptions.ClientError as e:
        print(e)
        show = True
        html_url = None
        message = f'No es posible encontrar el archivo resultante de la exttracción para {uuid}'

        return show, message, local_pdf, html_url, data, val_score, style
    else:
        html_url = f"{settings.AWS['BUCKET_URL']}/{fullname_html}"

        return show, message, local_pdf, html_url, data, val_score, style


# INCONSISTENCIAS
def filter_df_inconsistencias(df, param: str, value: str):
    dff = df[df[param] == value].copy()
    return dff


@app.callback(
    Output('radio-item-grupo', 'options'),
    [Input('entidad-dropdown', 'value')],
)
def update_grupo_options(entidad: str):
    dff = filter_df_inconsistencias(df_x, 'entidadnombre', entidad)
    grupo_ids = dff['grupoid'].unique()

    return [{"label": v, "value": k} for k, v in grupo_dict.items() if k in grupo_ids]


def SetMoneda(num, simbolo="US$", n_decimales=2):
    """Convierte el numero en un string en formato moneda
    SetMoneda(45924.457, 'RD$', 2) --> 'RD$ 45,924.46'     
    """
    #con abs, nos aseguramos que los dec. sea un positivo.
    n_decimales = abs(n_decimales)
    
    #se redondea a los decimales idicados.
    num = round(num, n_decimales)

    #se divide el entero del decimal y obtenemos los string
    num, dec = str(num).split(".")

    #si el num tiene menos decimales que los que se quieren mostrar,
    #se completan los faltantes con ceros.
    dec += "0" * (n_decimales - len(dec))
    
    #se invierte el num, para facilitar la adicion de comas.
    num = num[::-1]
    
    #se crea una lista con las cifras de miles como elementos.
    l = [num[pos:pos+3][::-1] for pos in range(0,50,3) if (num[pos:pos+3])]
    l.reverse()
    
    #se pasa la lista a string, uniendo sus elementos con comas.
    num = str.join(",", l)
    
    #si el numero es negativo, se quita una coma sobrante.
    try:
        if num[0:2] == "-,":
            num = "-%s" % num[2:]
    except IndexError:
        pass
    
    #si no se especifican decimales, se retorna un numero entero.
    if not n_decimales:
        return "%s %s" % (simbolo, num)
        
    return "%s %s.%s" % (simbolo, num, dec)


@app.callback(
    Output('total-valor-contrato-text', 'children'),
    [Input('radio-item-grupo', 'value'),
     Input('entidad-dropdown', 'value')]
)
def update_total_valor_contrato(grupo: str, entidad: str):
    dff = filter_df_inconsistencias(df_x, 'entidadnombre', entidad)
    dff = filter_df_inconsistencias(dff, 'grupoid', grupo)
    return SetMoneda(dff['contratocuantia'][dff['contratocuantia'].index[0]],"$", 2) if not dff.empty else 0


@app.callback(
    Output('total-valor-adiciones-text', 'children'),
    [Input('radio-item-grupo', 'value'),
     Input('entidad-dropdown', 'value')]
)
def update_total_adiciones_contrato(grupo: str, entidad: str):
    dff = filter_df_inconsistencias(df_x, 'entidadnombre', entidad)
    dff = filter_df_inconsistencias(dff, 'grupoid', grupo)
    return SetMoneda(dff['contratoconadicionesvalor'][dff['contratocuantia'].index[0]],"$", 2) if not dff.empty else 0


@app.callback(
    Output('total-cantidad-text', 'children'),
    [Input('radio-item-grupo', 'value'),
     Input('entidad-dropdown', 'value')]
)
def update_total_cantida(grupo: str, entidad: str):
    dff = filter_df_inconsistencias(df_x, 'entidadnombre', entidad)
    dff = filter_df_inconsistencias(dff, 'grupoid', grupo)
    return dff['cantidad'] if not dff.empty else 0


@app.callback(
    Output('ooc_graph_id', 'value'),
    [Input('radio-item-grupo', 'value'),
     Input('entidad-dropdown', 'value')]
)
def update_coincidencia_pct(grupo: str, entidad: str):
    dff = filter_df_inconsistencias(df_x, 'entidadnombre', entidad)
    dff = filter_df_inconsistencias(dff, 'grupoid', grupo)
    return dff['coincidencia'] * 10

# Main
if __name__ == "__main__":
    app.run_server(host=settings.HOST, debug=settings.DEBUG)
