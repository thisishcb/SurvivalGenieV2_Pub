import dash
import dash_bootstrap_components as dbc
from dash import html, dcc ,callback, Input, Output, State, clientside_callback, MATCH

from utils import PROJ_META, DATASETS, SURVIVAL_TYPE_KEYS, TIL_SET_KEYS, TUMOR_TYPE_KEYS

dash.register_page(
    __name__,
    path='/help',
    title='SurvivalGenie2.0 Help',
    location="navbar"
)

# --- Components --- #

def dataset_table():
    table_content = [html.Tr([
        html.Th(("Program"),style={"width":"10%"}),
        html.Th(("Project"),style={"width":"20%"}),
        html.Th(("Tissue"),style={"width":"35%"}),
        html.Th(("Disease"),style={"width":"35%"})])]
    for p_key, p_value in PROJ_META.items():
        info_row = [html.Tr([
            html.Td(p_value["program"],style={"width":"10%"}),
            html.Td(p_key,style={"width":"20%"}),
            html.Td(' | '.join(p_value["primary_site"]),style={"width":"35%"}),
            html.Td(' | '.join(p_value["disease_type"]),style={"width":"35%"})],
            id = {"index": p_key, "type": "trProject"})]
        # for ds,ds_val in DATASETS[p_key].items():
        #     verbose = ds_val["verbose"]
        #     for surv_key,surv_val in ds_val.items():
        #         if surv_key=="verbose":
        #             continue
        #         surv_type = SURVIVAL_TYPE_KEYS[surv_key].verbose


        # ds_content = [html.Tr([
        #     html.Td(ds),
        #     html.Td(ds),
        #     html.Td(ds),
        #     html.Td(ds)],
        #     id={"index": p_key, "type": "trProject-details"},
        #     style={"display":"none"}) ] 
        # TODO https://stackoverflow.com/questions/55418928/collapse-html-table-rows-by-default
        # https://jsfiddle.net/isherwood/hrg4d5oj/5/
        # info_row.extend(ds_content)
        table_content.extend(info_row)
    supported_ds = dbc.Table(table_content,id="all-dataset-table", striped=True, bordered=True, hover=True)
    return supported_ds

HELP = [
        html.H2("Reference manual for Survival Genie 2.0", className="card-title"),
        # html.P("This page will contain the tutorial and reference manual for Survival Genie 2.0.", className="card-text", style={"font-size": "1.1rem"}),
        html.P([
            "This page contains help information regarding Survival Genie 2.0.",
            html.Br(),
            "For figured tutorial, please go back to the home page and expand the tutorial tab."
            ]),
        html.H3("Supported Datasets"),
        dataset_table(),
        ]

# --- Layout --- #
def layout():
    layout = dbc.Container([
        html.Br(),
        dbc.Row(
            [dbc.Col(HELP,
                     md=dict(size=12),
                     lg=dict(size=10),
                     xl=dict(size=8))],
            justify="center",
        ),
        html.Script(src='assets/custom-script.js')
        ],
    fluid=True,

    )
    return layout


# -------------------------

# --- hide/show proj details ---

# @callback(
#     Output({"index": MATCH, "type": "trProject-details"}, "style"),
#     Input({"index": MATCH, "type": "trProject"}, "n_clicks"),
#     State({"index": MATCH, "type": "trProject-details"}, "style"),
#     prevent_initial_call=True,
# )
# def item_selected(n_clicks, style):
#     if n_clicks:
#         new_style = {} if "display" in style else {"display":"none"}
#     return new_style
