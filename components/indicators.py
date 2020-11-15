import dash_core_components as dcc
import dash_html_components as html

map_variables = [
    {'label': 'Coincidencia', 'value': 'coincidencia'},
    {'label': 'Cantidad', 'value': 'cantidad'},
]

component = html.Div(
    [

        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.P('Variable a analizar:'),
                                dcc.RadioItems(
                                    id='map-variable',
                                    options=map_variables,
                                    value='cantidad',
                                    labelStyle={'display': 'inline-block'}
                                )
                            ],
                            className="pretty_container"
                        )
                    ],
                    id="info-container",
                    className="row container-display",
                ),
                html.P(id='map-title'),
                dcc.Graph(id="contracts_map_plot")],
            id="countGraphContainer",
            className="pretty_container",
        ),
    ],
    id="right-column",
    className="eight columns",
)