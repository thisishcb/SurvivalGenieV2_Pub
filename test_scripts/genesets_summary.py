import json
import pandas as pd
import os
from pathlib import Path


# PROJ_META = json.load(open("/opt/megaseq-data/SurvivalGenie2_Dash/test_scripts/session_outputs_tmp/projectmeta.json",'r'))

# PROJECTS = tuple(PROJ_META.keys())

# iccpath = "/labs/bhasinlab/Shiny_Test/SurvivalGenie/data/CIBERSOFT"

FILE_DIR = "./"

DS_PATH = Path("data/SIG_SETS")

def searching_all_files(directory: Path):   
    file_list = [] # A list for storing files existing in directories

    for x in directory.iterdir():
        if x.is_file():

           file_list.append(x)
        else:

           file_list.append(searching_all_files(directory/x))

    return file_list

def get_genes(dir: Path):
    with open(dir, 'r') as f:
        lines  = f.read().strip().split()
    return lines

genesets = {i.stem:get_genes(i) for i in searching_all_files(DS_PATH)}


print(min([len(genesets[i]) for i in genesets]))
[i for i in genesets if len(genesets[i])==1]

print(max([len(genesets[i]) for i in genesets]))

with open("data/genesets.json", "w") as f:
   json.dump(genesets, f)
