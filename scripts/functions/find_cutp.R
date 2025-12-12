std_cutp <- function (data, method, upper_per, lower_per) { 
  
  f <- switch(method,
              mean =  mean(data),
              median = median(data),
              percentile=quantile(data, probs=c(lower_per, upper_per))
  )
  return(f)
}

opt_cutp <- function (data, index, surv_type) { 
      #### optimal cut-point finder Contal et al 1999 & Mandrekar et al 2003

  if(toupper(surv_type) == "OVERALL"){
    data$overall_survival_time_in_months = (data$overall_survival_time_in_days)/30.42
    data$os = Surv(time=data$overall_survival_time_in_months, event=data$vital_status=="Dead")
  } else {
    data$event_free_survival_time_in_months = (data$event_free_survival_time_in_days)/30.42
    data$os = Surv(time=data$event_free_survival_time_in_months, event=data$event_status=="Event")
	}
  gx <- data[,index]
  cox.os = coxph(os ~ gx, data=data) 
  c1 <- survMisc::cutp(cox.os)$gx
  data.table::setorder(c1, gx)
  percentile <- ecdf(c1$gx)
  low <- as.numeric(c1[order(c1$Q), ][nrow(c1), 1])
  low
}

# subset_tils_cli$Overall.Survival.Time.in.Months = (subset_tils_cli$Overall.Survival.Time.in.Days)/30.42
# subset_tils_cli$os = Surv(time=subset_tils_cli$Overall.Survival.Time.in.Months, event=subset_tils_cli$Vital.Status=="Dead")

sep_groups <- function(group_method, clios, scores, upper_per, lower_per, surv_type){
  if ((length(unique(scores$gx)) < 3) & (tolower(group_method) == "cutp")){
    # samller than defCont https://rdrr.io/cran/survMisc/src/R/cutp.R
    group_method <- "mean"
  }
  if(tolower(group_method) == "cutp"){
    #samples common to both clinical and immmune cell proportion
    subset_tmp <- merge(clios, scores, by="sample", sort=FALSE)
    end <- grep("gx", colnames(subset_tmp))
    f <- opt_cutp(subset_tmp, end, surv_type)

    low_cpi <- signif(as.numeric(f[[1]]),3)
    high_cpi <- signif(as.numeric(f[[1]]),3)

  } else if (tolower(group_method) == "percentile"){
    f <- std_cutp(scores$gx, "percentile", as.numeric(upper_per)/100, as.numeric(lower_per)/100)

    low_cpi <- signif(as.numeric(f[[1]]),3)
    high_cpi <- signif(as.numeric(f[[2]]),3)

  } else {
    # group_method %in% c("mean","median")
    f <- std_cutp(scores$gx, group_method, NA, NA)

    low_cpi <- signif(as.numeric(f[[1]]),3)
    high_cpi <- signif(as.numeric(f[[1]]),3)
  }
  
  los = scores$sample[scores$gx <= low_cpi]
  his = scores$sample[scores$gx > high_cpi]
  #identify samples within each low and high cut-points
  scores$group[scores$sample %in% los] = "Low"
  scores$group[scores$sample %in% his] = "High"
  #samples common to both clinical and immmune cell proportion
  subset_tils_cli <- merge(clios, scores, by="sample", sort=FALSE)

  return(list("subset_tils_cli" = subset_tils_cli, "cpi" = c(low_cpi, high_cpi)))
}
