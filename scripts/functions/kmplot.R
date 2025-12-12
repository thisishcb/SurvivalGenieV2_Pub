
get_kmplot <- function(model, df, lrp, COL_GROUPS){
    kmplot <- survminer::ggsurvplot(model, # km_models[[ds]]
        data=df, # input_df[[ds]]
        censor = FALSE, # so only the lines no censor points
        palette= unname(COL_GROUPS),
        xlab = "Time in Months", 
        ylab = "Survival Probability",
        pval = paste0("Logrank p=", signif(lrp, digits=3)), #lrpval[[ds]]
        legend.title = "Group",
        legend.labs = c(paste0("Low (n=", model$n[1], ")"), 
                    paste0("High (n=", model$n[2], ")")),
        )$plot
    # kmplot$data <- kmplot$data |>
    #     dplyr::mutate(
    #         # Create the custom hover text using the glue package or paste()
    #         # You can include any variables present in p$data
    #         text = paste0("Survival: ",time,"<br>",
    #                     "ID: ",submitter_id,"<br>",
    #                     "Status: ", status))
    return(kmplot)
}
