#!/usr/bin/env Rscript

# Load necessary libraries
library(data.table)
library(optparse)
library(progress)

# Define command line options
option_list <- list(
  make_option(c("-i", "--input"), type = "character", help = "Comma-separated list of input files", metavar = "input_files"),
  make_option(c("-o", "--output"), type = "character", default = "merged_result_v6.tsv", help = "Output file name [default: %default]", metavar = "output_file")
)

# Parse command line options
opt_parser <- OptionParser(option_list = option_list)
opt <- parse_args(opt_parser)

# Check if input file parameter is provided
if (is.null(opt$input)) {
  print_help(opt_parser)
  stop("Input files must be provided", call. = FALSE)
}

# Define function to merge data tables
merge_data_tables <- function(dt_list) {
  Reduce(function(x, y) merge(x, y, by = c("chr", "pos", "strand"), all = TRUE), dt_list)
}

# Split input file list
file_list <- strsplit(opt$input, ",")[[1]]

# Initialize progress bar
pb <- progress_bar$new(
  format = "  Reading files [:bar] :percent in :elapsed",
  total = length(file_list), clear = FALSE, width = 60
)

# Read and merge data tables
dt_list <- lapply(file_list, function(file) {
  pb$tick()
  fread(file)
})
merged_data <- merge_data_tables(dt_list)

# Replace all NAs with 0
merged_data[is.na(merged_data)] <- 0

# Sort by the sign of the 'strand' column
merged_data <- merged_data[order(strand == "+", decreasing = TRUE), ]

# Save the merged data table
fwrite(merged_data, opt$output, sep = "\t")

# Clean up memory
rm(dt_list, merged_data)
gc()

# Output message
cat("Files have been successfully merged and saved as '", opt$output, "'.\n")
