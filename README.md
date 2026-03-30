# Univiz: Chromatogram Extraction, Reading, and Visualization

This package provides a workflow to extract, read, and visualize chromatograms from ÄKTA runs. It is designed to automate the process of unzipping run files, extracting chromatogram data, and plotting the results.

## Features
- Extracts .zip files containing ÄKTA run data
- Automatically extracts all Chrom.1_x_True
- Reads chromatogram data into a convenient class
- Plots chromatogram curves with fraction events

## Installation

Clone the repository and install the required dependencies:

```bash
pip install .
```

## Usage

You can run the full workflow from the command line:

```bash
python -m src --fi <input_zip_file> [--fo <output_directory>]
```

- `--fi`: Path to the .zip file to extract (default: `./../docs/zip_files/HiTrap_run_1.zip`)
- `--fo`: Output directory for extracted content (optional; defaults to a directory in `docs/unzipped_files/` with the same name as the zip file)

Example:

```bash
python -m src --fi ./../docs/zip_files/HiTrap_run_1.zip
```

## Workflow Steps
1. **Extract**: Unzips the specified .zip file to the output directory.
2. **Batch Extract**: Unzips all `Chrom.1_x_True` found in the extracted folder.
3. **Read Chromatograms**: Loads chromatogram data using the `Chromatogram` class.
4. **Plot Chromatograms**: Plots the chromatogram curves and fraction events using matplotlib.

## Project Structure

- `src/unzip.py`: Contains the `unzip_files` function for extraction.
- `src/read_chromatograms.py`: Contains the `Chromatogram` class for reading data.
- `src/plot_chromatogram.py`: Contains the plotting functions.
- `src/__main__.py`: Main workflow script (entry point).

## Requirements
- Python >=3.10
- matplotlib
- numpy
- pandas
- seaborn
- py7zr
- stream-unzip

## License
GPLv3

## Author
Marco Payr
