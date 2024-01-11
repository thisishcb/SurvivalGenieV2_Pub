import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html, callback, Input, Output, no_update, State, clientside_callback, Patch, dash_table
from dash_daq import BooleanSwitch
from dash_iconify import DashIconify

from sqlalchemy import func

# import pandas as pd
import re
# from time import sleep
import os
import pandas as pd
import base64
import io

from utils import CUTP_KEYS, SURVIVAL_TYPE_KEYS, TIL_SET_KEYS, BS_COLORS, GENE_SYMBOLS, TUMOR_TYPE_KEYS,PROJ_META, PROJECTS, DISEASES, PRIM_SITES, DISEASE_2_PROJ, SITE_2_PROJ, DS_VALIDATION, id_factory, LNC_SYMBOLS, CASE_AGE_GROUP_KEYS
from pages.shared_components import open_help, review_card_content
from server import task_tb, db
from configs import TMP_OUTPUT_PATH
## = ==========
def ds_validation(datasets, tumor_type, til_set, til_filter):
    # if available samples < 20 : not enough samples
    ## also need to count the number of samples with p < 0.05 
    for d in datasets:
        if not DS_VALIDATION[d][TUMOR_TYPE_KEYS[tumor_type].val]['FPKM']:
            # error: not enough samples
            return True, f"Dataset {d} does not contain enough samples for the analysis requested, please try with another dataset or tumor type"
        filt_key = "Filtered" if til_filter else "Total"
        if not DS_VALIDATION[d][TUMOR_TYPE_KEYS[tumor_type].val]['ICC'][TIL_SET_KEYS[til_set]][filt_key]:
            # error: not enough samples for feature set
            msg= f"Dataset {d} does not contain enough samples for the TIL signature set selected"
            msg += ' after filtering. ' if til_filter else '. '
            msg += "Please also try other datasets or parameters."
            return True, msg
    return False, None

def input_tab_select_dataset(id_factory):
    input_options = [{"value": f"pj_{i}", "label": d, "group": "Project"} for i,d in enumerate(PROJECTS) ] + \
        [{"value": f"dz_{i}", "label": d, "group": "Disease Type"} for i,d in enumerate(DISEASES) ] + \
        [{"value": f"st_{i}", "label": d, "group": "Primary Site"} for i,d in enumerate(PRIM_SITES) ]
    default_vals = ["pj_{}".format(PROJECTS.index("TCGA-LGG")),
                    "dz_{}".format(DISEASES.index("Gliomas")),
                    "st_{}".format(PRIM_SITES.index("Brain"))]
    dataset_tab = dbc.Card(
        dbc.CardBody([
            dbc.Row([
                html.P([
                    "Please select the datasets to be used for analysis. (Maximum: 5 datasets)",
                    html.Br(),
                    html.Small(["For more information about datasets, please visit ",
                    dcc.Link("GDC Data Portal.", href='https://portal.gdc.cancer.gov/projects')])], 
                    className="card-text"),
                dmc.MultiSelect(
                            label="Select Projects of Interest (By Project Name / Primary Tissue / Disease Type)",
                            placeholder="Use the dropdown menu to select options.",
                            id=id_factory("dataset-search-box"),
                            value = default_vals,
                            searchable=True,
                            data=input_options,
                            style={"width": "auto", "marginBottom": 15},
                        )
                ],),
            dbc.Row(
                dash_table.DataTable(
                    data=[],
                    columns=[
                        {'name': 'Project', 'id': 'Project'},
                        {'name': 'Disease Type(s)', 'id': 'Disease'},
                        {'name': 'Primary Site(s)', 'id': 'Prim_Site'},
                    ],
                    style_data={
                        'whiteSpace': 'normal',
                        'height': 'auto',
                    },
                    style_cell = {
                        'font_family': 'sans-serif',
                        'maxHeight': "31px",
                        'font_size': '15px',
                        'text_align': 'left'
                    },
                    style_data_conditional=[                
                        {
                            "if": {"state": "selected"},  # 'active' | 'selected'
                            "backgroundColor": "rgba(0, 116, 217, 0.3)",
                            "border": "1px solid blue",
                        },
                    ],
                    page_size=10,
                    row_selectable="multi",
                    sort_action="native",
                    filter_action="native",
                    selected_row_ids=[],
                    id=id_factory("dataset-datatable")
                )
            ), # Dash table
            html.Br(),
            html.H6("Selected Datasets:"),
            html.Div(id=id_factory("selected-ds")),
            html.Br(),
            dbc.Row([
                dbc.Col([
                    html.H6("Selected Tumor Type:"),
                    html.Div(
                        dbc.RadioItems(
                            id=id_factory("tumor-type"),
                            className="btn-group", # btn-group
                            # inline=True,
                            inputClassName="btn-check",
                            labelCheckedClassName="active",
                            labelClassName="btn btn-outline-primary btn-sm",
                            options=[
                                {"label": "Primary", "value": 1},
                                {"label": "Recurrent", "value": 2},
                                {"label": "Metastatic", "value": 3},
                                ],
                            value=1,
                        ),
                    className="radio-group",
                    style={"overflow-x":"auto"}
                    ),
                ]),
                dbc.Col([
                    html.H6("Case Group Filter:"),
                    html.Div(
                        dbc.RadioItems(
                            id=id_factory("age-group"),
                            className="btn-group", # btn-group
                            # inline=True,
                            inputClassName="btn-check",
                            labelCheckedClassName="active",
                            labelClassName="btn btn-outline-primary btn-sm",
                            options=[
                                {"label": "ALL", "value": "ALL"},
                                {"label": "Adult", "value": "ADULT"},
                                {"label": "Pediatric", "value": "PEDIATRIC"},
                                ],
                            value="ALL",
                        ),
                    className="radio-group",
                    style={"overflow-x":"auto"}
                    ),
                ]),
            ]),
            html.Br(),
            dbc.Button("Next",  id=id_factory("next2"), color="primary", n_clicks=0),
        ]),
        className="mt-3",
    )

    @callback(
        Output(id_factory("dataset-datatable"), "selected_cells"),
        Output(id_factory("dataset-datatable"), "selected_rows"),
        Output(id_factory("dataset-datatable"), "active_cell"),
        Output(id_factory("dataset-datatable"), "data"),
        Output(id_factory("dataset-datatable"), "selected_row_ids"),
        Input(id_factory("dataset-search-box"), "value"),
        State(id_factory("dataset-datatable"), "selected_row_ids"),
        prevent_intial_call=True
    )
    def update_dashtb(inputs,sel_ids):
        potential_datasets  = set()
        for dt in inputs:
            if dt[:2] == 'pj': # Project
                potential_datasets.add(PROJECTS[int(dt[3:])])
            elif dt[:2] == 'dz': # disease type
                potential_datasets.update(DISEASE_2_PROJ[DISEASES[int(dt[3:])]])
            elif dt[:2] == 'st': # primary site
                potential_datasets.update(SITE_2_PROJ[PRIM_SITES[int(dt[3:])]])
        sel_ids = list(set(sel_ids) & potential_datasets)
        potential_datasets = tuple(potential_datasets)
        sel_rows = [potential_datasets.index(i) for i in sel_ids]
        data = [
            {"id":p,"Project":p,
             "Disease":' | '.join(PROJ_META[p]["disease_type"]),
             "Prim_Site":' | '.join(PROJ_META[p]["primary_site"])}
             for p in potential_datasets]
        return [],sel_rows,None,data, sel_ids

    return dataset_tab

def input_survival_tab(pgid):
    """
    Survival tab, inputs: cutpoint methods; overall/event-free; LM6/22; filt with pval
    """
    surv_tab =  dbc.Card(
        dbc.CardBody(
            [
            html.Div([ ## cut point method
                html.P("Please select options for survival analysis.", className="card-text"),
                html.H6("Cut point determination method"),
                html.P(["Select the statistical method for partitioning the selected cohort into high and low gene expression groups. ", html.B("Optimal Cut Point is significally slower than other methods.")], className="card-text", style={"color":"gray", "font-size":"0.9rem"}),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                    dbc.RadioItems(
                                        id=pgid("cutp"),
                                        className="btn-group", # btn-group
                                        # inline=True,
                                        inputClassName="btn-check",
                                        labelCheckedClassName="active",
                                        labelClassName="btn btn-outline-primary",
                                        options=[
                                            {"label": "Optimal cut point", "value": 1},
                                            {"label": "Median", "value": 2},
                                            {"label": "Percentile", "value": 3},
                                            {"label": "Mean", "value": 4},
                                            ],
                                        value=4,
                                    ),
                            className="radio-group",
                            style={"overflow-x":"auto"}
                            ),
                            width="auto",
                        ),
                        dbc.Col(
                            [
                                dmc.Button(
                                    "Help",
                                    id=pgid("group-help"),
                                    leftIcon=[DashIconify(icon="ep:question-filled", width=20, height=20, inline=True, color="#9ebdf2")],
                                    variant="subtle",
                                    n_clicks=0,
                                    size="sm",
                                    radius="xl", 
                                    compact=True
                                ),
                            ],
                        width="auto",
                        ),
                    ],
                justify="left", 
                align="center",
                style={"margin-bottom": "15px"},
                ),
                dbc.Row(
                    dbc.Toast(
                                    [
                                        "Optimal cut point determination is a outcome-oriented method (log-rank test) for dichotomizing a continuous covariate (i.e. gene expression) using cutp from the survMisc R package. Generally this appraoch is expected to produce improved statisical prediction compared to commonly used data-oriented methods, such as median and percentile. For median cut point determination, the median expresison of the gene of interest to partition into high (above median) and low (below median) groups. This same approach is applied for mean cut points. For percertile cut points, a percentile is selected (e.g. 75th percentile) as a threshold to define the high expression group, while the remaining cohort is defined as the low expression group.",
                                        html.A("Please refer to Mandrekar et. al. for additional details.", href="https://support.sas.com/resources/papers/proceedings/proceedings/sugi28/261-28.pdf", target="_blank")
                                    ],
                                    id=pgid("group-help-toast"), header="Help on cut point determination", icon="primary", is_open=False, duration=20000, dismissable=True, style={"position": "static", "margin-bottom": "15px", "width": "auto"},
                                ),
                    justify="left", 
                ),
                dbc.Row(
                    html.Div(dcc.RangeSlider(
                        id=pgid('percentile-slider'),
                        min=0, max=100, step=0.1, value=[50,50], 
                        marks={i: f"{str(i)}%" for i in range(0,101,20)},
                        className="rev-slider my-2", 
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    id=pgid("percentile-slider-div"),
                    style={"width":"420px","overflow-x":"auto","display":"none"}),
                ),
                html.Hr()]),
            html.Div([ ## overall/event free
                html.H6("Outcome selection"),
                html.P("Select whether survival analysis should be based on overall survival (OS) or event free survival (EFS); EFS only supports TARGET datasets currently!", className="card-text", style={"color":"gray", "font-size":"0.9rem"}),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                    dbc.RadioItems(
                                        id=pgid("outcomes"),
                                        className="btn-group btn-group-md",
                                        inputClassName="btn-check",
                                        labelCheckedClassName="active",
                                        labelClassName="btn btn-outline-primary",
                                        options=[
                                            {"label": "Overall", "value": 1},
                                            {"label": "Event-Free", "value": 2, 'disabled': False},
                                            ],
                                        value=1
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
                html.Hr()]),
            html.Div([ ## LM6/22
                html.H6("TIL signature set selection"),
                html.P("Select which signature set would be used to compute the correlation with survival information.", style={"color":"gray", "font-size":"0.9rem"}),
                dbc.Row(
                    [
                        dbc.Col(
                            html.Div(
                                    dbc.RadioItems(
                                        id=pgid("sg-til-set"),
                                        className="btn-group btn-group-md",
                                        inputClassName="btn-check",
                                        labelCheckedClassName="active",
                                        labelClassName="btn btn-outline-primary",
                                        options=[
                                            {"label": "LM22", "value": 22},
                                            {"label": "LM6", "value": 6},
                                            ],
                                        value=22
                                    ),
                            className="radio-group",
                            ),
                        width="auto",
                        ),
                        dbc.Col(html.Table(
                            html.Tr([
                                html.Td(
                                    BooleanSwitch(id=pgid("btn-lm-filter"), color=BS_COLORS["primary"], on=True, labelPosition=None,className="my-auto")
                                        ),
                                html.Td(
                                    html.P("Apply filter of p<0.05 for samples in the dataset.",
                                        style={"color":"gray", "font-size":"0.9rem"},
                                        className="my-auto")
                                        )
                                ],
                                style={'vertical-align': 'middle'},
                                ),),
                        align="center",width="auto")
                    ],
                    justify="start", 
                    align="center",
                    style={"margin-bottom": "15px"},
                )]),
            # html.Div([ ## lnc/ligand receptor pair
            #     html.H6("Context gene selection"),
            #     html.P("Select the context expression matrix to be used", className="card-text", style={"color":"gray", "font-size":"0.9rem"}),
            #     dbc.Row(
            #         [
            #             dbc.Col(
            #                 html.Div(
            #                         dbc.RadioItems(
            #                             id=pgid("outcomes"),
            #                             className="btn-group btn-group-md",
            #                             inputClassName="btn-check",
            #                             labelCheckedClassName="active",
            #                             labelClassName="btn btn-outline-primary",
            #                             options=[
            #                                 {"label": "Overall", "value": 1},
            #                                 {"label": "Event-Free", "value": 2, 'disabled': False},
            #                                 ],
            #                             value=1
            #                         ),
            #                 className="radio-group",
            #                 ),
            #             width="auto",
            #             ),
            #         ],
            #     justify="left", 
            #     align="center",
            #     style={"margin-bottom": "15px"},
            #     ),
            #     html.Hr()]),
                dbc.Row(
                    dbc.Col(
                        dbc.Button("Review",  id=pgid("btn-review"), color="warning", n_clicks=0),
                        width="auto",
                    ),
                    justify="end", 
                ),
            ],
        ),
        className="mt-3",
    )


    return surv_tab

def input_pagecard(pgid, input_contents, review_contents):
    SG_INPUT = dbc.Card(
        dbc.CardBody([
            html.H5("Select analysis options.", className="card-title", style={"text-align": "left"}),
            html.Hr(),
            dcc.ConfirmDialog(
                id=pgid('error-msg'),
                message='Something went wrong! Please double check your input or contact our teams.',
            ),
            input_contents,
            html.Div(
                [html.Br(),
                review_contents,
                dcc.Loading(
                        id=pgid("loading-res"),
                        type="default",
                        fullscreen=True,
                        children=[]
                    ),
                ],
                style={'display': 'none'},
                id=pgid("div-review")
            )

        ],id=pgid("input-block"))# , style={"width": "80vw"},
    )
    return SG_INPUT

def ds_survival_callbacks(pgid,max_dataset: int = 5):

    # @callback(
    #         Output(pgid("percentile-slider-div"),"style"),
    #         Input(pgid("cutp"), "value"),
    #         prevent_initial_call = True
    # )
    # def showslider(cutp):
    #     patched_style = Patch()
    #     patched_style["display"] = "block" if cutp == 3 else "none"
    #     return patched_style
    showslider = clientside_callback(
        """
        function(cutp, currentStyle) {
            var patchedStyle = { ...currentStyle };  // Copy the current style object
            patchedStyle['display'] = cutp === 3 ? 'block' : 'none';
            return patchedStyle;
        }
        """,
        Output(pgid("percentile-slider-div"),"style"),
        Input(pgid("cutp"), 'value'),
        State(pgid("percentile-slider-div"),"style"),
    )

    @callback(
        Output(pgid("cutp-review"), "children"),
        Output(pgid("outcome-review"), "children"),
        Output(pgid("til-review"), "children"),
        Input(pgid("cutp"), "value"),
        Input(pgid("percentile-slider"),"value"),
        Input(pgid("outcomes"), "value"),
        Input(pgid("sg-til-set"), "value"),
        Input(pgid("btn-lm-filter"),"on"),
    )
    def review_cutp_n_other_stats( cutp_in, percentiles, outcomes_in, tilset, tilfilter):
        cutp_out = CUTP_KEYS[cutp_in]["verbose"]
        if cutp_in == 3:
            cutp_out = f"{cutp_out} [0%-{min(percentiles)}%, {max(percentiles)}%-100%]"

        outcomes_out = SURVIVAL_TYPE_KEYS[outcomes_in]["verbose"]
            ## Event-Free survival is only available for TARGET datasets
            ## Implemented in the dataset section
        
        tilset_out = TIL_SET_KEYS[tilset]
        if tilfilter:
            tilset_out = f"{tilset_out} (only with samples p<0.05)"
        else: 
            tilset_out = f"{tilset_out} (all samples)"
        
        return cutp_out, outcomes_out, tilset_out, 

    @callback(
        Output(pgid("dataset-review"), "children"), # review card
        Output(pgid("selected-ds"), "children"), # tab capsule view 
        Output(pgid("outcomes"),"options"), # disable enet-free when non TARGET
        Output(pgid("outcomes"),"value"), # force overall when non TARGET
        Input(pgid("dataset-datatable"), "selected_row_ids"),
        Input(pgid("tumor-type"), "value"),
        Input(pgid("age-group"), "value"),
        prevent_initial_call= True
    )
    def review_datasets(datasets_in, tumor_type, age_group):
        if len(datasets_in)==0:
            return "Please select datasets of interest.", [dbc.Badge("Haven't selected yet",color="white", text_color="muted", className="border me-1",)], no_update, no_update

        msgs = []
        if len(datasets_in)>max_dataset:
                msgs.extend([dbc.Badge(f"Over {max_dataset} datasets are selected! Only the following {max_dataset} dataset(s) will be processed.", color="danger", className="me-1"), html.Br()])
                datasets_in = datasets_in[:max_dataset]
        datasets_out = ", ".join(datasets_in)
        msgs.extend([dbc.Badge(p, text_color="dark", color="light", 
                            className="me-1") for p in datasets_in])

        datasets_out = "[{}-{}] ".format(TUMOR_TYPE_KEYS[tumor_type].verbose, CASE_AGE_GROUP_KEYS[age_group].verbose) + datasets_out

        options = Patch()
        if all([ids.startswith("TARGET-") for ids in datasets_in]):
                options[1]["disabled"] = False
                return datasets_out, msgs, options, no_update
        options[1]["disabled"] = True
        
        return  datasets_out, msgs, options, 1

    reviewOptions = clientside_callback(
        """function reviewOptions(nclicks) {
            if (nclicks % 2 !== 0) {
                return { 'display': 'block' };
            } else {
                return { 'display': 'none' };
            }
        }""", # "display: 'none'"
        Output(pgid("div-review"), "style"),
        Input(pgid("btn-review"), "n_clicks"),
        prevent_initial_call=True
    )

    return reviewOptions, showslider

def parse_file_N_save(file_contents, new_fname, analysis_type):
    content_type, content_string = file_contents.split(',')
    # print(content_type)
    content_decoded = base64.b64decode(content_string)
    df = None
    if 'csv' in content_type:
        df = pd.read_csv(
            io.StringIO(content_decoded.decode('utf-8')))
    elif 'xls' in content_type:
        # Assume that the user uploaded an excel file
        df = pd.read_excel(io.BytesIO(content_decoded))
    elif 'txt' in content_type or "text" in content_type:
        delim_tab = content_decoded.decode('utf-8').count('\t')
        delim_com = content_decoded.decode('utf-8').count(',')
        delim = '\t' if delim_tab > delim_com else ','
        df = pd.read_csv(
            io.StringIO(content_decoded.decode('utf-8')), delimiter=delim)
    if not df is None:
        req_cols = ["cluster", "gene", "p_val_adj"] if analysis_type == "cluster_marker" else ["gene_name","module"]
        missing_cols = [i for i in req_cols if i not in df.columns]
        if len(missing_cols)>0:
            return "Required column(s) {} are not in the dataset".format(', '.join(missing_cols))
        df.to_csv(new_fname,index=False)
        return ''
    return "Invalid Input File: cannot be parsed"

def parse_geneset(gs_str):
    for delimiter in [',', '\n', ' ', '\t']:
        gs_str = "\t".join(gs_str.split(delimiter))
    res = gs_str.split('\t')
    res = [i for i in res if i]
    return res

def auto_remove():
    onedayago = func.datetime('now','-24 hours') # this line would be db specific
    oldfinished = db.session.query(task_tb).filter(task_tb.status==0,
                                                task_tb.update_time < onedayago )
    for task in oldfinished:
        tmpfiles = [filename for filename in os.listdir(TMP_OUTPUT_PATH) if filename.startswith(task.ssid)]
        for file in tmpfiles:
            try:
                os.remove(file)
            except OSError as e:
                dash.get_app().logger.warning(f"Error: Cannot Remove File {file}:\n{e.stderr}")
        task.status=3
    db.session.commit()


def add_or_update_record(ssid, analysis_type=None, status=1):
    """status 0 for DONE; 1 for still in process; 2 for failed; 3: expired; 4: Protected"""
    task_obj = db.session.get(task_tb, ssid)
    if not task_obj and status==1:
        if not analysis_type:
             return "required analysis type is missing"
        task_obj = task_tb(ssid, analysis_type, status)
        db.session.add(task_obj)
        db.session.commit()
        auto_remove()
    else:
        if not task_obj:
            return f"{ssid} Does Not Exist! try to change status to {task_obj.status_keys[status]}!"
        if task_obj.status == 4:
            return "Trying to modify a protected task. Please start a new window with a new Analysis ID"
        task_obj.analysis_type = analysis_type
        task_obj.status = status
    db.session.commit()


def check_lncRNA(input_genes):
    pass

def check_TFs(input_genes):
    pass
