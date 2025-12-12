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

from utils import BS_COLORS, CUTP_KEYS, SURVIVAL_TYPE_KEYS,TIL_SET_KEYS,TUMOR_TYPE_KEYS, GENE_FILTER_KEYS, id_factory, make_valid_name
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
    rv_genes, rv_datasets, rv_cutp, rv_til = sg_review_params(pgid, figdata["params"])
    tabkeys = [i for i in figdata.keys() if i not in ["hrplot","forestplot", "analysis_type", "rparams", "params", "signature_corr", "dfJSON"] ]
    # print(tabkeys)
    # dataset specific figures:
    fig_ds_spec = [db_specific_tabs(pgid, figdata[ds], ds, figdata["params"]["analyze_type"]) for ds in tabkeys]#[db_specific_tabs(ds, figdata[ds]) for ds in params["dataset"]]

    # general fig1 : hr plot

    plt_hr = plotly.io.from_json(figdata["hrplot"][0])
    plt_hr.update_layout(showlegend=True)
    # remove the og reference lines if any, they were transformed to fixedlength shapes 
    plt_hr.data = tuple(
        trace for trace in plt_hr.data
        if not (
            trace.type == 'scatter' and
            trace.mode == 'lines' and
            (len(set(trace.x)) == 1 or
            len(set(trace.y)) == 1)
        ))
    # re-do the two reference lines 
    plt_hr.add_shape(
        type="line",
        x0=1, x1=1,  # x location
        y0=0, y1=1,  # span full height
        xref="x",
        yref="paper",
        line=dict(color="#666666", width=1, dash="dot")
    )
    plt_hr.add_shape(
        type="line",
        x0=0, x1=1, # span full height
        y0=1.30103, y1=1.30103,  
        xref="paper",
        yref="y",
        line=dict(color="#666666", width=1, dash="dot")
    )
    # change the text label position # vjust lost in json transform
    y_all=[]
    for trace in plt_hr.data:
        if hasattr(trace, 'text') and trace.mode=="text":
            # Manually set position
            trace.textposition = 'top center'
            if hasattr(trace, 'y') and trace.y is not None:
                y_all.extend(trace.y)
    plt_hr.update_layout(yaxis=dict(range=[min([1.2,min(y_all)-0.05*max(y_all)]), max(y_all)*1.05]))

    df_forest = redo_forest_table(pd.DataFrame.from_dict(json.loads(figdata["forestplot"][0])))

    if figdata["params"]["analyze_type"] not in ["cluster_marker", "wgcna_module", "multi_sg", "grn_module"]:
        return fig_ds_spec,f"plt-tab-{make_valid_name(tabkeys[0])}", plt_hr, df_forest.to_dict("records"), {}, rv_genes, rv_datasets, rv_cutp, rv_til
    
    plt_tils = plotly.io.from_json(figdata["signature_corr"][0])
    plt_tils.update_xaxes(tickangle = 45)
    for i in range(len(plt_tils.data)):
        if not plt_tils.data[i]["legendgroup"]:
            continue
        legend_label = str(plt_tils.data[i]["legendgroup"])
        plt_tils.data[i]["legendgroup"] = "P<=0.05" if legend_label=='22' else "P>0.05"
        plt_tils.data[i]["name"] = plt_tils.data[i]["legendgroup"]
    return fig_ds_spec,f"plt-tab-{make_valid_name(tabkeys[0])}", plt_hr, df_forest.to_dict("records"), plt_tils, rv_genes, rv_datasets, rv_cutp, rv_til

def layout(analysis_type=None, **other_unknown_query_strings):
    titles = {
        "single_gene": "Example Single Gene Analysis Result Visualization",
        "multi_sg": "Example Multiple Genes Analyses Result Visualization",
        "gene_ratio": "Example Gene Ratio Analysis Result Visualization",
        "gene_set": "Example Gene Set Analysis Result Visualization",
        "gene_set_contrast":"Example Gene Set Contrast Analysis Result Visualization",
        "cluster_marker": "Example Cluster Marker Analysis Result Visualization",
        "wgcna_module": "Example WGCNA module Analysis Result Visualization",
        "grn_module": "Example GRN Analysis Result Visualization",
        "lrsignal": "Example Ligand-Receptor Signaling Analysis Result Visualization"
    }

    example_id = {
        "single_gene": "f3b5148330404f369353aa86eba0cede",
        "multi_sg": "6220bdbf57fa445385ce835bc1de36b0",
        "gene_ratio": "0477895a8e754a7dbcb7c80557476a45",
        "gene_set": "4cb40fee3368429bb28dbfc9796f72b9",
        "gene_set_contrast":"80755734bae9494f853b89e23222a476",
        "cluster_marker": "727996d257cf46c79eb222843b4c6dcd",
        "wgcna_module": "0e71b75573b049dc994d89011e59d179",
        "grn_module": "b7c375e733db44989fd0766550a185f9",
        "lrsignal": "29278242c0ff4258b3e76fc88031bc2a"
    }

    if not analysis_type or analysis_type=="none":
        layout = error_page(layout, "No Analysis Type Specified!")
    elif analysis_type not in titles:
        layout = error_page(layout, f"Analysis type {analysis_type} does not exist!")
    
    fig_ds_spec,active_ds_tab, plt_hr, frst_df_dict, plt_tils, rv_genes, rv_datasets, rv_cutp, rv_til = get_figures(example_id[analysis_type])

    REVIEW_CARD = review_card_content(pgid, analysis_type, 
                                      rv_genes = rv_genes,
                                      rv_datasets = rv_datasets,
                                      rv_cutp = rv_cutp,
                                      rv_til = rv_til)

    REVIEW_COLLAPSE = dbc.Card(
        collapse_card(
            title = html.H6(
                children=titles[analysis_type],
                id=pgid("title"), className="my-1",
                ),
            btn_text = "Show Parameters",
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
    layout = gen_layout(pgid, REVIEW_COLLAPSE, DB_SPECIFIC_PLOTS, CROSS_DB_PLOTS, example_page=True, 
                        frst_df_dict = frst_df_dict)


    return layout
    


# --- call backs ---
collapse_callback(pgid("review-collapse"))
collapse_callback(pgid("plot-tabs-collapse"))
collapse_callback(pgid("plot-inter-collapse"))

collapse_callback(pgid("review-genes-pos"),prevent_initial_call=True)
collapse_callback(pgid("review-genes-neg"),prevent_initial_call=True)
collapse_callback(pgid("review-genes"),prevent_initial_call=True)
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- 

plt_callbacks_forestplt(pgid)


clientside_callback(
    """
    function(nclick,button_id){
        downloadPlotSVG(button_id.index)
        return(nclick);
    }
    """,
    Output({'type': pgid('save-btn-plot'), 'index': dash.MATCH}, 'n_clicks'),
    Input({'type': pgid('save-btn-plot'), 'index': dash.MATCH}, 'n_clicks'),
    State({'type': pgid('save-btn-plot'), 'index': dash.MATCH}, 'id'),
    prevent_initial_call=True
)

clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.history.back();
        }
        // We must return something to the output, 
        // but it doesn't matter what since the div is hidden.
        return "";
    }
    """,
    Output(pgid("dummy-output"), "children"),
    Input(pgid("output-last-page"), "n_clicks"),
    prevent_initial_call=True
)
