import dash_core_components as dcc
import dash_html_components as html

from controls import grupo_options, grupo_dict, estado_proceso_dict, estado_proceso_options, table_df, tags, datevalues, dates_amount

component = html.Div(
    [
        html.P(
            "Filtrar por fecha de cargue al SECOP I:",
            className="control_label",
        ),
        dcc.RangeSlider(
            id="year_slider",
            min=1,
            max=dates_amount,
            value=[1, dates_amount],
            marks=tags,
            className="dcc_control",
        ),
        html.P("Filtrar por estado del proceso:", className="control_label"),
        dcc.Dropdown(
            id="estado_proceso_dropdown",
            options=estado_proceso_options,
            multi=True,
            value=list(estado_proceso_dict.keys()),
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