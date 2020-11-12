import dash_bootstrap_components as dbc
from components import table

import dash_html_components as html
import dash_core_components as dcc

from controls import validation_state

layout = html.Div(
    [
        html.Div(
            html.Div(
                [
                    html.Div(id='selected-rows', style={'display': 'none'}),
                    html.Div(
                        [html.H6(id="count-reviewed-text", children=validation_state), html.P("Procesos revisados")],
                        id="count-reviewed",
                        className="mini_container",
                    ),
                    html.Div(
                        [html.H6(id="selected-contracts-text"), html.P("Procesos a revisar")],
                        id="count-selected",
                        className="mini_container",
                    ),
                    html.Button('Procesar', id='button-process'),
                    dcc.ConfirmDialog(
                        id='process-dialog',
                    ),
                    dcc.Input(id='input-uuid', placeholder='UUID del contrato a inspeccionar', style={'width': '300px'}),
                    html.Button('Inpeccionar', id='button-inspect'),
                    dcc.ConfirmDialog(
                        id='inspect-dialog',
                    ),
                ],
                id="info-container",
                className="row container-display",
            ),
            className="row flex-display"
        ),
        html.Div(
            [table.component],
            # className="pretty_container",
        )
    ],
)