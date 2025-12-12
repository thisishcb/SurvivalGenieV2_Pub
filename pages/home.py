import os
import json
# import re
import uuid
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback, no_update, State, clientside_callback, Patch, MATCH
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
## Warnings and news 
# Purple #6f42c1
color_spec = dict(
    single_gene = "primary", # blue
    gene_ratio = "info", # cyan
    multi_genes = "success", # green
    LR_pairs = "#d63384", # pink 
    geneset = "#fd7e14", # orange
    geneset_contrast = "#6610f2", # indigo
    cluster_marker = "warning", # yellow
    coexp_network = "#20c997", # TEAL
    grn = "#8a6d3b" #brown #"#6f42c1" # purple
    # "#c0eb75"  # lime 
    #8a6d3b #brown
    #5c6e80 #Slate
    #f0e6d2 #Stone
)

news_tab = dbc.Row(
        dbc.Col([
            dbc.Alert(
                ["The functionality of SurvivalGenie 1 has been integrated into SurvivalGenie 2. The service remains available at ", 
                html.A("https://bhasinlab.bmi.emory.edu/archive/SurvivalGenie/",href="https://bhasinlab.bmi.emory.edu/archive/SurvivalGenie/", className="alert-link"), 
                ". Please note that the archived SurvivalGenie 1 service will be discontinued after June 1, 2026. If you have any questions or suggestions, feel free to reach out via our contact page."],
                id="home-alert-1",
                dismissable=True,
                is_open=True,
                color="warning",
            )
        ], 
        sm=dict(size=12),
        lg=dict(size=8)),
    justify="center")


## single gene analysis  /singlegene/input
single_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("Survival outcomes are predicted by stratifying samples into high versus low groups based on the FPKM expression of the gene of interest in up to 5 datasets.", className="card-text"),
            # html.P(html.A("Example output Page", href="") ,style={"font-style": "italic", "color": "var(--bs-primary)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color=color_spec["single_gene"], href=URL_BASE+"example_out/single_gene", id={'type': 'btn', 'index': 0}),
                dbc.Button("Begin", color=color_spec["single_gene"], href=URL_BASE+"singlegene/input",id={"type": "submit", "index": "singlegene"}, value="singlegene", n_clicks=0),
            ])
        ]
    ),
    className="mt-3",
)

## gene ratio analysis /ratio/input
ratio_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("Survival outcomes are predicted by stratifying samples into high versus low groups based on the log expression ratio of two genes of interest.", className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-info)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color=color_spec["gene_ratio"], href=URL_BASE+"example_out/gene_ratio", id={'type': 'btn', 'index': 1}),
                dbc.Button("Begin", color=color_spec["gene_ratio"], href=URL_BASE+"ratio/input",id={"type": "submit", "index": "ratio"}, value="ratio", n_clicks=0),
            ])
        ]
    ),
    className="mt-3",
)

## gene-set analysis /gene-set/input
geneset_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Survival outcomes are predicted by stratifying samples into high versus low groups based on the Gene Set Variation Analysis (GSVA) enrichment score of a gene list or gene signatures."
                    ], className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-success)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, style={"border-color":color_spec["geneset"], "color":color_spec["geneset"]}, href=URL_BASE+"example_out/gene_set", id={'type': 'btn', 'index': 2}),
                dbc.Button("Begin", color=color_spec["geneset"],href=URL_BASE+"gene-set/input",id={"type": "submit", "index": "geneset"}, n_clicks=0,value="geneset", style={'background-color': color_spec["geneset"],"color":"#ffffff",}),
            ])
            
        ]
    ),
    className="mt-3",
)

## gene-set analysis /gene-set/input
multi_sg_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("Survival outcomes are predicted by stratifying samples into high versus low groups based on the FPKM expression of gene(s) of interest individually in one dataset.", className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-success)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color=color_spec["multi_genes"], href=URL_BASE+"example_out/multi_sg", id={'type': 'btn', 'index': 3}),
                dbc.Button("Begin", color=color_spec["multi_genes"],href=URL_BASE+"multi-genes/input",id={"type": "submit", "index": "geneset"}, n_clicks=0,value="multisg"),
            ])
            
        ]
    ),
    className="mt-3",
)

## gene-set analysis /gene-set/input
## indigo 
geneset_contrast_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Survival outcomes are predicted by stratifying samples into high versus low groups based on the Gene Set Variation Analysis enrichment score difference between two gene list or gene signatures(i.e. two sets of genes of interest). This analysis is useful for comparing the enrichment of two gene sets, particularly when they are expected to exhibit distinct enrichment patterns."], className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-success)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, href=URL_BASE+"example_out/gene_set_contrast", style={"border-color":color_spec["geneset_contrast"], "color":color_spec["geneset_contrast"],}, id={'type': 'btn', 'index': 4}),
                dbc.Button("Begin", color=color_spec["geneset_contrast"],href=URL_BASE+"/gene-set-contrast/input",id={"type": "submit", "index": "geneset-contrast"}, n_clicks=0,value="gene-set-contrast",style={'background-color': '#6610f2',"color":"#ffffff",}),
            ])
            
        ]
    ),
    className="mt-3",
)

## cluster marker based analysis /cluster-marker/input
cluster_marker_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["This analysis predicts survival outcomes by stratifying samples into high versus low GSVA enrichment scores based on the marker genes in each cluster (typically the output of differential expression analysis tools from ", html.A("Seurat", href="https://satijalab.org/seurat/reference/findmarkers", target="_blank")," or ", html.A("scanpy", href="https://scanpy.readthedocs.io/en/stable/tutorials/basics/clustering.html#differentially-expressed-genes-as-markers", target="_blank"), ").",
             html.Br(),
            ("Required Input: "),
            "A table file containing marker gene symbols, adjusted p-values, and cluster information. See ", html.A("example data",href="http://bhasinlab.bmi.emory.edu/SurvivalGenie2/example_files/reducedheart0609.top10.markers.csv",target="_blank"), ". ",
                    html.Br(),
                    html.Small(html.I("*Note: All uploaded data is deleted immediately after analysis. Generated results are retained for 24 hours. All data transfer is secured over HTTPS with TLS encryption."))
                    ], className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-warning)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, color=color_spec["cluster_marker"], href=URL_BASE+"example_out/cluster_marker", id={'type': 'btn', 'index': 5}),#style={"border-color":color_spec["cluster_marker"], "color":color_spec["cluster_marker"]}
                dbc.Button("Begin", color=color_spec["cluster_marker"],href=URL_BASE+"cluster-marker/input",id={"type": "submit", "index": "lrsignal"}, n_clicks=0,style={'background-color':color_spec["cluster_marker"],"color":"#ffffff",}),
            ])
        ]
    ),
    className="mt-3",
)

## cluster marker based analysis /cluster-marker/input
lr_singal_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P("[EXPERIMENTAL FUNCTION!] Survival outcomes are predicted by stratifying samples into high versus low groups based on the inferred signaling strength between input ligands and receptors (product of geometric mean expressions). Note: This analysis does not validate the biological authenticity of the specified ligand-receptor pairs.", className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-warning)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, style={"border-color":color_spec["LR_pairs"], "color":color_spec["LR_pairs"]}, href=URL_BASE+"example_out/lrsignal", id={'type': 'btn', 'index': 6}),
                dbc.Button("Begin", color=color_spec["LR_pairs"],href=URL_BASE+"signaling_strength/input",id={"type": "submit", "index": "rnqseq"}, n_clicks=0,style={'background-color':color_spec["LR_pairs"],"color":"#ffffff",}),
            ])
        ]
    ),
    className="mt-3",
)

wgcna_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Survival outcomes are predicted by stratifying samples into high versus low groups based on the eigengene GSVA enrichment scores for each co-expression module/network (typically the output of co-expression network analysis tool like ", html.A("hdWGCNA", href="https://smorabit.github.io/hdWGCNA/", target="_blank"),").", html.Br(),
            ("Required Input: "),
            "A table containing gene symbols, module assignments. See ", html.A("example data",href="http://bhasinlab.bmi.emory.edu/SurvivalGenie2/example_files/reduced_module_hub_genes.csv",target="_blank"),". ",
            "Need help generating modules? Check out our wrapped hdWGCNA function on ", html.A("github link", href="https://github.com/bhasin-lab/SurvivalGenieV2/blob/main/scripts/get_wgcna_result.R", target="_blank"),
                    html.Br(),
                    html.Small(html.I("*Note: All uploaded data is deleted immediately after analysis. Generated results are retained for 24 hours. All data transfer is secured over HTTPS with TLS encryption."))
                    ], className="card-text"),
            # html.P("Example output:", style={"font-style": "italic", "color": "var(--bs-danger)", "font-size": "0.9em"}),
            # html.P("<example output figure>", style={"font-style": "italic", "color": "#808080"}),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, style={"border-color":color_spec["coexp_network"], "color":color_spec["coexp_network"]}, href=URL_BASE+"example_out/wgcna_module", id={'type': 'btn', 'index': 7}),
                dbc.Button("Begin", color=color_spec["coexp_network"],href=URL_BASE+"coexp-module/input",value="wgcna",id={"type": "submit", "index": "wgcna"}, n_clicks=0, style={'background-color':color_spec["coexp_network"],"color":"#ffffff",}),
            ])
        ]
    ),
    className="mt-3",
)

grn_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Survival outcomes are predicted by stratifying samples into high versus low groups based on the regulated gene GSVA enrichment scores for each GRN (typically the output of GRN analysis tool like ", html.A("PySCENIC", href="https://github.com/aertslab/pySCENIC", target="_blank"),").", html.Br(),
            ("Required Input: "),
            "A table containing gene symbols, regulon/GRN assignments. See ", html.A("example data",href="http://bhasinlab.bmi.emory.edu/SurvivalGenie2/example_files/reducedPlasma_top_regulon.tsv",target="_blank"),". ",
                    html.Br(),
                    html.Small(html.I("*Note: All uploaded data is deleted immediately after analysis. Generated results are retained for 24 hours. All data transfer is secured over HTTPS with TLS encryption."))
                    ], className="card-text"),
            html.Div([
                dbc.Button("Example Output Page", className="me-2", outline=True, style={"border-color":color_spec["grn"], "color":color_spec["grn"]}, href=URL_BASE+"example_out/grn_module", id={'type': 'btn', 'index': 8}),
                dbc.Button("Begin", color=color_spec["grn"],href=URL_BASE+"grn-module/input",value="grn",id={"type": "submit", "index": "grn"}, n_clicks=0, style={'background-color':color_spec["grn"],"color":"#ffffff",}),
            ])
        ]
    ),
    className="mt-3",
)


INPUTS = dbc.Tabs(
    [
        dbc.Tab(single_tab, label="Single Gene",tab_id="single-gene"),
        dbc.Tab(multi_sg_tab, label="Multiple Genes",tab_id="multi-genes"),
        dbc.Tab(ratio_tab, label="Gene Ratio",tab_id="gene-ratio"),
        dbc.Tab(lr_singal_tab, label="L-R Pairs",tab_id="lrsignal"),
        dbc.Tab(geneset_tab, label="Gene Set",tab_id="geneset"),
        dbc.Tab(geneset_contrast_tab, label="Gene Set Contrast",tab_id="geneset-contrast"),
        dbc.Tab(cluster_marker_tab, label="Cluster Markers",tab_id="marker"),
        dbc.Tab(wgcna_tab, label="Co-expression Network",tab_id="network"),
        dbc.Tab(grn_tab, label="Gene Regulatory Network",tab_id="grn"),
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
    ], id = "home-tutorial-collapse", is_open=True)

OPENSOURCE = dbc.Row(
    dbc.Col([
        html.Hr(),
        dbc.FormText(["The Survival Genie platform is an open access tool developed by ", html.A("the Bhasin Lab at Emory University", href="https://bhasinlab.org/"), " for researchers to freely use, including for academic and commercial use under ", html.A("MIT Liscence", href="https://github.com/git/git-scm.com/blob/main/MIT-LICENSE.txt"),". This Web Server is developed under ", html.A("Dash Framework",href="https://dash.plotly.com/"), ". The source code is available at ", html.A("Github.", href="https://github.com/bhasin-lab/SurvivalGenieV2/")])],
        sm=dict(size=12),lg=dict(size=8)
    ), justify="center"
)
# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        news_tab,
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
    prevent_initial_call = False
)

# show spinner in example page buttons 
clientside_callback(
    """
    function (click) {
        return [""" + json.dumps(dbc.Spinner(size='sm').to_plotly_json()) + """, " Loading..."]
    }
    """,
    Output({'type': 'btn', 'index': MATCH}, 'children'),
    Input({'type': 'btn', 'index': MATCH}, 'n_clicks'),
    prevent_initial_call=True
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
     "network":URL_BASE+"static/tt_input_modules.svg",
     "grn":URL_BASE+"static/tt_input_modules.svg",
     "geneset-contrast":URL_BASE+"static/tt_input_gene_set_contrast.svg",
     "multi-genes":URL_BASE+"static/tt_input_multi_sg.svg",
     "lrsignal":URL_BASE+"static/tt_input_lrsignal.svg",}
    ttinput = Patch()
    ttinput[1]["src"] = ttin_files[tab]
    ttout = Patch()
    if tab in ["single-gene","gene-ratio","geneset","geneset-contrast"]:
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
