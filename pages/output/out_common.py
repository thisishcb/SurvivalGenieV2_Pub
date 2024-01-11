import os
import json
import dash
import dash_bootstrap_components as dbc
from dash_daq import BooleanSwitch
from dash_iconify import DashIconify
from dash import dcc, html, Input, Output, State, callback, no_update, clientside_callback, ctx
# import plotly.graph_objects as go
import plotly.io
import pandas as pd
import re

import plotly.graph_objects as go
from numpy import float64
from collections import defaultdict
# from utils import id_factory
from pages.shared_components import collapse_card
from utils import BS_COLORS, CUTP_KEYS, SURVIVAL_TYPE_KEYS,TIL_SET_KEYS,TUMOR_TYPE_KEYS, GENE_FILTER_KEYS, id_factory, CASE_AGE_GROUP_KEYS
from configs import TMP_OUTPUT_PATH
##############################################
######               Figs               ######
##############################################
def redo_forest_table(forest_df):
    ## converts the R dataframe to the desired format in python
    ## maybe can do this in R 
    fp_values = forest_df.loc[2:,].copy() # following rows with actual values
    fp_values.loc[:,"HR_Ratio"] = fp_values["HR_Ratio"].astype(float64)
    fp_values.loc[:,"HR_Pvalue"] = fp_values["HR_Pvalue"].astype(float64)

    fp_values.loc[:,"HR_CI_high"] = fp_values["HR_CI_high"].astype(float64)
    fp_values.loc[:,"HR_CI_low"] = fp_values["HR_CI_low"].astype(float64)

    fp_values.loc[:,"HR_CI_up"] = fp_values["HR_CI_high"] - fp_values["HR_Ratio"]
    fp_values.loc[:,"HR_CI_minus"] = fp_values["HR_Ratio"] - fp_values["HR_CI_low"]

    fp_values.loc[:,"nlow"] = fp_values["nlow"].astype(int)
    fp_values.loc[:,"nhigh"] = fp_values["nhigh"].astype(int)
    # size representing the n_samples 
    fp_values.loc[:,"dot_size"] = fp_values["nlow"] + fp_values["nhigh"]
    fp_values.loc[:,"dot_size"] = 15 + 10*fp_values["dot_size"] / max(fp_values["dot_size"])
    # highlight the significant ones 
    fp_values.loc[:,"dot_color"] = "grey"
    fp_values.loc[fp_values.HR_Pvalue<0.05,"dot_color"] = BS_COLORS["res_red"]
    fp_values.loc[(fp_values.HR_Pvalue<0.05)&(fp_values.HR_Ratio<1),"dot_color"] = BS_COLORS["res_blue"]
    return fp_values

def df2forestplot(fp_values, filter=False, analysis_type=""):
    """Create the forest plot with metadata annotations
    the dataframe includes two lines of headers as in the forestplot R pkg"""

    if filter:
        fp_values = fp_values[fp_values["HR_Pvalue"] < 0.05]

    if (fp_values.shape[0] == 0) or (fp_values is None):
        forest_plot = go.Figure(layout=dict(
                template="simple_white",
                xaxis = dict(
                    range=[-1,1],
                    fixedrange=True,
                    visible = False),
                yaxis = dict(
                    range=[-1,1],
                    fixedrange=True,
                    visible = False),
            ))
        forest_plot.add_annotation(x=0, y=0,
                        text="No Value Available",
                        showarrow=False,yshift=0,font = {"size": 20})
        return forest_plot, 0
    # the range for HR intervals 
    min_val = min(min(fp_values["HR_CI_low"]),0)
    max_val = max(max(fp_values["HR_CI_high"]),3)

    
    if analysis_type == "cluster_marker":
        first_col_name = "<b>Cluster</b>"
    elif analysis_type == "wgcna_module":
        first_col_name = "<b>Module</b>"
    else:
        first_col_name = "<b>Dataset</b>"
    fp_values = pd.concat([fp_values, pd.DataFrame([[first_col_name, 1, min_val, max_val, "<b>nLow<br>Cases</b>", "<b>nHigh<br>Cases</b>", "<b>HR<br>(95% CI)</b>", "<b>HR<br>P value</b>", "<b>Cut<br>Point</b>", "<b>LR<br>P value</b>",0,max_val-1,1-min_val,0,"grey"]], columns=fp_values.columns)], ignore_index=True).reset_index()

    # other metadata columns to display and their position
    vars2show = ["Dataset","nlow","nhigh","Cut_Point",
                 "HR","HR_Pvalue","LR_Pvalue"]
    col_gap=(max(fp_values["HR_CI_high"]) - min(fp_values["HR_CI_low"]))/2
    # slightly more space for HE (HR(high/low)), slightly longer 
    xvals = [min_val-5.5*col_gap, min_val-4*col_gap, min_val-3*col_gap, min_val-1.5*col_gap,
              max_val+1.5*col_gap ,max_val+3*col_gap, max_val+4.2*col_gap]

    forest_plot = go.Figure(data=go.Scatter(
            x=fp_values.HR_Ratio,
            y=fp_values.Dataset,
            mode='markers',
            showlegend=False,name="",
            marker=dict(
                color=fp_values.dot_color,
                size=fp_values.dot_size.tolist(),
                symbol="square"),
            error_x=dict(
                type='data',
                symmetric=False,
                array=fp_values.HR_CI_up,
                arrayminus=fp_values.HR_CI_minus)
            ),
            layout=dict(
                template="simple_white",
                xaxis = dict(
                    fixedrange=False,
                    tickvals=[0,.2,.5,1,1.5,2,3], # ticks, important!!!
                    showgrid=True,
                    zeroline=False,
                    visible = True),
                yaxis = dict(
                    # domain=(0.25, 0.75),
                    fixedrange=True,
                    showgrid=True,
                    zeroline=False,
                    visible = False),
            ))
    # the meta tables 
    for i, study in enumerate(fp_values['Dataset']):
        for j in range(7):
            forest_plot.add_annotation(
                text=str(fp_values[vars2show[j]][i]),
                x= xvals[j],
                y=study,
                showarrow=False,
            )
        if study == first_col_name: # the funny arrow looks good
            forest_plot.add_annotation(x=(min_val+max_val)/2, y=study,
                        text="<i>Better Survival ~~ Poorer Survival</i>",
                        showarrow=False,yshift=15,font = {"size": 10})
            forest_plot.add_traces([
                go.Scatter(
                    x=[min_val], y=[study],mode='markers',showlegend=False,name="",
                    marker=dict( color="black", size=15, symbol="triangle-left"),
                    ),
                go.Scatter(
                    x=[max_val], y=[study],mode='markers',showlegend=False,name="",
                    marker=dict( color="black", size=15, symbol="triangle-right"),
                    ),
                ])

    forest_plot.add_vline(x=1,line_width=2, line_dash="dash", line_color="#bbbbbb")
    
    return forest_plot, fp_values.shape[0]

##############################################
######         page content             ######
##############################################

def db_specific_tabs(ds_figdata, ds, analysis_type):
    '''[[tab for box/waterfall], modules, km-plot]'''
    # waterfall plot hide x-axis; til plots: keep ticks, rm row label
    # fig.update_xaxes(showticklabels=False)
    plt_box = plotly.io.from_json(ds_figdata["boxplot"][0])
    plt_box.update_layout(showlegend=False)
    # -------------------
    plt_wf = plotly.io.from_json(ds_figdata["waterfall"][0])
    plt_wf.update_xaxes(showticklabels=False)
    plt_wf.update_layout(legend=dict(
        yanchor="top", y=0.99,
        xanchor="left", x=0.01
    ))
    # -------------------
    plt_km = plotly.io.from_json(ds_figdata["kmplot"][0])
    plt_km.update_layout(legend=dict(
        yanchor="top", y=0.99,
        xanchor="right", x=0.99
    ))
    for i in range(len(plt_km.data)):
        if not plt_km.data[i]["legendgroup"]:
            continue
        legendmatch = re.search(r'\((.*),\d\)',plt_km.data[i]["legendgroup"])
        plt_km.data[i]["legendgroup"] = legendmatch.group(1) if legendmatch else plt_km.data[i]["legendgroup"]
        plt_km.data[i]["name"] = plt_km.data[i]["legendgroup"]
    plt_km_newdata = list(plt_km.data)
    p_anno = plt_km_newdata.pop()["text"]
    plt_km.data = plt_km_newdata
    plt_km.add_annotation(text=p_anno,#font=dict(size=16),
                    xref="paper", yref="paper",
                    x=0.01, y=0.01, showarrow=False)
    # -------------------
    plt_tils = None
    if analysis_type not in ["cluster_marker", "wgcna_module"]:
        plt_tils = plotly.io.from_json(ds_figdata["signature_corr"][0])
        for i in range(len(plt_tils.data)):
            if not plt_tils.data[i]["legendgroup"]:
                continue
            legend_label = str(plt_tils.data[i]["legendgroup"])
            plt_tils.data[i]["legendgroup"] = "P<=0.05" if legend_label=='22' else "P>0.05"
            plt_tils.data[i]["name"] = plt_tils.data[i]["legendgroup"]

    # -------------------
    # print(analysis_type)
    if analysis_type in ["cluster_marker", "wgcna_module"]:
        # only km plot and box/waterfall 
        tab_layout = dbc.Tab(dbc.Row([
            dbc.Col(
                children = [
                    # box-plot / waterfall plot
                    html.Br(),
                    dbc.Card([
                        dbc.CardHeader("Distribution of Low and High Sample Groups"),
                        dbc.CardBody(dbc.Tabs([
                                dbc.Tab(dcc.Graph(figure=plt_box,
                                            style={'height': '350px'}),
                                    label="Box Plot",tab_id="bxp"),
                                dbc.Tab(dcc.Graph(figure=plt_wf,
                                            style={'height': '350px'}),
                                    label="Waterfall Plot",tab_id="wfp"),
                            ],active_tab="bxp"))
                        ]),
                    ],
                    sm=dict(size=12), lg=dict(size=6),align="center"
                ),
                dbc.Col(
                    [html.Br(),
                    # kmplot
                    dbc.Card([
                        dbc.CardHeader("Kaplan-Meier Plot"),
                        dbc.CardBody([
                            dcc.Graph(figure=plt_km,
                                    style={'height': '391px'})
                            ]),
                    ])],
                    sm=dict(size=12), lg=dict(size=6),align="center")
        ]), label=ds, tab_id=f"plt-tab-{ds}") 
    else: # 3 figures 
        tab_layout = dbc.Tab(dbc.Row([
            dbc.Col(
                children = [
                    # box-plot / waterfall plot
                    html.Br(),
                    dbc.Card([
                        dbc.CardHeader("Distribution of Low and High Sample Groups"),
                        dbc.CardBody(dbc.Tabs([
                                dbc.Tab(dcc.Graph(figure=plt_box,
                                            style={'height': '350px'}),
                                    label="Box Plot",tab_id="bxp"),
                                dbc.Tab(dcc.Graph(figure=plt_wf,
                                            style={'height': '350px'}),
                                    label="Waterfall Plot",tab_id="wfp"),
                            ],active_tab="bxp"))
                        ]),
                    html.Br(),
                    # kmplot
                    dbc.Card([
                        dbc.CardHeader("Kaplan-Meier Plot"),
                        dbc.CardBody([
                            dcc.Graph(figure=plt_km,
                                    style={'height': '350px'})
                            ]),
                        ]),
                    ],
                    sm=dict(size=12), lg=dict(size=6),align="center"
                ),
            dbc.Col(
                children=[
                    html.Br(),
                    dbc.Card([
                        dbc.CardHeader("Correlation with Immune Cell - Lymphocytes Signature"),
                        dbc.CardBody([dcc.Graph(figure=plt_tils,
                                    style={'height': '845px'})])
                        ]),  # , style={'height': '97.6%'}
                    ],
                    sm=dict(size=12), lg=dict(size=6)#,align="center",
                    
                ),
        ]), label=ds, tab_id=f"plt-tab-{ds}")
    return tab_layout

def db_specific_plots(pgid, analysis_type, **kwargs):
    titles = defaultdict(lambda: "Intra-Dataset Results", {
        "cluster_marker": "Intra-Cluster Results",
        "wgcna_module": "Intra-Module Results"
    })
    plt_tabs = kwargs.pop("fig_ds_spec", [])
    plt_tab_active = kwargs.pop("active_ds_tab", {})
    DB_SPECIFIC_PLOTS = dbc.Card(
        collapse_card(
            title = html.H6(
                children=titles[analysis_type],#"Dataset-Specific Results",
                className="my-1", id=pgid("db-spec-tt")
                ),
            btn_text = "Show Figures",
            collapse_id=pgid("plot-tabs-collapse"),
            cardbody =
                dbc.CardBody(
                    dbc.Tabs(
                        plt_tabs,# callback to set [DB_SPECIFIC_TAB(ds) for ds in ]
                        id=pgid("plot-tabs"),
                        active_tab=plt_tab_active,
                        class_name="mx-auto")
                    )
            )
    )
    return DB_SPECIFIC_PLOTS

def cross_db_plots(pgid,analysis_type, **kwargs):
    plt_hr = kwargs.pop("plt_hr", {})
    plt_tils = kwargs.pop("plt_tils", {})
    # if analysis_type in ["cluster_marker", "wgcna_module"]:
    cardbody =  dbc.CardBody([
        html.Div([dbc.Row([
            dbc.Col(dbc.Card([
                    dbc.CardHeader("Correlation with Immune Cell - Lymphocytes Signature"),
                    dbc.CardBody([dcc.Graph(id=pgid("plot-tils-sgds"),
                                            figure = plt_tils,
                                            style={'height': '845px'})
                                            ])
                    ]),
                    width=12)
            ]),
            html.Br()],
            style={"display":"block" if analysis_type in ["cluster_marker", "wgcna_module"] else "none"}),
        dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Hazard-Ratio Plot"),
                    dbc.CardBody(
                        dcc.Graph(id=pgid("plot-hr"),
                                  figure = plt_hr, 
                                  style={'height': '350px'})
                        )
                    ]),id=pgid("plot-hr-col"),
                    xl=dict(size=4),lg=dict(size=8),md=dict(size=12)),
                dbc.Col(dbc.Card([
                    dbc.CardHeader(dbc.Row([
                        dbc.Col(
                            "Forest Plot", align="center", md=dict(size=9), xs=dict(size=12)
                            ),
                        dbc.Col(
                            html.Tr([
                            html.Td(
                                BooleanSwitch(id=pgid("btn-forest-filter"), color=BS_COLORS["primary"], on=False, labelPosition=None,className="my-auto")
                                    ),
                            html.Td(
                                html.P("HR P-value < 0.05",
                                    style={"color":"gray", "font-size":"0.9rem"},
                                    className="my-auto")
                                    )
                            ],
                            style={'vertical-align': 'middle'},
                            ),
                            align="center", md=dict(size=3), xs=dict(size=12)
                            )
                        ], justify="center")
                    ),
                    dbc.CardBody(
                        dbc.Spinner(dcc.Graph(id=pgid("plot-forest"),
                                style={'height': '350px'}))
                        )
                    ]),id=pgid("plot-forest-col"),
                    xl=dict(size=8),lg=dict(size=12))
                ],justify="center")
                ])
    # general layout separate by the multi-dataset or multi-modules/cluster
    titles = defaultdict(lambda: "Inter-Dataset Results", {
        "cluster_marker": "Inter-Cluster Results",
        "wgcna_module": "Inter-Module Results"
    })
    CROSS_DB_PLOTS = dbc.Card(
        collapse_card(
            title = html.H6(
                children=titles[analysis_type],
                className="my-1", id=pgid("db-cros-tt")
                ),
            btn_text = "Show Figures",
            collapse_id=pgid("plot-inter-collapse"),
            cardbody = cardbody
            )
        )
    return CROSS_DB_PLOTS

def gen_layout(pgid, REVIEW_COLLAPSE, DB_SPECIFIC_PLOTS, CROSS_DB_PLOTS, **kwargs):
    frst_df_dict = kwargs.pop("frst_df_dict", {})
    layout = html.Div([dbc.Container(dbc.Col(
        [
            html.Br(),
            dbc.Row(
                [dbc.Col(id=pgid("review-params"), children=REVIEW_COLLAPSE, width=12)],
                justify="center",
            ),
            html.Br(),
            dbc.Row(
                [dbc.Col(DB_SPECIFIC_PLOTS)],
                justify="center",
            ),
            html.Br(),
            dbc.Row(
                [dbc.Col(CROSS_DB_PLOTS)],
                justify="center",
            ),
            # dbc.Row(
            #     [dbc.Col(id=pgid("output1"), children="", width="auto")],
            #     justify="center", class_name="mb-5"
            # ),
            html.Br(),
        ],
        sm=dict(size=12),# style={"width": "80vw"},
        md=dict(size=10),
        lg=dict(size=9), className="mx-auto"),
        fluid=True,
    ),
    dcc.Store(id=pgid("forest-table"), storage_type="memory",data=frst_df_dict),])
    return layout

def long_gene_review(id_factory, title=None, genes=None):
    space4genes  = [
        html.A(
            title,
            id=id_factory("review-genes-btn"),
            n_clicks=0,
            ),
        dbc.Collapse(
            html.Span(genes,style={"color": BS_COLORS["dark"], "font-size":"0.8rem"}, id = id_factory("review-genes-detail")),
            id=id_factory("review-genes"),
            is_open=False,
            )
        ]
    return space4genes

def sg_review_params(pgid, params):
    if params["analyze_type"] == "single_gene":
        genes = params["gene_symbol"]
    elif params["analyze_type"] == "gene_ratio":
        genes = f"log({params['gene_symbol'][0]}/{params['gene_symbol'][1]})"
    elif params["analyze_type"] == "gene_set":
        genesprint = f"Gene Set: {params['gene_set']} " if params['gene_set']!= "userinput" else "Customized Gene Set. "
        genesprint = [genesprint, DashIconify(icon="ion:caret-down", width=20,height=20, color="light")]
        genes =  long_gene_review(pgid, genesprint, ", ".join(params["gene_symbol"]))
    elif params["analyze_type"] == "cluster_marker":
        if params["input_type"] == "example_data":
            genes = "Example Data"
        elif params["input_type"] == "URL":
            genes = f"Cluster Markers from {params['url']}"
        else:
            genes = f"Cluster Markers from {params['file_name']}"
        genes += f' [{GENE_FILTER_KEYS[params["gene_filter"]].verbose}]'
    elif params["analyze_type"] == "wgcna_module":
        if params["input_type"] == "example_data":
            genes = "Example Data"
        elif params["input_type"] == "URL":
            genes = f"Module Eigen-genes from {params['url']}"
        else:
            genes = f"Module Eigen-genes from {params['file_name']}"
        genes += f' [{GENE_FILTER_KEYS[params["gene_filter"]].verbose}]'

    datasets = ', '.join(params["dataset"])
    datasets = "[{}-{}] ".format(TUMOR_TYPE_KEYS[params["tumor_type"]].verbose, CASE_AGE_GROUP_KEYS[params.get("case_age_group","ALL")].verbose) + datasets
    
    cutp_out = CUTP_KEYS[params["cutp_method"]]["verbose"]
    if params["cutp_method"] == 3:
        cutp_out = f"{cutp_out} [0%-{min(params['percentiles'])}%, {max(params['percentiles'])}%-100%]"

    tilset = TIL_SET_KEYS[params["til_set"]]
    if params["til_fil"]:
        tilset = f"{tilset} (only with samples p<0.05)"
    else: 
        tilset = f"{tilset} (all samples)"
    return genes, datasets, cutp_out,\
        SURVIVAL_TYPE_KEYS[params["survival_type"]]["verbose"], tilset

def plt_callbacks_general(pgid):
    @callback(
            Output(pgid("plot-tabs"), 'children'),
            Output(pgid("plot-tabs"), 'active_tab'), 
            Output(pgid('plot-hr'), 'figure'),
            Output(pgid("forest-table"), "data"),
            Output(pgid("plot-tils-sgds"), "figure"),
            Output(pgid("genes-review"), "children"),
            Output(pgid("dataset-review"), "children"),
            Output(pgid("cutp-review"), "children"),
            Output(pgid("outcome-review"), "children"),
            Output(pgid("til-review"), "children"),
            Input('session-id', 'data'),
            #   State('storesession', 'data'),
            prevent_initial_call=False
          )
    def result(session_id): #params
        res_file = os.path.join(TMP_OUTPUT_PATH, f"{session_id}_visualization.json")
        figdata = None
        with open(res_file, 'r') as f:
            figdata = json.load(f)
        if not figdata:
            return no_update
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
            return fig_ds_spec,f"plt-tab-{tabkeys[0]}", plt_hr, df_forest.to_dict("records"), no_update, rv_genes, rv_datasets, rv_cutp, rv_surv, rv_til
        
        plt_tils = plotly.io.from_json(figdata["signature_corr"][0])
        plt_tils.update_xaxes(tickangle = 45)
        for i in range(len(plt_tils.data)):
            if not plt_tils.data[i]["legendgroup"]:
                continue
            legend_label = str(plt_tils.data[i]["legendgroup"])
            plt_tils.data[i]["legendgroup"] = "P<=0.05" if legend_label=='22' else "P>0.05"
            plt_tils.data[i]["name"] = plt_tils.data[i]["legendgroup"]
        return fig_ds_spec, f"plt-tab-{tabkeys[0]}", plt_hr, df_forest.to_dict("records"), plt_tils, rv_genes, rv_datasets, rv_cutp, rv_surv, rv_til

def plt_callbacks_forestplt(pgid):
    @callback(
        Output(pgid('plot-forest'), 'figure'),
        Output(pgid('plot-forest'), 'style'),
        Output(pgid("plot-hr"), 'style'),
        Output(pgid("plot-hr-col"), 'xl'),
        Output(pgid("plot-forest-col"), 'xl'),
        Input(pgid("btn-forest-filter"), "on"),
        Input(pgid("forest-table"), 'data'),
        State('storesession', 'data'),
        State('url', 'pathname')
    )
    def update_forest(frst_filt, dfdata, params, url):
        if "analyze_type" in params:
            analyze_type = params["analyze_type"]
        else:
            url_cmps = str(url).split('/')
            analyze_type = url_cmps[-2] if str(url).endswith('/') else url_cmps[-1]
        fpvalues = pd.DataFrame(dfdata)
        # print(sum(fpvalues["HR_Pvalue"] < 0.05), fpvalues.shape[0], ctx.triggered_id, pgid("btn-forest-filter"))
        if sum(fpvalues["HR_Pvalue"] < 0.05) == fpvalues.shape[0] and ctx.triggered_id == pgid("btn-forest-filter"):
            return no_update
        plt_forest, figrows = df2forestplot(fpvalues, frst_filt, analyze_type)
        forest_height = max([350, 50*figrows])
        forest_style={'height': f'{forest_height}px'}
        hr_style= {'height': '450px'} if forest_height > 400 else {'height': '350px'}
        hr_width = dict(size=6) if forest_height > 400 else dict(size=4)
        fr_width = dict(size=12) if forest_height > 400 else dict(size=8)
        return plt_forest,forest_style, hr_style, hr_width, fr_width
