import dash_html_components as html

component = html.Div(
    [
        html.Div(
            [
                html.Img(
                    src="../assets/ds4a.png",
                    id="ds4a-image",
                    style={
                        "height": "60px",
                        "width": "auto",
                        "margin-bottom": "25px",
                    },
                )
            ],
            className="one-third column",
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3(
                            "DS4A 3.0 - Team 34",
                            style={"margin-bottom": "0px"},
                        ),
                        html.A(
                            html.H5("Colombia Compra Eficiente", style={"margin-top": "0px"}),
                            href='https://www.colombiacompra.gov.co/'
                        )
                    ]
                )
            ],
            className="one-half column",
            id="title",
        ),
        html.Div(
            [
                html.Img(
                    src="../assets/mintic.png",
                    id="mintic-image",
                    style={
                        "height": "60px",
                        "width": "auto",
                        "margin-bottom": "25px",
                    },
                )
            ],
            className="one-third column"
        ),
    ],
    id="header",
    className="row flex-display",
    style={"margin-bottom": "25px"},
)