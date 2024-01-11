import json
import pandas as pd
import os

FILE_DIR = "./"
PROJ_META = json.load(open("projectmeta.json",'r'))

PROJECTS = tuple(PROJ_META.keys())

iccpath = "data/CIBERSOFT"

tb = []
for p in PROJECTS:
    for tp in ["primary","metastatic","recurrent"]:
        for til in ["LM6", "LM22"]:
            file = os.path.join(iccpath,tp,f"cibersoft_results_{p}_{til}.txt")
            try:
                df = pd.read_csv(file, sep='\t')
                tb.append(dict(
                    Dataset=p,
                    Type = tp,
                    TILSet = til,
                    N_Total=df.shape[0],
                    N_Filter=sum(df["P-value"]<0.05),
                ))
            except FileNotFoundError:
                tb.append(dict(
                    Dataset=p,
                    Type = tp,
                    TILSet = til,
                    N_Total=0,
                    N_Filter=0,
                ))

summarytable = pd.DataFrame(tb)
summarytable.loc[:,"Valid_Total"] = summarytable["N_Total"]>=20
summarytable.loc[:,"Valid_Filter"] = summarytable["N_Filter"]>=20

summarytable.to_csv("data/icc_summary.tsv",sep="\t", index=False)

## ==============


# The counts in summary is baded on clinical os sample counts
PROJ_QC_SUMMARY = pd.read_csv("data/summary.txt",sep='\t')

ICC_SUMMARY = pd.read_csv("data/icc_summary.tsv",sep="\t")


def ttvalid(ds):
    """
    Out Structure:
    output  - Primary/M/R   -- FPKM < bool >
                            |- ICC   - LM6/LM22  - Total/Filtered
    """
    out = dict()
    for ttype in ["primary","metastatic","recurrent"]:
        tt_valid = dict(
            FPKM = None,
            ICC = None
        )
        try: 
            tt_valid["FPKM"] = bool(PROJ_QC_SUMMARY[ttype.title()][PROJ_QC_SUMMARY.Dataset==ds].values[0] >=20)
        except IndexError:
            tt_valid["FPKM"] = False

        ICC_Dict = dict()
        for tils in ["LM6", "LM22"]:
            tilres = dict(
                Total = False,
                Filtered = False,
            )
            try:  # algo anyway works for 3, no ds has 2; not working for only 1
                tilres["Total"] = bool(ICC_SUMMARY.N_Total[(ICC_SUMMARY.Dataset==ds) & (ICC_SUMMARY.Type==ttype) & (ICC_SUMMARY.TILSet==tils)].values[0] > 1)
                tilres["Filtered"] = bool(ICC_SUMMARY.N_Filter[(ICC_SUMMARY.Dataset==ds) & (ICC_SUMMARY.Type==ttype) & (ICC_SUMMARY.TILSet==tils)].values[0] > 1)
            except IndexError:
                pass
            ICC_Dict[tils] = tilres
        tt_valid["ICC"] = ICC_Dict

        out[ttype] = tt_valid
    
    return out



validsets = {ds: ttvalid(ds) for ds in PROJECTS}

with open("data/dataset_validation.json", "w") as f:
   json.dump(validsets, f)


