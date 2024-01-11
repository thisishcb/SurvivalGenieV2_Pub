import pandas as pd
import numpy as np


df = pd.read_csv("data/CellChatDB_L-R.csv")


genes = list(set(
    list(df.Ligand) +
    list(df["Receptor 1"]) +
    list(df["Receptor 2"]) +
    list(df["Receptor 3"]) +
    list(df["Receptor 4"])
    ))# 965

valgenes  = [g for g in genes if g==g] # remove nan # 964

GENE_SYMBOLS = open("data/approved_symbols.txt",'r').read().splitlines()[1:]

vvv = list(set(GENE_SYMBOLS) &  set(valgenes)) # 923

with open("data/approved_lr.txt","w") as f:
    for g in vvv:
        f.write(f"{g}\n")

# # https://github.com/aertslab/pySCENIC/blob/master/resources/hs_hgnc_tfs.txt
# df = pd.read_csv("data/hs_hgnc_tfs.txt")

valgenes  = open("data/hs_hgnc_tfs.txt",'r').read().splitlines() # 1839

GENE_SYMBOLS = open("data/approved_symbols.txt",'r').read().splitlines()[1:] 

vvv = list(set(GENE_SYMBOLS) &  set(valgenes)) # 1823

with open("data/approved_tf.txt","w") as f:
    for g in vvv:
        f.write(f"{g}\n")
