import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

def get_yAxis(df, curve):
    """Get AmplitudeUnits from specific curve (e.g. A280, conductivity) from dataframe."""
    # AmplitudeUnit = list(xml_root.iter("AmplitudeUnit"))[0].text
    AmplitudeUnit = df[curve]['AmplitudeUnit']
    return AmplitudeUnit

def plot_chromatograms(
        # df, types = ["Sample flow", "System flow"], leftAxis="A280", rightAxis="Conc B"):
        df, types = ["A280", "A260", "Conc B"], 
        leftAxis="A280", rightAxis="Conc B", 
        addFracs=False, fractionValues=None, fractionLabels=None, 
        xAxis="elution Volume",
        label_height=100):
        # df, types = ["A280"], leftAxis="A280", rightAxis="Conc B", addFracs=False, fractionValues=None, fractionLabels=None):
    """Plot chromatograms"""
    
    sns.set_context("talk")
    sns.set_style("whitegrid")
    palette = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c']
    sns.set_palette(palette)
    
    fig, ax1 = plt.subplots(figsize=(12, 9))
    ax2 = None

    type_conv = df.loc["Name"].to_dict()
    type_conv["Curve00"] = "A280"; type_conv["Curve01"] = "A260"; type_conv["Curve02"] = "A214"
    # print(type_conv)
    
    for i, type in enumerate(types):
        # find curve to associated value
        if type in type_conv.values():  
            curve = next(k for k, v in type_conv.items() if v == type)
            if type == leftAxis:
                if len(df[curve]['CurvePoints']) > 0:
                    if df[curve][xAxis] is not None:
                        sns.lineplot(x=df[curve][xAxis], y=df[curve]['CurvePoints'], ax=ax1, label=type, color=palette[i], sort=False, errorbar=None)
                        ax1.set_xlabel("Volume (ml)")
                    else:
                        sns.lineplot(x=df[curve]['xarr'], y=df[curve]['CurvePoints'], ax=ax1, label=type, color=palette[i], sort=False, errorbar=None)
                    ax1.set_ylabel(get_yAxis(df, curve))
                    ax1.tick_params(axis='y')
                    y1_min, y1_max = ax1.get_ylim()
                    ax1.set_ylim(y1_min - 0.1*y1_min, y1_max + 0.1*y1_max)
                    y1_min -= 0.1*y1_min; y1_max += 0.1*y1_max
                else:
                    print(f"Data curve {type} not loaded/available.")

            elif type == rightAxis:
                # Create second y-axis
                if len(df[curve]['CurvePoints']) > 0:
                    ax2 = ax1.twinx()
                    if df[curve][xAxis] is not None:
                        sns.lineplot(x=df[curve][xAxis], y=df[curve]['CurvePoints'], ax=ax2, label=type, color=palette[i], sort=False, errorbar=None)
                    else:
                        sns.lineplot(x=df[curve]['xarr'], y=df[curve]['CurvePoints'], ax=ax2, label=type, color=palette[i], sort=False, errorbar=None)
                    ax2.set_ylabel(get_yAxis(df, curve))
                    ax2.get_legend().remove()

                    # --- Align right-axis ticks with left-axis ---
                    left_ticks = ax1.get_yticks()[1:-1]       # Get tick positions from left axis
                    y2_min, y2_max = ax2.get_ylim()
                    # Map left-axis ticks to right-axis scale
                    right_ticks = y2_min + (left_ticks - y1_min) / (y1_max - y1_min) * (y2_max - y2_min)
                    ax2.set_yticks(right_ticks)
                    ax2.tick_params(axis='y')
                else:
                    print(f"Data curve {type} not loaded/available.")

            else:
                if len(df[curve]['CurvePoints']) > 0:
                    if df[curve][xAxis] is not None:
                        sns.lineplot(x=df[curve][xAxis], y=df[curve]['CurvePoints'], ax=ax1, label=type, color=palette[i], sort=False, errorbar=None)
                    else:
                        sns.lineplot(x=df[curve]['xarr'], y=df[curve]['CurvePoints'], ax=ax1, label=type, color=palette[i], sort=False, errorbar=None)
                    ymin = np.min(df[curve]['CurvePoints'])
                    ymax = np.max(df[curve]['CurvePoints'])
                    # ax1.set_ylim(4.8, ymax + 0.1*ymax)
                else:
                   print(f"Data curve {type} not loaded/available.") 
        else:
            print("Type {} does not exist.".format(type))

    # --- Automatically merge legends ---
    if ax1 and ax2:
        axes = [ax1, ax2]          # list of all axes
        lines = []
        labels = []

        for ax in axes:
            lns, lbs = ax.get_legend_handles_labels()
            lines.extend(lns)
            labels.extend(lbs)

        ax1.legend(lines, labels, loc='upper right')  # one combined legend

    # add fractionation events as a second x-axis (top)
    if addFracs and df[curve][xAxis] is not None:
        if fractionValues is None or fractionLabels is None:
            print("Provide fraction values and labels.")
        else:
            # Extract x-positions from provided fraction values (use second column like before)
            try:
                fv = np.asarray(fractionValues)
                x_positions = fv[:, 1].astype(float)
            except Exception:
                x_positions = [float(frac[1]) for frac in fractionValues]

            # Keep only positions within current x-limits
            x_min, x_max = ax1.get_xlim()
            in_range = [(x, lbl) for x, lbl in zip(x_positions, fractionLabels) if x_min <= x <= x_max]

            if in_range:
                xs, lbls = zip(*in_range)
                # Optionally skip 'Waste' labels to reduce clutter
                xs2, lbls2 = [], []
                for x, l in zip(xs, lbls):
                    if l == "Waste" or l == "Frac":
                        continue
                    xs2.append(x)
                    lbls2.append(l)
                if not xs2:  # if all were 'Waste', fall back to all
                    xs2, lbls2 = list(xs), list(lbls)

                ax_bottom = ax1.twiny()
                ax_bottom.set_xlim(ax1.get_xlim())

                # Dynamically thin tick labels if they would overlap: keep labels at least
                # a threshold number of display pixels apart along x.
                xs_arr = np.asarray(xs2, dtype=float)
                lbls_arr = list(lbls2)
                order = np.argsort(xs_arr)
                xs_sorted = xs_arr[order]
                lbls_sorted = [lbls_arr[i] for i in order]

                # Convert data x positions to display pixels using the twin axis transform
                pts = ax_bottom.transData.transform(
                    np.column_stack([xs_sorted, np.zeros_like(xs_sorted)])
                )
                xs_px = pts[:, 0]

                # Pixel threshold for minimum spacing between adjacent labels
                threshold_px = 55  # adjust if needed
                kept_sorted_idx = []
                last_px = None
                for i, px in enumerate(xs_px):
                    if last_px is None or (px - last_px) >= threshold_px:
                        kept_sorted_idx.append(i)
                        last_px = px
                # Ensure last label is included; if it's too close, replace previous
                if len(xs_px) and (not kept_sorted_idx or kept_sorted_idx[-1] != len(xs_px) - 1):
                    if kept_sorted_idx and (xs_px[-1] - xs_px[kept_sorted_idx[-1]] < threshold_px):
                        kept_sorted_idx[-1] = len(xs_px) - 1
                    else:
                        kept_sorted_idx.append(len(xs_px) - 1)

                # Build labels array the same length/order as xs2, leaving non-kept positions blank
                kept_orig_idx = order[kept_sorted_idx]
                lbls_all = ["" for _ in range(len(lbls2))]
                for idx in kept_orig_idx:
                    lbls_all[int(idx)] = lbls2[int(idx)]

                # Keep ticks at all original positions; only show labels at kept indices
                ax_bottom.set_xticks(xs2)
                # Draw ticks on the bottom side of this twin axis, but place labels above the ticks (inside) via negative pad
                ax_bottom.tick_params(
                    axis='x', top=False, bottom=True,
                    labeltop=False, labelbottom=True,
                    length=10, direction='in', color='red', pad=-label_height #-0.04*y1_max
                )
                ax_bottom.set_xticklabels(lbls_all, rotation=45, ha='center', color='red')
                # Style the axis: hide the bottom spine to avoid double spine with the main axis
                ax_bottom.spines['bottom'].set_visible(False)
                ax_bottom.grid(False)
            else:
                print("No fraction ticks within current x-limits.")

    if ax2 is not None:
        return fig, ax1, ax2
    else:
        return fig, ax1
