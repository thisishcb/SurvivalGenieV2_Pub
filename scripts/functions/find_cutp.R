std_cutp <- function (data, method, upper_per, lower_per) { 
  
  f <- switch(method,
              mean =  mean(data),
              median = median(data),
              percentile=quantile(data, probs=c(lower_per, upper_per))
  )
  return(f)
}
opt_cutp <- function (data, index, type) { 
      #### optimal cut-point finder Contal et al 1999 & Mandrekar et al 2003

  if(toupper(args$options$survival) == "OVERALL"){
    data$Overall.Survival.Time.in.Months = (data$Overall.Survival.Time.in.Days)/30.42
    data$os = Surv(time=data$Overall.Survival.Time.in.Months, event=data$Vital.Status=="Dead")
  } 
	else {
    data$Event.Free.Survival.Time.in.Months = (data$Event.Free.Survival.Time.in.Days)/30.42
    data$os = Surv(time=data$Event.Free.Survival.Time.in.Months, event=data$Event.Status=="Event")
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
