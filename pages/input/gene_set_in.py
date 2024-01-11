import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
# from dash_iconify import DashIconify
from dash import dcc, html, callback, Input, Output, no_update, State, clientside_callback, Patch
from dash_iconify import DashIconify
# import pandas as pd
import os
import logging
import re
import json
# from time import sleep
import subprocess
from utils import CUTP_KEYS, SURVIVAL_TYPE_KEYS, TIL_SET_KEYS, BS_COLORS, GENE_SYMBOLS, TUMOR_TYPE_KEYS, BUILTIN_GENE_SET, id_factory, LNC_SYMBOLS, TF_SYMBOLS, LR_SYMBOLS
from configs import URL_BASE, TMP_OUTPUT_PATH, SCRIPT_PATH
from pages.shared_components import open_help, review_card_content, collapse_callback
from .input_common import ds_validation, input_tab_select_dataset, input_survival_tab, input_pagecard, ds_survival_callbacks, parse_geneset, add_or_update_record

## =================================================
##      page of single gene analysis param input
## =================================================

# --- Register page --- #ß
dash.register_page( 
    __name__,
    top_nav=True,
    path='/gene-set/input',
    title='SurvivalGenie2.0 Gene Set Based Analysis Options', 
    location="navbar"
)

pgid = id_factory("gnset-in")
app = dash.get_app()
# --- Components --- #

geneset_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Please Select/Enter the gene set of interest.",
                    html.Br(),
                    html.Small(["The GeneSet Variation ", html.A("(GSVA) ", href="https://doi.org/10.1186/1471-2105-14-7", target="_blank"), "Score will be used for the analysis. Please select the built-in gene set of ineterest or use the Valid Gene Symbols as input, e.g. TP53, EGFR."])
                    ], className="card-text"),
            
            html.Br(),
            dbc.Col([
                dmc.Group([
                    dmc.Button("Use My Own Gene Set",  id=pgid("sel-user-gnset"), className="btn btn-primary", type="button", n_clicks=0),
                    dmc.Text("OR", weight=700),
                    dmc.Text("Select a Built-in Gene Set:"),
                    dmc.Select(
                            id=pgid("sel-builtin-gnset"),
                            data=[{"label": "Use My Own Gene Set" , "value": "userinput"}] + [{"label": key , "value": key} for key in BUILTIN_GENE_SET],
                            style={"width": 400},
                            ),
                    dmc.ActionIcon(DashIconify(icon="ep:question-filled", width=30,height=30, color="secondary"),  id=pgid("geneset-help"), n_clicks=0),
                    ],
                    
                #     className="input-group mb-3",
                #     style={"margin-bottom": "15px", "overflow-x":"auto"},
                ),
                html.Br(),
                dbc.Textarea(
                    size="sm",
                    readOnly=False,
                    debounce=True,
                    className="mb-3",
                    placeholder="The Genes in the Gene Set, where each gene is separated by new line, tab, space, or comma",
                    id=pgid("genes_in_sets"),
                ),
                dbc.FormText(id=pgid("gene-set-warning"), color='danger'),
                dbc.Toast(
                    [
                        "The gene symbols in the selected gene set will be displayed below. For providing your own geneset, please enter the official gene symbol for your genes of interest. The patient cohort of interest (selected under the 'Datasets for analysis tab') will be partioned into high and low expression groups by their GSVA values (based on the analysis parameters under 'Survival options') to predict outcomes correlated to the log ratio of the expression of selected genes. ",
                        html.A("Please refer to the HGNC for official gene symbols.", href="https://www.genenames.org/", target="_blank")
                    ],
                    id=pgid("geneset-help-toast"), header="Help on gene set input", icon="warning", is_open=False, duration=20000, dismissable=True, style={"position": "static", "margin-bottom": "15px", "width": "auto"},
                ),
            ]),
            html.Br(),
            html.Div([ ## lnc/ligand receptor pair
                html.H6("Gene Filter"),
                html.P(["Select which genes will be used for the analysis. \"All\" by Default. Other available options are only long non-coding RNAs (Only lncRNAs), only ",html.A("Transcroptional factors",href="https://github.com/aertslab/pySCENIC/tree/master")," (Only TFs), and ",html.A("Ligand-Receptors",href="https://github.com/sqjin/CellChat")," (Only LRs). The input genes will be filtered instantly, genes not in the category will be removed for the analysis."], className="card-text", style={"color":"gray", "font-size":"0.9rem"}),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                    dbc.RadioItems(
                                        id=pgid("gene-filter"),
                                        className="btn-group btn-group-md",
                                        inputClassName="btn-check",
                                        labelCheckedClassName="active",
                                        labelClassName="btn btn-outline-primary",
                                        options=[
                                            {"label": "All", "value": 'all'},
                                            {"label": "lncRNA only", "value": 'lnc'},
                                            {"label": "TF only", "value": 'tf'},
                                            {"label": "LR only", "value": 'lr'},
                                            ],
                                        value='all'
                                    ),
                            className="radio-group",
                            ),
                        width="auto",
                        ),
                    ],
                justify="left", 
                align="center",
                style={"margin-bottom": "15px"},
                ),
                html.Br()]),
            dbc.Button("Next",  id=pgid("next1"), color="primary", n_clicks=0),
        ]
    ),
    className="mt-3",
)

INPUTS = dbc.Tabs(
    [
        dbc.Tab(geneset_tab, label="Gene of interest", tab_id="geneset-tab"),
        dbc.Tab(input_tab_select_dataset(pgid), label="Dataset for analysis", tab_id="dataset-tab"),
        dbc.Tab(input_survival_tab(pgid), label="Survival options", tab_id="survival-tab"),
    ],
    id=pgid("input-tabs"),
    active_tab="geneset-tab",
)

REVIEW = dbc.Card(
    dbc.CardBody([
        html.H5("Review selected options", style={"margin-top": "15px"}),
        review_card_content(pgid, "gene_set", long_gene_list=True),
        dbc.Row(
                dbc.Col(dbc.Button("Analyze", id=pgid("btn-analyze"), color="warning", n_clicks=0, size="md", disabled=True), width="auto", style={"margin-top": "15px"}),#, href="/single_gene/result"
                justify="end",
            ),
    ]),
    className="card text-white bg-primary mb-3",
)

SG_INPUT = input_pagecard(pgid, INPUTS, REVIEW)

# --- Layout --- #
def layout():
    layout = dbc.Container(
        [
            html.Br(),
            dbc.Row(
                [dbc.Col(id=pgid("options"), children=SG_INPUT,
                     md=dict(size=12),
                     lg=dict(size=10),
                     xl=dict(size=8),)],
                justify="center",
            ),
        ],
        fluid=True,
    )

    return layout


# --- Callbacks --- #

# user_info_validation()

open_help(pgid("geneset-help-toast"),pgid("geneset-help"))
open_help(pgid("group-help-toast"),pgid("group-help"))

clientside_callback(
    """function(next1, next2, gs_valid) {
        if (!(gs_valid)) { return "geneset-tab"; }
        else if (gs_valid && (next2 == 0)) { return "dataset-tab"; }
        else {return "survival-tab";}
    }""",
    Output(pgid("input-tabs"), "active_tab"),
    Input(pgid("next1"), "n_clicks"),
    Input(pgid("next2"), "n_clicks"),
    State(pgid("genes_in_sets"), "valid"),
    prevent_initial_call=True
)


@callback(
    Output(pgid("genes_in_sets"), "readOnly", allow_duplicate=True),
    Output(pgid("genes_in_sets"), "value", allow_duplicate=True),
    Input(pgid("sel-builtin-gnset"), "value"),
    prevent_initial_call=True
)
def sel_geneset(geneset):
    if geneset == "userinput":
        return False, no_update
    genes_concat = "\t".join(BUILTIN_GENE_SET[geneset])
    return True, genes_concat

@callback(
    Output(pgid("sel-builtin-gnset"), "value",allow_duplicate=True),
    Output(pgid("genes_in_sets"), "readOnly"),
    Input(pgid("sel-user-gnset"), "n_clicks"),
    prevent_initial_call=True
)
def input_own_gs(nclicks):
    if nclicks:
        return "userinput", False
    return no_update, no_update
# 
@callback(
    Output(pgid("genes_in_sets"), "invalid"),
    Output(pgid("genes_in_sets"), "valid"),
    Output(pgid("gene-set-warning"), "children"),
    Output(pgid("genes_in_sets"), "value"),
    Output(pgid("sel-builtin-gnset"), "value",allow_duplicate=True),
    Input(pgid("genes_in_sets"), "value"),
    Input(pgid("gene-filter"), "value"),
    State(pgid("sel-builtin-gnset"), "value"),
    prevent_initial_call=True
)
def sel_geneset(genes_str, genes_filter, geneset):
    if not(genes_str):
        return False, False, None, no_update, no_update
    if (geneset != "userinput") and (genes_filter == 'all'):
        return False, True, None, no_update, no_update
    genes = parse_geneset(genes_str)

    genesvalid, genesinvalid = [], []
    if genes_filter == "lnc":
        for g in genes:
            (genesinvalid, genesvalid)[g in LNC_SYMBOLS].append(g)
    elif genes_filter == "tf":
        for g in genes:
            (genesinvalid, genesvalid)[g in TF_SYMBOLS].append(g)
    elif genes_filter == "lr":
        for g in genes:
            (genesinvalid, genesvalid)[g in LR_SYMBOLS].append(g)
    else:
        for g in genes:
            (genesinvalid, genesvalid)[g in GENE_SYMBOLS].append(g)
    warntext = ''
    if len(genesvalid)==0:
        warntext = "No gene symbol pass the filter."
    elif len(genesinvalid)>0:
        warntext = 'Unsupported Gene Symbols Removed: '+', '.join(genesinvalid)+'. ' if len(genesinvalid)>0 else ''
    return False, True, warntext, '\t'.join(genesvalid), "userinput"

@callback(
    Output(pgid("btn-analyze"), "disabled"),
    Input(pgid("genes_in_sets"), "valid"),
    Input(pgid("dataset-datatable"), "selected_row_ids")
)
def analyze_disabled(gs_valid, datasets):
    return (not gs_valid) or (len(datasets)<=0)

@callback(
        Output(pgid("review-genes-btn"), "children"),
        Output(pgid("review-genes-detail"), "children"),
        Input(pgid("genes_in_sets"), "value"),
        Input(pgid("sel-builtin-gnset"), "value"),
        prevent_initial_call= False
    )
def review_gene_input(genes_str,geneset):
    if not genes_str:
        return "Please Provide Gene Set of Interest", None
    
    genes = genes_str.split()
    genesprint = f"Gene Set: {geneset} " if geneset!= "userinput" else "Customized Gene Set. "
    genesprint = [genesprint, DashIconify(icon="ion:caret-down", width=20,height=20, color="light")]
    return genesprint, ", ".join(genes)

collapse_callback(pgid("review-genes"),prevent_initial_call=True)

ds_survival_callbacks(pgid)


@app.long_callback(
    [Output("storesession","data",allow_duplicate=True),
     Output(pgid("loading-res"), "children"),
     Output(pgid('error-msg'), 'displayed'),
     Output(pgid('error-msg'), 'message'),],
    [Input(pgid("btn-analyze"),"n_clicks")],
    [State(pgid("genes_in_sets"), "value"),
     State(pgid("sel-builtin-gnset"), "value"),
     State(pgid("dataset-datatable"), "selected_row_ids"),
     State(pgid("tumor-type"), "value"),
     State(pgid("age-group"), "value"),
     State(pgid("cutp"), "value"),
     State(pgid("percentile-slider"),"value"),
     State(pgid("outcomes"), "value"),
     State(pgid("sg-til-set"), "value"),
     State(pgid("btn-lm-filter"),"on"),
     State("session-id","data")],
    prevent_initial_call=True
)
def submit_analyze(nclicks, genes_in_gs, geneset, dataset, tumor_type, age_group, cutp, percentiles, outcomes, 
                   til_set, til_filter, session_id):
    if not nclicks:
        return no_update
    
    dataset = dataset if len(dataset)<6 else dataset[:5]

    ds_invalid, msg = ds_validation(dataset, tumor_type, til_set, til_filter)
    if ds_invalid:
        return no_update, no_update, ds_invalid, msg

    analyze_params = {
        "analyze_type":"gene_set",
        "gene_symbol": list(set(genes_in_gs.split())),
        "gene_set": geneset,
        "dataset":dataset,
        "tumor_type":tumor_type,
        "cutp_method": cutp,
        "percentiles": percentiles,
        "survival_type": outcomes,
        "case_age_group":age_group,
        "til_set": til_set,
        "til_fil": til_filter,
    }
    
    cmds = ["Rscript",os.path.join(SCRIPT_PATH, "gene_set_analysis.R"),
            "--session_id",session_id,
            "-A",analyze_params["analyze_type"],
            "--genes",' '.join(set(genes_in_gs.split())),
            "--gene_set", geneset,
            "--datasets", ' '.join(dataset),
            "--tumor_type",TUMOR_TYPE_KEYS[tumor_type].val,
            "-S",SURVIVAL_TYPE_KEYS[outcomes]["val"],
            "--group_method",CUTP_KEYS[cutp]["val"],
            "--upper_per", str(max(percentiles)),
            "--lower_per", str(min(percentiles)),
            "--case_age_group", age_group,
            "--wd", SCRIPT_PATH,
            "--out_dir", TMP_OUTPUT_PATH]
    msg=add_or_update_record(session_id, analyze_params["analyze_type"], 1)
    if msg:
        return dict(), no_update, True, msg
    app.logger.info(f"{session_id}-{analyze_params['analyze_type']}: start analysis")
    subppp = subprocess.Popen(cmds, 
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    # print(' '.join(cmds))
    _, res_err = subppp.communicate()
    subppp.wait()
    res_err = res_err.decode()
    if "[SUCCESS] Pipeline Finished [SSECCUS]" in res_err:
        res_file = os.path.join(TMP_OUTPUT_PATH, f"{session_id}_visualization.json")
        figdata = None
        try:
            with open(res_file, 'r') as f:
                figdata = json.load(f)
            if not figdata:
                app.logger.warning(f"{session_id}: Result does not exist or is broken.")
                return dict(), no_update, True, "Result does not exist or is broken."
            figdata["params"] = analyze_params
            with open(res_file, 'wt') as f:
                json.dump(figdata, f)
        except IOError:
            app.logger.warning(f"{session_id}: Result does not exist or is broken.")
            add_or_update_record(session_id, analyze_params["analyze_type"], 2)
            return dict(), no_update, True, "IOError: Result does not exist or is broken."
        add_or_update_record(session_id, analyze_params["analyze_type"], 0)
        return analyze_params , dcc.Location(pathname=URL_BASE+"result_visualization/"+analyze_params["analyze_type"], id=""), False, no_update
    else:
        add_or_update_record(session_id, analyze_params["analyze_type"], 2)
        r_errors = re.findall(r'^\[IT\d{3}\].*\n', res_err, flags=re.MULTILINE)
        r_errors = ["Following Errors Occured:\n"] + r_errors + ["Please try other parameters or reach out to our team with the Analysis ID, input and error codes."]
        app.logger.warning(f"{session_id} error msg:\n{res_err}")
        return dict(), no_update, True, ''.join(r_errors)



# def validate_input():
#     pass