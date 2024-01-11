library(tidyverse)
library(stringr)

FILE_DIR = "./"
datasets = read_delim(FILE_DIR+"/program_datasets.txt",delim='\t')

avail_programs = datasets |> colnames()
avail_projects <- datasets |> pivot_longer(cols = all_of(avail_programs), names_to = "Program", values_to = "Project") |> filter(!is.na(Project)) |> arrange(Program) 

library(GenomicDataCommons)
cquery = cases()
default_fields(cquery)
ccfields = available_fields(cquery) |> as.data.frame()
cases() |> filter(`project.project_id` == 'TARGET-ALL-P1') |> count()

# GenomicDataCommons has confliction with dplyr filter and select
proj_cases = cquery |> GenomicDataCommons::filter(`project.project_id` == 'TCGA-ACC') |> GenomicDataCommons::select("diagnoses.age_at_diagnosis") |> results()

get_meta <- function(db_name){
  proj_cases = cases() |> GenomicDataCommons::filter(`project.project_id` == db_name) |> GenomicDataCommons::select("diagnoses.age_at_diagnosis") |> results_all()
  proj_cases = proj_cases$diagnoses |> enframe() |> unnest(cols=c("value"))
  names(proj_cases) <- c("case_id", "age_at_diagnosis")
  proj_cases$age_at_diagnosis = proj_cases$age_at_diagnosis/365.25
  return(proj_cases)
}

library(tidyverse)

datasets = read_delim("./project_meta/program_datasets.txt", delim='\t')
avail_programs = datasets |> colnames()
avail_projects <- datasets |> pivot_longer(cols = all_of(avail_programs), names_to = "Program", values_to = "Project") |> filter(!is.na(Project)) |> arrange(Program) 

for(p in avail_projects$Project){
  # print(p)
  ages = get_meta(p)
  ages |> write_csv(file=paste0("./case_ages/",p,"_ages.csv"))
}
