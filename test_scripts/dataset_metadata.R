library(tidyverse)
library(stringr)
FILE_DIR = "./"
datasets = read_delim(FILE_DIR+"/program_datasets.txt",delim='\t') # change the MMRF-COMMPASS program info to MMRF
metatable = read_delim(FILE_DIR+"/projects-table.2023-11-09.tsv",delim='\t')
meta_json
# get tissue datas
avail_programs = datasets |> colnames()

avail_projects <- datasets |> pivot_longer(cols = all_of(avail_programs), names_to = "Program", values_to = "Project") |> filter(!is.na(Project)) |> arrange(Program) 

merged_table = merge(avail_projects, metatable, by =c("Project", "Program") , all.x=T, all.y=F)

str_split_fixed(merged_table$`Primary Site`,', ',) |> unique() |> length()


## json is simply better in conserving all the info
`%notin%` <- Negate(`%in%`)
library("rjson")
meta_json <- fromJSON(file=FILE_DIR+"/projects.2023-11-09.json")

merged_json = vector("list",length=length(avail_projects$Project))
names(merged_json) <- avail_projects$Project

for (i in seq_along(meta_json)) {
    ds_entry = meta_json[[i]]
    if (ds_entry$project_id %notin% avail_projects$Project) {
        next
    }
    print(ds_entry$project_id)
    merged_json[[ds_entry$project_id]] = list(
        primary_site = ds_entry$primary_site,
        disease_type = ds_entry$disease_type,
        program = ds_entry$program$name
    )
}
merged_json |> toJSON() |> write(FILE_DIR+"projectmeta.json")
