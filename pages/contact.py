import dash
import dash_bootstrap_components as dbc
from dash import html

# --- Register page --- #
dash.register_page(
    __name__,
    path='/contact',
    title='SurvivalGenie2.0 Contact Us',
    location="navbar"
)

# --- Components --- #
CONTACT = dbc.Card(
    dbc.CardBody(
        [
            html.H1("Contact", className="card-title"),
            html.P(["This page will contain a form that sends the message to us. For now, please contact through ", html.A("our lab page!", href="https://bhasinlab.org/contact-us/", target="_blank")], className="card-text", style={"font-size": "1.1rem"}),#SurvivalGenie2 support gmail.
        ],
    ),
    style={"width": "90rem"},
)

# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        dbc.Row(
            [dbc.Col(CONTACT, width="auto")],
            justify="center",
        ),
        ],
    fluid=True,
    )
    return layout