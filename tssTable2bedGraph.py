#!/usr/bin/env python
import click
import pandas as pd

# Define the version of the script
VERSION = "0.1.0"

@click.command()
@click.option('-i', '--input_file', type=click.Path(exists=True), required=True, help='Path to the input TSS table file')
@click.option('--prefix', type=str, required=True, help='Prefix for the output file names')
@click.version_option(version=VERSION, prog_name="TSS raw table to BedGraph Converter")
def process_tss(input_file, prefix):
    # Read the input file
    df = pd.read_csv(input_file, sep='\t')

    # Sum the signal values from columns 3 and 4
    df['signal_sum'] = df.iloc[:, 3] + df.iloc[:, 4]

    # Calculate the overall TPM transformation (without filtering any data)
    total_sum = df['signal_sum'].sum()
    df['tpm'] = (df['signal_sum'] / total_sum) * 1e6
    df['tpm'] = df['tpm'].round(6)

    # Filter out rows where the sum of the original signal values is less than 2
    df_filtered = df[df['signal_sum'] >= 2]

    # Separate positive and negative strands
    df_positive = df_filtered[df_filtered['strand'] == '+']
    df_negative = df_filtered[df_filtered['strand'] == '-']

    # Export to bedGraph format, ensuring 0-based indexing, and the second column is less than the third column
    df_positive_bedgraph = df_positive[['chr', 'pos', 'tpm']].copy()
    df_positive_bedgraph['pos_start'] = df_positive_bedgraph['pos'] - 1  # Convert to 0-based indexing
    df_positive_bedgraph['pos_end'] = df_positive_bedgraph['pos']
    df_positive_bedgraph = df_positive_bedgraph[['chr', 'pos_start', 'pos_end', 'tpm']]

    df_negative_bedgraph = df_negative[['chr', 'pos', 'tpm']].copy()
    df_negative_bedgraph['pos_start'] = df_negative_bedgraph['pos'] - 1  # Convert to 0-based indexing
    df_negative_bedgraph['pos_end'] = df_negative_bedgraph['pos']
    df_negative_bedgraph['tpm'] = -df_negative_bedgraph['tpm']  # Set tpm to negative value
    df_negative_bedgraph = df_negative_bedgraph[['chr', 'pos_start', 'pos_end', 'tpm']]

    # Save output files
    df_positive_bedgraph.to_csv(f'{prefix}_normalized_TPM.plus.bedgraph', sep='\t', header=False, index=False)
    df_negative_bedgraph.to_csv(f'{prefix}_normalized_TPM.minus.bedgraph', sep='\t', header=False, index=False)

    print(f"Files successfully generated: {prefix}_normalized_TPM.plus.bedgraph and {prefix}_normalized_TPM.minus.bedgraph")

if __name__ == '__main__':
    process_tss()

