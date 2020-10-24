import dash_core_components as dcc
import dash_html_components as html

from components import filters, indicators

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
                    [dcc.Graph(id="tipo_proceso_graph")],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        )
    ],
    className="row flex-display",
)