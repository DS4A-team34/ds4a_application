import dash_core_components as dcc
import dash_html_components as html
from controls import quantity_files_fig, size_files_fig

layout = html.Div(
    [
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
