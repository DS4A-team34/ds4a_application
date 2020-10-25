import dash_core_components as dcc
import dash_html_components as html
from components import filters, indicators
from controls import min_graf, plot_grf

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
                    [dcc.Graph(id="count_contratos_graph", figure=plot_grf)],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="grupos_contratos_grapsh", figure=min_graf)],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        ),
    ],
)
