celltype_name_mapping <- list(ori = c("B.cells.naive", "B.cells.memory", "Plasma.cells", "T.cells.CD8", "T.cells.CD4.naive", "T.cells.CD4.memory.resting", "T.cells.CD4.memory.activated", "T.cells.follicular.helper", "T.cells.regulatory..Tregs.", "T.cells.gamma.delta", "NK.cells.resting", "NK.cells.activated", "Monocytes", "Macrophages.M0", "Macrophages.M1", "Macrophages.M2", "Dendritic.cells.resting", "Dendritic.cells.activated", "Mast.cells.resting", "Mast.cells.activated", "Eosinophils", "Neutrophils", "B.cells", "CD8.T.cells", "CD4.T.cells", "NK.cells"), target = c("Naive B Cells", "Memory B Cells", "Plasma Cells", "CD8+ T Cells", "CD4+ Naive T Cells", "Resting Memory T Cells", "Activated Memory T Cells", "Follicular Helper T Cells", "Regulatory T Cells", "gamma-delta T Cells", "Resting Natural Killer Cells", "Activated Natural Killer Cells", "Monocytes", "M0 Macrophages", "M1 Macrophages", "M2 Macrophages", "Resting Dendritic Cells", "Activated Dendritic Cells", "Resting Mast Cells", "Activated Mast Cells", "Eosinophils", "Neutrophils", "B Cells", "CD8+ T Cells", "CD4+ (Helper) T Cells", "Natural Killer Cells")) # loaded form data/cell_names.tsv

corr_tils_sep <- function(corr_score_df, ds_proj, ds_wp, tils_pval_filter, til_set, tumor_type, FILE_DIR, ICC_DIR){
    # ds_proj: ds_proj name
    # ds_wp: short name, with parameters 
    iccFile <- paste0(ds_proj, "_CIBERSORT_", til_set, ".txt")
    readICCFile <- paste(FILE_DIR, ICC_DIR, tumor_type, iccFile, sep='/')
    if(!file.exists(readICCFile)){
        write(paste("[IT002] cell proportions estimated for", ds_proj, "is missing\n"),
            stderr())
        stop()
    } 
    icc <- read.table(readICCFile, sep="\t", row.names=1)
    icc$sample_val <- make.names(rownames(icc))
    corr_score_df$sample_val <- make.names(corr_score_df$sample)
    #subset samples by CIBERSOFT p-value <=0.05
    if(tils_pval_filter == "True"){
        icc_sig <- subset(icc, icc$P.value<=0.05)
    } else {
        icc_sig <- icc
    }

    if(til_set == "LM22"){
        end = 22+1
    } else {
        end = 6+1
    }

    icc_sig_subset <- merge(icc_sig, corr_score_df, by="sample_val", sort=FALSE)

    x <- as.matrix(icc_sig_subset[,ds_wp]) #GX
    y <- as.matrix(icc_sig_subset[,c(2:end)]) #cell prop
    cor.coef <- cor(x, y)
    cor.coef[is.na(cor.coef)] <- 0

    icc_sig_subset <- cbind(x, y) #combined matrix for p-value
    p.coef <- corrplot::cor.mtest(icc_sig_subset)
    p.coef_p <- p.coef$p[1,-1]
    p.coef_p[is.na(p.coef_p)] <- 1
    p <- rbind(cor.coef, p.coef_p)
    rownames(p) <- c(ds_wp, "pvalue")
    tp <- data.frame(t(p))
    tp$cell <- rownames(tp)
    dm <- tidyr::pivot_longer(tp, cols=-c("cell", "pvalue"), names_to ="variable")

    dm$shape <- "1"
    dm$shape[dm$pvalue<=0.05] = "22"

    dm$size = 1
    dm$size[dm$pvalue<=0.05] = 1.4

    dm <- dm |>
    dplyr::arrange(desc(pvalue)) |>
    dplyr::mutate(text = paste0("Cell Type: ", cell, "\n",
                            "Correlation: ", value, "\n",
                            "P-value: ", pvalue))

    dm$cell_name = plyr::mapvalues(dm$cell, from = celltype_name_mapping$ori, to =  celltype_name_mapping$target)
    dm$cell_name <- factor(dm$cell_name, levels = dm$cell_name)

    cp <- ggplot(dm, aes(x=cell_name, y=variable, text=text, fill=value, color=value)) +
        geom_point(aes(shape=factor(shape), 
                            text=paste0("Cell Type: ", cell_name, "<br>Variable: ", variable, "<br>Correlation: ", round(value, 6), "<br>P-value: ", round(pvalue, 6))),
                    size=6, show.legend = TRUE) +
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
    return(cp)
}


corr_tils_coll <- function(corr_score_df, ds_proj, num_cls, tils_pval_filter, til_set, tumor_type, FILE_DIR, ICC_DIR){

    iccFile <- paste0(ds_proj, "_CIBERSORT_", til_set, ".txt")
    readICCFile <- paste(FILE_DIR, ICC_DIR, tumor_type, iccFile, sep='/')
    if(!file.exists(readICCFile)){
        write(paste("[IT002] cell proportions estimated for", ds_proj, "is missing\n"),
            stderr())
        stop()
    } 
    icc <- read.table(readICCFile, sep="\t", row.names=1)
    icc$sample_val <- make.names(rownames(icc))
    corr_score_df$sample_val <- make.names(corr_score_df$sample)
    #subset samples by CIBERSOFT p-value <=0.05
    if(tils_pval_filter == "True"){
        icc_sig <- subset(icc, icc$P.value<=0.05)
    } else {
        icc_sig <- icc
    }

    if(til_set == "LM22"){
        end = 22+2
    } else {
        end = 6+2
    }

    icc_sig_subset <- merge(icc_sig, corr_score_df, by="sample_val", sort=FALSE)
    sample_index = dim(icc_sig)[[2]]+2

    x <- as.matrix(icc_sig_subset[,c(sample_index:ncol(icc_sig_subset))]) #GX
    y <- as.matrix(icc_sig_subset[,c(2:(end-1))]) #cell prop
    cor.coef <- cor(x, y)
    cor.coef[is.na(cor.coef)] <- 0

    icc_sig_subset <- cbind(x, y) #combined matrix for p-value
    p.coef <- corrplot::cor.mtest(icc_sig_subset)
    p.coef_p <- p.coef$p[1:num_cls,-c(1:num_cls)]
    p.coef_p[is.na(p.coef_p)] <- 1

    if (num_cls==1) {
        p <- rbind(cor.coef, p.coef_p)
        rownames(p) <- c(names(corr_score_df)[2], "pvalue")
        tp <- data.frame(t(p))
        tp$cell <- rownames(tp)
        dm <- reshape2::melt(tp, id.vars=c("cell", "pvalue"))
    } else {
        colnames(p.coef_p) <- colnames(cor.coef)
        rownames(p.coef_p) <- rownames(cor.coef)

        dm_coef <- reshape2::melt(cor.coef)
        colnames(dm_coef)[3] <- "value"
        dm_coef_p <- reshape2::melt(p.coef_p)
        colnames(dm_coef_p)[3] <- "pvalue"
        
        dm <- merge(dm_coef, dm_coef_p, by=c("Var1", "Var2"))
        colnames(dm)[1] <- "variable"
        colnames(dm)[2] <- "cell"
    }

    dm$shape <- "1"
    dm$shape[dm$pvalue<=0.05] = "22"

    dm$size = 1
    dm$size[dm$pvalue<=0.05] = 1.4

    dm$cell_name = plyr::mapvalues(dm$cell, from = celltype_name_mapping$ori, to =  celltype_name_mapping$target)
    cellorder <- dm |> dplyr::group_by(cell_name) |> dplyr::summarize(sigcount = sum(pvalue<=0.05), meanp= mean(pvalue)) |> dplyr::arrange(sigcount,desc(meanp)) |> dplyr::pull(cell_name)
    dm$cell_name <- factor(dm$cell_name,levels = cellorder)
    dm <- dm |>
        dplyr::arrange(cell_name) |>
        dplyr::mutate(text = paste0("Cell Type: ", cell_name, "\n",
                                "Correlation: ", value, "\n",
                                "P-value: ", pvalue))


    cp <- ggplot(dm, aes(x=cell_name, y=variable, text=text, fill=value, color=value)) +
        geom_point(aes(shape=factor(shape), 
                            text=paste0("Cell Type: ", cell_name, "<br>Variable: ", variable, "<br>Correlation: ", round(value, 6), "<br>P-value: ", round(pvalue, 6))),
                        size=6, show.legend = TRUE,
                ) +
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
    return(cp)
}
