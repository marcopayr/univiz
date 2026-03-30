import xml.etree.ElementTree as ET
import numpy as np
from pathlib import Path
import struct
import pandas as pd

class Chromatogram:
    def __init__(self, path) -> None:
        # path is the root dir of unzipped Aekta run (e.g. /docs/unzipped_files/SEC_run_1/)

        # run all functions to get chromatograms
        self.root_dir = Path(path)
        self.xml_root = self.load_xml(self.root_dir)
        self.curves = self.get_chromatograms(self.xml_root, self.root_dir) # curves -> dict of all chromatograms
        self.add_elution_Volumes()
        self.curves_df = pd.DataFrame.from_dict(data=self.curves, orient='columns')

        # run all functions to get Events (e.g., fractionation)
        self.events = self.get_chromatograms(self.xml_root, self.root_dir, elem="EventCurve")
        self.events_df = pd.DataFrame(self.events)

    @staticmethod
    def read_binary_file(fn = None) -> bytes:
        """Return the raw bytes from a binary file (SEC_run_1/Chrom.1_x_True_unzipped/CoordinateData.Amplitudes)."""
        if fn is None: 
            print(f"Provide a filename. Filename is {fn}.") 
        try:
            with fn.open("rb") as binary_file:
                return binary_file.read()
        except FileNotFoundError:
            print(f"File not found: {fn}")
            
    @staticmethod
    def convert_binary(fn = None) -> struct:
        """Convert binary chromatogram to human readable format."""
        if fn is None: 
            print(f"Provide a filename. Filename is {fn}.") 
        # check if chromatogram is already unzipped
        if Path(fn).exists():
            data = Chromatogram.read_binary_file(fn)
            # identified starting idx as 23
            float_data = data[23:]
            # 'f' = 4-byte float, '<' = little-endian
            return struct.unpack('<' + 'f' * (len(float_data) // 4), float_data[:(len(float_data)//4)*4])
        
        raise FileNotFoundError(f"Could not find file: {fn}")
    
    def get_chromatograms(self, xml_root = None, path = None, elem = "Curve") -> None:
        """Return dict of all chromatograms parsed from xml and binary files."""
        curves = {}
        if xml_root is None: xml_root = self.xml_root
        if path is None: path = self.root_dir

        for num, curve in enumerate(xml_root.iter(elem)):
            # print(curve.attrib)
            # print(len(curve))

            # check if each Chrom.1_x_True already got unzipped
            if path.parent:
                num_suffix = f"{num:02d}"
                curves[f"{curve.tag}{num_suffix}"] = Chromatogram.get_xml_elems(path, curve)
                # add x-axis array
                if elem == "Curve": 
                    xarr = Chromatogram.add_xarray(curves[f"{curve.tag}{num_suffix}"])
                    curves[f"{curve.tag}{num_suffix}"]["xarr"] = xarr
                    curves[f"{curve.tag}{num_suffix}"]["eluted Volume"] = xarr * 4.9
                    curves[f"{curve.tag}{num_suffix}"]["CV"] = xarr / self.get_CV()

        return curves
    
    @staticmethod
    def get_xml_elems(path: Path, elem: ET.Element) -> dict:
        # Traverse the XML tree iteratively and collect leaf node values.
        parsed_xml = {}
        stack = [elem]
        if elem.tag == "EventCurve":
            eventTime, eventVolume, eventText = [], [], []
        while stack:
            node = stack.pop()
            children = list(node)
            if children:
                stack.extend(children)
            else:
                if node.tag == 'BinaryCurvePointsFileName':
                    fn = path / Path(node.text + "_unzipped/CoordinateData.Amplitudes")
                    chromatogram = Chromatogram.convert_binary(fn)
                    parsed_xml['CurvePoints'] = np.asarray(chromatogram)
                elif node.tag == 'EventTime':
                    eventTime.append(float(node.text))
                elif node.tag == 'EventVolume':
                    eventVolume.append(float(node.text))
                elif node.tag == 'EventText':
                    eventText.append(node.text)
                else:
                    try:
                        parsed_xml[node.tag] = float(node.text)
                    except (ValueError, TypeError):
                        parsed_xml[node.tag] = node.text

        if elem.tag == "EventCurve": 
            parsed_xml["EventsValues"] = np.asarray(list(zip(eventTime, eventVolume)))
            parsed_xml["EventsName"] = np.asarray(eventText)

        return parsed_xml

    @staticmethod
    def load_xml(fn) -> ET.Element:
        """Load XML file from Chrom.1.Xml."""
        fn /= Path("Chrom.1.Xml") 
        tree = ET.parse(fn)
        return tree.getroot()  # Root element

    @staticmethod
    def add_xarray(curve):
        """Add an x axis array, normalize data points with 'DistanceBetweenPoints'."""
        return np.arange(0, len(curve['CurvePoints'])) * float(curve['DistanceBetweenPoints'])

    def get_CV(self):
        """Get column volume (CV) from xml."""
        CV = list(self.xml_root.iter("ColumnVolume"))[0].text
        # CV = df[curve]['ColumnVolume']
        return float(CV)

    def add_elution_Volumes(self) -> dict:
        """
        Calculate and add 'elution Volume' arrays to each chromatogram in self.curves.

        This method computes the cumulative total flow for each chromatogram curve,
        resamples it to match the resolution of each curve, and ensures the resulting
        'elution Volume' arrays are strictly increasing for downstream analysis and plotting.
        The method modifies self.curves in place by adding the 'elution Volume' key to each curve.

        Returns:
            None
        """

        def _ensure_strictly_increasing(arr: np.ndarray, min_step: float | None = None) -> np.ndarray:
            """Return a copy of arr that is strictly increasing.
            If there are plateaus or slight decreases due to resampling/precision,
            bump values forward by a tiny step to maintain strict monotonicity.
            """
            x = np.asarray(arr, dtype=float).copy()
            if x.size <= 1:
                return x
            diffs = np.diff(x)
            if min_step is None:
                pos = diffs[diffs > 0]
                if pos.size:
                    min_step = float(np.min(pos)) * 1e-6  # tiny fraction of smallest positive step
                else:
                    span = float(np.nanmax(x) - np.nanmin(x))
                    min_step = (span if span > 0 else 1.0) * 1e-12
            # Enforce strictly increasing in one pass
            for i in range(1, x.size):
                if x[i] <= x[i - 1]:
                    x[i] = x[i - 1] + min_step
            return x

        # get system and sample flow
        sysFlow = self.curves['Curve06']['CurvePoints']
        sampFlow = self.curves['Curve09']['CurvePoints']

        # make sure distance between points is equal
        sysFlowDistPoint = self.curves['Curve06']['DistanceBetweenPoints']
        sampFlowDistPoint = self.curves['Curve09']['DistanceBetweenPoints']
        assert np.isclose(sysFlowDistPoint, sampFlowDistPoint, rtol=1e-6)

        # get total Flow, and make sure both arrays are same length
        if len(sysFlow) > len(sampFlow):
            totFlow = sampFlow + sysFlow[:len(sampFlow)]
        else:
            totFlow = sysFlow + sampFlow[:len(sysFlow)]

        cum_totFlow_corr = np.cumsum(totFlow)*sysFlowDistPoint # cumulative total flow, corrected with distance between points

        # ------- resample cum_totFlow to match dimension of other curves
        # ------- then store as "elution Volume" for each curve in curves
        x_old = np.linspace(0, 1, len(cum_totFlow_corr)) # Original x-coordinates
        for curve in self.curves:
            # print(curve)
            high_res = self.curves[curve]['CurvePoints']
            # New x-coordinates based on high_res' length
            x_new = np.linspace(0, 1, len(high_res))
            # Interpolate when chromatogram successfully got read
            if len(x_new) > 0 and len(x_old) > 0: cum_totFlow_corr = np.interp(x_new, x_old, cum_totFlow_corr)
            # Ensure strictly increasing x for plotting and downstream consumers
            self.curves[curve]['elution Volume'] = _ensure_strictly_increasing(cum_totFlow_corr)

            # reset arrays
            cum_totFlow_corr = np.cumsum(totFlow)*sysFlowDistPoint
            x_old = np.linspace(0, 1, len(cum_totFlow_corr)) # Original x-coordinates

        return None


if __name__ == "__main__":

    from plot_chromatogram import plot_chromatograms
    import matplotlib.pyplot as plt

    print(Path.cwd())
    
    # specify root dir
    fn = "./../docs/unzipped_files/HiTrap_run_1/"

    # create Chromatogram class
    chromatograms = Chromatogram(fn)

    plot_chromatograms(
        chromatograms.curves_df, 
        types=['A280', 'A260', 'Conc B'],
        addFracs=True,
        fractionValues=chromatograms.events_df['EventCurve00']['EventsValues'], 
        fractionLabels=chromatograms.events_df['EventCurve00']['EventsName'],
        label_height=50)

    plt.show()