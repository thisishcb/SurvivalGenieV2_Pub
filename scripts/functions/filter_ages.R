filter_ages <- function(ds, group, cutoff=20) {
    agefile = paste0("../data/case_ages/", ds, "_ages", ".csv")
    case_ages = read.table(agefile, header=T, sep=",")
    if (toupper(group)=="ADULT"){
        return(case_ages$diagnosis_id[case_ages$age_at_diagnosis>=cutoff])
    } else if (toupper(group)=="PEDIATRIC") {
        return(case_ages$diagnosis_id[case_ages$age_at_diagnosis<cutoff])
    }
    return(case_ages$diagnosis_id)
}