df_boxplot <- function(df,ds){
    df |> dplyr::select(group, gx) |> dplyr::mutate(dataset=ds)
}


df_waterfal <- function(df,ds){
    
}