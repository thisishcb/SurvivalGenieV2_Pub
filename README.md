# ![SurvGenieLogo](assets/SurvGenie2Logo_page.svg) [Survival Genie V2](https://bhasinlab.bmi.emory.edu/SurvivalGenie2/home)
### by [BhasinLab](https://bhasinlab.org)
---
Survical Genie Version 2 is now available on [https://bhasinlab.bmi.emory.edu/SurvivalGenie2/home](https://bhasinlab.bmi.emory.edu/SurvivalGenie2/home)  
[Survival Genie V1](https://bhasinlab.bmi.emory.edu/SurvivalGenie) is still online.

## ⭐️ Features 
 - 🆕 Pediatric/Adult Case filter
   - You can now select whether to use only Pediatric cases or Adult cases or All cases.
   - Currently, the groups are defined by age cutoff of 20 years old at diagnosis.
 - 🆕 Result Retrieval 
   - You can access previous results with your analysis with in 24 hours!
 - 🆕 Co-expression Module Analysis
   - you can input wgcna modules (or another co-expression networks as long as the column names are compliant) for Survival Analysis in supported public datasets
   - ❓Have No Experience in Co-expression network?
     - if you are using single-cell data: https://smorabit.github.io/hdWGCNA/
     - or use our wrapped function [here](./scripts/get_wgcna_result.R) [hdWGCNA based] - tutorial see [Tutorial](#tutorial)
 - Single Gene Analysis 
   - Perform the survival analysis based on the High/Low groups partitioned by the expression profile of a single gene in supported public datasets
 - Gene-Ratio Analysis
   - Perform the survival analysis based on the High/Low groups partitioned by the expression ratio of two genes in supported public datasets
 - Gene-Ratio Analysis
   - Perform the survival analysis based on the High/Low groups partitioned by the expression ratio of two genes in supported public datasets
## Tutorial
 - Tutorial for the website (Explanation of Inputs and Outputs) is available on [SurvivalGenie2 home page](https://bhasinlab.bmi.emory.edu/SurvivalGenie2/home) or check higher resolution [figures](./static/).  

 - for [wrapped wgcna function](./scripts/get_wgcna_result.R):
```{R}
source("")
# following parameters are by default, see the script for more information and full parameters
your_seurat_obj |> get_wgcna_result(
    meta_cols = "orig.ident",
    reduction = "harmony",
    gene_select_method = "fraction",
    gene_fraction = 0.05,
    soft_power = "interactive",
    out_path = "./tmp_wgcna",
    n_threads = 8,
    save_srt_obj = TRUE,
)
```
## Updates
 - Nov 14, 2023
   - Survival Genie V2 is now online!

## Citation

Survival Genie V2 is still under review; 
for Survival Genie V1, please cite  
```Dwivedi B, Mumme H, Satpathy S, Bhasin SS, Bhasin M. Survival Genie, a web platform for survival analysis across pediatric and adult cancers. Sci Rep. 2022 Feb 23;12(1):3069. doi: 10.1038/s41598-022-06841-0. PMID: 35197510; PMCID: PMC8866543.```