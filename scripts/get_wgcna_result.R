#' @name get_wgcna_result
#' @aliases get_wgcna_result
#' @title Calculate hdWGCNA result based on Seurat Object input
#' @description given a seurat object to get the WGCNA result
#' @usage get_wgcna_result(srt_obj, meta_cols, out_path, n_threads, ...)
#' @param seurat_obj  one Seurat Object
#' @param meta_cols Metadata column names to keep when creating metacells. if a vector is provided, the firest element will be used as ident for metacells. "orig.ident" by default.
#' @param reduction Reduction for the metadata construction for WGCNA analysis. "harmony" dy default. "pca" will be used if 'harmony' is not available.
#' @param gene_select_method Method to select genes when creating the WGCNA data slot; can be "variable", "fraction", "all" or "custom"
#' @param gene_fraction cell fraction cutoff to filter the genes when creating the WGCNA data slot; if 0.05, means only genes expressed in at least 5% of the cells will be used. 0.05 by default. used when `gene_select_method` is "fraction"
#' @param gene_list only used when the `gene_select_method` is "custom". NULL by default.
#' @param group_by the metadata column of interest, this should also be included in the meta_cols. if "NULL" or by default, the first element in `meta_cols` will be used.
#' @param group_name the group name of interest in the `group_by` column. if "NULL" or by dafault, the first level in the `group_by` will be used.
#' @param soft_power soft power used for wgcna analysis, value should be an integer or "interactive". If the value is "interactive", the soft power plot will be displayed and ask for value input. If "NULL", program will auto select one. "interactive" by default.
#' @param vars_to_harmonize the variable to be harmonized (regress out) when calculating the module eigen genes. If NULL or by default, the second element in `meta_cols` will be used.
#' @param out_path Path to save the intermediate output files and output files. "./tmp_wgcna" by default.
#' @param n_threads Number of parallel threads for WGCNA. "8" by default.
#' @param save_srt_obj Whether to save the seurat Object after running the pipeline. True by Default.
#' @param random_seed random seed for re-productivity. NULL by default.
#' @details This function uses "hdWGCNA" to get the WGCNA modules ......
#' @return WGCNA modules
#' @import WGCNA
#' @import hdWGCNA
#' @import dylyr
#' @import ggplot2
#' @import patchwork
#' @importFrom patchwork wrap_plots
#' @importFrom magrittr %>%
#' @examples
#' g <- 10 ## number of genes
#' s <- 30 ## number of samples
#' @seealso hdWGCNA
#' @export
get_wgcna_result <- function(
    seurat_obj,
    meta_cols = "orig.ident",
    reduction = "harmony",
    gene_select_method = "fraction",
    gene_fraction = 0.05,
    gene_list = NULL,
    group_by = NULL,
    group_name = NULL,
    vars_to_harmonize = NULL,
    soft_power = "interactive",
    out_path = "./tmp_wgcna",
    n_threads = 8,
    save_srt_obj = TRUE,
    random_seed = NULL
    ) {
    WGCNA::enableWGCNAThreads(nThreads = n_threads)
    if (! file.exists(out_path)) {
        dir.create(out_path)
    }
    set.seed(random_seed)
    seurat_obj <- hdWGCNA::SetupForWGCNA(
        seurat_obj,
        gene_select = gene_select_method, # the gene selection approach, can use only HVGs
        fraction = gene_fraction,
        features = gene_list,
        wgcna_name = "wgcna4surv"
        )
    while (! reduction %in% names(seurat_obj@reductions)) {
        if (reduction == "harmony") {
            reduction <- "pca"
        } else if (reduction == "pca") {
            seurat_obj <- Seurat::RunPCA(seurat_obj, reduction.name = "pca")
        } else {
            reduction <- "harmony"
        }
    }
    seurat_obj <- hdWGCNA::MetacellsByGroups(
        seurat_obj = seurat_obj,
        group.by = meta_cols, # specify the columns in seurat_obj@meta.data to group by
        reduction = reduction, # select the dimensionality reduction to perform KNN on
        k = 25, # nearest-neighbors parameter
        max_shared = 10, # maximum number of shared cells between two metacells
        ident.group = meta_cols[[1]] # set the Idents of the metacell seurat object
    ) # long run time
    seurat_obj <- hdWGCNA::NormalizeMetacells(seurat_obj)

    if (is.null(group_by)) {
        group_by <- meta_cols[[1]]
    }
    if (is.null(group_name)) {
        group_name <- levels(seurat_obj@meta.data[[group_by]])[[1]]
    }
    seurat_obj <- hdWGCNA::SetDatExpr(
        seurat_obj,
        group_name = group_name, # the name of the group of interest in the group.by column
        group.by = group_by, # the metadata column containing the cell type info. This same column should have also been used in MetacellsByGroups
        assay = "RNA", # using RNA assay
        slot = "data" # using normalized data
        )
    seurat_obj <- hdWGCNA::TestSoftPowers(
        seurat_obj,
        networkType = "signed" # you can also use "unsigned" or "signed hybrid"
    ) # long run time
    if (soft_power == "interactive") {
        plot_list <- hdWGCNA::PlotSoftPowers(seurat_obj)
        patchwork::wrap_plots(plot_list, ncol = 2)
        soft_power <- as.integer(readline("What is the value of soft power?\n"))
    }
    pdf(file.path(out_path, "softPowers.pdf"))
        patchwork::wrap_plots(plot_list, ncol = 2)
    dev.off()

    # check if the output diectory exists

    seurat_obj <- hdWGCNA::ConstructNetwork(
        seurat_obj, soft_power = soft_power,
        setDatExpr = FALSE,
        tom_outdir = out_path,
        tom_name = group_name
    ) ## longlong runtime
    pdf(file.path(out_path, "moduleDendrogram.pdf"))
        hdWGCNA::PlotDendrogram(seurat_obj, main = paste(group_name, "hdWGCNA Dendrogram"))
    dev.off()

    # get Eigen Genes
    seurat_obj <- Seurat::ScaleData(seurat_obj, features = Seurat::VariableFeatures(seurat_obj))
    if (is.null(vars_to_harmonize)) {
        vars_to_harmonize <- meta_cols[[2]]
    }
    seurat_obj <- hdWGCNA::ModuleEigengenes(
        seurat_obj,
        group.by.vars = vars_to_harmonize
        ) ##  insanely long
    seurat_obj <- hdWGCNA::ModuleConnectivity(
        seurat_obj,
        group.by = group_by, group_name = group_name
        )
    seurat_obj <- hdWGCNA::ResetModuleNames(
        seurat_obj,
        new_name = paste0(group_name, "-M")
        )
    ncols <- ceiling(sqrt(length(unique(seurat_obj@misc$wgcna4surv$wgcna_modules))))
    pdf(file.path(out_path, "kMEs.pdf"))
        hdWGCNA::PlotKMEs(seurat_obj, ncol = ncols)
    dev.off()
    if (save_srt_obj) {
        saveRDS(seurat_obj, file.path(out_path, "seurat_obj_after_wgcna.rds"))
    }
    # hMEs <- hdWGCNA::GetMEs(seurat_obj, seurat_obj)
    # modules <- hdWGCNA::GetModules(seurat_obj)
    hub_df <- hdWGCNA::GetHubGenes(seurat_obj, n_hubs = 25)
    set.seed(NULL)
    hub_df |> dplyr::filter(module!="grey") |> dplyr::group_by(module) |> dplyr::arrange(dplyr::desc(kME)) |> write.csv(file.path(out_path, "module_hub_genes.csv"))
    return(seurat_obj, hub_df)
}