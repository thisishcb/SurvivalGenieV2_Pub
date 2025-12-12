df_boxplot <- function(df,ds){
    df |> dplyr::select(group, gx) |> dplyr::mutate(dataset=ds)
}


df_waterfal <- function(df,ds){
    
}

plotly2json <- function(p, even_safer = T) {
    plotly:::plotly_json(plotly::plotly_build(p)$x[c("data","layout","config")], F, F) |>
    str_replace_all(fixed('transparent'), '#ffffff') |>
    str_replace_all(fixed(',"frame":null'), '') |>
    str_replace_all(fixed('"family":"",'), '') |>
    str_replace_all(fixed(',"linetype":[]'), '') |>
    str_replace_all(fixed(',"linetype":'), ',"dash":')
}

merge_df <- function(input_df, analysis_type){
    dfs <- vector("list", length = length(input_df))
    names(dfs) <- names(input_df)
    for (df_name in names(input_df)){
        df = input_df[[df_name]]
        sub_df = df |> dplyr::select(submitter_id, group, gx, os)
        sub_df$`SurvTime(Months)` <- sub_df$os[,1]
        sub_df$`Event` <- ifelse(sub_df$os[,2] == 1, TRUE, FALSE)
        sub_df = sub_df |> dplyr::select(-os)
        # sub_df$tab = df_name
        dfs[[df_name]] <- sub_df
    }
    merged_df <- dplyr::bind_rows(dfs, .id = "tab")
    if (analysis_type %in% c("single_gene", "multi_sg")) {
        names(merged_df) <- c("tab", "ID", "group", "log(FPKM+1)", "SurvTime(Months)", "Event")
    } else { # c("cluster_marker", "wgcna_module", "grn_module")
        names(merged_df) <- c( "tab", "ID", "group", "score", "SurvTime(Months)", "Event")
    }
    return(merged_df)
}
