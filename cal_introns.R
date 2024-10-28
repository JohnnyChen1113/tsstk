#!/usr/bin/env Rscript

# Load required libraries without output messages
if (!require("GenomicFeatures", character.only = TRUE)) {
    suppressMessages(suppressWarnings(BiocManager::install("GenomicFeatures", ask = FALSE)))
}
if (!require("rtracklayer", character.only = TRUE)) {
    suppressMessages(suppressWarnings(BiocManager::install("rtracklayer", ask = FALSE)))
}

suppressMessages(library(GenomicFeatures))
suppressMessages(library(rtracklayer))


# Parse command-line arguments
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
    stop("Please specify a GFF3 file path using -f, e.g., Rscript script.R -f path/to/file.gff3")
}

# Get file path
file_arg <- which(args == "-f") + 1
if (file_arg > length(args)) {
    stop("Please specify a GFF3 file path using -f, e.g., Rscript script.R -f path/to/file.gff3")
}
gff3_file <- args[file_arg]

# Create TxDb object
annotation <- makeTxDbFromGFF(file = gff3_file, format = "gff")

# Extract and summarize intron length information
introns <- intronsByTranscript(annotation)
introns <- unlist(introns)
cat("Intron width summary:\n")
print(summary(width(introns)))

cat("95th percentile of intron widths:\n")
print(quantile(width(introns), 0.95))

