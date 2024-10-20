#!/usr/bin/env python3
import gffutils
import click

__version__ = "0.1.0"

@click.command()
@click.option('-i', '--input', 'input_file', required=True, help='Input GFF3 file')
@click.option('-o', '--output', 'output_file', required=True, help='Output TSV file')
@click.option('--version', is_flag=True, help='Print the version number and exit')
def extract_gene_regions(input_file, output_file, version):
    if version:
        print(f"extract_gene_regions version {__version__}")
        return

    # Create a database from the GFF3 file
    db = gffutils.create_db(input_file, dbfn='annotation.db', force=True, keep_order=True, merge_strategy='merge', sort_attribute_values=True)

    # Open the database
    db = gffutils.FeatureDB('annotation.db')

    # Open a file to save the results
    with open(output_file, "w") as out_file:
        # Iterate through all gene entries
        for gene in db.features_of_type('gene'):
            gene_id = gene.attributes.get('ID', [''])[0]  # Get gene ID
            chromosome = gene.seqid  # Get chromosome name
            strand = gene.strand  # Get strand information

            # Initialize the gene start and end positions
            gene_start = gene.start
            gene_end = gene.end

            # Get all CDS entries for the gene
            cds_list = list(db.children(gene, featuretype='CDS', order_by='start'))
            if not cds_list:
                continue  # Skip if no CDS found

            # Adjust start and end positions based on strand
            if strand == '+':
                gene_end = cds_list[-1].end  # Positive strand, extend to the end of the last CDS
                gene_start = max(1, gene_start - 2000)  # Extend upstream by 2000 bp, but not less than 1
            elif strand == '-':
                gene_start = cds_list[0].start  # Negative strand, start from the first CDS
                gene_end += 2000  # Extend downstream by 2000 bp

            # Write the extracted information
            out_file.write(f"{chromosome}	{gene_start}	{gene_end}	{strand}	{gene_id}\n")

    print(f"Extraction complete, results saved in {output_file}")

if __name__ == "__main__":
    extract_gene_regions()

