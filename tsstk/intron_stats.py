#!/usr/bin/env python

VERSION = "0.1.0"

import click
import pandas as pd
import os

def parse_gtf(gtf_file):
    # Load the GTF file into a DataFrame, considering only the necessary columns
    col_names = ["seqname", "source", "feature", "start", "end", "score", "strand", "frame", "attribute"]
    df = pd.read_csv(gtf_file, sep='\t', comment='#', names=col_names)
    
    # Filter for exons
    exons = df[df['feature'] == 'exon'].copy()
    
    # Extract transcript ID from the attributes column
    exons.loc[:, 'transcript_id'] = exons['attribute'].str.extract('transcript_id "([^"]+)"')
    
    # Sort by sequence name, transcript ID, and start position
    exons = exons.sort_values(by=['seqname', 'transcript_id', 'start'])
    
    # Calculate intron start and end positions
    exons['intron_start'] = exons['end'].shift(1) + 1
    exons['intron_end'] = exons['start'] - 1
    
    # Find introns within the same transcript
    exons['same_transcript'] = exons['transcript_id'].eq(exons['transcript_id'].shift(1))
    
    # Filter rows that are introns
    introns = exons[exons['same_transcript']].copy()
    
    # Calculate intron length
    introns.loc[:, 'intron_length'] = introns['intron_end'] - introns['intron_start'] + 1
    
    return introns[['seqname', 'intron_start', 'intron_end', 'intron_length']]

def calculate_statistics(introns):
    # Calculate statistics for intron lengths
    stats = {
        'max_length': introns['intron_length'].max(),
        'min_length': introns['intron_length'].min(),
        'mean_length': introns['intron_length'].mean(),
        'median_length': introns['intron_length'].median(),
        'std_dev_length': introns['intron_length'].std(),
        'count': introns['intron_length'].count()
    }
    return stats

@click.command()
@click.option('-i', '--input', 'input_file', required=True, type=click.Path(exists=True), help='Path to the input GTF file')
@click.option('-o', '--output', 'output_prefix', required=False, type=str, help='Prefix for the output file (optional)')
@click.version_option(version=VERSION, prog_name="Intron Length Analyzer")

def main(input_file, output_prefix):
    # Determine output file name
    if output_prefix:
        output_file = f"{output_prefix}.intron_len.txt"
    else:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = f"{base_name}.intron_len.txt"

    # Parse GTF and get introns
    introns = parse_gtf(input_file)
    
    # Calculate statistics
    stats = calculate_statistics(introns)

    # Print statistics
    print("Intron Length Statistics:")
    for stat, value in stats.items():
        print(f"{stat}: {value}")
    
    # Save intron details to a file
    introns.to_csv(output_file, sep='\t', index=False)

    # Print the intron lengths distribution
    length_distribution = introns['intron_length'].value_counts().sort_index()
    print("\nIntron Length Distribution:")
    print(length_distribution)

if __name__ == "__main__":
    main()

