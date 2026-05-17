from dash import Dash, html, dcc, Input, Output
import dash_auth
from flask import request
import base64

from tabs.vergelijking import (
    vergelijking_layout,
    register_callbacks
)

from tabs.rapportage import rapportage_layout
from tabs.worksheet import worksheet_layout

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
# CURRENT USER HELPER
# =========================================

def get_current_user():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None

    try:

        auth_type, credentials = auth_header.split()

        if auth_type.lower() != "basic":
            return None

        decoded = base64.b64decode(
            credentials
        ).decode("utf-8")

        username, password = decoded.split(":", 1)

        return username

    except:
        return None

# =========================================
# MAIN LAYOUT
# =========================================

app.layout = html.Div(id="main-layout")

# =========================================
# DYNAMIC TABS BASED ON USER
# =========================================

@app.callback(
    Output("main-layout", "children"),
    Input("main-layout", "id")
)
def render_layout(_):

    username = get_current_user()

    tabs = [

        dcc.Tab(
            label="Vergelijking",
            children=vergelijking_layout()
        ),

        dcc.Tab(
            label="Rapportage",
            children=rapportage_layout()
        )
    ]

    # Alleen Cyclinglab ziet Worksheet
    if username == "Cyclinglab":

        tabs.append(

            dcc.Tab(
                label="Worksheet",
    app.run(debug=True)
