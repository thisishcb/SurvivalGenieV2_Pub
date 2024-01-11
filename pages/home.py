import os
# import json
# import re
import uuid
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback, no_update, State, clientside_callback, Patch
from server import db, task_tb
from configs import URL_BASE
# from pages.shared_components import collapse_card, collapse_callback
# from utils import id_factory
# from scripts.utils import user_info_validation
## ==========================================
##      page of selecting analysis type
## ==========================================


# --- Register page --- #
dash.register_page( 
    __name__,
    top_nav=True,
    path='/home',
    title='SurvivalGenie2.0 Get Started', 
    location="navbar"
)

# --- Components --- #
## single gene analysis  /singlegene/input
single_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("Prediction of survival outcomes will be performed based on the high versus low noramlized (FPKM) expression of a gene of interest.", className="card-text"),
            # html.P(html.A("Example output Page", href="") ,style={"font-style": "italic", "color": "var(--bs-primary)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color="primary", href=URL_BASE+"example_out/single_gene"),
                dbc.Button("Begin", color="primary", href=URL_BASE+"singlegene/input",id={"type": "submit", "index": "singlegene"}, value="singlegene", n_clicks=0),
            ])
        ]
    ),
    className="mt-3",
)

## gene ratio analysis /ratio/input
ratio_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("Prediction of survival outcomes will be performed based on the high versus low log (FPKM) expression ratio of two genes of interest.", className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-info)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color="info", href=URL_BASE+"example_out/gene_ratio"),
                dbc.Button("Begin", color="info", href=URL_BASE+"ratio/input",id={"type": "submit", "index": "ratio"}, value="ratio", n_clicks=0),
            ])
        ]
    ),
    className="mt-3",
)

## gene-set analysis /gene-set/input
geneset_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("Prediction of survival outcomes will be performed based on the aggregated high versus low GeneSet Variation Score of a gene list or gene signature (i.e., multiple genes of interest).", className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-success)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color="success", href=URL_BASE+"example_out/gene_set"),
                dbc.Button("Begin", color="success",href=URL_BASE+"gene-set/input",id={"type": "submit", "index": "geneset"}, n_clicks=0,value="geneset"),
            ])
            
        ]
    ),
    className="mt-3",
)

## cluster marker based analysis /cluster-marker/input
cluster_marker_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("Prediction of survival outcomes will be performed based on the aggregated high versus low GeneSet Variation Score of of marker genes provided per-cluster. Expected input would be a table file containing the marker gene symbol, adjusted pvalue, and cluster information. Example data is offered. ", className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-warning)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color="warning", href=URL_BASE+"example_out/cluster_marker"),
                dbc.Button("Begin", color="warning",href=URL_BASE+"cluster-marker/input",id={"type": "submit", "index": "rnqseq"}, n_clicks=0,),
            ])
        ]
    ),
    className="mt-3",
)

wgcna_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Prediction of survival outcomes will be performed based on the aggregated high versus low GeneSet Variation Score of of eigen genes provided per-module/per-network. Expected input would be a table file containing gene symbols, module assignments and optional kME scores (eigengene-based connectivities). Example data is offered.", html.Br(), "Have troubles in generating modules? Don't worry, check our wrapped hdWGCNA function on ", html.A("github link", href="")
                    ], className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-danger)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color="danger", href=URL_BASE+"example_out/wgcna_module"),
                dbc.Button("Begin", color="danger",href=URL_BASE+"coexp-module/input",value="scrnaseq",id={"type": "submit", "index": "scrnaseq"}, n_clicks=0),
            ])
        ]
    ),
    className="mt-3",
)

INPUTS = dbc.Tabs(
    [
        dbc.Tab(single_tab, label="Single Gene",tab_id="single-gene"),
        dbc.Tab(ratio_tab, label="Gene Ratio",tab_id="gene-ratio"),
        dbc.Tab(geneset_tab, label="Gene set",tab_id="geneset"),
        dbc.Tab(cluster_marker_tab, label="Cluster Markers",tab_id="marker"),
        dbc.Tab(wgcna_tab, label="Co-expression Network",tab_id="network"),
    ],
    active_tab="single-gene",
    id="home-select-analysis-type"
)

INPUT_FORM = dbc.Card(
    dbc.CardBody([
        html.H5("Select your input type to get started.", className="card-title", style={"text-align": "left"}),
        html.Hr(),
        INPUTS,
    ]),
    # style={"width": "90vw"},
)

GET_RES = dbc.Form(dbc.InputGroup(
            [dbc.InputGroupText("I Have an Analysis ID:"),
             dbc.Input(id="input-session-id"),
             dbc.Button("Retrieve", id="get-session-id-res",
                        n_clicks=0,disabled=False,class_name="submit")],
            className="my-auto",
        ))

input_figures = [
    {"key": "ttin_0", "src": URL_BASE+"static/tt_input_overview.svg", "name": "Input Overview"},
    {"key": "ttin_1", "src": URL_BASE+"static/tt_input_single_gene.svg", "name": "Analysis Specific Input"},
    {"key": "ttin_2", "src": URL_BASE+"static/tt_input_dataset.svg", "name": "Select Dataset"},
    {"key": "ttin_3", "src": URL_BASE+"static/tt_input_other.svg", "name": "Analysis Parameters"},
    {"key": "ttin_4", "src": URL_BASE+"static/tt_input_review.svg", "name": "Input Review"},
]
# for i in range(len(input_figures)):
#     input_figures[i]['key'] = f"ttin_{i}"

output_figures = [
    {"key": "ttout_0", "src": URL_BASE+"static/tt_output_overview.svg", "name": "Output Overview"},
    {"key": "ttout_1", "src": URL_BASE+"static/tt_output_multi_ds_intra.svg", "name": "Intra-Dataset Figures"},
    {"key": "ttout_2", "src": URL_BASE+"static/tt_output_multi_ds_inter.svg", "name": "Inter-Dataset Figures"}
]
# for i in range(len(output_figures)):
#     output_figures[i]['key'] = f"ttout_{i}"

HELPER_CONDENSED = dbc.Collapse([
    dbc.Row([
        dbc.Col([
            html.Div(
                    dbc.RadioItems(
                        id="home-tutorial-input-radio",
                        className="btn-group-vertical",
                        inputClassName="btn-check",
                        labelCheckedClassName="active",
                        labelClassName="btn btn-outline-primary",
                        options=[{"label":i["name"], "value":i["key"]} for i in input_figures],
                        value=input_figures[0]["key"]
                    ),
            className="radio-group radio-group-v",
            ),
        ], width=2, align="center"),
        dbc.Col([
            dbc.Carousel(
                items=[{"key":i["key"], "src":i["src"]} for i in input_figures],
                controls=False, indicators=False, variant="dark",
                id = "home-tutorial-input"#,className="carousel-fade",
            )
        ], sm=dict(size=10), lg=dict(size=6)),
    ], justify="center"),
    html.Br(),
    dbc.Row([
        dbc.Col([
            html.Div(
                    dbc.RadioItems(
                        id="home-tutorial-output-radio",
                        className="btn-group-vertical",
                        inputClassName="btn-check",
                        labelCheckedClassName="active",
                        labelClassName="btn btn-outline-primary",
                        options=[{"label":i["name"], "value":i["key"]} for i in output_figures],
                        value=output_figures[0]["key"]
                    ),
            className="radio-group radio-group-v",
            ),
        ], width=2, align="center"),
        dbc.Col([
            dbc.Carousel(
                items=[{"key":i["key"], "src":i["src"]} for i in output_figures],
                controls=False, indicators=False, variant="dark",
                id = "home-tutorial-output"#,className="carousel-fade",
                )
            ], sm=dict(size=10), lg=dict(size=6)),
        ], justify="center"),
    ], id = "home-tutorial-collapse", is_open=False)

OPENSOURCE = dbc.Row(
    dbc.Col([
        html.Hr(),
        dbc.FormText(["The Survival Genie platform is an open access tool developed by ", html.A("the Bhasin Lab at Emory University", href="https://bhasinlab.org/"), " for researchers to freely use, including for academic and commercial use under ", html.A("MIT Liscence", href="https://github.com/git/git-scm.com/blob/main/MIT-LICENSE.txt"),". This Web Server is developed under ", html.A("Dash Framework",href="https://dash.plotly.com/"), ". The source code is available at ", html.A("Github.", href="")])],
        sm=dict(size=12),lg=dict(size=8)
    ), justify="center"
)
# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        dbc.Row(
            dbc.Col(GET_RES,
                sm=dict(size=12),
                lg=dict(size=8),),
            justify="center"
            ),
        html.Br(),
        dbc.Row(
            [dbc.Col(INPUT_FORM,
                     sm=dict(size=12),
                     lg=dict(size=8),)],
            justify="center"
        ),
        html.Br(),
        html.Div([
            html.Hr(),

            # html.Div(
            dbc.Button("Show Tutorial", outline=False,color="primary",
                       className="position-absolute top-0 start-50 translate-middle rounded-pill",
                       style={"width": "200px"},
                       id="home-tutorial-collapse-btn"),
                # align="center",width=2,
            ],
            className="position-relative col-8 mx-auto text-center"
        ),
        html.Br(),
        HELPER_CONDENSED,
        OPENSOURCE,
        dcc.ConfirmDialog(
                id='retrieve-error-msg',
                message='This session does not exist!',
            ),
        ],
    fluid=True,
    )
    return layout

# --- callbacks ---

# collapse tutorial
clientside_callback(
    """function(n_clicks, is_open) {
        var open = is_open
        var btntxt = "Show Tutorial"
        if (n_clicks) { open = !is_open; }
        if (open) {btntxt = "Hide Tutorial"}
        return [open, btntxt];
    }""",
    Output("home-tutorial-collapse", "is_open"),
    Output("home-tutorial-collapse-btn", "children"),
    Input("home-tutorial-collapse-btn", "n_clicks"),
    State("home-tutorial-collapse", "is_open"),
    prevent_initial_call = True
)

# swap tutorial page
def change_tt_page(caro_id):
    clientside_callback(
        """function(value) {return parseInt(value.split("_")[1]);}""",
        Output(caro_id, "active_index"),
        Input(f"{caro_id}-radio", "value"),
        prevent_initial_call = True
    )
change_tt_page("home-tutorial-input")
change_tt_page("home-tutorial-output")

@callback(
    Output("home-tutorial-input","items"),
    Output("home-tutorial-output","items"),
    Input("home-select-analysis-type","active_tab"),
    prevent_initial_call=True
)
def change_tutorials(tab):
    ttin_files = {"single-gene":URL_BASE+"static/tt_input_single_gene.svg",
     "gene-ratio":URL_BASE+"static/tt_input_gene_ratio.svg",
     "geneset":URL_BASE+"static/tt_input_gene_set.svg",
     "marker":URL_BASE+"static/tt_input_markers.svg",
     "network":URL_BASE+"static/tt_input_modules.svg"}
    ttinput = Patch()
    ttinput[1]["src"] = ttin_files[tab]
    ttout = Patch()
    if tab in ["single-gene","gene-ratio","geneset"]:
        ttout[1]["src"] = URL_BASE+"static/tt_output_multi_ds_intra.svg"
        ttout[2]["src"] = URL_BASE+"static/tt_output_multi_ds_inter.svg"
    else:
        ttout[1]["src"] = URL_BASE+"static/tt_output_sg_ds_intra.svg"
        ttout[2]["src"] = URL_BASE+"static/tt_output_sg_ds_inter.svg"
    return ttinput, ttout

@callback(
    Output("session-id","data"),
    Output("storesession","data",allow_duplicate=True),
    Output('hidden-div-for-redirect-callback', 'children',allow_duplicate=True),
    Output('retrieve-error-msg',"displayed"),
    Output('retrieve-error-msg',"message"),
    Input("get-session-id-res", "n_clicks"),
    State("input-session-id", "value"),
    prevent_initial_call=True
)
def retrieve_res(nclicks, ssid):
    if not (nclicks and ssid):
        return no_update
    task = db.session.get(task_tb, ssid)
    if not task:
        return no_update,no_update,no_update,True, "This session does not exist or has not been submited!"
    if task.is_finished():
        return ssid, {"analyze_type":task.analysis_type}, dcc.Location(pathname=URL_BASE+"result_visualization/"+task.analysis_type, id=""), False, str(task)
    else:
        return no_update, no_update, no_update, True, str(task)

# @callback(Output("session","data",allow_duplicate=True),
#           Input({"type": "submit", "index": ALL},"n_clicks"),
#           State("session","data"),
#           prevent_initial_call=True)
# def select_analysis(n_clicks,data):
#     return data
