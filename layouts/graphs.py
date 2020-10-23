import dash_html_components as html

from components import filters, indicators

layout = html.Div(
    [
        filters.component,
        indicators.component,
    ],
    className="row flex-display",
)