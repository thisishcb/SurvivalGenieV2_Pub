import dash
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc
from dash import dcc, html, callback, Input, Output, no_update, State, clientside_callback, Patch, dash_table, MATCH, ALL, ctx
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
from collections import defaultdict 

from utils import CUTP_KEYS, SURVIVAL_TYPE_KEYS, TIL_SET_KEYS, BS_COLORS, GENE_SYMBOLS, TUMOR_TYPE_KEYS,PROJ_META, PROJECTS, DISEASES, PRIM_SITES, DISEASE_2_PROJ, SITE_2_PROJ, DS_VALIDATION, id_factory, LNC_SYMBOLS, CASE_AGE_GROUP_KEYS, DATASETS, ds2str
from pages.shared_components import open_help, review_card_content, ds_review
from server import task_tb, db
from configs import TMP_OUTPUT_PATH, URL_BASE
## = ==========
def ds_validation(datasets, til_set, til_filter):
    """
    if available samples < 20 : not enough samples
    also need to count the number of samples with p < 0.05 
    used to need to validate dataset & options, after updating dataset selction, they have to be valid, just give warning to til filters
    """
    bad_ds = []
    for ds in datasets:
        d=ds["dataset"]
        tumor_type = ds["tumor_type"] 
        surv_type = ds["surv_type"]
        # if not DS_VALIDATION[d][TUMOR_TYPE_KEYS[tumor_type].val][str(surv_type)]['FPKM']:
            # error: not enough samples
            # return True, f"Dataset {d} does not contain enough samples for the analysis requested, please try with another dataset or tumor type"
        filt_key = "filt_count" if til_filter else "count"

        if DATASETS[ds["project"]][d][str(surv_type)][tumor_type]['groups'][CASE_AGE_GROUP_KEYS[ds['age_grp']].val][TIL_SET_KEYS[til_set]][filt_key] < 20:
            bad_ds.append(ds2str(ds))
            # error: not enough samples for feature set
    if bad_ds:
        msg = f"Warning: Following dataset(s) do not contain enough (>20) samples for the {TIL_SET_KEYS[til_set]} signature set"
        msg += ' after applying p<0.05 filtering. Please remove the filtering :' if til_filter else '. '
        msg += "\n---OR--- \nIf you want to ignore this warning. Re-Submit the analysis again with dataset unchanged will bypass this warning and start the analysis."
        msg = [msg]
        msg.extend(bad_ds)
        return True, '\n'.join(msg)
    return False, None

def input_tab_select_dataset(id_factory, max_dataset: int = 5):
    input_options = [{"value": f"pj_{i}", "label": PROJ_META[d]["verbose"], "group": "Project"} for i,d in enumerate(PROJECTS) ] + \
        [{"value": f"dz_{i}", "label": d, "group": "Disease Type"} for i,d in enumerate(DISEASES) ] + \
        [{"value": f"st_{i}", "label": d, "group": "Primary Site"} for i,d in enumerate(PRIM_SITES) ]
    default_vals = ["dz_{}".format(DISEASES.index("Myeloid Leukemias")),]
    dataset_tab = dbc.Card(
        dbc.CardBody([
            dbc.Row([# General Intros 
                html.P([
                    f"Please select the datasets to be used for analysis. (Maximum: {max_dataset} dataset{'s' if max_dataset>1 else ''})",
                    html.Br(),
                    html.Small([
                        "Current all supported datasets are listed on ",
                        html.A("help page.",href=URL_BASE+"help", target="_blank"),
                        html.Br(),
                        "For more information about datasets, please visit ",
                        dcc.Link("GDC Data Portal.", href='https://portal.gdc.cancer.gov')
                        ])# , className="card-text"
                    ]),
                ]),
            # html.Br(),
            dbc.Row([ # data table shows datasets
                html.P([html.H6("Selected Dataset:"),html.Small("Only datasets with enough(>20) samples with the selected filters are shown.")]),
                dmc.MultiSelect(
                    label="Select Projects of Interest (By Project Name / Primary Tissue / Disease Type)",
                    placeholder="Type to search or use the dropdown menu to select options.",
                    id=id_factory("dataset-search-box"),
                    value = default_vals,
                    searchable=True,
                    data=input_options,
                    style={"width": "auto", "marginBottom": 15},
                ), 
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
                    style_cell_conditional=[
                        {'if': {'column_id': 'AddProj'}, 'width': '10px'}
                    ],
                    page_size=10,
                    row_selectable="single",
                    sort_action="native",
                    filter_action="native",
                    selected_row_ids=["TARGET-AML",],
                    id=id_factory("dataset-datatable")
                )
            ]), # Dash table
            html.Br(),
            dbc.Row([ # apply filters
                dbc.Col([ # select subset
                    # html.H6("Available Dataset(s):"),
                    dmc.Select(id=id_factory('ds-sub-sel'),
                               label = "Dataset(s):",
                               data=[{'label': 'N/A', 'value': 'N/A'}],
                               value='N/A')
                ], align="center"),
                dbc.Col([ ## overall/event free
                    dmc.Select(id=id_factory('outcomes'),
                        label = dmc.Group([
                            "Outcome Type(s)", 
                            dmc.Tooltip(
                                DashIconify(icon="ep:question-filled", width=15, height=15, color="#9ebdf2"), style={"display":"inline"},
                                label = "Select whether survival analysis should be based on overall survival (OS) or event free survival (EFS); EFS only supports TARGET/MP2PRT datasets currently!",
                                multiline=True, width = 220, transition=True, withArrow=True,color="grey")]),
                        data=[{'label': 'Overall Survival', 'value': '1'},
                            {'label': 'Event-Free Survival', 'value': '2'}],
                        value='1'),
                    # html.P("Select whether survival analysis should be based on overall survival (OS) or event free survival (EFS); EFS only supports TARGET datasets currently!", className="card-text", style={"color":"gray", "font-size":"0.9rem"}),
                ], align="center"),
                dbc.Col([ ## Tumor types primary/rec/met/...
                    dmc.Select(id=id_factory('tumor-type'),
                        label = dmc.Group([
                            "Tumor Type(s):",
                            dmc.Tooltip(
                                DashIconify(icon="ep:question-filled", width=15, height=15, color="#9ebdf2"), style={"display":"inline"},
                                label = "Select a Tumor Type to analyze. Usual types are Primary/Recurrent/Metastatic. \"Normal\" type are the samples labeled as Solid Tissue Normal or [tissue name] Normal in GDC which are usually normal tissues from patients. \"Others\" are either Tumors with type un-specified in dataset or will have a following note (e.g. post-treatment sample from patients). Only types with >20 samples are shown.",
                                multiline=True, width = 250, transition=True, withArrow=True,color="grey")]),
                        data=[{"label": TUMOR_TYPE_KEYS[key].verbose, "value": key} for key in TUMOR_TYPE_KEYS],
                        value='1'),
                ], align="center"),
                dbc.Col([ ## pediatric/adult
                    dmc.Select(id=id_factory('age-group'),
                        label = dmc.Group([
                            "Age Group Filter:",
                            dmc.Tooltip(
                                DashIconify(icon="ep:question-filled", width=15, height=15, color="#9ebdf2"), style={"display":"inline"},
                                label = "Select \"Adult\"/\"Pedicatric\"/\"All\" samples to apply analysis on. Patients with age-at-diagnosis >20 are considered \"Adults\" and <20 are considered \"Pediatric\". \"All Samples\" will include samples with unknown age-at-diagnosis. Only categories with >20 samples are shown.",
                                multiline=True, width = 250, transition=True, withArrow=True,color="grey")]),
                        data=[{"label": "ALL", "value": "ALL"},
                              {"label": "Adult", "value": "ADULT"},
                              {"label": "Pediatric", "value": "PEDIATRIC"},],
                        value="ALL",),
                ], align="center"),
                dbc.Col([ ## button add
                    dmc.Button("Add Dataset",  id=id_factory("add-ds"), color="primary", n_clicks=0),
                ], align="end")
            ]),
            html.Br(),
            html.H6("Selected Dataset(s):"),
            html.Div(
                dbc.Badge(
                    html.Tr([
                        html.Td(
                        dmc.ActionIcon(
                            DashIconify(
                                icon="bi:exclamation-triangle-fill",
                                width=15, height=15,color="white"),
                            variant="transparent"),
                            style= {"text-align": "left", "transform": "translateY(1px)" }),
                        html.Td("No Dataset is selected.")]),
                    color="warning", className="me-1",
                    id = id_factory("no-dataset-selected"),
                    style = {})
            ),
            html.Div(
                id=id_factory("selected-ds"),
                children = [
                    dbc.Badge(
                        html.Tr([
                            html.Td(
                            dmc.ActionIcon(
                                DashIconify(
                                    icon="bi:exclamation-triangle-fill",
                                    width=15, height=15,color="white"),
                                variant="transparent"),
                                style= {"text-align": "left", "transform": "translateY(1px)" }),
                            html.Td("Dataset Maximum Reached. Please remove existing datasets to add new ones.")]),
                        color="danger", className="me-1",
                        id = id_factory("max-dataset-warning"),
                        style = {"display":"none"})
                    ]
                ),
            html.Br(),

            dbc.Button("Next",  id=id_factory("next2"), color="primary", n_clicks=0),
            html.Div(id=id_factory("ds_dummy"), style={'display': 'none'}),
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
        if not potential_datasets:
            return no_update
        sel_ids = list(set(sel_ids) & potential_datasets)
        potential_datasets = tuple(potential_datasets)
        sel_rows = [potential_datasets.index(i) for i in sel_ids]
        if not sel_rows:
            sel_rows = [0]
            sel_ids = [potential_datasets[0]]
        data = [
            {"id":p,"Project":PROJ_META[p]["verbose"],#"AddProj":"➕",
             "Disease":' | '.join(PROJ_META[p]["disease_type"]),
             "Prim_Site":' | '.join(PROJ_META[p]["primary_site"])}
             for p in potential_datasets]
        return [],sel_rows,None,data, sel_ids
    
    @callback(
        Output(id_factory('ds-sub-sel'),"data"),
        Output(id_factory('ds-sub-sel'),"value"),
        Input(id_factory("dataset-datatable"), "selected_row_ids")
    )
    def update_ds(project):
        if not project:
            return [],None
        project = project[0]
        subsets = DATASETS[project].keys()
        options = [{"label":DATASETS[project][i]["verbose"], "value":i} for i in subsets]
        return options, options[0]["value"]
    
    @callback(
        Output(id_factory('outcomes'),"data"),
        Output(id_factory('outcomes'),"value"),
        Input(id_factory('ds-sub-sel'),"value"),
        State(id_factory("dataset-datatable"), "selected_row_ids"),
        State(id_factory('outcomes'),"value"),
    )
    def update_survtype_on_ds(ds, project, tp):
        if not project:
            return [],None
        project = project[0]
        survtypes_codes = [i for i in DATASETS[project][ds].keys() if i != "verbose"]
        survtypes = [{"label":SURVIVAL_TYPE_KEYS[i].verbose,"value":i} for i in survtypes_codes]
        survtypes_val = tp if tp in survtypes_codes else survtypes_codes[0]
        return survtypes, survtypes_val
    
    @callback(
        Output(id_factory('tumor-type'),"data"),
        Output(id_factory('tumor-type'),"value"),
        Input(id_factory('outcomes'),"value"),
        Input(id_factory('ds-sub-sel'),"value"),
        State(id_factory("dataset-datatable"), "selected_row_ids"),
        State(id_factory('tumor-type'),"value"),
    )
    def update_tmtype_on_surv(survp, ds, project, tm):
        if not project:
            return [],None
        project = project[0]
        info = DATASETS[project][ds][survp]
        tmtypes = [i for i in info.keys()]
        options = [{"label":f"{TUMOR_TYPE_KEYS[i].verbose}({info[i]['note']})" if info[i]['note'] else TUMOR_TYPE_KEYS[i].verbose,"value":i} for i in tmtypes]
        tmtype_val = tm if tm in tmtypes else tmtypes[0]
        return options,tmtype_val
    
    @callback(
        Output(id_factory('age-group'),"data"),
        Output(id_factory('age-group'),"value"),
        Input(id_factory('tumor-type'),"value"),
        State(id_factory("dataset-datatable"), "selected_row_ids"),
        Input(id_factory('ds-sub-sel'),"value"),
        Input(id_factory('outcomes'),"value"),
        State(id_factory('age-group'),"value"),
    )
    def update_age_on_tm(tm, project, ds, tp, age_grp):
        if not project:
            return [],None
        project = project[0]
        agegroups = DATASETS[project][ds][tp][tm]["groups"].keys()
        age_options = [{"label":CASE_AGE_GROUP_KEYS[i].verbose,"value":i} for i in agegroups]
        age_val = age_grp if age_grp in agegroups else age_options[0]["value"]
        return age_options, age_val
    
    def ds_badge(id):
        return dbc.Badge(
                html.Tr([
                    html.Td(id),
                    html.Td(
                        dmc.ActionIcon(
                            DashIconify(icon="bi:x-circle-fill", width=15, height=15),
                            id = dict(
                                type="del-ds-2-select",
                                index=id
                            ), 
                            color="primary",),
                        style= {"text-align": "right", "transform": "translateY(1px)"})
                        ]),
                color="white",
                text_color="primary",
                className="border me-1",)

    @callback(
        Output(id_factory("selected-ds"), "children"),
        Output(id_factory("no-dataset-selected"), "style"),
        Input(id_factory("ds_dummy"), "child"), # should never be triggered except the initial load 
        State(id_factory('selected-datasets'), "data"),
    )
    def disp_ori_selected_ds(_, curr_datasets):
        if curr_datasets:
            disp_res = Patch()
            for ds_dict in curr_datasets[::-1]:
                disp_res.prepend(ds_badge(ds2str(ds_dict)) )
            return disp_res, {"display":"none"}
        return no_update, no_update


    @callback(
        Output(id_factory('selected-datasets'), "data",allow_duplicate=True),
        Output(id_factory("selected-ds"), "children",allow_duplicate=True),
        Output(id_factory("max-dataset-warning"), "style",allow_duplicate=True),
        Output(id_factory("no-dataset-selected"), "style",allow_duplicate=True),
        Input(id_factory("add-ds"), "n_clicks"),
        State(id_factory("dataset-datatable"), "selected_row_ids"),
        State(id_factory('ds-sub-sel'),"value"),
        State(id_factory('outcomes'),"value"),
        State(id_factory('tumor-type'),"value"),
        State(id_factory('age-group'),"value"),
        State(id_factory('selected-datasets'), "data"),
        prevent_initial_call = True
    )
    def store_selected_ds(n_clicks,project, ds, tp, tm, age_grp, curr_datasets):
        if not n_clicks: 
            return no_update, no_update, {"display":"none"},no_update
        sel_ds = dict(
            project = project[0],
            verbose = DATASETS[project[0]][ds]["verbose"],
            dataset = ds,
            surv_type = tp,
            tumor_type = tm,
            tm_type_note = DATASETS[project[0]][ds][tp][tm]["note"],
            age_grp = age_grp
        )
        sel_ds_str = ds2str(sel_ds)
        curr_ds = [ds2str(i) for i in curr_datasets]
        if sel_ds_str in curr_ds:
            return no_update, no_update, {"display":"none"}, {"display":"none"}
        if len(curr_datasets) >= max_dataset:
            return no_update, no_update, {}, {"display":"none"}

        data_res = Patch()
        data_res.prepend(sel_ds)
        disp_res = Patch()
        disp_res.prepend(ds_badge(sel_ds_str))
        return data_res, disp_res, {"display":"none"},{"display":"none"}

    @callback(
        Output(id_factory('selected-datasets'), "data",allow_duplicate=True),
        Output(id_factory("selected-ds"), "children",allow_duplicate=True),
        Output(id_factory("max-dataset-warning"), "style",allow_duplicate=True),
        Output(id_factory("no-dataset-selected"), "style",allow_duplicate=True),
        Input(dict(type="del-ds-2-select", index=ALL), "n_clicks"),
        State(id_factory('selected-datasets'), "data"),
        prevent_initial_call=True
    )
    def del_ds(n_clicks, curr_dss):
        btn_id = ctx.triggered_id
        del_idx = [ds2str(i) for i in curr_dss ].index(btn_id["index"])
        if not n_clicks[del_idx]:
            return no_update
        data_res = Patch()
        del data_res[del_idx]
        disp_res = Patch()
        del disp_res[del_idx]
        if len(curr_dss) == 1:
            return data_res, disp_res, {"display":"none"},{}
        return data_res, disp_res, {"display":"none"},{"display":"none"}
    
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
                html.P(["Select the statistical method for partitioning the selected cohort into high and low gene expression groups. ", html.B("Optimal Cut Point is significally slower than other methods. "), "Additional details regarding the comparison between cut-point selection methods can be found in ", html.A("Mandrekar et. al.", href="https://support.sas.com/resources/papers/proceedings/proceedings/sugi28/261-28.pdf", target="_blank"), "."], className="card-text", style={"color":"gray", "font-size":"0.9rem"}),
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
                                            {"label": "Optimal cut point", "value": '1'},
                                            {"label": "Median", "value": '2'},
                                            {"label": "Percentile", "value": '3'},
                                            {"label": "Mean", "value": '4'},
                                            ],
                                        value='4',
                                        persistence=True, persistence_type="session",
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
                                        "Optimal cut point determination is a outcome-oriented method (log-rank test) for dichotomizing a continuous covariate (i.e. gene expression) using cutp from the survMisc R package. Generally this appraoch is expected to produce improved statisical prediction compared to commonly used data-oriented methods, such as median and percentile. For median cut point determination, the median expresison of the gene of interest to partition into high (above median) and low (below median) groups. This same approach is applied for mean cut points. For percertile cut points, two percentileare selected (e.g. 25th and 75th percentile) as thresholds. The (high threshold to 100%) will be defined as the high expression group, while the (0% to low threshold) will be defined as the low expression group.",
                                        html.A("Please refer to Mandrekar et. al. for additional details.", href="https://support.sas.com/resources/papers/proceedings/proceedings/sugi28/261-28.pdf", target="_blank")
                                    ],
                                    id=pgid("group-help-toast"), header="Help on cut point determination", icon="primary", is_open=False, duration=20000, dismissable=True, style={"position": "static", "margin-bottom": "15px", "width": "auto"},
                                ),
                    justify="left", 
                ),
                dbc.Row(
                    html.Div(dcc.RangeSlider(
                        id=pgid('percentile-slider'),
                        min=0, max=100, step=0.5, value=[25,75], 
                        marks={i: f"{str(i)}%" for i in range(0,101,20)},
                        className="rev-slider my-2", 
                        tooltip={"placement": "bottom", "always_visible": True},
                        persistence=True,
                        persistence_type="session",
                    ),
                    id=pgid("percentile-slider-div"),
                    style={"width":"420px","overflow-x":"auto","display":"none"}),
                ),
                html.Hr()]),
            html.Div([ ## LM6/22
                html.H6("Immune cell signature set selection"),
                html.P("Select which deconvoluted immune signature set would be used to compute the correlation with the enrichment/expressions/score based on input type.", style={"color":"gray", "font-size":"0.9rem"}),
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
                                        value=22,
                                        persistence=True, persistence_type="session",
                                    ),
                            className="radio-group",
                            ),
                        width="auto",
                        ),
                        dbc.Col(html.Table(
                            html.Tr([
                                html.Td(
                                    BooleanSwitch(id=pgid("btn-lm-filter"), color=BS_COLORS["primary"], on=True, labelPosition=None,className="my-auto",persistence=True, persistence_type="session",)
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
    SG_INPUT = dcc.Loading(
        id=pgid("loading-res"),
        type="default",
        # color='#f0ad4e',
        # fullscreen=True,
        overlay_style={"visibility":"visible", "filter": "blur(10px)"},
        children=[
            dbc.Card(
                dbc.CardBody([
                    html.H5("Select analysis options.", className="card-title", style={"text-align": "left"}),
                    html.Hr(),
                    dcc.ConfirmDialog(
                        id=pgid('error-msg'),
                        message='Something went wrong! Please double check your input or contact our teams.',
                        submit_n_clicks = 0
                    ),
                    input_contents,
                    html.Div(
                        [html.Br(),
                        review_contents,
                        ],
                        style={'display': 'none'},
                        id=pgid("div-review")
                    ),
                ],id=pgid("input-block"))# , style={"width": "80vw"},
            ),
            dcc.Store(id=pgid('selected-datasets'), storage_type='session', data=[]),
        ],
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
    #     patched_style["display"] = "block" if cutp == "3" else "none"
    #     return patched_style
    showslider = clientside_callback(
        """
        function(cutp, currentStyle) {
            var patchedStyle = { ...currentStyle };  // Copy the current style object
            patchedStyle['display'] = cutp == 3 ? 'block' : 'none';
            return patchedStyle;
        }
        """,
        Output(pgid("percentile-slider-div"),"style"),
        Input(pgid("cutp"), 'value'),
        State(pgid("percentile-slider-div"),"style"),
    )

    @callback(
        Output(pgid("cutp-review"), "children"),
        # Output(pgid("outcome-review"), "children"),
        Output(pgid("til-review"), "children"),
        Input(pgid("cutp"), "value"),
        Input(pgid("percentile-slider"),"value"),
        # Input(pgid("outcomes"), "value"),
        Input(pgid("sg-til-set"), "value"),
        Input(pgid("btn-lm-filter"),"on"),
    )
    def review_cutp_n_other_stats( cutp_in, percentiles, tilset, tilfilter):
        cutp_out = CUTP_KEYS[cutp_in]["verbose"]
        if cutp_in == '3':
            cutp_out = f"{cutp_out} [0%-{min(percentiles)}%, {max(percentiles)}%-100%]"

        # outcomes_out = SURVIVAL_TYPE_KEYS[outcomes_in]["verbose"]
            ## Event-Free survival is only available for TARGET datasets
            ## Implemented in the dataset section
        
        tilset_out = TIL_SET_KEYS[tilset]
        if tilfilter:
            tilset_out = f"{tilset_out} (only with samples p<0.05)"
        else: 
            tilset_out = f"{tilset_out} (all samples)"
        
        return cutp_out, tilset_out

    @callback(
        Output(pgid("dataset-review"), "children"),
        Output(pgid('error-msg'), 'submit_n_clicks'),
        Input(pgid('selected-datasets'), "data"),
    )
    def review_dataset(sel_dss):
        if not sel_dss:
            return "Please select dataset(s).", 0
        res=[]
        for ds in sel_dss:
            res.extend(ds_review(pgid, ds) )
            
        return res, 0

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

def parse_file_N_save(file_contents, ori_fname, new_fname, analysis_type):
    content_type, content_string = file_contents.split(',')
    content_decoded = base64.b64decode(content_string)
    df = None
    if 'csv' in content_type:
        df = pd.read_csv(
            io.StringIO(content_decoded.decode('utf-8')))
    elif 'tsv' in content_type: # won't work cuz some browsers will treat this as base 64 
        df = pd.read_csv(
            io.StringIO(content_decoded.decode('utf-8')), delimiter='\t')
    elif 'xls' in content_type:
        # Assume that the user uploaded an excel file
        df = pd.read_excel(io.BytesIO(content_decoded))
    elif 'txt' in content_type or "text" in content_type or ".txt" in ori_fname:
        delim_tab = content_decoded.decode('utf-8').count('\t')
        delim_com = content_decoded.decode('utf-8').count(',')
        delim = '\t' if delim_tab > delim_com else ','
        df = pd.read_csv(
            io.StringIO(content_decoded.decode('utf-8')), delimiter=delim)
    elif '.csv' in ori_fname:
        df = pd.read_csv(
            io.StringIO(content_decoded.decode('utf-8')))
    elif '.tsv' in ori_fname: # won't work cuz some browsers will treat this as base 64 
        df = pd.read_csv(
            io.StringIO(content_decoded.decode('utf-8')), delimiter='\t')
    elif '.xls' in ori_fname:
        # Assume that the user uploaded an excel file
        df = pd.read_excel(io.BytesIO(content_decoded))
    if not df is None:
        all_req_cols = defaultdict(lambda: [],{
            "cluster_marker": ["cluster", "gene", "p_val_adj"],
            "wcgna_module":["gene_name","module"],
            "grn_module":["gene","regulon"]
        })
        req_cols = all_req_cols[analysis_type]
        missing_cols = [i for i in req_cols if i not in df.columns]
        if len(missing_cols)>0:
            return "Required column(s) {} are not in the dataset".format(', '.join(missing_cols))
        df.to_csv(new_fname,index=False)
        return ''
    return "Unsupported File Format: This file type is not supported. Please upload a table file in one of the following formats: .csv, .tsv, .txt, or .xlsx."

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
                os.remove(os.path.join(TMP_OUTPUT_PATH,file))
            except FileNotFoundError as e:
                dash.get_app().logger.warning(f"Error: Cannot Remove File {file}:\n{e}")
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
