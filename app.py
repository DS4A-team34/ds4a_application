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
from controls import DB, DB3, db2, table_df, tipo_proceso_dict, datevalues, grupo_dict
from dash.exceptions import PreventUpdate
from layouts import data, files, graphs

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


# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id="aggregate_data"),
        # empty Div to trigger javascript file for graph resizing
        html.Div(id="output-clientside"),

        # header
        header.component,

        dcc.Tabs(id='tabs-control', value='graphs', children=[
            dcc.Tab(label='Dahboard', value='graphs'),
            dcc.Tab(label='Gestor de archivos', value='files'),
            dcc.Tab(label='Auditoría', value='contracts'),
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
    content_dict = {
        'files': files.layout,
        'contracts': data.layout,
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
    Output('amnt-inconsistencies-text', 'children'),
    [
        Input('year_slider', 'value'),
        Input('grupo_dropdown', 'value'),
        Input('estado_proceso_dropdown', 'value'),
    ]
)
def update_amnt_inconsistencies(year_slider: list, grupo_dropdown: list, estado_proceso_dropdown: list):
    import random
    dff = filter_dataframe(table_df, year_slider, grupo_dropdown, estado_proceso_dropdown)
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
    dff = filter_dataframe(table_df, year_slider, grupo_dropdown, estado_proceso_dropdown)
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
    dff = filter_dataframe(table_df, year_slider, grupo_dropdown, estado_proceso_dropdown)
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
    # dff = filter_dataframe(table_df, year_slider, grupo_dropdown, estado_proceso_dropdown)
    # count_reviewed = random.randint(1, len(dff))
    return f'0/0'

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
    dff['period'] = dff['period'].astype(str)
    dff['nombregrupo'] = dff['grupoid'].map(grupo_dict)
    
    # dff = pd.read_sql(
    #     f'''
    #     SELECT annosecop, A.grupoid, nombregrupo, count(A.grupoid) 
    #     FROM secop1general C JOIN secop1grupo A 
    #     ON C.grupoid=A.grupoid
    #     WHERE C.grupoid in ({grupo_list}) and annosecop in ({year_list})
    #     group by annosecop, nombregrupo, A.grupoid
    #     HAVING count(A.grupoid) > 10000
    #     ORDER BY count(A.grupoid) DESC
    #     ''', engine)

    fig = px.bar(dff, y="count", x="period", color='nombregrupo',
                 title='Grupos más frecuentes por periodo',
                 labels={'count': 'Cantidad', 'period': 'Periodo'}).update_layout(legend_title_text='Nombre grupo')

    return fig


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
    Output('contracts-table', "data"),
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

        return dff.to_dict('records')
    except AttributeError:
        raise PreventUpdate


@app.callback(
    [
        Output('selected-contracts-text', 'children'),
        Output('selected-rows', 'children'),
        Output('process-dialog', 'message')
    ],
    [Input('contracts-table', 'selected_rows'),]
)
def update_styles(selected_rows):
    # selected columns is a list of indexes
    # uuid_selected = table_df.iloc[selected_columns]['uuid']
    dialog = f"Selected rows: {selected_rows}"
    return len(selected_rows), selected_rows, dialog


@app.callback(Output('process-dialog', 'displayed'),
              [Input('button-process', 'n_clicks')])
def display_confirm(n_clicks):
    if n_clicks:
        return True
    return False


# Main
if __name__ == "__main__":
    app.run_server(host=settings.HOST, debug=settings.DEBUG)
