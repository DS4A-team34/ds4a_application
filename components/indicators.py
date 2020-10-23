import dash_core_components as dcc
import dash_html_components as html

component = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [html.H6(id="amnt-inconsistencies-text"), html.P("No. Inconsistencias")],
                    id="amnt-inconsistencies",
                    className="mini_container",
                ),
                html.Div(
                    [html.H6(id="pct-inconsistencies-text"), html.P("% Inconsistencias")],
                    id="pct-inconsistencies",
                    className="mini_container",
                ),
                html.Div(
                    [html.H6(id="avg-severity-text"), html.P("Severidad Promedio")],
                    id="avg-severity",
                    className="mini_container",
                ),
            ],
            id="info-container",
            className="row container-display",
        ),
        html.Div(
            [dcc.Graph(id="count_graph")],
            id="countGraphContainer",
            className="pretty_container",
        ),
    ],
    id="right-column",
    className="eight columns",
)