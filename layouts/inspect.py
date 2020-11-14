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
                                dash_table.DataTable(
                                    id='validation-table',
                                    columns=val_columns,
                                    # data={},
                                    # filter_action='custom',
                                    # style_data = {
                                    #     'overflow': 'hidden',
                                    #     'textOverflow': 'ellipsis',
                                    #     'maxWidth': 0
                                    # },
                                    # style_table={'overflowX': 'auto'},
                                    # tooltip_data=[
                                    #     {
                                    #         column: {'value': str(value), 'type': 'markdown'}
                                    #         for column, value in row.items()
                                    #     } for row in table_df.to_dict('rows')
                                    # ],
                                    # row_selectable="multi",
                                    # selected_rows=[],
                                )
                            ],
                            className="row flex-display",
                        ),
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
