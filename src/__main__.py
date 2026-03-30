# ------- FULL WORKFLOW TO EXTRACT, READ & VISUALIZE CHROMATOGRAMS FROM AEKTA RUNS ------------------------------

import argparse
from pathlib import Path

def main():

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument('--fi',type=Path, 
                        default="./../docs/zip_files/HiTrap_run_1.zip",
                        help='Specify file location for extraction.')

    parser.add_argument('--fo',type=Path,
                        default=argparse.SUPPRESS,
                        help='Specify file location of extracted content.')
    args = parser.parse_args()
    input_args = []
    if not hasattr(args, 'fo'):
        args.fo = args.fi.with_suffix('') # removes .zip
        fn = args.fo.name
        parent = args.fo.parent.parent
        args.fo = parent / Path("unzipped_files") / fn

    # specify src and dst dirs
    src = args.fi
    dst = args.fo

    from unzip import unzip_files
    # extract
    # 1a) extract .zip file
    unzip_files(src, dst)
    print(f"------------ Extracted {src} → {dst} ------------\n")

    # 1b) extract all Chrom.1_x_True directories in the parent directory
    parent = dst
    for item in parent.iterdir():
        # print(item)
        if item.name.startswith("Chrom.1_") and item.name.endswith("_True"):
            src = item
            dst = parent / f"{item.name}_unzipped"
            unzip_files(src, dst)
            print(f"\n------------ Extracted {src} → {dst} ------------\n")



    # 2) read chromatograms
    from read_chromatograms import Chromatogram
    from plot_chromatogram import plot_chromatograms
    import matplotlib.pyplot as plt

    # create Chromatogram class and read binary data
    chromatograms = Chromatogram(parent)


    # 3) plot chromatograms
    plot_chromatograms(
        chromatograms.curves_df, 
        types=['A280', 'A260', 'Conc B'],
        addFracs=True,
        fractionValues=chromatograms.events_df['EventCurve00']['EventsValues'], 
        fractionLabels=chromatograms.events_df['EventCurve00']['EventsName'],
        label_height=50)

    plt.show()

if __name__ == '__main__':
	main()