import re
import json
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback, State, no_update
from configs import URL_BASE
## ==========================================
##              first page
##      page of recording user info
## ==========================================

# --- Register page --- #
dash.register_page( 
    __name__,
    path='/',
    title='Welcome to SurvivalGenie2.0', 
    location="navbar"
)

# --- Components --- #
EMAIL = dbc.FormFloating(
    [
        dbc.Input(id="email-input", placeholder="Email address", type="email", style={"margin-bottom": "15px"}),
        dbc.Label("Email address", style={"margin-left": "20px"}),
    ]
)

AFFILIATE = dbc.FormFloating(
    [
        dbc.Input(id="affiliate-input", placeholder="Affiliated institution", type="text", style={"margin-bottom": "15px"}),
        dbc.Label("Affiliated institution", style={"margin-left": "20px"}),
    ]
)

USERINFO = dbc.Card(
            dbc.CardBody([
                dbc.CardImg(src="/assets/tool_logo.png", top=True),
                html.H4("Welcome to Survival Genie 2.0", className="card-title", style={"text-align": "center"}),
                html.H6("an accessible platform for network-based survival analysis", style={"text-align": "center", "margin-bottom": "30px"}),
                html.H6("Please enter the following information to proceed", style={"text-align": "center", "margin-bottom": "10px", "font-weight": "normal"}),
                dbc.Form([
                    dbc.Row([EMAIL]),
                    dbc.Row([AFFILIATE]),
                    dbc.FormText("Note this information is soley collected for tool analytic purposes", style={"font-size": "0.75em", "text-align": "center", "font-style": "italic"}),
                    html.Hr(),
                    dbc.Row(
                        [dbc.Col(dbc.Button("Skip", id="btn-user-info-skip", href=URL_BASE+"home", n_clicks=0, size="md", type="submit", className="btn btn-primary"), width="auto"),
                         dbc.Col(dbc.Button("Continue", id="btn-user-info", href=URL_BASE+"home", n_clicks=0, size="md", type="submit", className="btn btn-primary disabled"), width="auto")],
                        justify="between",
                    ),
                ]) # it's a fake form; not posting results with ajax etc, simply dash load variables
            ])#,
            #style={"width": "40rem"}
        )

# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        # dbc.Row(
        #     [dbc.Col(USERINFO,
        #              sm=dict(size=12),
        #              lg=dict(size=6),
        #              xl=dict(size=4))],
        #     justify="center"
        # ),
        ],
    fluid=True,
    )
    return layout

# --- Callbacks --- #



# @callback(
#     Output("btn-user-info", "className"),
#     Output("btn-user-info", "href"),
#     Output("email-input", "invalid"),
#     [Input("email-input", "value"), 
#      Input("affiliate-input", "value")]
# )
# def form_validation(email, affiliation):
#     if email and affiliation:
#         email_rgx = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'
#         if re.match(email_rgx,email) and len(affiliation) >= 1:
#             return "btn btn-primary", "/home", False
#         return "btn btn-primary disabled", "/", True
#     return "btn btn-primary disabled", "/", False


# @callback(Output("user-info","data"),
#         Input("btn-user-info","n_clicks"),
#         State("email-input", "value"), 
#         State("affiliate-input", "value"),
#         prevent_initial_call=True
#         )
# def select_analysis(n_clicks,email,affilitation):
#     if n_clicks:
#         return {"email":email, "affilitation":affilitation}
#     return no_update