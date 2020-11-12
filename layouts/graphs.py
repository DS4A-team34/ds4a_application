import dash_core_components as dcc
import dash_html_components as html
from components import filters, indicators
from controls import municipios_options

layout = html.Div(
    [
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
                    [dcc.Graph(id="contracts_map_plot")],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="contracts_deparment_plot")],
                    className="pretty_container ten columns",
                ),
                html.Div(
                    [
                        html.P(
                            "Contexto del municipio:",
                            className="control_label",
                        ),
                        dcc.Dropdown(
                            id='tipo_municipio_dropdown',
                            options=municipios_options,
                            value='municipioobtencion'
                        )
                    ],
                    className="pretty_container two columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="count_contratos_graph")],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
)
