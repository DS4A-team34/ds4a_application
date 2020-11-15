import dash_core_components as dcc
import dash_html_components as html
from components import filters, indicators
from controls import municipios_options, quantity_files_fig, size_files_fig

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
                    [dcc.Graph(id="grupos_contratos_grapsh")],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="contracts_deparment_plot")],
                    className="pretty_container nine columns",
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
                    className="pretty_container three columns",
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
        html.H2('Exploración de documentos'),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="quantity_files_grapsh",
                               figure=quantity_files_fig)],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="size_files_grapsh", figure=size_files_fig)],
                    className="pretty_container seven columns",
                ),
            ],
            className="row flex-display",
        )
    ],
)
