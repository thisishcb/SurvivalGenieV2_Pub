import dash
import dash_bootstrap_components as dbc
from dash import html

dash.register_page(
    __name__,
    path='/help',
    title='SurvivalGenie2.0 Help',
    location="navbar"
)

# --- Components --- #


HELP = dbc.Card(
    dbc.CardBody(
        [
            html.H1("Reference manual for Survival Genie 2.0", className="card-title"),
            html.P("This page will contain the tutorial and reference manual for Survival Genie 2.0.", className="card-text", style={"font-size": "1.1rem"}),
        ],
    ),
    style={"width": "90rem"},
)

# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        dbc.Row(
            [dbc.Col(HELP, width="auto")],
            justify="center",
        ),
        ],
    fluid=True,
    )
    return layout