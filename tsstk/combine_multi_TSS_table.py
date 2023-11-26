import click
import pandas as pd
import concurrent.futures


def process_file(file):
    df = pd.read_csv(file, sep="\t", low_memory=False)
    df = df[(df["chr"] != 0) | (df["pos"] != 0)]  # remove incorrect line if any
    df.fillna(0, inplace=True)  # replace NA with 0
    return df


@click.command()
@click.argument("input_files", nargs=-1, type=click.Path(exists=True))
@click.option("--output", "-o", default="combined_TSS.raw.txt", help="Output file name.")
def process_files(input_files, output):
    """
    This script processes and merges multiple TSSr TSS table files based on 'chr', 'pos', 'strand' columns.
    """
    
    with concurrent.futures.ProcessPoolExecutor() as executor:
        dfs = list(executor.map(process_file, input_files))

    # combine all files
    combined_df = pd.concat(dfs).groupby(["chr", "pos", "strand"]).sum().reset_index()

    # as value type into int
    for col in combined_df.columns:
        if combined_df[col].dtype == "float64":
            combined_df[col] = combined_df[col].astype(int)

    # sort
    combined_df.sort_values(by=["strand", "chr", "pos"], inplace=True)

    # save
    combined_df.to_csv(output, sep="\t", index=False)


if __name__ == "__main__":
    process_files()
