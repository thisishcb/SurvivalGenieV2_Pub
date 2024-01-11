import os
import json
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback, no_update, clientside_callback, State
# import plotly.graph_objects as go
# from dash_iconify import DashIconify

from server import task_tb
from .out_common import cross_db_plots, db_specific_plots, gen_layout, plt_callbacks_general, plt_callbacks_forestplt
from utils import BS_COLORS, CUTP_KEYS, SURVIVAL_TYPE_KEYS,TIL_SET_KEYS,TUMOR_TYPE_KEYS, GENE_FILTER_KEYS, id_factory
from pages.shared_components import collapse_callback, collapse_card, review_card_content, error_page

# from scripts.utils import user_info_validation
# --- Register page --- #
dash.register_page( 
    __name__,
    path_template='/result_visualization/<analysis_type>',
    # path='/result_visualization',
    title='Survivial Genie V2 - Analysis Output Visualization', 
    location="navbar"
)

pgid = id_factory("out-visual")

# --- Components --- #

def layout(analysis_type=None, **other_unknown_query_strings):
    titles = {
        "single_gene": "Single Gene Analysis Result Visualization",
        "gene_ratio": "Gene Ratio Analysis Result Visualization",
        "gene_set": "Gene Set Analysis Result Visualization",
        "cluster_marker": "Cluster Marker Analysis Result Visualization",
        "wgcna_module": "WGCNA module Analysis Result Visualization"
    }

    if not analysis_type or analysis_type=="none":
        layout = error_page(layout, "No Analysis Type Specified!")
    elif analysis_type not in titles:
        layout = error_page(layout, f"Analysis type {analysis_type} does not exist!")

    REVIEW_CARD = review_card_content(pgid, analysis_type)

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

    DB_SPECIFIC_PLOTS = db_specific_plots(pgid,analysis_type)

    CROSS_DB_PLOTS = cross_db_plots(pgid,analysis_type)
    layout = gen_layout(pgid, REVIEW_COLLAPSE, DB_SPECIFIC_PLOTS, CROSS_DB_PLOTS)


    return layout
    


# --- call backs ---
collapse_callback(pgid("review-collapse"))
collapse_callback(pgid("plot-tabs-collapse"))
collapse_callback(pgid("plot-inter-collapse"))
collapse_callback(pgid("review-genes"),prevent_initial_call=True)
# ---- ---- ---- ---- ---- ---- ---- ---- ---- ---- 

plt_callbacks_general(pgid)
plt_callbacks_forestplt(pgid)