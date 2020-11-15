import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq

from controls import df_x, grupo_dict, grupo_options, fig_top_contratistas_good, fig_top_contratistas_bad

available_indicators = df_x.entidadnombre.unique()

# Colors
bgcolor = "#f3f3f1"  # mapbox light map land color
bar_bgcolor = "#b0bec5"  # material blue-gray 200
bar_unselected_color = "#78909c"  # material blue-gray 400
bar_color = "#546e7a"  # material blue-gray 600
bar_selected_color = "#37474f"  # material blue-gray 800
bar_unselected_opacity = 0.8

# Figure template
row_heights = [150, 500, 300]
template = {"layout": {"paper_bgcolor": bgcolor, "plot_bgcolor": bgcolor}}
def blank_fig(height):
    """
    Build blank figure with the requested height
    """
    return {
        "data": [],
        "layout": {
            "height": height,
            "template": template,
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
        },
    }

layout = html.Div(
    [

        html.H2('Métricas generales de inconsistencias'),

        html.Div(
            [
                html.Div(
                    [dcc.Graph(id="contratistas-bad", figure=fig_top_contratistas_bad)],
                    className="pretty_container twelve columns",
                ),
            ],
            className="row flex-display",
        ),
        
        # html.Div(
        #     [
        #         html.Div(
        #             [dcc.Graph(id="contratistas-good", figure=fig_top_contratistas_good)],
        #             className="pretty_container twelve columns",
        #         ),
        #     ],
        #     className="row flex-display",
        # ),

        html.H2('Control de inconsistencias por entidades'),

        html.Div(id='main-selector', children=[

            html.Div(id="select-container", children=[
                    html.P(
                        id="chart-selector", children="Filtrar por entidad:"),
                    dcc.Dropdown(id="entidad-dropdown",
                                options=[
                                    {'label': i, 'value': i} for i in available_indicators],
                                value="Nombre de entidad",
                                )

                ],),

            html.Div(id='select-grupo', children=[

                html.P(
                    id="text-grupo", className="control_label", children="Filtrar por grupo del contrato:"),
                dcc.RadioItems(id='radio-item-grupo',
                               className="dcc_control",
                               options=grupo_options,
                               value='Grupo',
                               labelStyle={'display': 'inline-block'}),
            ]),
        ],
        # className="pretty_container"
        ),

        html.Div(id='contenedor', children=[
            html.Div(id='valor-contrato', children=[
                html.H3(id='vc1', children=" Total valor cuantías"),
                html.H4(id='total-valor-contrato-text', className="valor-text"),
            ],),
            html.Div(id='valor-contrato1', children=[
                html.H3(id='vc2', children=" Total valor cuantía con adiciones"),
                html.H4(id='total-valor-adiciones-text', className="valor-text"),
            ],),
            html.Div(id='valor-contrato2', children=[
                html.H3(id='vc3', children=" Porcentaje promedio de similitud"),
                daq.GraduatedBar(
                    id='ooc_graph_id',
                    color={
                        "gradient": True,
                        "ranges": {
                            "red": [0, 7],
                            "yellow": [7, 9],
                            "green": [9, 10],
                        }
                    },
                    showCurrentValue=True,
                    max=10,
                    value=0,
                ),
            ],),
            html.Div(id='valor-contrato3', children=[
                html.H3(id='vc4', children=" Cantidad de contratos"),
                html.H4(id='total-cantidad-text', className="valor-text"),
            ],),

        ], style={'columnCount': 2}),
    ]
)
