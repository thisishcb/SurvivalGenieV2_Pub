generate_boxplot = function(df,selected,label){
  
  #low.col = rgb(0, 0, 0.5)
  #high.col = rgb(0.5, 0, 0)
  #cols = c(high.col,low.col)
  # source("palattes.R")

  boxplot(df$gx ~ df$group, 
          main = selected, 
          notch = FALSE, 
          col = COL_GROUPS, 
          show.names=TRUE,
          ylab=label,
          xlab="",
          cex.lab=2.0, cex.names=2.0, cex.axis=2.0, cex.main=2.0)
  abline(v=1.5,lty=2,col='black')
}

generate_boxplot_gg = function(df, ds, label,COL_GROUPS){
  
  #  <- data.frame(df$sample, df$group, df$gx)
  # colnames(gx_data) <- c("sample", "group", ds)
  # df.m <- melt(gx_data, id.vars=c("sample", "group"))
  # source("palattes.R") # COL_GROUPS, cbPalette

  p <- df |> dplyr::select(sample,group,gx) |> 
    dplyr::mutate(dataset=ds) |>
    ggplot(aes(x=group, y=gx)) + 
      scale_fill_manual(values=COL_GROUPS) +
      geom_boxplot(aes(fill = group)) +
      # geom_point(aes(y=gx, group=group), position = position_dodge(width=0.75)) +
      # facet_wrap( ~ dataset, scales="free") + 
      geom_vline(xintercept = 1.5, color="black", lty=4) + 
      xlab("") + ylab(label) + #paste0("CIBERSOFT fraction", "\n")
      theme(legend.position="none",
            # panel.background = element_rect(fill="NA"), 
            # panel.border = element_rect(colour = "black", fill="NA"),
            # panel.grid.major.y = element_line(colour="NA"),
            # panel.grid.minor = element_line(colour="NA"),
            # axis.text.x = element_text(hjust = 0.5, vjust = 0.5, colour = "black", face="bold", size=16.0),
            # axis.text.y = element_text(hjust = 1.0, vjust = 0.5, colour = "black", face="bold", size=14.0),
            # axis.title.y = element_text(colour="black", face="bold", size=16.0),
            # axis.title.x = element_text(colour="black", face="bold", size=16.0),
            # strip.text = element_text(colour="black", face="bold", size = 20),
            )
  return(p)
}

