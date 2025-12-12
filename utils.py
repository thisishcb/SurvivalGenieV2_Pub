from os import path
import json
import re
# import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
# from math import ceil
from numpy import float64
from collections import defaultdict 
from collections.abc import Iterable
from configs import DATA_PATH
from pygtrie import CharTrie
"""
## Miscellaneous Variables and Functions
### Variables:  
CUTP_KEYS, SURVIVAL_TYPE_KEYS ,
PROJ_META, PROJECTS, DISEASES, SITES, DISEASE_2_PROJ, SITE_2_PROJ

"""

#(?<=['"][\w\-_]*)_(?=[\w\\-_]*['"])

##############################################
######          Useful things           ######
##############################################
def flatten(xs):
    for x in xs:
        if isinstance(x, Iterable) and not isinstance(x, (str, bytes)):
            yield from flatten(x)
        else:
            yield x

BS_COLORS = defaultdict(lambda: "UnKnown Type",{
    "res_blue":"#2f67b1",
    "res_red":"#bf2c23",
    "primary": "#007bff", # blue
    "info": "#17a2b8", #teal
    "success": "#28a745", # green
    "warning": "#ffc107", # yellow
    "danger": "#dc3545", # red
    "dark": "#343a40", # " dark grey"
    "secondary": "#6c757d", # grey
    "light": "#f8f9fa" # light grey
})

class KeyVal:
    def __init__(self,val,verbose=None, abbrev=None) -> None:
        """
        val: value for R;
        verbose; 
        abbrev: abbreviation; 
        """
        self.val = val
        self.verbose = verbose if verbose else val
        self.abbrev = abbrev if abbrev else val
    def __str__(self) -> str:
        return str(self.verbose)
    def __getitem__(self, arg):
        assert arg in self.__dict__.keys()
        return self.__dict__[arg]

CUTP_KEYS = defaultdict(lambda: "UnKnown Method",{
    '1': KeyVal(verbose="Optimal cut point", val="cutp"),
    '2': KeyVal(verbose="Median", val="median"),
    '3': KeyVal(verbose="Percentile", val="percentile"),
    '4': KeyVal(verbose="Mean", val="mean")
})

TUMOR_TYPE_KEYS = defaultdict(lambda: "UnKnown Type",{
    '1': KeyVal(verbose="[PR]Primary", val="primary", abbrev = "PR"),
    '2': KeyVal(verbose="[RE]Recurrent", val="recurrent", abbrev="RE"),
    '3': KeyVal(verbose="[ME]Metastatic", val="metastatic", abbrev="ME"),
    '4': KeyVal(verbose="[NM]Normal", val="normal", abbrev="NM"),
    '5': KeyVal(verbose="[OT]Other", val="other", abbrev="OT")
})

CASE_AGE_GROUP_KEYS = defaultdict(lambda: "ALL",{
    "ALL": KeyVal(verbose="[AS]All Samples", val="ALL", abbrev="AS"),
    "ADULT": KeyVal(verbose="[AD]Adult", val="ADULT", abbrev="AD"),
    "PEDIATRIC": KeyVal(verbose="[PD]Pediatric", val="PEDIATRIC", abbrev="PD")
})

SURVIVAL_TYPE_KEYS = defaultdict(lambda: "UnKnown Type",{
    '1': KeyVal(verbose="[OVS]Overall survival", val="overall", abbrev="OVS"),
    '2': KeyVal(verbose="[EFS]Event-free survival", val="event_free", abbrev="EFS")
})

def ds2str(ds:dict, sep=" | ", mode = "abbrev")->str:
    if mode == "abbrev":
        return sep.join([ds['dataset'], SURVIVAL_TYPE_KEYS[ds['surv_type']].abbrev, TUMOR_TYPE_KEYS[ds['tumor_type']].abbrev, CASE_AGE_GROUP_KEYS[ds['age_grp']].abbrev])
    else:
        if 'verbose' not in ds:
            ds['verbose'] = ds['dataset']
        tt_verbo = TUMOR_TYPE_KEYS[ds['tumor_type']].verbose
        tt_verbo += f"[{ds['tm_type_note']}]" if ds["tm_type_note"] else ''
        return [ds['dataset'], html.Br(), ds['verbose'], html.Br(), f"Survival Type: {SURVIVAL_TYPE_KEYS[ds['surv_type']].verbose}",html.Br(), f"Tumor Type: {tt_verbo}",html.Br(), f"Age Group: {CASE_AGE_GROUP_KEYS[ds['age_grp']].verbose}"]

GENE_FILTER_KEYS = defaultdict(lambda: "UnKnown FIlter",{
    'all': KeyVal(verbose="All Genes", val="all"),
    'lnc': KeyVal(verbose="Only lncRNA", val="lnc"),
    'tf': KeyVal(verbose="Only TFs", val="tf"),
    'lr': KeyVal(verbose="Only ligand-receptors", val="lr")
})

TIL_SET_KEYS = defaultdict(lambda: "UnKnown Set",{
    6: "LM6",
    22: "LM22"
})

with open(path.join(DATA_PATH,"approved_symbols.txt"),'r') as f:
    GENE_SYMBOLS = f.read().splitlines()
with open(path.join(DATA_PATH,"approved_lncRNAs.txt"),'r') as f:
    LNC_SYMBOLS = f.read().splitlines() # no symbol column name
with open(path.join(DATA_PATH,"approved_tf.txt"),'r') as f:
    TF_SYMBOLS = f.read().splitlines()
with open(path.join(DATA_PATH,"approved_lr.txt"),'r') as f:
    LR_SYMBOLS = f.read().splitlines()
GENE_SYMBOLS = [i.upper() for i in GENE_SYMBOLS]
LNC_SYMBOLS = [i.upper() for i in LNC_SYMBOLS]
LR_SYMBOLS = [i.upper() for i in LR_SYMBOLS]
TF_SYMBOLS = [i.upper() for i in TF_SYMBOLS]
# 6 times faters than pd.read_csv; [1:] to omit the first row of "Symbol"

with open(path.join(DATA_PATH,"projectmeta.json"),'r') as f:
    PROJ_META = json.load(f)

PROJECTS = tuple(PROJ_META.keys())

for p in PROJECTS:
    if isinstance(PROJ_META[p]["disease_type"],(str, bytes)):
        PROJ_META[p]["disease_type"] = [PROJ_META[p]["disease_type"],]
    if isinstance(PROJ_META[p]["primary_site"],(str, bytes)):
        PROJ_META[p]["primary_site"] = [PROJ_META[p]["primary_site"],]

DISEASES = tuple(sorted(set(flatten([PROJ_META[p]["disease_type"] for p in PROJECTS]))))
PRIM_SITES = tuple(sorted(set(flatten([PROJ_META[p]["primary_site"] for p in PROJECTS]))))

DISEASE_2_PROJ = defaultdict(list)
SITE_2_PROJ = defaultdict(list)

for p in PROJECTS:
    for d in PROJ_META[p]["disease_type"]:
        DISEASE_2_PROJ[d].append(p)
    for s in PROJ_META[p]["primary_site"]:
        SITE_2_PROJ[s].append(p)

with open(path.join(DATA_PATH,"avail_datasets.json"),'r') as f:
    DATASETS = json.load(f)

with open(path.join(DATA_PATH,"dataset_validation.json"),'r') as f:
    DS_VALIDATION = defaultdict(lambda x: "Invalid Geneset",json.load(f))

# PROJ_QC_SUMMARY = pd.read_csv("/opt/megaseq-data/SurvivalGenie2_Dash/data/summary.txt",sep='\t')
# ICC_QC_SUMMARY = pd.read_csv("/opt/megaseq-data/SurvivalGenie2_Dash/data/icc_summary.tsv",sep='\t')

with open(path.join(DATA_PATH,"genesets.json"),'r') as f:
    BUILTIN_GENE_SET = json.load(f)

def id_factory(page: str):
    def func(_id: str):
        """
        Dash pages require each component in the app to have a totally
        unique id for callbacks. This is easy for small apps, but harder for larger 
        apps where there is overlapping functionality on each page. 
        For example, each page might have a div that acts as a trigger for reloading;
        instead of typing "page1-trigger" every time, this function allows you to 
        just use id('trigger') on every page.
        
        > Adopted from `https://community.plotly.com/t/how-do-we-repeat-element-id-in-multi-page-apps/41339/2` 

        How:
            prepends the page to every id passed to it
        Why:
            saves some typing and lowers mental effort
        **Example**
        # SETUP
        from system.utils.utils import id_factory
        id = id_factory('page1') # create the id function for that page
        
        # LAYOUT
        layout = html.Div(
            id=id('main-div')
        )
        # CALLBACKS
        @app.callback(
            Output(id('main-div'),'children'),
            Input(id('main-div'),'style')
        )
        def funct(this):
            ...
        """
        return f"{page}-{_id}"
    return func

def make_valid_name(string):
    """Converts a string to a valid Python variable name."""

    # Replace invalid characters with underscores
    string = re.sub(r'[^a-zA-Z0-9_-]', '_', string)

    # If the string starts with a digit, prepend an underscore
    if string[0].isdigit():
        string = '_' + string

    return string


GENE_SYMBOLS_TREE = CharTrie()
for gene in GENE_SYMBOLS:
    GENE_SYMBOLS_TREE[gene] = gene