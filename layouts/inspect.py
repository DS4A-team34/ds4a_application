import dash_table
import dash_core_components as dcc
import dash_html_components as html
from components import filters, indicators
from controls import municipios_options

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
                                html.Button('Inpeccionar', id='button-inspect'),
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
                                html.Iframe(
                                    title='Texto extraido',
                                    src='https://bootcampaws315.s3.us-east-2.amazonaws.com/19-12-9155011-8329932/13-CONTRATO.html',
                                    className='iframe-contract one-half.colum',
                                    id='iframe-contract-extracted'
                                )
                            ],
                            className="pretty_container twelve columns",
                        )
                    ],
                    className="pretty_container twelve columns",
                )
            ],
            className="row flex-display",
        )
    ],
)
