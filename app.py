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

from tabs.worksheet import worksheet_layout

from tabs.sql_editor import (
    sql_editor_layout,
    register_sql_callbacks
)

# =========================================
# DASH APP
# =========================================

app = Dash(__name__)
server = app.server

# =========================================
# LOGIN USERS
# =========================================

VALID_USERNAME_PASSWORD_PAIRS = {
    "Cyclinglab": "2019",
    "SEG": "Cyclinglab"
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# =========================================
# CURRENT USER
# =========================================

def get_current_user():

    auth_header = request.headers.get(
        "Authorization"
    )

    if not auth_header:
        return None

    try:

        auth_type, credentials = (
            auth_header.split()
        )

        decoded = base64.b64decode(
            credentials
        ).decode("utf-8")

        username, _ = decoded.split(
            ":",
            1
        )

        return username

    except:
        return None

# =========================================
# MAIN LAYOUT
# =========================================

app.layout = html.Div([

    # =========================================
    # FILTERS
    # =========================================

    dcc.Dropdown(
        id="name",
        placeholder="Select renner",
        style={
            "marginBottom": "10px"
        }
    ),

    dcc.Dropdown(
        id="geslacht",
        multi=True,
        placeholder="Geslacht",
        style={
            "marginBottom": "10px"
        }
    ),

    html.Label("Leeftijd"),

    dcc.RangeSlider(
        id="leeftijd",
        min=15,
        max=40,
        value=[15, 40],
        tooltip={
            "placement": "bottom",
            "always_visible": True
        }
    ),

    html.Br(),

    # =========================================
    # TABS
    # =========================================

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
            ),

            dcc.Tab(
                label="SQL Editor",
                value="sql_editor"
            )
        ],

        style={
            "marginBottom": "10px"
        }
    ),

    # =========================================
    # TAB CONTENT
    # =========================================

    html.Div(id="tab-content")

])

# =========================================
# TAB RENDERING
# =========================================

@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value")
)
def render_tab(tab):

    username = get_current_user()

    if tab == "vergelijking":

        return vergelijking_layout()

    elif tab == "rapportage":

        return rapportage_layout()

    elif tab == "worksheet":

        if username == "Cyclinglab":
            return worksheet_layout()

        return html.Div()

    elif tab == "sql_editor":

        if username == "Cyclinglab":
            return sql_editor_layout()

        return html.Div()

    return html.Div()

# =========================================
# REGISTER CALLBACKS
# =========================================

register_callbacks(app)
register_rapportage_callbacks(app)
register_sql_callbacks(app)

# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    app.run(debug=True)
