suppressPackageStartupMessages(library("optparse"))

# Rscript ./test_scripts/grn_module_analysis.R -A scRNA --input_type example_data --datasets TCGA-ACC --tumor_type primary -S overall --group_method median

TEST <- FALSE
# ====================================
#            Input Parsing 
# ====================================

option_list <- list(
    make_option("--session_id", default="tmp",
        help = "session_id to write results to."),
    make_option(c('-F',"--use_file"), type="character", default='',
        help = "whether to get parameter directly from session file",),
    make_option(c("-A", "--analysis_type"), type="character",
        help="Analysis Type [scRNA, SingleGene, GeneSet, ...]",
        metavar="number"),
    make_option("--input_type", default="",
        help = "Input type [user_upload, example_data, URL]"),
    make_option("--data_path", default="",
        help = "path to the data"),
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
    make_option("--wd", default="./scripts",
        help = "Working Directory"),
    make_option("--out_dir", default="session_outputs_tmp",
        help = "the output directory under working directory, create if not exist"),
    make_option("--gene_filter", default="all",
        help = "filters apply to the input genes. [all, lnc, tf]")
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
        analysis_type="grn_module",
        input_type = 'example_data',
        datasets="TCGA-ACC",
        tumor_type="primary",
        survival="OVERALL",
        tils="LM22",
        tils_pval="False",
        group_method="mean",
        wd="./scripts",
        case_age_group="ADULT",
        out_dir="session_outputs_tmp",
        gene_filter="all"),
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

# get input data 
if(args$options$input_type == "example_data"){ #if an example gene set
    dataFile <- paste(FILE_DIR, EXAMPLE_DIR, "reducedPlasma_top_regulon.tsv",sep='/')#"../data", "module_hub_genes.csv"
    if (!file.exists( dataFile) ){
        write("[IT007] GRN file does not exist.\n", stderr())
        stop()
    }
    sig_list <-  fread(dataFile, header=T, sep="\t", stringsAsFactors = T)
} else if(args$options$input_type == "user_upload"){ #if user-uploaded

    dataFile <- args$options$data_path
    if (!file.exists( dataFile) ){
        write("[IT007] GRN does not exist.\n", stderr())
        stop()
    }

    sig_list <-  fread(dataFile, header=T, sep=",", stringsAsFactors = T)
    if (ncol(sig_list)==1){
        sig_list = fread(dataFile, header=T, stringsAsFactors = T)
    }
} else if(args$options$input_type == "URL"){ #if user-url

    dataFile <- args$options$data_path
    if(httr::HEAD(dataFile)$status_code != 200){
        write("[IT007] GRN file url cannot be loaded.\n", stderr())
        stop()
    }
    sig_list <-  read.csv(dataFile)
    if (ncol(sig_list)==1){
        sig_list = read.csv(dataFile,sep = "\t")
    }
}

colnames(sig_list) <- tolower(colnames(sig_list))
# check whether requires columns present
for (req_col in c("regulon", "gene")) {
    if(!(req_col %in% colnames(sig_list))) {
        write(paste0("[IT008] Required column [",req_col,"] is not in the file provided\n"), stderr())
        stop()
    }
}

## filter genes 
REF_DIR = "../data"
if (args$options$gene_filter == "lnc") {
    lncref = read.table(paste(REF_DIR, "approved_lncRNAs.txt", sep='/'),header=F)[["V1"]]
    sig_list <- subset(sig_list, sig_list$gene %in% lncref)
} else if (args$options$gene_filter == "tf") {
    tfref = read.table(paste(REF_DIR, "approved_tf.txt", sep='/'),header=F)[["V1"]]
    sig_list <- subset(sig_list, sig_list$gene %in% tfref)
} else if (args$options$gene_filter == "lr") {
    lrref = read.table(paste(REF_DIR, "approved_lr.txt", sep='/'),header=F)[["V1"]]
    sig_list <- subset(sig_list, sig_list$gene %in% lrref)
} else {
    ref = read.table(paste(REF_DIR, "approved_symbols.txt", sep='/'),header=F)[["V1"]]
    sig_list <- subset(sig_list, sig_list$gene %in% ref)
}


# sig_list <- subset(sig_list, sig_list$p_val_adj<=0.05) # modules without markers?
modules <- unique(as.character(sig_list$regulon))
num_mdls <- length(modules)
if(num_mdls == 0 || any(dim(sig_list) == 0)){
    write("[IT008] Module Eigen-gene are empty after applying Gene Filter.\n", stderr())
    stop()
}

if(num_mdls > 20 ){
    write("[IT001] Only first 20 modules/networks will be used.\n", stderr())
    num_mdls = 20
    modules = modules[1:20]
}

## ----------------

gene_datasets <- args$options$datasets
if(length(gene_datasets)>1){
    write("[IT001] Only first dataset selections will be used.\n", stderr())
}

ds_names = sapply(gene_datasets, function(x){x$short})
gene_datasets = gene_datasets[[1]]
ds_names = ds_names[[1]]

## =========== get the dataset ======================

fpkm <- load_exp(gene_datasets["dataset"], gene_datasets$tumor_type, FILE_DIR, FPKM_DIR)

samples <- load_clios(gene_datasets$surv_type, 
    gene_datasets["dataset"], 
    gene_datasets$tumor_type, 
    FILE_DIR, FPKM_DIR, EFS_DIR)

cases = intersect(names(fpkm),samples$sample)
if (toupper(gene_datasets$age_grp) != "ALL") {
    cases = intersect(cases, filter_ages_in_clios(samples,gene_datasets$age_grp))
    if (length(cases)<20) {
        write(paste0("[IT003] Not enough ",gene_datasets$age_grp, " samples for survival analysis in dataset ", gene_datasets[["short"]], "\n"),
                stderr())
            stop()
    }
}
## ===============  loop through each module===================


cutp_vec <- rep("", num_mdls)
names(cutp_vec) <- modules
lrpval <- vector("list",length=num_mdls)
names(lrpval) <- modules
scores_df <- vector("list",length=num_mdls)
names(scores_df) <- modules
input_df <- vector("list",length=num_mdls)
names(input_df) <- modules
km_models <- vector("list",length=num_mdls)
names(km_models) <- modules


cox.tbl = data.frame(matrix(vector(), num_mdls+2, 10,
        dimnames=list(c(),c("Dataset", "HR_Ratio","HR_CI_low", "HR_CI_high", "nlow", "nhigh", "HR", "HR_Pvalue", "Cut_Point", "LR_Pvalue"))))

res <-c("module", "HR", "HR", "HR", "nLow", "nHigh", "HR", "HR", "Point", "LR")
cox.tbl[1,] <- res
res <-c("", "Ratio", "CI-lower", "CI-upper", "Cases", "Cases", "(95% CI)", "Pvalue", "Cut", "Pvalue")
cox.tbl[2,] <- res

for(i in 1:num_mdls){ ## allow upto five datasets

    sig_genes <- as.character(sig_list$gene[sig_list$regulon==modules[i]])
    sig_genes <- toupper(sig_genes)

    # names -> ensg, GENENAME, sample_IDs
    gene_fpkm <- fpkm[fpkm$symbol %in% sig_genes, ]
    dt <- data.table(gene_fpkm)

    subset_fpkm <- dt[ ,cases, with=FALSE]
    #subset_fpkm <- dt[, samples$sample, with=TRUE] # this will generate error when list is not found
    symbol_order <- dt$symbol
    gx <- as.matrix(log2(subset_fpkm+1))
    rownames(gx) <- symbol_order

    if(sum(gx)==0 || nrow(gx)==0){
        write(paste0("[IT004] Gene not found or has no expression!", gene_datasets$short, "\n"),
            stderr())
        stop()
    }

    if(length(unique(sig_genes))>=3){
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
        args$options$upper_per, args$options$lower_per, gene_datasets$surv_type)
    subset_tils_cli = res[["subset_tils_cli"]]
    cpi = res[["cpi"]]

    cutp_vec[i] <- cpi
    

    if(toupper(gene_datasets$surv_type) =="OVERALL"){
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

    res <-c(as.character(modules[i]), HR.ratio, HR.confint.lower, HR.confint.upper, nlow, nhigh, HR, hrpval, paste0(unique(cpi),collapse=','), lr_pval)
    cox.tbl[2+i,] <- res
    rownames(cox.tbl)[2+i] <- as.character(modules[i])

    input_df[[i]] <- subset_tils_cli
}

cox.dt <- data.table(cox.tbl)
cox.dt <- cox.dt[order(-cox.dt$HR_Ratio, cox.dt$HR_Pvalue)]
cox.dt.df <- data.frame(cox.dt)


# ------outputs/ variables for the following visualization------
# return_data=list(scores_df=scores_df, cpi=cutp_vec, input_df=input_df, lrpval=lrpval, cox.tbl=cox.dt.df, n=num_mdls, gene_datasets=gene_datasets)
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

figures <- vector("list",length=num_mdls+4)
names(figures) <- c(modules,"analysis_type","hrplot", "forestplot","signature_corr")
figures$analysis_type = args$options$analysis_type
## ===== expression in groups =====
## plot per group
for (mdl in modules){
    ds_figure = vector("list",length=4)
    names(ds_figure) = c("boxplot","waterfall","kmplot")

    ds_figure[["waterfall"]] = (waterfallplot(scores_df[[mdl]],mdl,"Enrichment Score",COL_GROUPS) + theme_classic()) |> plotly::ggplotly(tooltip = "text") |> plotly2json()
    ds_figure[["boxplot"]] = (generate_boxplot_gg(scores_df[[mdl]],mdl,label="Enrichment Score",COL_GROUPS) + theme_classic()) |> plotly2json()

    ## -------------- km-plot --------------
    kmplot <- survminer::ggsurvplot(km_models[[mdl]],
        data=input_df[[mdl]],
        palette= unname(COL_GROUPS),
        xlab = "Time in Months", 
        ylab = "Survival Probability",
        pval = paste0("Logrank p=", signif(lrpval[[mdl]], digits=3)),
        legend.title = "Group",
        legend.labs = c(paste0("Low (n=", km_models[[mdl]]$n[1], ")"), 
                    paste0("High (n=", km_models[[mdl]]$n[2], ")")),
        )$plot #+ theme(legend.position=c(.8,.8))
    ds_figure[["kmplot"]] = kmplot |> plotly2json()
    figures[[mdl]] <- ds_figure
}


# -------------- corr with signature sets --------------

suppressWarnings({

    corr_score_df <- vector("list",length=length(modules))
    names(corr_score_df) = modules
    for (mdl in modules){
        gx_scores <- scores_df[[mdl]][,c("sample", "gx")]
        colnames(gx_scores) <- c("sample", mdl)
        corr_score_df[[mdl]] = gx_scores
    }
    corr_score_df <- Reduce(function(dtf1, dtf2) merge(dtf1, dtf2, by = "sample", all.x = TRUE),corr_score_df)
    cp <- corr_tils_coll(corr_score_df, gene_datasets$dataset, num_mdls,
                args$options$tils_pval,
                args$options$tils, 
                gene_datasets$tumor_type,
                FILE_DIR, ICC_DIR)

}) #supressWarnings
    # + theme(plot.margin = unit(c(2,10,2,12),"pt"))
figures[["signature_corr"]] = cp |> plotly::ggplotly(tooltip = "text") |> plotly2json()

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
