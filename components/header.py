import dash_html_components as html

component = html.Div(
    [
        html.Div(
            [
                html.Img(
                    src="../assets/cce.png",
                    id="cce-image",
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
                            "Colombia Compra Eficiente",
                            style={"margin-bottom": "0px"},
                        ),
                        html.H5(
                            "Validating Public Purchasing Data", 
                            style={"margin-top": "0px"}
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