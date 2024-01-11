import dash
import dash_bootstrap_components as dbc
from dash import html

# --- Register page --- #
dash.register_page(
    __name__,
    path='/about',
    title='SurvivalGenie2.0 About Us',
    location="navbar"
)

# --- Components --- #
ABOUT = dbc.Card(
    dbc.CardBody(
        [
            html.H1("About Us", className="card-title"),
            html.P([
                "Visit Our ", html.A("New Lab Website!", href="https://bhasinlab.org/")
                ],
                className="card-text", style={"font-size": "1.1rem"}),
        ],
    ),
    style={"width": "90rem"},
)

# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        dbc.Row(
            [dbc.Col(ABOUT, width="auto")],
            justify="center",
        ),
        ],
    fluid=True,
    )
    return layout