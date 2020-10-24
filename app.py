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
import pandas as pd
import plotly.express as px
from dash.dependencies import ClientsideFunction, Input, Output, State
from sqlalchemy import create_engine

import settings
from components import filters, header, indicators, table
from controls import df, df_small, DB, db2, DB3
from layouts import data, graphs

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

        html.Div(
            [
                filters.component,
                indicators.component,
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="tipo_proceso_graph")],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="municipio_estado_graph", figure=px.treemap(DB, path=['municipioentrega','procesoestatus'], values='count'))],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="municipio_estado_graph", figure=px.treemap(DB, path=['municipioentrega','procesoestatus'], values='count'))],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="municipio_estado_graph", figure=px.treemap(DB, path=['municipioentrega','procesoestatus'], values='count'))],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        ),

        # dcc.Tabs(id='tabs-control', value='graphs', children=[
        #     dcc.Tab(label='Graphs', value='graphs'),
        #     dcc.Tab(label='Data', value='data'),
        # ]),

        # content will be rendered in this element
        # html.Div(id='tab-content')

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

# @app.callback(
#     Output('tab-content', 'children'),
#     [Input('tabs-control', 'value')]
# )


def update_content(value):
    if value == 'data':
        return data.layout

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
    dff = filter_dataframe(df, year_slider, grupo_dropdown, estado_proceso_dropdown)
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
    dff = filter_dataframe(df, year_slider, grupo_dropdown, estado_proceso_dropdown)
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
    dff = filter_dataframe(df, year_slider, grupo_dropdown, estado_proceso_dropdown)
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
    dff = filter_dataframe(df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    count_reviewed = random.randint(1, len(dff))
    return f'{count_reviewed}/{len(dff)}'


@app.callback(
    Output('tipo_proceso_graph', 'figure'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_tipo_proceso_graph(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    dff = filter_dataframe(df, year_slider, grupo_dropdown, estado_proceso_dropdown)

    graph_df = dff.groupby(['ID Tipo de Proceso'])['UID'].count(
    ).reset_index().rename(columns={'UID': 'count'})
    graph_df.sort_values('count', ascending=False, inplace=True)
    graph_df = graph_df.head(5)

    fig = px.bar(graph_df, x='ID Tipo de Proceso', y='count')

    return fig


# Main
if __name__ == "__main__":
    app.run_server(host='0.0.0.0', debug=settings.DEBUG)
