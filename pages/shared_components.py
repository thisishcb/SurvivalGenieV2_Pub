import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html, Input, Output, State, callback, clientside_callback, no_update, dash_table, Patch
from utils import BS_COLORS


def collapse_card(title,btn_text,collapse_id,cardbody,default_isopen=False):
    """
    Only returns the [] content for a dbc.Card.
    so we can add classes,
    collapse btn will have id {collapse_id-btn
    no footer
    """
    return [
        dbc.CardHeader(dbc.Row([
            dbc.Col(
                title, align="center", md=dict(size=8), xs=dict(size=12)
                ),
            dbc.Col(
                dbc.Button(
                    btn_text,
                    id=f"{collapse_id}-btn",
                    className="my-1 float-end",
                    color="primary",
                    n_clicks=0,
                    ), align="center", md=dict(size=4), xs=dict(size=12)
                )
            ], justify="center")
        ),
        
        dbc.Collapse(
            cardbody,
            id=collapse_id,
            is_open=bool(default_isopen),
        )]

def collapse_callback(collapse_id, btn_id = None, prevent_initial_call=False):
    """
    clentside callabck
    assume collapse_id = {collapse_id}-btn if no input
    """
    btn_id = f"{collapse_id}-btn" if not btn_id else btn_id
    return clientside_callback(
        """function(n_clicks, is_open) {
            if (n_clicks) { return !is_open; }
            return is_open;
        }""",
        Output(collapse_id, "is_open"),
        Input(btn_id, "n_clicks"),
        State(collapse_id, "is_open"),
        prevent_initial_call = prevent_initial_call
    )

## ================ collapse ==========
def open_help(out_id,in_id):
    """'
    used to toggle toast boxes
    """

    return clientside_callback(
        """function(n_clicks) {
            if (n_clicks>0) { return true }
            return false;
        }""",
        Output(out_id, "is_open"),
        [Input(in_id, "n_clicks")],
        prevent_initial_call=True
    )

# ============= components ==============
def error_page(message,error_type="Page Not Found"):
    ## Need original layout to fill in the ids so the callbacks won't raise errors
    layout = dbc.Container(
        [#html.Div(ori_layout, style={"display": "none"}),
        html.Br(),html.Br(),html.Br(),
        dbc.Row([
            dbc.Col([],width=2),
            dbc.Col([
                html.H1(error_type),
                html.Br(),
                html.P(html.B(message))
            ],width=6),
            dbc.Col([],width=4),
        ],align="center",)]
    )
    return layout

def review_card_content(id_factory, analysis_type, long_gene_list=None, **kwargs):
    """
    serves the gene inputs
    only generate a dbc.Row displaying the Parameters, so that other btns can be added
    """
    rv_genes = kwargs.pop("rv_genes", None)
    rv_datasets = kwargs.pop("rv_datasets", "")
    rv_cutp = kwargs.pop("rv_cutp", "")
    rv_surv = kwargs.pop("rv_surv", "")
    rv_til = kwargs.pop("rv_til", "Please select a TIL set.")
    if long_gene_list is None:
        long_gene_list = True if analysis_type in ["gene_set"] else False
    space4genes  = [
        html.A(
            id=id_factory("review-genes-btn"),
            n_clicks=0,
            ),
        dbc.Collapse(
            html.Span(style={"color": BS_COLORS["light"], "font-size":"0.8rem"}, id = id_factory("review-genes-detail")),
            id=id_factory("review-genes"),
            is_open=False,
            )
        ]
    rv_genes = rv_genes if rv_genes else space4genes if long_gene_list else "Please provide genes of interest."
    return dbc.Row(
            [
                dbc.Col([
                    html.Div([
                        html.H6("Gene(s) of interest: ", style={"margin-top": "15px"}),
                        html.Span(children= rv_genes,
                                id=id_factory("genes-review"))
                        ]),
                    html.Div([
                        html.H6("Datasets: ", style={"margin-top": "15px"}),
                        html.P(children=rv_datasets, id=id_factory("dataset-review"))
                        ]),
                    html.Div([
                        html.H6("TIL set: ", style={"margin-top": "15px"}),
                        html.P(children=rv_til, id=id_factory("til-review")),
                        ])
                    ]),
                dbc.Col([
                    html.Div([
                        html.H6("Cut point determination: ", style={"margin-top": "15px"}),
                        html.P(children=rv_cutp, id=id_factory("cutp-review"))
                        ]),
                    html.Div([
                        html.H6("Survival outcomes: ", style={"margin-top": "15px"}),
                        html.P(children=rv_surv, id=id_factory("outcome-review"))
                        ])
                    ]),
            ]
        )
