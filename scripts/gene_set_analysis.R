suppressPackageStartupMessages(library("optparse"))

# Rscript ./test_scripts/gene_set_analysis.R -A single_gene --gene_set Cytotoxic --genes "GZMK GZMA CD8A CD8B KLRB1 KLRD1" --datasets "TCGA-ACC TCGA-LGG" --tumor_type primary -S overall --group_method median

TEST = F
# ====================================
#            Input Parsing 
# ====================================
valid.run.parameters <- c( "analysis_type", "genes", "datasets", "tumor_type", "survival", "group_method")

option_list <- list(
    make_option("--session_id", default="tm_gs",
        help = "session_id to write results to."),
    make_option(c('-F',"--use_file"), type="character", default='',
        help = "whether to get parameter directly from session file",),
    make_option(c("-A", "--analysis_type"), type="character",
        help="Analysis Type [SingleGene, GeneSet, ...]",
        metavar="number"),
    make_option("--gene_set", default="",
        help = "Genes Set Name for geneset Analysis"),
    make_option("--genes", default="",
        help = "Genes Symbols for single gene (len=1), gene ratio (len=2) or geneset Analysis (len>=2)"),
    make_option("--datasets",
        help="Datasets used for the analysis"),
    make_option("--tumor_type",
        help="Tumor Type to analysis in the Dataset"),
    make_option(c("-S", "--survival"),
        help="survival analysis type [overall, event-free]"),
    make_option("--tils", default = "LM22",
        help="Signature sets [LM6 LM22]"),
    make_option("--tils_pval", default="False",
        help="Filter by pvlaue for Signature sets [True False]"),
    make_option("--group_method", default="median",
        help="Method for spliting high/low group [cutp, mean, median]"),
    make_option("--upper_per", default =50,
        help="upper bound in percentile Only used when Method is percentile [0 to 1]"),
    make_option("--lower_per", default = 50,
        help="lower bound in percentile Only used when Method is percentile [0 to 1]"),
    make_option("--case_age_group", default='ALL',
        help="case groups [ALL | Pediatric | Adult]"),
    make_option("--wd", default="./scripts",,
        help = "Working Directory"),
    make_option("--out_dir", default="session_outputs_tmp",
        help = "the output directory under working directory, create if not exist")
    )
parser <-OptionParser(option_list=option_list)
cmd_args <- parse_args(parser, positional_arguments=TRUE)
# print(args)
# args

#print(arguments)

suppressPackageStartupMessages(library("data.table"))
suppressPackageStartupMessages(library("matrixStats"))
suppressPackageStartupMessages(library("survival"))

if (TEST){
    args = list(
    options = list(
        session_id="9e7dedc9159c4e94b75654a81f6f3d27", #"tmp",
        use_file = "/opt/megaseq-data/SurvivalGenie2_Dash/test_scripts/session_outputs_tmp/9e7dedc9159c4e94b75654a81f6f3d27_visualization.json",
        analysis_type="gene_set",
        gene_set="userinput",
        genes="GZMK GZMA CD8A CD8B KLRB1 KLRD1",
        datasets="TCGA-ACC TCGA-LGG",
        tumor_type="primary",
        survival="OVERALL",
        tils="LM22",
        tils_pval="False",
        group_method="mean",
        wd="./scripts",
        case_age_group="ADULT",
        out_dir="session_outputs_tmp"),
    args = list()
    )
}

if (cmd_args$options$use_file != '') {
    paramfromf = jsonlite::read_json(cmd_args$options$use_file)
    pyparams = paramfromf[["params"]]
    args = paramfromf[["rparams"]]
} else {
    args = cmd_args
    paramfromf = list(rparams = args)
}

setwd(args$options$wd)

SCRIPT_PATH = "functions"
source(paste(SCRIPT_PATH,"paths.R",sep="/"))

# ====================================
#            Analysis
# ====================================


source(paste(SCRIPT_PATH,"load_files.R",sep="/"))
source(paste(SCRIPT_PATH,"find_cutp.R",sep="/"))
source(paste(SCRIPT_PATH,"callGSVA.R",sep="/"))
source(paste(SCRIPT_PATH,"callZSCORE.R",sep="/"))
source(paste(SCRIPT_PATH,"filter_ages.R",sep="/"))

if(tolower(args$options$gene_set) == "userinput"){ #if a signature gene set
    sig_genes <- args$options$genes
    sig_genes <- toupper(sig_genes) |> unique()
    if(length(sig_genes)<2){
        write("[IT006] Only one/None gene is provided for geneset analysis!.\n", stderr())
        stop()
    }
} else { #if a signature gene set
    #subset gx data for genes in the signature set
    readSIGFile <- paste(FILE_DIR,GENESET_DIR,paste0(args$options$gene_set, ".txt"), sep='/')
    if(!file.exists(readSIGFile)){
        write(paste("[IT002] Selected Gene Set",args$options$gene_set ,"does not exist! \n"), stderr())
        stop()
    }
    sig_list <-  read.table(readSIGFile, header=F, sep="\t")
    sig_genes <- as.character(sig_list[,1])
    sig_genes <- toupper(sig_genes) |> unique()
}

gene_datasets <- args$options$datasets
if(length(gene_datasets)>5){
    write("[IT001] Only first five dataset selections will be used.\n", stderr())
}
if(length(gene_datasets)==0){
    write("[IT001] No dataset is selected.\n", stderr())
    stop()
}

# original "showsiglist" is just for display purpose 

num_ds = min(length(gene_datasets), 5)
gene_datasets <- gene_datasets[1:num_ds]
ds_names = sapply(gene_datasets, function(x){x$short})

cutp_vec <- rep("", length(gene_datasets))
names(cutp_vec) <- ds_names
lrpval <- vector("list",length=num_ds)
names(lrpval) <- ds_names
scores_df <- vector("list",length=num_ds)
names(scores_df) <- ds_names
input_df <- vector("list",length=num_ds)
names(input_df) <- ds_names
km_models <- vector("list",length=num_ds)
names(km_models) <- ds_names


cox.tbl = data.frame(matrix(vector(), num_ds+2, 10,
        dimnames=list(c(),c("Dataset", "HR_Ratio","HR_CI_low", "HR_CI_high", "nlow", "nhigh", "HR", "HR_Pvalue", "Cut_Point", "LR_Pvalue"))))

res <-c("Dataset", "HR", "HR", "HR", "nLow", "nHigh", "HR", "HR", "Point", "LR")
cox.tbl[1,] <- res
res <-c("", "Ratio", "CI-lower", "CI-upper", "Cases", "Cases", "(95% CI)", "Pvalue", "Cut", "Pvalue")
cox.tbl[2,] <- res

for(i in 1:num_ds){ ## allow upto five datasets
    curr_dataset <- gene_datasets[[i]]
    fpkm <- load_exp(curr_dataset["dataset"], curr_dataset$tumor_type, FILE_DIR, FPKM_DIR)

    samples <- load_clios(curr_dataset$surv_type, 
        curr_dataset["dataset"], 
        curr_dataset$tumor_type, 
        FILE_DIR, FPKM_DIR, EFS_DIR)

    gene_fpkm <- fpkm[fpkm$symbol %in% sig_genes, ]
    dt <- data.table(gene_fpkm)
    #to remove duplicated ensemble gene ids
    dt$var <- rowVars(as.matrix(dt[,-c(1:2)]))
    dtt <- dt[order(dt$symbol, -dt$var), ]
    dt <- dtt[ !duplicated(dtt$symbol), ]

    cases = intersect(names(dt),samples$sample)
    if (toupper(curr_dataset$age_grp) != "ALL") {
        cases = intersect(cases, filter_ages_in_clios(samples,curr_dataset$age_grp))
        if (length(cases)<20){
            write(paste0("[IT003] Not enough ",curr_dataset$age_grp, " samples for survival analysis in dataset ", curr_dataset[["short"]], "\n"),
                stderr())
            stop()
        }
    }
    subset_fpkm <- dt[ ,cases, with=FALSE]
    #subset_fpkm <- dt[, samples$sample, with=TRUE] # this will generate error when list is not found
    symbol_order <- dt$symbol
    gx <- as.matrix(log2(subset_fpkm+1))
    rownames(gx) <- symbol_order

    if(sum(gx)==0 | nrow(gx)==0){
        write(paste0("[IT004] Gene not found or has no expression!", curr_dataset["dataset"], "\n"),
            stderr())
        stop()
    }

    #if(length(unique(sig_genes))>=3){
    if(length(sig_genes)>=3){
        scores <- callGSVA(gx, symbol_order)
        colnames(scores) <- "gx"
    } else {
        zscores <- callZSCORE(gx)
        scores <- as.matrix(zscores[,-1])
        rownames(scores) <- zscores$sample
        colnames(scores) <- "gx"
    }

    ##Get the cut-point for each disease GSVA score
    scores <- data.frame(rownames(scores),scores)
    colnames(scores) <- c("sample","gx")
    res <- sep_groups(args$options$group_method, samples, scores,
        args$options$upper_per, args$options$lower_per, curr_dataset$surv_type)
    subset_tils_cli = res[["subset_tils_cli"]]
    cpi = res[["cpi"]]

    cutp_vec[i] <- cpi
    

    if(toupper(curr_dataset$surv_type) =="OVERALL"){
        subset_tils_cli$overall_survival_time_in_months = (subset_tils_cli$overall_survival_time_in_days)/30.42
        subset_tils_cli$os = Surv(time=subset_tils_cli$overall_survival_time_in_months, event=subset_tils_cli$vital_status=="Dead")
    } else {
        subset_tils_cli$event_free_survival_time_in_months = (subset_tils_cli$event_free_survival_time_in_days)/30.42
        subset_tils_cli$os = Surv(time=subset_tils_cli$event_free_survival_time_in_months, event=subset_tils_cli$event_status=="Event")
    }

    #make low expression as the reference level
    subset_tils_cli$group = factor(subset_tils_cli$group, levels = c("Low", "High"))

    scores_df[[i]] <- subset_tils_cli

    #stratify patients by group
    cox.os = coxph(os ~ group, data=subset_tils_cli)
    km.os = survfit(os ~ group, data = subset_tils_cli, conf.type = "log-log")

    km_models[[i]] = km.os # save the model for kmplot

    nlow <- km.os$n[1]
    nhigh <- km.os$n[2]

    lrpval[i] <-signif(summary(cox.os)$sctest["pvalue"], digits=3)
    lr_pval <-signif(summary(cox.os)$sctest["pvalue"], digits=3)
    hrpval <-signif(summary(cox.os)$wald["pvalue"], digits=3)
    HR.ratio <-signif(summary(cox.os)$coefficients[2], digits=2);
    HR.confint.lower <- signif(summary(cox.os)$conf.int[3], 2)
    HR.confint.upper <- signif(summary(cox.os)$conf.int[4],2)
    HR <- paste0(HR.ratio, " (",
                    HR.confint.lower, "-", HR.confint.upper, ")")

    res <-c(as.character(curr_dataset["short"]), HR.ratio, HR.confint.lower, HR.confint.upper, nlow, nhigh, HR, hrpval, paste0(unique(cpi),collapse=','), lr_pval)
    cox.tbl[2+i,] <- res
    rownames(cox.tbl)[2+i] <- as.character(curr_dataset["short"])

    input_df[[i]] <- subset_tils_cli
}

cox.dt <- data.table(cox.tbl)
cox.dt <- cox.dt[order(-cox.dt$HR_Ratio, cox.dt$HR_Pvalue)]
cox.dt.df <- data.frame(cox.dt)


# ------outputs/ variables for the following visualization------
# return_data=list(scores_df=scores_df, cpi=cutp_vec, input_df=input_df, lrpval=lrpval, cox.tbl=cox.dt.df, n=num_ds, gene_datasets=gene_datasets)
# km_models

# ====================================
#            Visualization
# ====================================
suppressPackageStartupMessages(library("ggplot2"))
suppressPackageStartupMessages(library("stringr"))
# plotly2json <- function(p, ...) {
#   plotly:::to_JSON(plotly::plotly_build(p), ...)
# }

source(paste(SCRIPT_PATH,"utils.R",sep="/"))



source(paste(SCRIPT_PATH,"waterfallplot.R",sep="/"))
source(paste(SCRIPT_PATH,"generate_boxplot.R",sep="/"))
source(paste(SCRIPT_PATH,"corr_w_tils.R",sep="/"))
source(paste(SCRIPT_PATH,"palattes.R",sep="/")) # COL_GROUPS, cbPalette
source(paste(SCRIPT_PATH,"hrplot.R",sep="/"))

figures <- vector("list",length=num_ds+3)
names(figures) <- c(ds_names,"analysis_type","hrplot", "forestplot")
figures$analysis_type = args$options$analysis_type
## ===== expression in groups =====
## plot per group
for (d in gene_datasets){
    ds = d$short
    ds_figure = vector("list",length=4)
    names(ds_figure) = c("boxplot","waterfall","kmplot","signature_corr")

    ds_figure[["waterfall"]] = (waterfallplot(scores_df[[ds]],ds,"Enrichment Score",COL_GROUPS) + theme_classic()) |> plotly::ggplotly(tooltip = "text") |> plotly2json()
    ds_figure[["boxplot"]] = (generate_boxplot_gg(scores_df[[ds]],ds,label="Enrichment Score",COL_GROUPS) + theme_classic()) |> plotly2json()

    ## -------------- km-plot --------------
    kmplot <- survminer::ggsurvplot(km_models[[ds]],
        data=input_df[[ds]],
        palette= unname(COL_GROUPS),
        xlab = "Time in Months", 
        ylab = "Survival Probability",
        pval = paste0("Logrank p=", signif(lrpval[[ds]], digits=3)),
        legend.title = "Group",
        legend.labs = c(paste0("Low (n=", km_models[[ds]]$n[1], ")"), 
                    paste0("High (n=", km_models[[ds]]$n[2], ")")),
        )$plot #+ theme(legend.position=c(.8,.8))
    ds_figure[["kmplot"]] = kmplot |> plotly2json()

    # -------------- corr with signature sets --------------
    suppressWarnings({
        gx_scores <- scores_df[[ds]][,c("sample", "gx")]
        colnames(gx_scores) <- c("sample", ds)
        cp <- corr_tils_sep(gx_scores, d$dataset, ds,
            args$options$tils_pval,
            args$options$tils, 
            d$tumor_type,
            FILE_DIR, ICC_DIR)
    }) #supressWarnings

    ds_figure[["signature_corr"]] = cp |> plotly::ggplotly(tooltip = "text") |> plotly2json()

    figures[[ds]] <- ds_figure
}

# ----------------- hr_plot -------------------
suppressWarnings({
    bp <- plot_hazard_ratio(cox.tbl, COL_GROUPS)
}) #supressWarnings
figures[["hrplot"]] <- bp |> plotly::ggplotly(tooltip = "text") |> plotly2json()


## -------------------- forest plot ---------------------

figures[["forestplot"]] <- cox.tbl |> jsonlite::toJSON()

## ------------- json for data -----------------
merged_df <- merge_df(input_df, args$options$analysis_type)
figures$dfJSON = merged_df |> jsonlite::toJSON()


figures |> jsonlite::toJSON() |> write(paste0(args$options$out_dir,'/',args$options$session_id,"_visualization.json"))

write("[SUCCESS] Pipeline Finished [SSECCUS]",stderr())
quit(save = "no", status = 0)