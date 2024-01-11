import dash
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from dash import dcc, html, callback, Input, Output, no_update, State, clientside_callback, Patch
import json 
import re
import os
import logging
import subprocess
from utils import CUTP_KEYS, SURVIVAL_TYPE_KEYS, TIL_SET_KEYS, BS_COLORS, GENE_SYMBOLS, TUMOR_TYPE_KEYS, id_factory
from configs import URL_BASE, TMP_OUTPUT_PATH, SCRIPT_PATH
from pages.shared_components import open_help, review_card_content
from .input_common import ds_validation, input_tab_select_dataset, input_survival_tab, input_pagecard, ds_survival_callbacks, add_or_update_record

## =================================================
##      page of single gene analysis param input
## =================================================

# --- Register page --- #ß
dash.register_page( 
    __name__,
    top_nav=True,
    path='/ratio/input',
    title='SurvivalGenie2.0 Gene Ratio Based Analysis Options', 
    location="navbar"
)

pgid = id_factory("ratio-in")
app = dash.get_app()
# --- Components --- #

ratio_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Please enter the gene symbols for your genes of interest.",
                    html.Br(),
                    html.Small(["The value of log((expression of Gene_A)/(expression of Gene_B)) will be used for the analysis. Please use the Valid Gene Symbols as input, e.g. TP53, EGFR. You can also switch the order of two genes with the ",DashIconify(icon="tabler:exchange", inline=True, color="secondary")," button."])
                    ], className="card-text"),
            
            html.Br(),
            html.Div([
                dbc.InputGroupText("log("),
                dbc.Input(id=pgid("gene_A"), placeholder="Gene symbol A", minLength=2, type="text", valid=False, invalid=False, value="", style={"width": "10rem"}),
                dbc.InputGroupText("/"),
                dbc.Input(id=pgid("gene_B"), placeholder="Gene symbol B", minLength=2, type="text", valid=False, invalid=False, value="", style={"width": "10rem"}),
                dbc.InputGroupText(")"),
                dbc.Button(DashIconify(icon="tabler:exchange", width=22,height=22, color="white"),  id=pgid("swith-genes"), className="btn btn-secondary", type="button"),
                dbc.Button("Help",  id=pgid("gene-help"), className="btn btn-secondary", type="button", n_clicks=0),
                ],
                className="input-group mb-3",
                style={"margin-bottom": "15px", "overflow-x":"auto"},
            ),
            dbc.Toast(
                [
                    "Please enter the official gene symbol for your genes of interest. The patient cohort of interest (selected under the 'Datasets for analysis tab') will be partioned into high and low expression groups (based on the analysis parameters under 'Survival options') to predict outcomes correlated to the log ratio of the expression of selected genes. ",
                    html.A("Please refer to the HGNC for official gene symbols.", href="https://www.genenames.org/", target="_blank")
                ],
                id=pgid("gene-help-toast"), header="Help on gene ratio input", icon="warning", is_open=False, duration=20000, dismissable=True, style={"position": "static", "margin-bottom": "15px", "width": "auto"},
            ),
            dbc.Button("Next",  id=pgid("next1"), color="primary", n_clicks=0),
        ]
    ),
    className="mt-3",
)

INPUTS = dbc.Tabs(
    [
        dbc.Tab(ratio_tab, label="Gene of interest", tab_id="ratio-tab"),
        dbc.Tab(input_tab_select_dataset(pgid), label="Dataset for analysis", tab_id="dataset-tab"),
        dbc.Tab(input_survival_tab(pgid), label="Survival options", tab_id="survival-tab"),
    ],
    id=pgid("input-tabs"),
    active_tab="ratio-tab",
)

REVIEW = dbc.Card(
    dbc.CardBody([
        html.H5("Review selected options", style={"margin-top": "15px"}),
        review_card_content(pgid, "gene_ratio"),
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

open_help(pgid("gene-help-toast"),pgid("gene-help"))
open_help(pgid("group-help-toast"),pgid("group-help"))

clientside_callback(
    """function(next1, next2, valid1, valid2) {
        if (!(valid1&&valid2)) { return "ratio-tab"; }
        else if ((valid1&&valid2) && next2 == 0) { return "dataset-tab"; }
        else {return "survival-tab";}
    }""",
    Output(pgid("input-tabs"), "active_tab"),
    Input(pgid("next1"), "n_clicks"),
    Input(pgid("next2"), "n_clicks"),
    State(pgid("gene_A"), "valid"),
    State(pgid("gene_B"), "valid"),
    prevent_initial_call=True
)

ds_survival_callbacks(pgid)

@callback(
    Output(pgid("btn-analyze"), "disabled"),
    Input(pgid("gene_A"), "valid"),
    Input(pgid("gene_B"), "valid"),
    Input(pgid("dataset-datatable"), "selected_row_ids")
)
def analyze_disabled(valid1, valid2, datasets):
    return (not (valid1 and valid2)) or (len(datasets)<=0)



@callback(
    Output(pgid("gene_A"), "valid"),
    Output(pgid("gene_A"), "invalid"),
    Input(pgid("gene_A"), "value"),
    prevent_initial_call= True
)
def validate_gene_input(symbol_in):
    if symbol_in == "":
        return False, False
    elif symbol_in not in GENE_SYMBOLS:
        return False, True
    else :
        return True, False

@callback(
    Output(pgid("gene_B"), "valid"),
    Output(pgid("gene_B"), "invalid"),
    Input(pgid("gene_B"), "value"),
    State(pgid("gene_A"), "value"),
    prevent_initial_call= True
)
def validate_gene_input(symbol_in, ga):
    if symbol_in == "":
        return False, False
    elif (symbol_in not in GENE_SYMBOLS) or (ga == symbol_in):
        return False, True
    else :
        return True, False


@callback(
        Output(pgid("genes-review"), "children"),
        Input(pgid("gene_A"), "value"),
        Input(pgid("gene_B"), "value")
    )
def review_gene_input(ga,gb):
    if not ga and not gb:
        return "Please provide genes of interest!"
    if ga == gb:
        return "Please provide two different genes!"
    return f"log({ga}/{gb})"


@callback(
        Output(pgid("gene_A"), "value"),
        Output(pgid("gene_B"), "value"),
        Input(pgid("swith-genes"), "n_clicks"),
        State(pgid("gene_A"), "value"),
        State(pgid("gene_B"), "value"),
)
def switch_genes(nclicks, ga, gb):
    if nclicks:
        return gb, ga
    return no_update,no_update

@app.long_callback(
    [Output("storesession","data",allow_duplicate=True),
     Output(pgid("loading-res"), "children"),
     Output(pgid('error-msg'), 'displayed'),
     Output(pgid('error-msg'), 'message'),],
    [Input(pgid("btn-analyze"),"n_clicks")],
    [State(pgid("gene_A"), "value"),
     State(pgid("gene_B"), "value"),
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
def submit_analyze(nclicks, gene_a, gene_b, dataset, tumor_type, age_group, cutp, percentiles, outcomes, 
                   til_set, til_filter, session_id):
    if not nclicks:
        return no_update
    
    dataset = dataset if len(dataset)<6 else dataset[:5]

    ds_invalid, msg = ds_validation(dataset, tumor_type, til_set, til_filter)
    if ds_invalid:
        return no_update, no_update, ds_invalid, msg

    analyze_params = {
        "analyze_type":"gene_ratio",
        "gene_symbol":[gene_a,gene_b],
        "dataset":dataset,
        "tumor_type":tumor_type,
        "cutp_method": cutp,
        "percentiles": percentiles,
        "survival_type": outcomes,
        "case_age_group":age_group,
        "til_set": til_set,
        "til_fil": til_filter,
    }
    
    cmds = ["Rscript",os.path.join(SCRIPT_PATH, "ratio_analysis.R"),
            "--session_id",session_id,
            "-A",analyze_params["analyze_type"],
            "--genes",' '.join([gene_a,gene_b]),
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
        return analyze_params , dcc.Location(pathname=URL_BASE+"/result_visualization/"+analyze_params["analyze_type"], id=""), False, no_update
    else:
        add_or_update_record(session_id, analyze_params["analyze_type"], 2)
        r_errors = re.findall(r'^\[IT\d{3}\].*\n', res_err, flags=re.MULTILINE)
        r_errors = ["Following Errors Occured:\n"] + r_errors + ["Please try other parameters or reach out to our team with the Analysis ID, input and error codes."]
        app.logger.warning(f"{session_id} error msg:\n{res_err}")
        return dict(), no_update, True, ''.join(r_errors)



# def validate_input():
#     pass