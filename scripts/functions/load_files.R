
load_exp <- function(ds, tumor_type, FILE_DIR, FPKM_DIR){
    expFile <- paste0(ds, "_", "FPKM", ".txt")
    readEXPFile <- paste(FILE_DIR, FPKM_DIR, tumor_type, expFile, sep='/')
    if(!file.exists(readEXPFile)){
        write(paste("[IT002] No genomics data for", ds, "\n"),
            stderr())
        stop()
    }
    fpkm <- data.table::fread(readEXPFile, sep="\t", stringsAsFactors = FALSE)
    colnames(fpkm)[2] <- "symbol" # gene_id, gene_name, ...
    fpkm$symbol <- toupper(fpkm$symbol)
    return(fpkm)
}

load_clios <- function(surv_type, ds, tumor_type, FILE_DIR, FPKM_DIR, EFS_DIR) {
    osFile <- paste0(ds, "_", "clinical_OS", ".txt")
    if(toupper(surv_type) == "OVERALL"){
        readOSFile <- paste(FILE_DIR, FPKM_DIR, tumor_type, osFile, sep='/')
    } else {
        readOSFile <- paste(FILE_DIR, EFS_DIR, tumor_type, osFile, sep='/')
    }
    if(!file.exists( readOSFile)){
        write(paste("[IT002] No clinical survival data for ", ds, "\n"),
            stderr())
        stop()
    }

    outcome <-  read.table(readOSFile, header=T, sep="\t")
    colnames(outcome)[1] <- "sample"

    if(toupper(surv_type) == "OVERALL"){
        samples = subset(outcome, !is.na(outcome$overall_survival_time_in_days) & !is.na(outcome$vital_status))
        samples = subset(samples, samples$vital_status == "Alive" | samples$vital_status == "Dead")
        rownames(samples) <- samples$sample

        if(all(samples$vital_status == "Alive") | nrow(samples)<20){
            write(paste0("[IT003] Not enough events for survival analysis in dataset", ds, "\n"),
                stderr())
            stop()
        }

    } else {
        samples = subset(outcome, !is.na(outcome$event_free_survival_time_in_days) & !is.na(outcome$first_event))
        samples$first_event <- as.character(samples$first_event)
        samples$event_status = "Event"
        if (grepl("MP2PRT", ds)) {
            samples$event_status[samples$first_event=="None"] <- "NoEvent"
        } else {
            samples$event_status[samples$first_event=="None" & samples$vital_status=="Alive"] <- "NoEvent"
            samples$event_status[samples$first_event=="Censored"  & samples$vital_status=="Alive"] <- "NoEvent"
        }
        
        rownames(samples) <- samples$sampleR

        if (all(samples$event_status == "NoEvent")) {
            write(paste0("[IT003] Not enough events (all samples have no events) for survival analysis in dataset ", ds, "\n"),
                stderr())
            stop()
        }
        if(nrow(samples)<20){ # length(unique(factor(samples$event_status)))<2 |
            write(paste0("[IT003] Not enough events for survival analysis in dataset ", ds, "\n"),
                stderr())
            stop()
        }

    }
    return(samples)
}
