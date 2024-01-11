from dash import html, dcc, clientside_callback, Output, Input, State
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from configs import URL_BASE

def create_navbar():
    navbar = dbc.Navbar(
        children=dbc.Container([
            html.A(
                dbc.Row(
                    [
                        dbc.Col(html.Img(src = URL_BASE+"assets/SurvGenie2Logo_page.svg", height= "40px")),
                        dbc.Col(dbc.NavbarBrand("Survival Genie 2.0", className = "ms-2")),
                    ], align="center", className="g-0",
                ),href=URL_BASE+"home",
                style={"textDecoration": "none"},
            ),
            dbc.Row([dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            dbc.Collapse(
                children = dbc.Nav([
                    dbc.NavItem([
                        dbc.NavLink([
                            dbc.FormText("Analysis ID: "),
                            dbc.FormText("",id="show-session-id"),
                            dbc.FormText("\t"),
                            dcc.Clipboard(
                            target_id="show-session-id",
                            title="copy",
                            style={
                                "display": "inline-block",
                                "fontSize": 15,
                                "verticalAlign": "center",
                                },
                            ),
                        ], id = "nav-session-id"),
                    ]),
                    dbc.NavItem([
                        dbc.NavLink(
                            [DashIconify(icon="ep:question-filled", width=20, height=25, inline=True, color="#4582ec")],
                            #href="",#URL_BASE+"help",
                            id="question-help",
                            target="_blank",
                        ),
                        dbc.Tooltip(
                            "Each session is assigned with a analysis ID. This ID will only be recorded when the analysis is submitted. Once the analysis starts you can track the status of the job with your analysis ID on the home page. You can share the result with other people through analysis ID as well. Each analysis's result will be stored for 24 hours. You can overwrite the result with an existing analysis ID, which will also refresh the storaging time.",
                            target="question-help",
                            placement="bottom", 
                            style={"background-color":"white"},
                        ),
                    ]),
                    dbc.NavItem([
                        dbc.NavLink(
                                [DashIconify(icon="solar:bug-bold-duotone", width=20, height=25, inline=True, color="#4582ec")],
                                href=URL_BASE+"support",
                                id="bug-report",
                                target="_blank",
                            ),
                            dbc.Tooltip(
                                "Report an issue",
                                target="bug-report", 
                                placement="bottom", 
                                style={"background-color":"white"},
                            ),
                    ]),
                    dbc.DropdownMenu(
                        nav=True,
                        in_navbar=True,
                        label="More",
                        align_end=True,
                        children=[  # Add as many menu items as you need
                            dbc.DropdownMenuItem("Referene manual", href=URL_BASE+'home', target="_blank"),
                            dbc.DropdownMenuItem("Guided tutorial", href=URL_BASE+"home", target="_blank"),
                            dbc.DropdownMenuItem(divider=True),
                            dbc.DropdownMenuItem("About Us", href="https://bhasinlab.org/", target="_blank"),#URL_BASE+'about'
                            dbc.DropdownMenuItem("Contact", href="https://bhasinlab.org/contact-us/", target="_blank"),#URL_BASE+'contact'
                        ],
                    ),
                ], horizontal ="end"),
                id="navbar-collapse",
                is_open=False,
                navbar=True,)], class_name="d-flex", justify="end")
        ])
        # brand='Survival Genie 2.0',
        # brand_href=URL_BASE+"home",
        # sticky="top",
    )

    clientside_callback(
        """
        function(n_clicks, is_open) {
            if (n_clicks) {
                return !is_open;
            }
            return is_open;
        }
        """,
        Output("navbar-collapse", "is_open"),
        Input("navbar-toggler", "n_clicks"),
        State("navbar-collapse", "is_open")
    )
    return navbar