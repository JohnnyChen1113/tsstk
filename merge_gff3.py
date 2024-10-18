#!/usr/bin/env python3

import click
import re

# 函数用于从 GFF3 行中提取染色体、起始和结束位置
def parse_gff3_line(line):
    fields = line.strip().split('\t')
    if len(fields) < 9:
        return None, None, None
    chrom = fields[0]
    start = int(fields[3])
    end = int(fields[4])
    return chrom, start, end

# 读取 GFF3 文件，并将记录按照染色体和起始位置排序
def read_gff3(file):
    genes = []
    gene_block = []
    with open(file, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            if re.match(r'.*\tgene\t.*', line):
                if gene_block:
                    genes.append(gene_block)
                    gene_block = []
            gene_block.append(line)
        if gene_block:
            genes.append(gene_block)
    return genes

# 合并 GFF3 文件并排序
def merge_gff3(gff3_files, output_file):
    all_genes = []
    for file in gff3_files:
        all_genes.extend(read_gff3(file))

    # 排序基因，先按染色体名称排序，再按起始位置排序
    all_genes.sort(key=lambda gene: (parse_gff3_line(gene[0])[0], parse_gff3_line(gene[0])[1]))

    with open(output_file, 'w') as f:
        for gene_block in all_genes:
            for line in gene_block:
                f.write(line)
        
        # 添加换行符确保文件末尾没有丢失行
        f.write('\n')

@click.command()
@click.option('-i1', '--input1', 'gff3_file1', required=True, help='Path to the first GFF3 file')
@click.option('-i2', '--input2', 'gff3_file2', required=True, help='Path to the second GFF3 file')
@click.option('-o', '--output', 'output_file', required=True, help='Path to the output merged GFF3 file')
def main(gff3_file1, gff3_file2, output_file):
    merge_gff3([gff3_file1, gff3_file2], output_file)
    print(f"Merged GFF3 files written to {output_file}")

if __name__ == "__main__":
    main()

