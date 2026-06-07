from dash import Dash, html, dcc, Input, Output
import dash_auth
from flask import request
import base64

from tabs.vergelijking import (
    vergelijking_layout,
    register_callbacks
)

from tabs.rapportage import (
    rapportage_layout,
    register_rapportage_callbacks
)

from tabs.worksheet import (
    worksheet_layout
)

app = Dash(__name__)
server = app.server

VALID_USERNAME_PASSWORD_PAIRS = {
    "Cyclinglab": "2019",
    "SEG": "Cyclinglab"
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)


def get_current_user():

    auth_header = request.headers.get(
        "Authorization"
    )

    if not auth_header:
        return None

    try:

        _, credentials = auth_header.split()

        decoded = base64.b64decode(
            credentials
        ).decode("utf-8")

        username, _ = decoded.split(
            ":",
            1
        )

        return username

    except Exception:
        return None


app.layout = html.Div([

    dcc.Dropdown(
        id="db",
        options=[],
        placeholder="Select database",
        style={"marginBottom": "10px"}
    ),

    dcc.Dropdown(
        id="name",
        placeholder="Select renner",
        style={"marginBottom": "20px"}
    ),

    dcc.Tabs(
        id="main-tabs",
        value="vergelijking",
        children=[

            dcc.Tab(
                label="Vergelijking",
                value="vergelijking"
            ),

            dcc.Tab(
                label="Rapportage",
                value="rapportage"
            ),

            dcc.Tab(
                label="Worksheet",
                value="worksheet"
            )
        ]
    ),

    html.Div(
        id="tab-content"
    )
])


@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value")
)
def render_tab(tab):

    username = get_current_user()

    if tab == "vergelijking":
        return vergelijking_layout()

    if tab == "rapportage":
        return rapportage_layout()

    if tab == "worksheet":

        if username == "Cyclinglab":
            return worksheet_layout()

        return html.Div(
            "Geen toegang"
        )

    return html.Div()


register_callbacks(app)
register_rapportage_callbacks(app)


if __name__ == "__main__":
    app.run(debug=True)
