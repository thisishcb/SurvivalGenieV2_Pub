from os import path
import json
import pandas as pd
import plotly.graph_objects as go
# from math import ceil
from numpy import float64
from collections import defaultdict 
from collections.abc import Iterable
from configs import DATA_PATH
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
    def __init__(self,val,verbose) -> None:
        self.verbose = verbose
        self.val = val
    def __str__(self) -> str:
        return str(self.verbose)
    def __getitem__(self, arg):
        assert arg in self.__dict__.keys()
        return self.__dict__[arg]

CUTP_KEYS = defaultdict(lambda: "UnKnown Method",{
    1: KeyVal(verbose="Optimal cut point", val="cutp"),
    2: KeyVal(verbose="Median", val="median"),
    3: KeyVal(verbose="Percentile", val="percentile"),
    4: KeyVal(verbose="Mean", val="mean")
})

TUMOR_TYPE_KEYS = defaultdict(lambda: "UnKnown Type",{
    1: KeyVal(verbose="Primary", val="primary"),
    2: KeyVal(verbose="Recurrent", val="recurrent"),
    3: KeyVal(verbose="Metastatic", val="metastatic")
})

CASE_AGE_GROUP_KEYS = defaultdict(lambda: "ALL",{
    "ALL": KeyVal(verbose="All Samples", val="ALL"),
    "ADULT": KeyVal(verbose="Adult", val="ADULT"),
    "PEDIATRIC": KeyVal(verbose="Pediatric", val="PEDIATRIC")
})

SURVIVAL_TYPE_KEYS = defaultdict(lambda: "UnKnown Type",{
    1: KeyVal(verbose="Overall survival", val="overall"),
    2: KeyVal(verbose="Event-free survival", val="evemnt_free")
})

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

GENE_SYMBOLS = open(path.join(DATA_PATH,"approved_symbols.txt"),'r').read().splitlines()[1:]
LNC_SYMBOLS = open(path.join(DATA_PATH,"approved_lncRNAs.txt"),'r').read().splitlines() # no symbol column name
TF_SYMBOLS = open(path.join(DATA_PATH,"approved_tf.txt"),'r').read().splitlines()
LR_SYMBOLS = open(path.join(DATA_PATH,"approved_lr.txt"),'r').read().splitlines()
# 6 times faters than pd.read_csv; [1:] to omit the first row of "Symbol"

PROJ_META = json.load(open(path.join(DATA_PATH,"projectmeta.json"),'r'))

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


DS_VALIDATION = defaultdict(lambda x: "Invalid Geneset",json.load(open(path.join(DATA_PATH,"dataset_validation.json"),'r')))

# PROJ_QC_SUMMARY = pd.read_csv("/opt/megaseq-data/SurvivalGenie2_Dash/data/summary.txt",sep='\t')
# ICC_QC_SUMMARY = pd.read_csv("/opt/megaseq-data/SurvivalGenie2_Dash/data/icc_summary.tsv",sep='\t')

BUILTIN_GENE_SET = json.load(open(path.join(DATA_PATH,"genesets.json"),'r'))

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