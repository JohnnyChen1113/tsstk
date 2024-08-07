# tsstk
An open source toolkit for TSS(transcription start site) analysis

## Marge multiple raw TSS tabels.
merge_raw_TSS.R
```
Rscript merge_raw_TSS.R --help
```
These packages needed:
- data.table
- optparse
- progress
```
Usage: merge_raw_TSS.R [options]


Options:
        -i INPUT_FILES, --input=INPUT_FILES
                Comma-separated list of input files

        -o OUTPUT_FILE, --output=OUTPUT_FILE
                Output file name [default: merged_result_v6.tsv]

        -h, --help
                Show this help message and exit

```
