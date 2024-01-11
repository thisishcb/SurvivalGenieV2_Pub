import base64
from urllib.parse import urlparse
import re
# from time import sleep
import subprocess
import os
import logging
import json

import pandas as pd

import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from dash import dcc, html, callback, Input, Output, no_update, State, clientside_callback, Patch

from configs import URL_BASE, TMP_OUTPUT_PATH, SCRIPT_PATH
from utils import CUTP_KEYS, SURVIVAL_TYPE_KEYS, TIL_SET_KEYS, BS_COLORS, GENE_SYMBOLS, TUMOR_TYPE_KEYS, id_factory, GENE_FILTER_KEYS
from pages.shared_components import open_help, review_card_content
from .input_common import ds_validation, input_tab_select_dataset, input_survival_tab, input_pagecard, ds_survival_callbacks, parse_file_N_save, add_or_update_record
# from scripts.utils import user_info_validation
## =================================================
##      page of single gene analysis param input
## =================================================

# --- Register page --- #ß
dash.register_page( 
    __name__,
    top_nav=True,
    path='/cluster-marker/input',
    title='SurvivalGenie2.0 Cluster Marker Analysis Options', 
    location="navbar"
)

pgid = id_factory("sc-cluster-in")
app = dash.get_app()
# --- Components --- #

example_data_table = [html.Thead(html.Tr([html.Th(""), html.Th("p_val_adj"), html.Th("cluster"), html.Th("gene"), html.Th("avg_logFC"), html.Th("...")])),
              html.Tbody([
                  html.Tr([html.Td("IL32"), html.Td("0"), html.Td("T cells"), html.Td("IL32"), html.Td("1.689023137"), html.Td("...")]),
                  html.Tr([html.Td("CD3E"), html.Td("0"), html.Td("T cells"), html.Td("CD3E"), html.Td("1.596225859"), html.Td("...")]),
                  html.Tr([html.Td("......",colSpan=6,)],style = {'text-align': 'center'}),
                  html.Tr([html.Td("UBB"), html.Td("1.46E-06"), html.Td("T cells"), html.Td("UBB"), html.Td("-0.480071137"), html.Td("...")]),
                  html.Tr([html.Td("S100A8.1"), html.Td("0"), html.Td("Mono/mac"), html.Td("S100A8"), html.Td("3.575487695"), html.Td("...")]),
                  html.Tr([html.Td("......",colSpan=6)],style = {'text-align': 'center'}),
              ])]


file_tab = dbc.Card(
    dbc.CardBody(
        [
            html.P(["Please Select/Upload the cluster marker file of interest.",
                    html.Br(),
                    html.Small(["A cluster marker file will be required for this analysis. The GeneSet Variation ", html.A("(GSVA) ", href="https://doi.org/10.1186/1471-2105-14-7", target="_blank"), "Score (Enrichment Score, ES) of markers will be calculated per cluster and will be used to survival analysis. For this analysis, only one dataset will be used. ", html.B("More clusters and more markers will take longer running time. "),"Full example data see ", html.A("example_markers.csv",href="https://bhasinlab.bmi.emory.edu/scwizard/scw_out/1623434401_heart0609.top10.markers.csv")])
                    ], className="card-text"),
            
            html.Br(),
            dbc.Col([
                dmc.Group([
                    html.Div(
                            dbc.RadioItems(
                                id=pgid("input-type"),
                                className="btn-group", # btn-group
                                # inline=True,
                                inputClassName="btn-check",
                                labelCheckedClassName="active",
                                labelClassName="btn btn-outline-primary",
                                options=[
                                    {"label": "Use Example Marker File", "value": 'example_data'},
                                    {"label": "Upload My Own Marker File", "value": 'user_upload'},
                                    {"label": "Upload through URL", "value": 'URL'},
                                    ],
                                value="example_data",
                            ),
                    className="radio-group",
                    style={"overflow-x":"auto"}
                    ),
                    dmc.ActionIcon(DashIconify(icon="ep:question-filled", width=30,height=30, color="secondary"),  id=pgid("sc-cluster-help"), n_clicks=0),
                    ],
                    
                #     className="input-group mb-3",
                #     style={"margin-bottom": "15px", "overflow-x":"auto"},
                ),
                html.Br(),
                dbc.Table(
                    example_data_table, 
                    id=pgid("example-df"),
                    style={"display":"block"},
                    bordered=True,
                    hover=True,
                    responsive=True,
                    striped=True,
                ),
                dcc.Upload(
                    id=pgid('user-uploader'),
                    className='pty-uploader mb-3',
                    children=dmc.Stack( className='pty-contents',
                        children=[
                            html.A(DashIconify(icon="ph:upload-duotone",width=60,height=60),className='fas fa-upload fa-fw fa-3x upload-icon'),
                            dmc.Text('Drag and drop files here to upload.', className='upload-text'),
                            dmc.Button(
                                "Select File",
                                className='upload-button',
                                color="primary",
                                radius='lg',
                            )
                        ], id=pgid("uploadbox"), align='center', spacing='md'),
                    style={"display":"none"}                
                ),
                dmc.TextInput(
                    id = pgid("user-url"),
                    label="Provide a link to the marker file",
                    style={"display":"none"},
                    placeholder="Link to a marker file",
                    icon=DashIconify(icon="tabler:link"),
                ),
                    
            ]),
            html.Br(),
            dbc.Toast(
                [
                    "Please provide the file of the marker genes, the gene names should be valid gene symbols. ", html.A("Please refer to the HGNC for official gene symbols. ", href="https://www.genenames.org/", target="_blank"), "The file should be in the format of .csv or .tsv or comma/tab separated .txt table file. Required columns are: " ,html.B("cluster")," for clusters; ", html.B("gene"), " for HGNC gene symbols, and ", html.B("p_val_adj"), " for adjusted p-value or FDR (filter of <0.05 will be applied). Example is shown under the \"Use Example Marker File\" tab."
                ],
                id=pgid("sc-cluster-help-toast"), header="Help on single gene input", icon="warning", is_open=False, duration=20000, dismissable=True, style={"position": "static", "margin-bottom": "15px", "width": "auto"},
            ),
            html.Div([ ## lnc/ligand receptor pair
                html.H6("Gene Filter"),
                html.P(["Select which genes will be used for the analysis. \"All\" by Default. Other available options are only long non-coding RNAs (Only lncRNAs), only ",html.A("Transcroptional factors",href="https://github.com/aertslab/pySCENIC/tree/master")," (Only TFs), and ",html.A("Ligand-Receptors",href="https://github.com/sqjin/CellChat")," (Only LRs). The input genes will be filtered when the analysis starts, genes not in the category will be removed for the analysis. Clusters which have no marker genes pass the filtering will be removed in the result."], className="card-text", style={"color":"gray", "font-size":"0.9rem"}),
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
        dbc.Tab(file_tab, label="Gene of interest", tab_id="file-tab"),
        dbc.Tab(input_tab_select_dataset(pgid), label="Dataset for analysis", tab_id="dataset-tab"),
        dbc.Tab(input_survival_tab(pgid), label="Survival options", tab_id="survival-tab"),
    ],
    id=pgid("input-tabs"),
    active_tab="file-tab",
)

REVIEW = dbc.Card(
    dbc.CardBody([
        html.H5("Review selected options", style={"margin-top": "15px"}),
        review_card_content(pgid, "cluser_marker"),
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

open_help(pgid("sc-cluster-help-toast"),pgid("sc-cluster-help"))
open_help(pgid("group-help-toast"),pgid("group-help"))

clientside_callback(
    """function(next1, next2, fname, url_valid, usr_input) {
        let res = false;
        if (usr_input === "example_data") {
            res = true; 
        } else if (usr_input === "URL") {
            res = url_valid; 
        } else {
            res = Boolean(fname);
        }
        if (!res) { return "file-tab"; }
        else if (res && next2 == 0) { return "dataset-tab"; }
        else {return "survival-tab";}
    }""",
    Output(pgid("input-tabs"), "active_tab"),
    Input(pgid("next1"), "n_clicks"),
    Input(pgid("next2"), "n_clicks"),
    State(pgid('user-uploader'),"filename"),
    State(pgid('user-url'),"valid"),
    State(pgid("input-type"), "value"),
    prevent_initial_call=True
)


clientside_callback(
    """
    function(inputType) {
        var uploadStyle = {'display': inputType === 'user_upload' ? 'block' : 'none'};
        var urlStyle = {'display': inputType === 'URL' ? 'block' : 'none'};
        var exmpStyle = {'display': inputType === 'example_data' ? 'block' : 'none'};
        return [uploadStyle, urlStyle, exmpStyle];
    }
    """,
    [Output(pgid('user-uploader'),"style"),
    Output(pgid('user-url'),"style"),
    Output(pgid("example-df"), "style")],
    Input(pgid("input-type"), "value"),
    prevent_initial_call = True
)


ds_survival_callbacks(pgid,max_dataset=1)

@callback(
    Output(pgid("uploadbox"), "children"),
    Input(pgid('user-uploader'),"filename"),
)
def show_uploaded_fname(fname):
    box_content=Patch()
    if fname:
        box_content[0] = html.A(DashIconify(icon="mdi:file-table-outline",width=60,height=60),className='fas fa-upload fa-fw fa-3x upload-icon')
        box_content[1] = dmc.Text(fname, className='upload-text')
    else:
        box_content[0] = html.A(DashIconify(icon="ph:upload-duotone",width=60,height=60),className='fas fa-upload fa-fw fa-3x upload-icon')
        box_content[1] = dmc.Text('Drag and drop files here to upload.', className='upload-text')
    return box_content

@callback(
    Output(pgid("btn-analyze"), "disabled"),
    Output(pgid('user-url'),"valid"),
    Output(pgid('user-url'),"invalid"),
    Output(pgid("genes-review"), "children"),
    [Input(pgid('user-uploader'),"filename"),
    Input(pgid('user-url'),"value"),
    Input(pgid("input-type"), "value"),
    Input(pgid("dataset-datatable"), "selected_row_ids"),
    Input(pgid("gene-filter"), "value")],
)
def analyze_disabled(upload_fname, url, input_type, datasets, gene_filter):
    if input_type == "example_data":
        return (len(datasets)<=0), no_update, no_update, "Cluster Markers in Example Data. [{}]".format(GENE_FILTER_KEYS[gene_filter].verbose) 
    elif input_type == "URL": 
        if not url:
            return True, False, False, "Provide an URL to the marker file " 
        result = urlparse(url)
        url_valid = result.scheme and result.netloc
        return (not url_valid) or (len(datasets)<=0), \
            url_valid, not url_valid, f"Cluster Markers from {url}. [{GENE_FILTER_KEYS[gene_filter].verbose}]"
    else:
        msg = f"Cluster Markers from {upload_fname}. [{GENE_FILTER_KEYS[gene_filter].verbose}]" if upload_fname else "Please Upload Your Cluster Marker File"
        return (not upload_fname) or (len(datasets)<=0),\
            no_update, no_update, msg

@app.long_callback(
    [Output("storesession","data",allow_duplicate=True),
     Output(pgid("loading-res"), "children"),
     Output(pgid('error-msg'), 'displayed'),
     Output(pgid('error-msg'), 'message'),],
    [Input(pgid("btn-analyze"),"n_clicks")],
    [State(pgid('user-uploader'),"contents"),
     State(pgid('user-uploader'),"filename"),
     State(pgid('user-url'),"value"),
     State(pgid("input-type"), "value"),
     State(pgid("gene-filter"), "value"),
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
def submit_analyze(nclicks, file_content, ori_fname, url, input_type, gene_filter, dataset, tumor_type, age_group, cutp, percentiles, outcomes, 
                   til_set, til_filter, session_id):
    if not nclicks:
        return no_update
    
    dataset = dataset if len(dataset)<2 else dataset[:1]

    ds_invalid, msg = ds_validation(dataset, tumor_type, til_set, til_filter)
    if ds_invalid:
        return no_update, no_update, ds_invalid, msg
    
    ## parse file content
    # return the new file name
    
    # print(content_type)
    if input_type == "user_upload":
        try:
            new_fname = os.path.join(TMP_OUTPUT_PATH, f"{session_id}_scrna_cluster_markers.csv")
            msg = parse_file_N_save(file_content, new_fname, "cluster_marker")
            if msg:
                return no_update, no_update, True, msg
        except:
            return no_update, no_update, True, "uploaded file format is invalid"

    analyze_params = {
        "analyze_type":"cluster_marker",
        "input_type":input_type,
        "url": url,
        "file_name":ori_fname, 
        "dataset":dataset,
        "tumor_type":tumor_type,
        "cutp_method": cutp,
        "percentiles": percentiles,
        "survival_type": outcomes,
        "case_age_group":age_group,
        "til_set": til_set,
        "til_fil": til_filter,
        "gene_filter": gene_filter
    }
    
    cmds = ["Rscript",os.path.join(SCRIPT_PATH, "scRNA_cluster_analysis.R"),
            "--session_id", session_id,
            "-A", analyze_params["analyze_type"],
            "--input_type", input_type,
            "--data_path", new_fname if input_type == "user_upload" else url,
            "--gene_filter", gene_filter,
            "--datasets", ' '.join(dataset),
            "--tumor_type", TUMOR_TYPE_KEYS[tumor_type].val,
            "-S", SURVIVAL_TYPE_KEYS[outcomes]["val"],
            "--group_method", CUTP_KEYS[cutp]["val"],
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
