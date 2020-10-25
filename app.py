# Import required libraries
import copy
import datetime as dt
import math
import os
import pathlib
import pickle
import urllib.request

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
from controls import DB, DB3, db2, df, tipo_proceso_dict
from layouts import data, files, graphs

# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}]
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


# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),

        # header
        header.component,

        dcc.Tabs(id='tabs-control', value='graphs', children=[
            dcc.Tab(label='Graphs', value='graphs'),
            dcc.Tab(label='Files', value='files'),
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
    [Input("count_graph", "figure")],
)


@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs-control', 'value')]
)
def update_content(value):
    if value == 'files':
        return files.layout

    return graphs.layout


def filter_dataframe(df, year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list) -> pd.DataFrame:
    dff = df[
        df["Anno Cargue SECOP"].isin(year_slider)
        & df["ID Grupo"].isin(grupo_dropdown)
        & df["Estado del Proceso"].isin(estado_proceso_dropdown)
    ].copy()
    return dff


@app.callback(
    Output('amnt-inconsistencies-text', 'children'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_amnt_inconsistencies(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    import random
    dff = filter_dataframe(
        df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    return random.randint(0, len(dff) / 2)


@app.callback(
    Output('pct-inconsistencies-text', 'children'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_pct_inconsistencies(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    import random
    dff = filter_dataframe(
        df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    return f'{random.randint(0, 100)}%'


@app.callback(
    Output('avg-severity-text', 'children'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_avg_severity(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    import random
    dff = filter_dataframe(
        df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    return random.randint(0, 5)


@app.callback(
    Output('count-reviewed-text', 'children'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_count_reviewed(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    import random
    dff = filter_dataframe(
        df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    count_reviewed = random.randint(1, len(dff))
    return f'{count_reviewed}/{len(dff)}'


def update_tipo_proceso_graph(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    dff = filter_dataframe(
        df, year_slider, grupo_dropdown, estado_proceso_dropdown)

    graph_df = dff.groupby(['ID Tipo de Proceso'])['UID'].count(
    ).reset_index().rename(columns={'UID': 'count'})
    graph_df.sort_values('count', ascending=False, inplace=True)
    graph_df = graph_df.head(5)

    # TODO: add table
    # data = {p: tipo_proceso_dict[p] for p in graph_df['ID Tipo de Proceso']}

    fig = px.bar(graph_df, x='ID Tipo de Proceso', y='count')

    return fig


@app.callback(
    Output('count_graph', 'figure'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_municipio_estado_graph(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    return px.treemap(DB, path=['municipioentrega', 'procesoestatus'], values='count')


def get_filters_string(dropdown: list) -> str:
    return str(dropdown).replace('[', '').replace(']', '')


# @app.callback(
#     Output('count_contratos_graph', 'figure'),
#     [
#         Input('year_slider', 'value'),
#         Input('grupo_dropdown', 'value'),
#         Input('estado_proceso_dropdown', 'value'),
#     ]
# )
def update_contratos_graph(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    estado_proceso_list = get_filters_string(estado_proceso_dropdown)

    dff = pd.read_sql(
        f'''
        SELECT fechacargasecop, count(procesocuantia)
        FROM secop1contrato
        WHERE fechacargasecop BETWEEN '{min(year_slider)}-01-01' and '{max(year_slider)}-12-31'
        AND procesoestatus in ({estado_proceso_list})
        group by fechacargasecop
        ''', engine)

    fig = px.line(dff, x="fechacargasecop", y="count", title='Contratos cargados en SECOP por año', labels={
                  'count': 'Cantidad', 'fechacargasecop': 'Año'})

    return fig

# @app.callback(
#     Output('grupos_contratos_grapsh', 'figure'),
#     [
#         Input('year_slider', 'value'),
#         Input('grupo_dropdown', 'value'),
#         Input('estado_proceso_dropdown', 'value'),
#     ]
# )


def update_grupos_contratos(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    grupo_list = get_filters_string(grupo_dropdown)
    year_list = get_filters_string(year_slider)

    dff = pd.read_sql(
        f'''
        SELECT annosecop, A.grupoid, nombregrupo, count(A.grupoid) 
        FROM secop1general C JOIN secop1grupo A 
        ON C.grupoid=A.grupoid
        WHERE C.grupoid in ({grupo_list}) and annosecop in ({year_list})
        group by annosecop, nombregrupo, A.grupoid
        HAVING count(A.grupoid) > 10000
        ORDER BY count(A.grupoid) DESC
        ''', engine)

    fig = px.bar(dff, y="count", x="annosecop", color='nombregrupo',
                 title='Grupos más frecuentes por año',
                 labels={'count': 'Cantidad', 'annosecop': 'Año'}).update_layout(legend_title_text='Nombre Grupo')

    return fig


# Main
if __name__ == "__main__":
    app.run_server(host=settings.HOST, debug=settings.DEBUG)
