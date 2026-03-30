from importlib.metadata import version
__version__ = version("univiz")

# Univiz package initialization
from .read_chromatograms import Chromatogram
from .plot_chromatogram import plot_chromatograms
from .unzip import unzip_files

__all__ = [
	"Chromatogram",
	"plot_chromatograms",
	"unzip_files",
]
