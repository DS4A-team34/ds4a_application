import dash_core_components as dcc
import dash_html_components as html

from controls import df, grupo_options, grupo_dict

component = html.Div(
    [
        html.P(
            # "Filter by construction date (or select range in histogram):",
            "Filtrar por año de cargo al SECOP:",
            className="control_label",
        ),
        dcc.RangeSlider(
            id="year_slider",
            min=df['Anno Cargue SECOP'].min(),
            max=df['Anno Cargue SECOP'].max(),
            value=[2018, 2019],
            className="dcc_control",
        ),
        html.P("Filtrar por grupo:", className="control_label"),
        dcc.Dropdown(
            id="grupo_dropdown",
            options=grupo_options,
            multi=True,
            value=list(grupo_dict.keys()),
            className="dcc_control",
        ),
    ],
    className="pretty_container four columns",
    id="cross-filter-options",
)