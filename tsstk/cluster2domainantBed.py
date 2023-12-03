#!/usr/bin/env python

"""
Script to Convert a Custom File Format to BED Format

Purpose:
This script is designed to read a specific file format with biological data 
and convert it to the BED format. The script allows adjustment of genomic regions 
based on the strand information and includes additional data columns for comprehensive analysis.

Design:
The script takes an input file with multiple columns, performs calculations based on 
strand ('+' or '-') to adjust the genomic start and end positions, and combines certain columns. 
The output is a BED format file suitable for genomic data analysis.

Usage:
Run the script with command line options to specify input file, upstream adjustment, 
downstream adjustment, and output file path. For example:
    python script_name.py -i input.tsv -u 150 -d 10 -o output.bed
Replace 'script_name.py', 'input.tsv', and 'output.bed' with your actual script file name and file paths.

Note: Default values for upstream and downstream adjustments are set to 150 and 10, respectively.
"""

import pandas as pd
import click

def process_file(input_file, upstream, downstream, output_file):
    # Read the file
    df = pd.read_csv(input_file, sep='\t')

    # Calculate start and end based on the strand symbol
    df['start'] = df.apply(lambda row: row['dominant_tss'] - upstream if row['strand'] == '+' else row['dominant_tss'] - downstream, axis=1)
    df['end'] = df.apply(lambda row: row['dominant_tss'] + downstream if row['strand'] == '+' else row['dominant_tss'] + upstream, axis=1)

    # Combine gene and cluster columns for a new column
    df['name'] = df['gene'] + '_' + df['cluster'].astype(str)

    # Select the required columns
    bed_df = df[['chr', 'start', 'end', 'name', 'tags.dominant_tss', 'strand']]

    # Write the results to a new BED file
    bed_df.to_csv(output_file, sep='\t', index=False, header=False)

# Command line interface using click
@click.command()
@click.option('-i', '--input', 'input_file', required=True, help='Input file path')
@click.option('-u', '--upstream', default=150, help='Upstream adjustment value', type=int)
@click.option('-d', '--downstream', default=10, help='Downstream adjustment value', type=int)
@click.option('-o', '--output', 'output_file', required=True, help='Output file path')
def main(input_file, upstream, downstream, output_file):
    process_file(input_file, upstream, downstream, output_file)

if __name__ == '__main__':
    main()

