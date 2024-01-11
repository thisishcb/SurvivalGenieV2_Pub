import dash
import dash_bootstrap_components as dbc
from dash import html

# --- Register page --- #
dash.register_page(
    __name__,
    path='/support',
    title='SurvivalGenie2.0 Help',
    location="navbar"
)

# --- Components --- #
SUPPORT = dbc.Card(
    dbc.CardBody(
        [
            html.H1("Report issues with Survival Genie 2.0", className="card-title"),
            html.P("Temporarily, please send your issues with analysis id to email SurvivalGenie@@gmail.com", className="card-text", style={"font-size": "1.1rem"}), # This page will contain a form to submit any issues with Survival Genie 2.0, which will be forwarded to the
        ],
    ),
    style={"width": "90rem"},
)

# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        dbc.Row(
            [dbc.Col(SUPPORT, width="auto")],
            justify="center",
        ),
        ],
    fluid=True,
    )
    return layout