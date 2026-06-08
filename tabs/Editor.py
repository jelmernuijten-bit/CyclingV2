from dash import html, dcc

def sql_editor_layout():

    return html.Div([

        html.H3("SQL Editor"),

        dcc.Textarea(
            id="sql-query",
            value="""
SELECT name
FROM sqlite_master
WHERE type='table';
""",
            style={
                "width": "100%",
                "height": "250px"
            }
        ),

        html.Br(),

        html.Button(
            "Uitvoeren",
            id="run-query-btn"
        ),

        html.Br(),
        html.Br(),

        html.Div(id="sql-message"),

        html.Div(id="sql-result")
    ])
