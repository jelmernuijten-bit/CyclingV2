
from dash import Dash, html, dcc
import dash_auth

from tabs.vergelijking import vergelijking_layout, register_callbacks
from tabs.rapportage import rapportage_layout
from tabs.worksheet import worksheet_layout

app = Dash(__name__)
server = app.server

VALID_USERNAME_PASSWORD_PAIRS = {
    "coach": "wielrennen2025"
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

app.layout = html.Div(

    style={
        "backgroundColor": "#f4f6f8",
        "padding": "10px"
    },

    children=[

        dcc.Tabs([

            dcc.Tab(
                label="Vergelijking",
                children=vergelijking_layout()
            ),

            dcc.Tab(
                label="Rapportage",
                children=rapportage_layout()
            ),

            dcc.Tab(
                label="Worksheet",
                children=worksheet_layout()
            )

        ])

    ]
)

register_callbacks(app)

if __name__ == "__main__":

    url = "http://localhost:8050/"

    print(f"\nOpen dashboard: {url}\n")

    app.run(debug=True)
