#!/usr/bin/env python3
import pandas as pd
import click
from sortedcontainers import SortedList

__version__ = "0.2.0"

@click.command()
@click.option('-c', '--clusters', 'clusters_file', required=True, help='Input TSV file containing cluster information')
@click.option('-g', '--genes', 'genes_file', required=True, help='Input TSV file containing gene regions extracted from GFF3')
@click.option('-o', '--output', 'output_file', required=True, help='Output TSV file with assigned gene information')
@click.option('--version', is_flag=True, help='Print the version number and exit')
def assign_clusters_to_genes(clusters_file, genes_file, output_file, version):
    if version:
        print(f"assign_clusters_to_genes version {__version__}")
        return

    # Load the clusters and genes data
    clusters_df = pd.read_csv(clusters_file, sep='\t')
    genes_df = pd.read_csv(genes_file, sep='\t', names=['chromosome', 'gene_start', 'gene_end', 'strand', 'gene_id'])

    # Sort genes by chromosome and start position for efficient lookup
    genes_df = genes_df.sort_values(by=['chromosome', 'gene_start']).reset_index(drop=True)

    # Add new columns to the clusters DataFrame for gene and nearby gene
    clusters_df['gene'] = 'NA'
    clusters_df['nearby'] = 'NA'

    # Using a dictionary to keep sorted lists of genes by chromosome and strand for efficient binary search
    gene_dict = {}
    for chrom, strand in genes_df[['chromosome', 'strand']].drop_duplicates().itertuples(index=False):
        key = (chrom, strand)
        gene_dict[key] = SortedList(genes_df[(genes_df['chromosome'] == chrom) & (genes_df['strand'] == strand)].itertuples(index=False))

    # Iterate through each cluster and assign gene information
    for index, cluster in clusters_df.iterrows():
        cluster_chr = cluster['chr']
        cluster_start = cluster['start']
        cluster_end = cluster['end']
        cluster_strand = cluster['strand']

        # Use the sorted list to find potential matching genes
        key = (cluster_chr, cluster_strand)
        if key in gene_dict:
            genes = gene_dict[key]
            left_index = genes.bisect_left((cluster_chr, cluster_start, cluster_end, cluster_strand, ''))

            # Check genes around the cluster position
            possible_genes = []
            if left_index < len(genes):
                possible_genes.append(genes[left_index])
            if left_index > 0:
                possible_genes.append(genes[left_index - 1])

            # Determine if any gene contains the cluster region
            containing_gene = None
            nearest_gene = None
            min_distance = float('inf')

            for gene in possible_genes:
                if gene.gene_start <= cluster_start and gene.gene_end >= cluster_end:
                    containing_gene = gene
                    break
                else:
                    distance = min(abs(gene.gene_start - cluster_start), abs(gene.gene_end - cluster_end))
                    if distance < min_distance:
                        min_distance = distance
                        nearest_gene = gene

            if containing_gene:
                clusters_df.at[index, 'gene'] = containing_gene.gene_id
            elif nearest_gene:
                clusters_df.at[index, 'nearby'] = nearest_gene.gene_id

    # Save the updated clusters DataFrame to the output file
    clusters_df.to_csv(output_file, sep='\t', index=False)
    print(f"Assignment complete, results saved in {output_file}")

if __name__ == "__main__":
    assign_clusters_to_genes()

