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
    path='/signaling_strength/input',
    title='SurvivalGenie2.0 Ligand-Receptor Signaling Analysis Options', 
    location="navbar"
)

pgid = id_factory("lrsignal-in")
app = dash.get_app()


# --- Components --- #

def create_gene_input(title="Genes Input",
                             id_postfix="",
                             helper_toast = True):
    col_content = [
        html.H6(title),
        html.Br(),
        dbc.Input(
            size="sm",
            className="mb-3",
            placeholder="Gene symbol(s)",
            id=pgid(f"genes_in_sets-{id_postfix}"),
            persistence=True, persistence_type="session",
        ),
        dbc.FormText(id=pgid(f"gene-set-warning-{id_postfix}"), 
        color='danger'),
        # add gene filter
        dbc.Row([
            dbc.Col("Filter:",width=1),
            dbc.Col(
                html.Div(
                    dbc.RadioItems(
                        id=pgid(f"gene-filter-{id_postfix}"),
                        className="btn-group btn-group-md",
                        inputClassName="btn-check",
                        labelCheckedClassName="active",
                        labelClassName="btn btn-sm btn-outline-primary ",
                        options=[
                            {"label": "All", "value": 'all'},
                            {"label": "Only CellChatDB", "value": 'lr'},
                            ],
                        value='all',
                        persistence=True, persistence_type="session",
                    ),
                    className="radio-group",
                ),
            width="auto",
                ),
            dbc.Col(
                dmc.Tooltip(
                        DashIconify(icon="ep:question-filled", width=20, height=20, color="#9ebdf2"), style={"display":"inline"},
                        label = ["Select which genes will be used for the analysis. \"All\" by Default, or only the ligand-receptors inlcuded in ",html.A("CellChatDB",href="https://github.com/sqjin/CellChat"), ". The input genes will be filtered instantly, and the genes not in the category will be removed for the analysis."],
                        multiline=True, width = 520, transition=True, withArrow=True,color="grey")
            )
            ],
        justify="left", 
        align="center",
        style={"margin-bottom": "15px"},
        ),
        # add the gene fillter 
    ] # end of col_content
    if helper_toast:
        col_content.append(
            dbc.Toast([
                "The gene symbols of the selected genes will be displayed in the Review tab. Please enter the official gene symbols corresponding to your genes of interest. Based on the selected dataset (as specified under the 'Select Dataset(s)' tab), samples will be partitioned into high and low expression groups according to their inferred signaling strength. This partitioning is determined using the cutpoint defined under the 'Analysis Settings' tab, enabling survival outcome analysis in relation to signaling activity.",
                html.A("Please refer to the HGNC for official gene symbols.", href="https://www.genenames.org/", target="_blank")
            ],
            id=pgid("genes-help-toast"), header="Help on gene input", icon="warning", is_open=False, duration=20000, dismissable=True, style={"position": "static", "margin-bottom": "15px", "width": "auto"},)
            )
    return dbc.Col(col_content)

geneset_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Please enter the genes of interest.",
                    html.Br(),
                    html.Small(["The inferred signaling strength (inferred by the product of geometric means of ligand and receptors in each sample) will be used for the analysis. Please input the genes of ineterests with the valid gene symbols as input, e.g. TP53, EGFR. "]),
                    html.Br(),
                    html.Small(["Note: This analysis does not validate the biological authenticity of the specified ligand-receptor pairs. It solely estimates the signaling strength based on the input genes. For more detailed and cell type-specific interaction analyses, we recommend using tools such as ", html.A("CellChat",href="https://doi.org/10.1038/s41467-021-21246-9", target="_blank"), " on single-cell datasets."])
                    ], className="card-text"),
            
            html.Hr(),
            #### <- insert tabs for select genes 
            create_gene_input(title="Ligands",
                             id_postfix="l",
                             helper_toast = False),
            html.Hr(),
            create_gene_input(title="Receptors",
                             id_postfix="r",
                             helper_toast = True),
            html.Hr(),
            dbc.Button("Next",  id=pgid("next1"), color="primary", n_clicks=0),
        ]
    ),
    className="mt-3",
)

INPUTS = dbc.Tabs(
    [
        dbc.Tab(geneset_tab, label="Input Genes", tab_id="gene-tab"),
        dbc.Tab(input_tab_select_dataset(pgid), label="Select Dataset(s)", tab_id="dataset-tab"),
        dbc.Tab(input_survival_tab(pgid), label="Analysis Settings", tab_id="survival-tab"),
    ],
    id=pgid("input-tabs"),
    active_tab="gene-tab",
)

REVIEW = dbc.Card(
    dbc.CardBody([
        html.H5("Review selected options", style={"margin-top": "15px"}),
        review_card_content(pgid, "lrsignal", long_gene_list=True, rv_postfixes=["l","r"]),
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
    """function(next1, next2, gs_valid_pos, gs_valid_neg) {
        if (!(gs_valid_pos && gs_valid_neg)) { return "geneset-tab"; }
        else if ((gs_valid_pos && gs_valid_neg) && (next2 == 0)) { return "dataset-tab"; }
        else {return "survival-tab";}
    }""",
    Output(pgid("input-tabs"), "active_tab"),
    Input(pgid("next1"), "n_clicks"),
    Input(pgid("next2"), "n_clicks"),
    State(pgid("genes_in_sets-l"), "valid"),
    State(pgid("genes_in_sets-r"), "valid"),
    prevent_initial_call=True
)

@callback(
    Output(pgid("genes_in_sets-l"), "invalid"),
    Output(pgid("genes_in_sets-l"), "valid"),
    Output(pgid("gene-set-warning-l"), "children"),
    # Output(pgid("genes_in_sets-l"), "value"),
    Input(pgid("genes_in_sets-l"), "value"),
    Input(pgid("gene-filter-l"), "value"),
    prevent_initial_call=True
)
def filter_geneset_pos(genes_str, genes_filter):
    if not(genes_str):
        return False, False, None#, no_update
    # if (genes_filter == 'all'):
    #     return False, True, None, no_update
    genes = parse_geneset(genes_str)

    genesvalid, genesinvalid = [], []
    if genes_filter == "lr":
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in LR_SYMBOLS].append(g)
    else:
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in GENE_SYMBOLS].append(g)
    warntext = ''
    valid_gs = True if len(genesinvalid)==0 else False 
    if len(genesvalid)==0:
        warntext = "No gene symbol passed the filter. " if genes_filter == "lr" else "No valid gene symbol(s). "
        valid_gs= False
    if len(genesinvalid)>0:
        warntext += 'Unsupported Gene Symbols: '+', '.join(genesinvalid)+'. ' if len(genesinvalid)>0 else ''
        # valid_gs = True
    return (not valid_gs), valid_gs, warntext#, '\t'.join(genesvalid)



@callback(
    Output(pgid("genes_in_sets-r"), "invalid"),
    Output(pgid("genes_in_sets-r"), "valid"),
    Output(pgid("gene-set-warning-r"), "children"),
    # Output(pgid("genes_in_sets-r"), "value"),
    Input(pgid("genes_in_sets-r"), "value"),
    Input(pgid("gene-filter-r"), "value"),
    prevent_initial_call=True
)
def filter_geneset_neg(genes_str, genes_filter):
    if not(genes_str):
        return False, False, None#, no_update
    # if (genes_filter == 'all'):
    #     return False, True, None, no_update
    genes = parse_geneset(genes_str)

    genesvalid, genesinvalid = [], []

    if genes_filter == "lr":
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in LR_SYMBOLS].append(g)
    else:
        for g in genes:
            (genesinvalid, genesvalid)[g.upper() in GENE_SYMBOLS].append(g)
    warntext = ''
    valid_gs= True if len(genesinvalid)==0 else False 
    if len(genesvalid)==0:
        warntext = "No gene symbol passed the filter. " if genes_filter == "lr" else "No valid gene symbol(s). "
        valid_gs = False
    if len(genesinvalid)>0:
        warntext += 'Unsupported Gene Symbols: '+', '.join(genesinvalid)+'. ' if len(genesinvalid)>0 else ''
        # valid_gs = True
    return (not valid_gs), valid_gs, warntext#, '\t'.join(genesvalid)

@callback(
    Output(pgid("btn-analyze"), "disabled"),
    Input(pgid("genes_in_sets-l"), "valid"),
    Input(pgid("genes_in_sets-r"), "valid"),
    Input(pgid('selected-datasets'), "data"),
    Input(pgid("btn-review"), "n_clicks"),
)
def analyze_disabled(gs_valid,gs_valid_neg,datasets, _):
    return (not gs_valid) or (len(datasets)<=0) or (not gs_valid_neg)

########## REVIEWING #########
@callback(
        Output(pgid("review-genes-l-btn"), "children"),
        Output(pgid("review-genes-detail-l"), "children"),
        Output(pgid("review-genes-r-btn"), "children"),
        Output(pgid("review-genes-detail-r"), "children"),
        Input(pgid("genes_in_sets-l"), "value"),
        Input(pgid("genes_in_sets-r"), "value"),
        prevent_initial_call= False
    )
def review_gene_input(genes_str_pos,genes_str_neg):
    if not genes_str_pos or not genes_str_neg:
        return "Please Provide Gene Set of Interest", None, None, None
    
    genes_pos = parse_geneset(genes_str_pos)
    genesprint_pos = "Ligand(s)"
    genesprint_pos = [genesprint_pos, DashIconify(icon="ion:caret-down", width=20,height=20, color="light")]

    genes_neg = parse_geneset(genes_str_neg)
    genesprint_neg = "Receptor(s)"
    genesprint_neg = [genesprint_neg, DashIconify(icon="ion:caret-down", width=20,height=20, color="light")]

    return genesprint_pos, ", ".join(genes_pos), genesprint_neg, ", ".join(genes_neg)

collapse_callback(pgid("review-genes-l"),prevent_initial_call=True)
collapse_callback(pgid("review-genes-r"),prevent_initial_call=True)

ds_survival_callbacks(pgid)


@callback(
    [Output("storesession","data",allow_duplicate=True),
     Output("hidden-div-for-redirect-callback", "children",allow_duplicate=True),
     Output(pgid('error-msg'), 'displayed'),
     Output(pgid('error-msg'), 'message'),],
    [Input(pgid("btn-analyze"),"n_clicks")],
    [State(pgid("genes_in_sets-l"), "value"),
     State(pgid("genes_in_sets-r"), "value"),
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
def submit_analyze(nclicks, genes_in_gs_pos, genes_in_gs_neg, dataset, cutp, percentiles, 
                   til_set, til_filter, session_id, error_nclicks):
    if not nclicks:
        return no_update
    
    dataset = dataset if len(dataset)<6 else dataset[:5]

    if error_nclicks < 1:
        ds_invalid, msg = ds_validation(dataset, til_set, til_filter)
        if ds_invalid:
            return no_update, no_update, ds_invalid, msg

    analyze_params = {
        "session_id":session_id,
        "analyze_type":"lrsignal",
        "gene_symbol_l": list(set(parse_geneset(genes_in_gs_pos))),
        "gene_symbol_r": list(set(parse_geneset(genes_in_gs_neg))),
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
            analysis_type="lrsignal",
            genes_l=list(set(parse_geneset(genes_in_gs_pos))),
            genes_r=list(set(parse_geneset(genes_in_gs_neg))),
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

    figdata = dict(params = analyze_params, rparams = rparams)
    cmds = ["Rscript",os.path.join(SCRIPT_PATH, "signaling_strength_analysis.R"),
            "--use_file", res_file,
            "--session_id",session_id]
    msg=add_or_update_record(session_id, analyze_params["analyze_type"], 1)
    if msg:
        return dict(), no_update, True, msg
    with open(res_file, 'wt') as f:
        json.dump(figdata, f)
    app.logger.info(f"{session_id}-{analyze_params['analyze_type']}: start analysis")
    with subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as subppp:
        # print(subprocess.list2cmdline(cmds))
        _, res_err = subppp.communicate()
        subppp.wait()
    res_err = res_err.decode()
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