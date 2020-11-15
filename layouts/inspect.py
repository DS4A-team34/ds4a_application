import dash_table
import dash_core_components as dcc
import dash_html_components as html
from components import filters, indicators
from controls import municipios_options, val_columns


layout = html.Div(
    [
        html.Div(
            [
                dcc.ConfirmDialog(
                    id='inspect-dialog',
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dcc.Input(id='input-uuid', placeholder='UUID del contrato a inspeccionar', style={'width': '300px'})
                            ],
                            className='three columns'
                        ),
                        html.Div(
                            [
                                html.Button('Inspeccionar', id='button-inspect'),
                            ],
                            className='two columns'
                        ),
                    ],
                    className="pretty_container twelve columns",
                )
            ],
            className="row flex-display",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H4('Validation score'),
                                        html.H5(id='validation-score'),   
                                    ],
                                    id='validation-score-card',
                                    className="mini_container"
                                    # className="pretty_container two columns"
                                ),
                            ],
                            className='row flex-display'
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        dash_table.DataTable(
                                            id='validation-table',
                                            columns=val_columns,
                                            style_data_conditional=[
                                                {
                                                    'if': {
                                                        'filter_query': '{coincidencia} >= 0.9',
                                                        'column_id': 'coincidencia'
                                                    },
                                                    'backgroundColor': 'green',
                                                    'color': 'black'
                                                },
                                                {
                                                    'if': {
                                                        'filter_query': '{coincidencia} > 0.6 && {coincidencia} < 0.9',
                                                        'column_id': 'coincidencia'
                                                    },
                                                    'backgroundColor': 'yellow',
                                                    'color': 'black'
                                                },
                                                {
                                                    'if': {
                                                        'filter_query': '{coincidencia} <= 0.6',
                                                        'column_id': 'coincidencia'
                                                    },
                                                    'backgroundColor': 'red',
                                                    'color': 'black'
                                                },
                                            ]
                                        ),
                                    ],
                                    className="eight columns"
                                )
                            ],
                            className="row flex-display",
                        ),
                        html.Br(),
                        html.Div(
                            [
                                html.ObjectEl(
                                    type="application/pdf",
                                    className='iframe-contract five columns',
                                    id='iframe-contract-file',
                                ),
                                html.Iframe(
                                    title='Texto extraido',
                                    # src='https://bootcampaws315.s3.us-east-2.amazonaws.com/19-12-9155011-8329932/13-CONTRATO.html',
                                    className='iframe-contract five columns',
                                    id='iframe-contract-extracted'
                                ),
                            ],
                            className="row twelve columns",
                        )
                    ],
                    className="pretty_container twelve columns",
                )
            ],
            className="row flex-display",
        )
    ],
)
