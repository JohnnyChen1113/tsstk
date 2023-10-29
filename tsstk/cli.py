# cli.py

import click
from tsstk import core  # 假设你在core.py中定义了具体的功能实现

@click.group()
def tsstk():
    """tsstk toolset for TSS analysis."""
    pass

@click.command()
@click.option('--bam', type=click.Path(exists=True), help='Path to the BAM file.')
@click.option('--tsstable', type=click.Path(exists=True), help='Path to the TSS table.')
def gettss(bam, tsstable):
    """Get TSS information from BAM or TSS table."""
    if bam:
        core.get_tss_from_bam(bam)  # 假设在core.py中定义了这个函数
    elif tsstable:
        core.get_tss_from_table(tsstable)  # 假设在core.py中定义了这个函数
    else:
        click.echo("Please provide either --bam or --tsstable.")

# 将子命令添加到主命令
tsstk.add_command(gettss)

if __name__ == '__main__':
    tsstk()

