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
from dash.dependencies import ClientsideFunction, Input, Output, State
from sqlalchemy import create_engine

from components import header, table, filters
from controls import df, df_small
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

        dcc.Tabs(id='tabs-control', value='graphs', children=[
            dcc.Tab(label='Graphs', value='graphs'),
            dcc.Tab(label='Data', value='data'),
        ]),

        # content will be rendered in this element
        html.Div(id='tab-content')

    ],
    id="mainContainer",
    style={"display": "flex", "flex-direction": "column"},
)


@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs-control', 'value')]
)
def update_content(value):
    if value == 'data':
        return data.layout

    return graphs.layout


@app.callback(
    Output('amnt-inconsistencies-text', 'children'),
    [
        Input('cross-filter-options', 'year_slider'),
        Input('cross-filter-options', 'grupo_dropdown')
    ]
)
def update_amnt_inconsistencies(year_slider, grupo_dropdown):
    import random

    print(year_slider)
    print(grupo_dropdown)
    
    return random.randint(1, 10000)


# Main
if __name__ == "__main__":
    app.run_server(debug=True)
