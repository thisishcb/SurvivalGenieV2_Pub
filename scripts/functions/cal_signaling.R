# geometric mean with option for zero.propagate
gm_mean = function(x, na.rm=TRUE, zero.propagate = T){
  if(any(x < 0, na.rm = TRUE)){
    return(NaN)
  }
  if(zero.propagate){
    if(any(x == 0, na.rm = TRUE)){
      return(0)
    }
    exp(mean(log(x), na.rm = na.rm))
  } else {
    exp(sum(log(x[x > 0]), na.rm=na.rm) / length(x))
  }
}

# get the geom mean of the genes input
cal_gene_gm = function(gene_exp){
    gmres <- data.frame(colnames(gene_exp),apply(t(gene_exp), 1, gm_mean),row.names=NULL)
    return(gmres)
}

cal_signaling = function(scores_l, scores_r) {
    scores <- merge(scores_l,scores_r,by="sample")
    scores$gx <- scores$gx_l * scores$gx_r
    scores <- scores[, c("sample","gx")]
    return(scores)
}