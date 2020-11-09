from components import table

import dash_html_components as html
import dash_core_components as dcc

layout = html.Div(
    [
        html.Div(
            [
                html.Div(id='selected-rows', style={'display': 'none'}),
                html.Div(
                    [html.H6(id="selected-contracts-text"), html.P("Procesos a revisar")],
                    id="count-selected",
                    className="mini_container",
                ),
                html.Button('Procesar', id='button-process'),
                dcc.ConfirmDialog(
                    id='process-dialog',
                ),
                # html.Div(
                #     [html.H6(id="count-reviewed-text"), html.P("Procesos revisados")],
                #     id="count-reviewed",
                #     className="mini_container",
                # ),
            ],
            id="info-container",
            className="row container-display",
        ),
        table.component
    ],
)
