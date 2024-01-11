import os
import json
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback, no_update, clientside_callback, State
# import plotly.graph_objects as go
# from dash_iconify import DashIconify

# from server import task_tb
import plotly.graph_objects as go
import plotly.io
import pandas as pd

from utils import BS_COLORS, CUTP_KEYS, SURVIVAL_TYPE_KEYS,TIL_SET_KEYS,TUMOR_TYPE_KEYS, GENE_FILTER_KEYS, id_factory
from pages.shared_components import collapse_callback, collapse_card, review_card_content, error_page
from configs import DATA_PATH
from pages.output.out_common import redo_forest_table, db_specific_tabs, db_specific_plots, cross_db_plots, sg_review_params, gen_layout, plt_callbacks_forestplt
# from scripts.utils import user_info_validation
# --- Register page --- #
dash.register_page( 
    __name__,
    path_template='/example_out/<analysis_type>',
    # path='/result_visualization',
    title='Survivial Genie V2 - Example Output Visualization', 
    location="navbar"
)

pgid = id_factory("example-out")

# --- Components --- #

def get_figures(session_id): #params
    res_file = os.path.join(DATA_PATH, "example_outs", f"{session_id}_visualization.json")
    figdata = None
    with open(res_file, 'r') as f:
        figdata = json.load(f)
    if not figdata:
        return None
    rv_genes, rv_datasets, rv_cutp, rv_surv, rv_til = sg_review_params(pgid, figdata["params"])
    tabkeys = [i for i in figdata.keys() if i not in ["hrplot","forestplot", "analysis_type", "params", "signature_corr"] ]
    # print(tabkeys)
    # dataset specific figures:
    fig_ds_spec = [db_specific_tabs(figdata[ds], ds, figdata["params"]["analyze_type"]) for ds in tabkeys]#[db_specific_tabs(ds, figdata[ds]) for ds in params["dataset"]]

    # general fig1 : hr plot

    plt_hr = plotly.io.from_json(figdata["hrplot"][0])
    plt_hr.update_layout(showlegend=True)

    df_forest = redo_forest_table(pd.DataFrame.from_dict(json.loads(figdata["forestplot"][0])))

    if figdata["params"]["analyze_type"] not in ["cluster_marker", "wgcna_module"]:
        return fig_ds_spec,f"plt-tab-{tabkeys[0]}", plt_hr, df_forest.to_dict("records"), {}, rv_genes, rv_datasets, rv_cutp, rv_surv, rv_til
    
    plt_tils = plotly.io.from_json(figdata["signature_corr"][0])
    plt_tils.update_xaxes(tickangle = 45)
    for i in range(len(plt_tils.data)):
        if not plt_tils.data[i]["legendgroup"]:
            continue
        legend_label = str(plt_tils.data[i]["legendgroup"])
        plt_tils.data[i]["legendgroup"] = "P<=0.05" if legend_label=='22' else "P>0.05"
        plt_tils.data[i]["name"] = plt_tils.data[i]["legendgroup"]
    return fig_ds_spec,f"plt-tab-{tabkeys[0]}", plt_hr, df_forest.to_dict("records"), plt_tils, rv_genes, rv_datasets, rv_cutp, rv_surv, rv_til

def layout(analysis_type=None, **other_unknown_query_strings):
    titles = {
        "single_gene": "Example Single Gene Analysis Result Visualization",
        "gene_ratio": "Example Gene Ratio Analysis Result Visualization",
        "gene_set": "Example Gene Set Analysis Result Visualization",
        "cluster_marker": "Example Cluster Marker Analysis Result Visualization",
        "wgcna_module": "Example WGCNA module Analysis Result Visualization"
    }

    example_id = {
        "single_gene": "f3b5148330404f369353aa86eba0cede",
        "gene_ratio": "0477895a8e754a7dbcb7c80557476a45",
        "gene_set": "4cb40fee3368429bb28dbfc9796f72b9",
        "cluster_marker": "727996d257cf46c79eb222843b4c6dcd",
        "wgcna_module": "0e71b75573b049dc994d89011e59d179"
    }

    if not analysis_type or analysis_type=="none":
        layout = error_page(layout, "No Analysis Type Specified!")
    elif analysis_type not in titles:
        layout = error_page(layout, f"Analysis type {analysis_type} does not exist!")
    
    fig_ds_spec,active_ds_tab, plt_hr, frst_df_dict, plt_tils, rv_genes, rv_datasets, rv_cutp, rv_surv, rv_til = get_figures(example_id[analysis_type])

    REVIEW_CARD = review_card_content(pgid, analysis_type, 
                                      rv_genes = rv_genes,
                                      rv_datasets = rv_datasets,
                                      rv_cutp = rv_cutp,
                                      rv_surv = rv_surv,
                                      rv_til = rv_til)

    REVIEW_COLLAPSE = dbc.Card(
        collapse_card(
            title = html.H6(
                children=titles[analysis_type],
                id=pgid("title"), className="my-1",
                ),
            btn_text = "Show Prameters",
            collapse_id=pgid("review-collapse"),
            cardbody= dbc.CardBody([REVIEW_CARD]),
            default_isopen = True
            ), 
        color="light")

    DB_SPECIFIC_PLOTS = db_specific_plots(pgid,analysis_type,
                                          fig_ds_spec = fig_ds_spec,
                                          active_ds_tab = active_ds_tab)

    CROSS_DB_PLOTS = cross_db_plots(pgid,analysis_type,
                                    plt_hr = plt_hr,
                                    plt_tils = plt_tils)
    layout = gen_layout(pgid, REVIEW_COLLAPSE, DB_SPECIFIC_PLOTS, CROSS_DB_PLOTS,
                        frst_df_dict = frst_df_dict)


    return layout
    


# --- call backs ---
collapse_callback(pgid("review-collapse"))
collapse_callback(pgid("plot-tabs-collapse"))
collapse_callback(pgid("plot-inter-collapse"))
collapse_callback(pgid("review-genes"),prevent_initial_call=True)
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- 

plt_callbacks_forestplt(pgid)
