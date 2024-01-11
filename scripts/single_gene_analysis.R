suppressPackageStartupMessages(library("optparse"))

# Rscript ./test_scripts/single_gene_analysis.R -A single_gene --genes "TP53" --datasets "TCGA-ACC TCGA-LGG" --tumor_type primary -S overall --group_method median

TEST = FALSE
# ====================================
#            Input Parsing 
# ====================================
valid.run.parameters <- c( "analysis_type", "genes", "datasets", "tumor_type", "survival", "group_method")

option_list <- list(
    make_option("--session_id", default="tmp",
        help = "session_id to write results to."),
    make_option(c("-A", "--analysis_type"), type="character",
        help="Analysis Type [SingleGene, GeneSet, ...]",
        metavar="number"),
    make_option("--genes", default="",
        help = "Genes Symbols for single gene or geneset Analysis"),
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
args <- parse_args(parser, positional_arguments=TRUE)
# print(args)
# args
# test error message capturing
# write(paste("[IT002] cell proportions estimated for", "TCGA-ACC", "\n"),
#     stderr())
# write(paste("[IT003] cell proportions estimated for", "HAHAHAHA", "\n"),
#     stderr())
# write(paste("fdgadfgasfgasdg", "TCGA-ACC", "\n"),
#     stderr())
# write(paste("dfgzfgzsdgdf", "HAHAHAHA", "\n"),
#     stderr())
# stop()
#print(arguments)

suppressPackageStartupMessages(library("data.table"))
suppressPackageStartupMessages(library("matrixStats"))
suppressPackageStartupMessages(library("survival"))

if (TEST){
    args = list(
    options = list(
        session_id="tmp",
        analysis_type="SingleGene",
        genes="TP53",
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


FILE_DIR = "SurvivalGenie/data"
FPKM_DIR = "GDC_FPKM"
MAF_DIR = "GDC_MAF"
ICC_DIR = "CIBERSOFT"
TARGET_DIR = "TARGET_EXCEL_CLINICAL"

SCRIPT_PATH = "functions"

# ====================================
#            Analysis
# ====================================


setwd(args$options$wd)
source(paste(SCRIPT_PATH,"find_cutp.R",sep="/"))
source(paste(SCRIPT_PATH,"filter_ages.R",sep="/"))

sig_genes <-  unlist(strsplit(x = args$options$genes, split = '\\s+' ))
sig_genes <- toupper(sig_genes)

if(length(sig_genes) == 0){
    stop()
}

gene_datasets <- unlist(strsplit(x = args$options$datasets, split = '\\s+' ))
if(length(gene_datasets)>5){
    write("[IT001] Only first five dataset selections will be used.\n", stderr())
}

num_ds = min(length(gene_datasets), 5)
gene_datasets <- gene_datasets[1:num_ds]
cutp_vec <- rep("", length(gene_datasets))
names(cutp_vec) <- gene_datasets[1:num_ds]

lrpval <- vector("list",length=num_ds)
names(lrpval) <- gene_datasets
scores_df <- vector("list",length=num_ds)
names(scores_df) <- gene_datasets
input_df <- vector("list",length=num_ds)
names(input_df) <- gene_datasets
km_models <- vector("list",length=num_ds)
names(km_models) <- gene_datasets


cox.tbl = data.frame(matrix(vector(), num_ds+2, 10,
        dimnames=list(c(),c("Dataset", "HR_Ratio","HR_CI_low", "HR_CI_high", "nlow", "nhigh", "HR", "HR_Pvalue", "Cut_Point", "LR_Pvalue"))))

res <-c("Dataset", "HR", "HR", "HR", "nLow", "nHigh", "HR", "HR", "Point", "LR")
cox.tbl[1,] <- res
res <-c("", "Ratio", "CI-lower", "CI-upper", "Cases", "Cases", "(95% CI)", "Pvalue", "Cut", "Pvalue")
cox.tbl[2,] <- res

for(i in 1:num_ds){ ## allow upto five datasets

    expFile <- paste0(gene_datasets[i], "_", "FPKM", ".txt")
    readEXPFile <- paste(FILE_DIR, FPKM_DIR, args$options$tumor_type, expFile, sep='/')
    if(!file.exists(readEXPFile)){
        write(paste("[IT002] No genomics data for", gene_datasets[i], "\n"),
            stderr())
        stop()
    }
    fpkm <- data.table::fread(readEXPFile, sep="\t", stringsAsFactors = FALSE)
    colnames(fpkm)[2] <- "symbol"

    if(toupper(args$options$survival) == "OVERALL"){
        osFile <- paste0(gene_datasets[i], "_", "clinical_OS", ".txt")
        readOSFile <- paste(FILE_DIR, FPKM_DIR, args$options$tumor_type, osFile, sep='/')
        if(!file.exists(readOSFile)){
            write(paste("[IT002] No clinical survival data for", gene_datasets[i], "\n"),
                stderr())
            stop()
        }
        outcome <-  read.table(readOSFile, header=T, sep="\t")
        colnames(outcome)[2] <- "sample"

        samples = subset(outcome, !is.na(outcome$Overall.Survival.Time.in.Days) & !is.na(outcome$Vital.Status))
        samples = subset(samples, samples$Vital.Status == "Alive" | samples$Vital.Status == "Dead")
        rownames(samples) <- samples$sample

        if(length(unique(factor(samples$Vital.Status)))<2 | nrow(samples)<20){
            write(paste0("[IT003] Not enough events for survival analysis in dataset", gene_datasets[i], "\n"),
                stderr())
            stop()
        }

    } else {

        osFile <- paste0(gene_datasets[i], "_", "clinical_OS", ".txt")
        readOSFile <- paste(FILE_DIR, TARGET_DIR, osFile, sep='/')
        if(!file.exists( readOSFile)){
            write(paste("[IT002] No clinical survival data for", gene_datasets[i], "\n"),
                stderr())
            stop()
        }

        outcome <-  read.table(readOSFile, header=T, sep="\t")
        colnames(outcome)[2] <- "sample"

        samples = subset(outcome, !is.na(outcome$Event.Free.Survival.Time.in.Days) & !is.na(outcome$First.Event))
        samples$First.Event <- as.character(samples$First.Event)
        samples$Event.Status = "Event"
        samples$Event.Status[samples$First.Event=="None" & samples$Vital.Status=="Alive"] <- "NoEvent"
        samples$Event.Status[samples$First.Event=="Censored"  & samples$Vital.Status=="Alive"] <- "NoEvent"
        rownames(samples) <- samples$sampleR

        if(length(unique(factor(samples$Event.Status)))<2 | nrow(samples)<20){
            write(paste0("[IT003] Not enough events for survival analysis in dataset", gene_datasets[i], "\n"),
                stderr())
            stop()
        }

    }

    fpkm$symbol <- toupper(fpkm$symbol)
    gene_fpkm <- fpkm[fpkm$symbol %in% sig_genes, ]
    dt <- data.table(gene_fpkm)
    cases = intersect(names(dt),samples$sample)
    if (toupper(args$options$case_age_group) != "ALL") {
        cases = intersect(cases, filter_ages(gene_datasets[i],args$options$case_age_group))
        if (length(cases)<20){
            write(paste0("[IT003] Not enough ",args$options$case_age_group, " samples for survival analysis in dataset ", gene_datasets[i], "\n"),
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
        write(paste0("[IT004] Gene not found or has no expression in ", gene_datasets[i], "!\n"),
            stderr())
        stop()
    }

    if(nrow(gx)>1){
        max_index <- which.max(rowVars(gx))
        scores <- as.matrix(gx[max_index, ])
        colnames(scores) <- "gx"
    } else {
        scores <- t(gx)
        colnames(scores) <- "gx"
    }

    ##Get the cut-point for each disease GSVA score
    if(tolower(args$options$group_method) == "cutp"){
        # if(update$checkgroup_cutp == "FALSE"){
        #     shinyalert("Please check Yes to proceed!", "", type="error")
        #     stop()
        # }

        #samples common to both clinical and immmune cell proportion
        subset_tils_cli <- merge(samples, scores, by="row.names", sort=FALSE)
        end <- grep("gx", colnames(subset_tils_cli))
        f <- opt_cutp(subset_tils_cli, end, type=args$options$survival)

        low_cpi <- signif(as.numeric(f),3)
        high_cpi <- signif(as.numeric(f),3)

        #identify samples within each low and high cut-points
        los = rownames(scores)[scores <= low_cpi]
        his = rownames(scores)[scores > high_cpi]
        scores <- data.frame(rownames(scores),scores)
        colnames(scores) <- c("sample","gx")
        scores$group[scores$sample %in% los] = "Low"
        scores$group[scores$sample %in% his] = "High"
        #samples common to both clinical and immmune cell proportion
        subset_tils_cli <- merge(samples, scores, by="sample", sort=FALSE)

        cpi <- c(low_cpi, high_cpi)

    } else if (tolower(args$options$group_method) == "percentile"){
        f <- std_cutp(scores, "percentile", as.numeric(args$options$upper_per)/100, as.numeric(args$options$lower_per)/100)

        low_cpi <- signif(as.numeric(f[[1]]),3)
        high_cpi <- signif(as.numeric(f[[2]]),3)
        # write(paste(c(low_cpi, high_cpi)), stderr())
        #identify samples within each low and high cut-points
        los = rownames(scores)[scores <= low_cpi]
        his = rownames(scores)[scores > high_cpi]
        scores <- data.frame(rownames(scores),scores)
        colnames(scores) <- c("sample","gx")
        scores$group[scores$sample %in% los] = "Low"
        scores$group[scores$sample %in% his] = "High"
        scores <- subset(scores, scores$group=="Low" | scores$group=="High")
        #samples common to both clinical and immmune cell proportion
        subset_tils_cli <- merge(samples, scores, by="sample", sort=FALSE)
        # write(paste(dim(subset_tils_cli)), stderr())
        cpi <- c(low_cpi, high_cpi)
    } else {
        # args$options$group_method %in% c("mean","median")
        f <- std_cutp(scores, args$options$group_method, NA, NA)

        low_cpi <- signif(as.numeric(f[[1]]),3)
        high_cpi <- signif(as.numeric(f[[1]]),3)

        #identify samples within each low and high cut-points
        los = rownames(scores)[scores <= low_cpi]
        his = rownames(scores)[scores > high_cpi]
        scores <- data.frame(rownames(scores),scores)
        colnames(scores) <- c("sample","gx")
        scores$group[scores$sample %in% los] = "Low"
        scores$group[scores$sample %in% his] = "High"
        #samples common to both clinical and immmune cell proportion
        subset_tils_cli <- merge(samples, scores, by="sample", sort=FALSE)

        cpi <- c(low_cpi, high_cpi)
    }

    cutp_vec[i] <- cpi
    

    if(toupper(args$options$survival) =="OVERALL"){
        subset_tils_cli$Overall.Survival.Time.in.Months = (subset_tils_cli$Overall.Survival.Time.in.Days)/30.42
        subset_tils_cli$os = Surv(time=subset_tils_cli$Overall.Survival.Time.in.Months, event=subset_tils_cli$Vital.Status=="Dead")
    } else {
        subset_tils_cli$Event.Free.Survival.Time.in.Months = (subset_tils_cli$Event.Free.Survival.Time.in.Days)/30.42
        subset_tils_cli$os = Surv(time=subset_tils_cli$Event.Free.Survival.Time.in.Months, event=subset_tils_cli$Event.Status=="Event")
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

    res <-c(as.character(gene_datasets[i]), HR.ratio, HR.confint.lower, HR.confint.upper, nlow, nhigh, HR, hrpval, paste0(low_cpi,",", high_cpi), lr_pval)
    cox.tbl[2+i,] <- res
    rownames(cox.tbl)[2+i] <- as.character(gene_datasets[i])

    input_df[[i]] <- subset_tils_cli
}

cox.dt <- data.table(cox.tbl)
cox.dt <- cox.dt[order(-cox.dt$HR_Ratio, cox.dt$HR_Pvalue)]
cox.dt.df <- data.frame(cox.dt)


# ------outputs/ variables for the following visualization------
return_data=list(scores_df=scores_df, cpi=cutp_vec, input_df=input_df, lrpval=lrpval, cox.tbl=cox.dt.df, n=num_ds, gene_datasets=gene_datasets)
# km_models

# ====================================
#            Visualization
# ====================================
suppressPackageStartupMessages(library("ggplot2"))
suppressPackageStartupMessages(library("stringr"))
# plotly2json <- function(p, ...) {
#   plotly:::to_JSON(plotly::plotly_build(p), ...)
# }

plotly2json <- function(p, even_safer = T) {
    plotly:::plotly_json(plotly::plotly_build(p)$x[c("data","layout","config")], F, F) |>
    str_replace_all(fixed('transparent'), '#ffffff') |>
    str_replace_all(fixed(',"frame":null'), '') |>
    str_replace_all(fixed('"family":"",'), '') |>
    str_replace_all(fixed(',"linetype":[]'), '') |>
    str_replace_all(fixed(',"linetype":'), ',"dash":')
}



source(paste(SCRIPT_PATH,"waterfallplot.R",sep="/"))
source(paste(SCRIPT_PATH,"generate_boxplot.R",sep="/"))
source(paste(SCRIPT_PATH,"palattes.R",sep="/")) # COL_GROUPS, cbPalette

figures <- vector("list",length=num_ds+3)
names(figures) <- c(gene_datasets,"analysis_type","hrplot", "forestplot")
figures$analysis_type = args$options$analysis_type
## ===== expression in groups =====
## plot per group
for (ds in gene_datasets){
    ds_figure = vector("list",length=4)
    names(ds_figure) = c("boxplot","waterfall","kmplot","signature_corr")

    ds_figure[["waterfall"]] = (waterfallplot(scores_df[[ds]],ds,"Log2(FPKM+1) Expression",COL_GROUPS) + theme_classic()) |> plotly2json()
    ds_figure[["boxplot"]] = (generate_boxplot_gg(scores_df[[ds]],ds,label="Log2(FPKM+1) Expression",COL_GROUPS) + theme_classic()) |> plotly2json()

    ## -------------- km-plot --------------
    kmplot <- survminer::ggsurvplot(km_models[[ds]],
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
    gx_scores <- scores_df[[ds]][,c("sample", "gx")]
    colnames(gx_scores) <- c("sample", ds)
    
    iccFile <- paste0("cibersoft_results_", ds, "_", args$options$tils, ".txt")
    readICCFile <- paste(FILE_DIR, ICC_DIR, args$options$tumor_type, iccFile, sep='/')
    if(!file.exists(readICCFile)){
        write(paste("[IT002] cell proportions estimated for", gene_datasets[i], "\n"),
            stderr())
        stop()
    } 
    icc <- read.table(readICCFile, sep="\t", row.names=1)
    icc$sample <- rownames(icc)
    suppressWarnings({
    #subset samples by CIBERSOFT p-value <=0.05
        if(args$options$tils_pval == "True"){
            icc_sig <- subset(icc, icc$P.value<=0.05)
        } else {
            icc_sig <- icc
        }

        if(args$options$tils == "LM22"){
            end = 22+1
        } else {
            end = 6+1
        }
        
        icc_sig_subset <- merge(icc_sig, gx_scores, by="sample", sort=FALSE)
        
        x <- as.matrix(icc_sig_subset[,ds]) #GX
        y <- as.matrix(icc_sig_subset[,c(2:end)]) #cell prop
        cor.coef <- cor(x, y)
        cor.coef[is.na(cor.coef)] <- 0
        
        icc_sig_subset <- cbind(x, y) #combined matrix for p-value
        p.coef <- corrplot::cor.mtest(icc_sig_subset)
        p.coef_p <- p.coef$p[1,-1]
        p.coef_p[is.na(p.coef_p)] <- 1
        p <- rbind(cor.coef, p.coef_p)
        rownames(p) <- c(ds, "pvalue")
        tp <- data.frame(t(p))
        tp$cell <- rownames(tp)
        dm <- melt(tp, id.vars=c("cell", "pvalue"))
        
        dm$shape <- "1"
        dm$shape[dm$pvalue<=0.05] = "22"
        
        dm$size = 1
        dm$size[dm$pvalue<=0.05] = 1.4
        
        dm <- dm |>
        dplyr::arrange(desc(pvalue)) |>
        dplyr::mutate(text = paste0("Cell Type: ", cell, "\n",
                                "Correlation: ", value, "\n",
                                "P-value: ", pvalue))
        
        dm$cell <- factor(dm$cell, levels = dm$cell)
        
        cp <- ggplot(dm, aes(x=cell, y=variable, text=text, fill=value, color=value)) +
            geom_point(aes(shape=factor(shape)), size=6, show.legend = TRUE) +
            scale_colour_gradient2(name = paste0("Correlation-", "\n", "coefficient"),
                                low=COL_GROUPS["Low"], high=COL_GROUPS["High"],
                                mid="grey", midpoint = 0,
                                guide = 'legend') +
            guides(color = guide_colorbar(reverse=FALSE)) + 
            scale_fill_gradient2(name = paste0("Correlation-", "\n", "coefficient"),
                                low=COL_GROUPS["Low"], high=COL_GROUPS["High"],
                                mid="grey", midpoint = 0,
                                guide = 'legend') +
            guides(fill=guide_colorbar(reverse=FALSE)) +  
            scale_shape_manual(name = 'P-value',
                            values = c(1,22),
                            breaks = c("1","22"),
                            labels = c('<=0.05','>0.05'),
                            guide = 'legend') +
            ylab("") + xlab("") + coord_flip() + theme_classic()
            # 
    }) #supressWarnings
        # + theme(plot.margin = unit(c(2,10,2,12),"pt"))
    ds_figure[["signature_corr"]] = cp |> plotly2json()

    figures[[ds]] <- ds_figure
}

# ----------------- hr_plot -------------------
suppressWarnings({
dfp <- cox.tbl[-c(1:2),c(1,2,7,8)]
x_vec <- as.vector(dfp$HR_Ratio)
y_vec <- as.vector(dfp$HR_Pvalue)
x_vec <- as.numeric(x_vec)
y_vec <- as.numeric(y_vec)

dfp$x_vec <- x_vec
dfp$y_vec <- y_vec

dfp$sig <- "p>0.05"
dfp$sig[dfp$y_vec<=0.05 & dfp$x_vec>1.0]="Adv"
dfp$sig[dfp$y_vec<=0.05 & dfp$x_vec<=1.0]="Fav"
dfp$y_vec <- -log(dfp$y_vec,10)
dfp$HR = paste0(dfp$Dataset, "\n", dfp$HR, "\n", "p=", dfp$HR_Pvalue)
bp <- ggplot(data=dfp,  aes(x=x_vec, y=y_vec, colour=factor(sig), text=HR)) + 
    geom_point(size=2) + 
    scale_color_manual(values=c("Adv"=COL_GROUPS[["High"]],  "Fav"=COL_GROUPS[["Low"]], "p>0.05"="grey"), name = "") +
    geom_text(aes(label=Dataset),hjust=0, vjust=0, size = 4, fontface="bold", show.legend = FALSE) + 
    theme_classic() + 
    ylab("-Log10(HR P-value)") + 
    xlab("HR Ratio") + 
    xlim(0, max(x_vec)+1.0) + 
    guides(fill=guide_legend(title="")) + 
    geom_vline(xintercept = 1, color="grey40", lty=4) + 
    geom_hline(yintercept = 1.30103, color="grey40", lty=3)
}) #supressWarnings
figures[["hrplot"]] <- bp |> plotly2json()


## -------------------- forest plot ---------------------

figures[["forestplot"]] <- cox.tbl |> jsonlite::toJSON()


figures |> jsonlite::toJSON() |> write(paste0(args$options$out_dir,'/',args$options$session_id,"_visualization.json"))

write("[SUCCESS] Pipeline Finished [SSECCUS]",stderr())
quit(save = "no", status = 0)