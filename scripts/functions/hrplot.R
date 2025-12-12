plot_hazard_ratio <- function(cox.tbl, COL_GROUPS) {
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
    bp <- ggplot(data=dfp,  aes(x=x_vec, y=y_vec, colour=factor(sig), 
                text = paste0("HR Ratio: ", round(x_vec,2), "<br> -log10(HR P-value): ", round(x_vec,3), "<br>Group: ", sig, "<br>", Dataset, "<br>", "HR P-Value: ", round(as.numeric(HR_Pvalue),6)))) + 
        geom_point(size=2) + 
        scale_color_manual(values=c("Adv"=COL_GROUPS[["High"]],  "Fav"=COL_GROUPS[["Low"]], "p>0.05"="grey"), name = "") +
        geom_text(aes(label=Dataset),hjust=0, vjust=0, size = 4, fontface="bold", show.legend = FALSE) + 
        theme_classic() + 
        ylab("-Log10(HR P-value)") + 
        xlab("HR Ratio") + 
        xlim(0, max(x_vec)+1.0) + 
        guides(fill=guide_legend(title=""))# + 
        # geom_vline(xintercept = 1, color="grey40", lty=4) + 
        # geom_hline(yintercept = 1.30103, color="grey40", lty=3)
}