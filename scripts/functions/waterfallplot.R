#'@name waterfallplot
#'@aliases waterfallplot
#'@title A plotting function for SISPA sample identifiers
#'@description Given a sample changepoint data frame, will plot all samples zscores from that data.
#'@usage waterfallplot(x)
#'@param x A data frame containing samples as rows followed by zscores and estimated sample_groups to be plotted.
#'@details This function expects the output from cptSamples function of SISPA package, and highlights the sample profile of interest in the changepoint 1 with orange filled bars.
#'@return Bar plot pdf illustrating distinct SISPA sample profiles.
#'@import ggplot2
#'@examples
#'samples <- c("s1","s2","s3","s4","s5","s6","s7","s8","s9","s10")
#'zscores <- c(3.83,2.70,2.67,2.31,1.70,1.25,-0.42,-1.01,-2.43,-3.37)
#'changepoints <- c(1,1,1,2,2,3,3,NA,NA,NA)
#'groups <- c(1,1,1,0,0,0,0,0,0,0)
#'my.data = data.frame(samples,zscores,changepoints,groups)
#'waterfallplot(my.data)
#'@export
waterfallplot = function(x, selected, label,COL_GROUPS){
    if(missing(x)){
      stop("input data is missing!")
    }
    # source("palattes.R") # COL_GROUPS, cbPalette
    # type <- samples <- End <- Start <- NULL # Setting the variables to NULL first
    
    # colnames(x)[1] <- "samples"
    # colnames(x)[ncol(x)] <- "groups"
    #create a start column
    # x$Start <- 0
    # #define global variable
    # #select and modify the data for readability
    # read_data_sort <- x[ order(x$gx, decreasing=FALSE), ]
    #arrange the columns
    arrange_read_data_sort <- x |> dplyr::select(sample, gx, group) |>
      dplyr::mutate(Start=0) |> 
      dplyr::arrange(gx)
    
    # data.frame(read_data_sort$sample,read_data_sort$Start,read_data_sort$gx,read_data_sort$group)
    colnames(arrange_read_data_sort)<-c("samples","End","type","Start")
    arrange_read_data_sort$type = factor(arrange_read_data_sort$type,levels = c("High","Low"))
    arrange_read_data_sort$samples <- factor(arrange_read_data_sort$samples,levels=unique(arrange_read_data_sort$samples))
    arrange_read_data_sort$id <- seq_along(arrange_read_data_sort$End)
    # arrange_read_data_sort$type <- arrange_read_data_sort$group#ifelse(arrange_read_data_sort$group=="High", "High", "Low")
    # arrange_read_data_sort <- arrange_read_data_sort[,c(5,1,6,2,3)]
    #generate the waterfall plot
    wf <- ggplot(arrange_read_data_sort, aes(fill=type, color=type)) + 
        geom_rect(aes(xmin=id-0.35,xmax=id+0.35,ymin=Start,ymax=End)) +
        scale_fill_manual(values=COL_GROUPS) +
        scale_colour_manual(values=COL_GROUPS) + 
        # theme(legend.position = c(0.15, 0.8)) + 
        #   axis.text.x = element_blank() 
        #   ) + 
        labs(x="Samples", y=label, fill="")
    return(wf)
}



          # axis.text.y = element_text(colour="black",size=14.0),
          # axis.title.x = element_text(colour="black",face="bold",size=16.0),
          # axis.title.y = element_text(colour="black",face="bold",size=16.0),
          # plot.title = element_text(colour="black", face="bold", size=18.0, hjust=0.5),
          # panel.background = element_rect(fill="NA"),
          # panel.border = element_rect(colour = "black", fill="NA"),
          # panel.grid.major.y = element_line(colour="NA"),
          # panel.grid.minor = element_line(colour = "NA"),
          # axis.ticks.x = element_blank(),
          # axis.ticks.y=element_line(colour="black")