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
from utils import CUTP_KEYS, SURVIVAL_TYPE_KEYS, TIL_SET_KEYS, BS_COLORS, GENE_SYMBOLS, TUMOR_TYPE_KEYS, BUILTIN_GENE_SET, id_factory, LNC_SYMBOLS, TF_SYMBOLS, LR_SYMBOLS, CASE_AGE_GROUP_KEYS, ds2str
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
    path='/multi-genes/input',
    title='SurvivalGenie2.0 Multiple-Genes Analysis Options', 
    location="navbar"
)

pgid = id_factory("mulsg-in")
app = dash.get_app()
# --- Components --- #
MAX_DS = 1

geneset_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Please Select/Enter the genes of interest. (Max:20 genes)",
                    html.Br(),
                    html.Small(["Survival analysis of each gene will be performed individually on the selected dataset. Please use the Valid Gene Symbols as input, e.g. TP53, EGFR. For visualization compatibility, current analysis limits the max number of genes to 20."])
                    ], className="card-text"),
            
            html.Br(),
            dbc.Col([
                dbc.Textarea(
                    size="sm",
                    readOnly=False,
                    debounce=True,
                    className="mb-3",
                    placeholder="Gene symbols: each gene should be separated by new line, tab, space, or comma. Maximum: 20 genes",
                    id=pgid("genes_in_sets"),
                    persistence=True, persistence_type="session",
                ),
                dbc.FormText(id=pgid("gene-set-warning"), color='danger'),
                dbc.Toast(
                    [
                        "The gene symbols in the selected gene set will be displayed below. For providing your own geneset, please enter the official gene symbol for your genes of interest. The patient cohort of interest (selected under the 'Datasets for analysis tab') will be partioned into high and low expression groups by their GSVA values (based on the analysis parameters under 'Survival options') to predict outcomes correlated to the log ratio of the expression of selected genes. ",
                        html.A("Please refer to the HGNC for official gene symbols.", href="https://www.genenames.org/", target="_blank")
                    ],
                    id=pgid("geneset-help-toast"), header="Help on gene input", icon="warning", is_open=False, duration=20000, dismissable=True, style={"position": "static", "margin-bottom": "15px", "width": "auto"},
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
                                        value='all',
                                        persistence=True, persistence_type="session",
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
        dbc.Tab(geneset_tab, label="Input Genes", tab_id="geneset-tab"),
        dbc.Tab(input_tab_select_dataset(pgid, max_dataset=MAX_DS), label="Select Dataset(s)", tab_id="dataset-tab"),
        dbc.Tab(input_survival_tab(pgid), label="Analysis Settings", tab_id="survival-tab"),
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
    Output(pgid("genes_in_sets"), "invalid"),
    Output(pgid("genes_in_sets"), "valid"),
    Output(pgid("gene-set-warning"), "children"),
    Output(pgid("genes_in_sets"), "value"),
    Input(pgid("genes_in_sets"), "value"),
    Input(pgid("gene-filter"), "value"),
    prevent_initial_call=False
)
def sel_genes(genes_str, genes_filter):
    if not(genes_str):
        return False, False, None, no_update

    genes = parse_geneset(genes_str)

    # if (genes_filter == 'all') and (len(genes) <= 20):
    #     gswarning = None
    #     return False, True, gswarning, no_update


    genesvalid, genesinvalid, genesoverflow = [], [], []
    if genes_filter == "lnc":
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in LNC_SYMBOLS].append(g)
    elif genes_filter == "tf":
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in TF_SYMBOLS].append(g)
    elif genes_filter == "lr":
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in LR_SYMBOLS].append(g)
    else:
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in GENE_SYMBOLS].append(g)
    
    warntext = ''
    if len(genesvalid) > 20:
        warntext = "Maximum of 20 genes reached. Only the first 20 genes will be used. "
        genesoverflow = genesvalid[20:]
        genesvalid = genesvalid[:20]
        warntext += 'Overflow Genes: '+', '.join(genesoverflow)+'. ' if len(genesoverflow)>0 else ''

    if len(genesvalid)==0:
        warntext = "No gene symbol passed the filter." if genes_filter != "all" else "No valid gene symbol(s)."
    elif len(genesinvalid)>0:
        warntext += 'Unsupported Gene Symbols Removed: '+', '.join(genesinvalid)+'. ' if len(genesinvalid)>0 else ''
    return False, True, warntext, '\t'.join(genesvalid)

@callback(
    Output(pgid("btn-analyze"), "disabled"),
    Input(pgid("genes_in_sets"), "valid"),
    Input(pgid('selected-datasets'), "data"),
    Input(pgid("btn-review"), "n_clicks"),
)
def analyze_disabled(gs_valid, datasets, _):
    return (not gs_valid) or (len(datasets)<=0)

@callback(
        Output(pgid("review-genes-btn"), "children"),
        Output(pgid("review-genes-detail"), "children"),
        Input(pgid("genes_in_sets"), "value"),
        prevent_initial_call= False
    )
def review_gene_input(genes_str):
    if not genes_str:
        return "Please Provide Gene Set of Interest", None
    
    genes = parse_geneset(genes_str)
    genesprint = "Customized Genes. "
    genesprint = [genesprint, DashIconify(icon="ion:caret-down", width=20,height=20, color="light")]
    return genesprint, ", ".join(genes)

collapse_callback(pgid("review-genes"),prevent_initial_call=True)

ds_survival_callbacks(pgid)


@callback(
    [Output("storesession","data",allow_duplicate=True),
     Output("hidden-div-for-redirect-callback", "children",allow_duplicate=True),
     Output(pgid('error-msg'), 'displayed'),
     Output(pgid('error-msg'), 'message'),],
    [Input(pgid("btn-analyze"),"n_clicks")],
    [State(pgid("genes_in_sets"), "value"),
     State(pgid('selected-datasets'), "data"),
     State(pgid("cutp"), "value"),
     State(pgid("percentile-slider"),"value"),
     State(pgid("sg-til-set"), "value"),
     State(pgid("btn-lm-filter"),"on"),
     State("session-id","data"),
     State(pgid('error-msg'), 'submit_n_clicks')],
    prevent_initial_call=True,
    background=True,
    running=[
        (Output(pgid("loading-res"), "display"), "show", "hide"),
        (Output(pgid("btn-analyze"), "disabled"), True, no_update)
            ]
)
def submit_analyze(nclicks, genes_in_gs, dataset, cutp, percentiles, 
                   til_set, til_filter, session_id, error_nclicks):
    if not nclicks:
        return no_update
    
    # Init params 
    dataset = dataset if len(dataset)<=MAX_DS else dataset[:MAX_DS]

    if error_nclicks < 1:
        ds_invalid, msg = ds_validation(dataset, til_set, til_filter)
        if ds_invalid:
            return no_update, no_update, ds_invalid, msg

    analyze_params = {
        "session_id":session_id,
        "analyze_type":"multi_sg",
        "gene_symbol": list(set(parse_geneset(genes_in_gs))),
        "dataset":dataset,
        "cutp_method": cutp,
        "percentiles": percentiles,
        "til_set": til_set,
        "til_fil": til_filter,
    }
    res_file = os.path.join(f"{TMP_OUTPUT_PATH}/{session_id}_visualization.json")
    dataset4r = [dict(
            project = ds["project"],
            dataset = ds["dataset"],
            short = ds2str(ds,sep='_'),
            surv_type = SURVIVAL_TYPE_KEYS[ds["surv_type"]].val,
            tumor_type = TUMOR_TYPE_KEYS[ds["tumor_type"]].val,
            age_grp = CASE_AGE_GROUP_KEYS[ds["age_grp"]].val
        ) for ds in dataset]
    rparams = dict( # retain the same structure as the R cmd line parser
        options = dict(
            session_id=session_id,
            analysis_type="multi_sg",
            genes=parse_geneset(genes_in_gs),
            datasets=dataset4r,
            tils=TIL_SET_KEYS[til_set],
            tils_pval=til_filter,
            group_method=CUTP_KEYS[cutp]["val"],
            upper_per = max(percentiles),
            lower_per = min(percentiles),
            wd=SCRIPT_PATH,
            out_dir=TMP_OUTPUT_PATH),
        args = dict()
        )

    # save the params and contruct the submit job cmd 
    figdata = dict(params = analyze_params, rparams = rparams)

    cmds = ["Rscript",os.path.join(SCRIPT_PATH, "multi_sg_analysis.R"),
            "--use_file", res_file,
            "--session_id",session_id]
    msg=add_or_update_record(session_id, analyze_params["analyze_type"], 1)
    if msg:
        return dict(), no_update, True, msg
    with open(res_file, 'wt') as f:
        json.dump(figdata, f)

    # submit jobs
    app.logger.info(f"{session_id}-{analyze_params['analyze_type']}: start analysis")
    with subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as subppp:
        # print(subprocess.list2cmdline(cmds))
        _, res_err = subppp.communicate()
        subppp.wait()
    res_err = res_err.decode()

    # check results and return
    if "[SUCCESS] Pipeline Finished [SSECCUS]" in res_err:
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