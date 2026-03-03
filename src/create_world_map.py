#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm

import matplotlib.colors as mcolors


WORLD_URL = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"

# ----------------------------
# Harmonize country names
# ----------------------------
def harmonize_country_names(df):
    mapping = {
        "United States": "United States of America",
        "Russia": "Russian Federation",
        "Congo": "Republic of the Congo",
        "Congo, Dem. Rep.": "Democratic Republic of the Congo",
        "Ivory Coast": "Côte d'Ivoire",
        "South Korea": "Republic of Korea",
        "North Korea": "Democratic People's Republic of Korea",
        "Hong Kong": "China",
        "EU": None
    }
    df["Country"] = df["Country"].replace(mapping)
    return df

# ----------------------------
# Create the world maps
# ----------------------------
def create_world_maps(input_csv, output_png, output_pdf):
    # Load data
    df = pd.read_csv(input_csv)

    # Keep only health-relevant documents
    df = df[df["Health relevance (1/0)"] >= 1]

    # Split pre/post 2015
    bef2015 = df[(df["Year"] >= 2000) & (df["Year"] <= 2015)].copy()
    aft2015 = df[df["Year"] >= 2016].copy()

    # Aggregate totals by country
    bef_counts = bef2015.groupby("Country")["Total documents"].sum().reset_index()
    aft_counts = aft2015.groupby("Country")["Total documents"].sum().reset_index()

    bef_counts = harmonize_country_names(bef_counts)
    aft_counts = harmonize_country_names(aft_counts)

    # Load world map
    world = gpd.read_file(WORLD_URL)


    world1 = world.merge(bef_counts, how="left", left_on="NAME", right_on="Country")
    world1["Total documents"] = world1["Total documents"].fillna(0)

    world2 = world.merge(aft_counts, how="left", left_on="NAME", right_on="Country")
    world2["Total documents"] = world2["Total documents"].fillna(0)

    # ----------------------------
    # Define human-readable bins and colors
    # ----------------------------
    # Determine max value across both datasets
    vmax = max(
        world1["Total documents"].max(skipna=True),
        world2["Total documents"].max(skipna=True)
    )

    # Define intuitive bins
    # Compute max across both panels
    global_max = max(world1["Total documents"].max(), world2["Total documents"].max())

    # Generate finer bins for gradient: e.g., 0 (grey) + increments of 1 up to a reasonable max
    low_bins = list(range(0, min(global_max, 20)+1))  # increments of 1 for 0–20
    high_bins = list(range(21, int(global_max)+5, max(1,int(global_max/10))))
    bins = sorted(list(set(low_bins + high_bins)))

    # Remove duplicates and sort
    bins = sorted(list(set(bins)))


    # Color list: 0 = grey, low→high = green gradient
    # Grey for zero
    grey = [0.8, 0.8, 0.8, 1]  

    # Gradient for non-zero counts: light green → dark green
    num_gradients = len(bins) - 1  # exclude 0
    greens = plt.cm.Greens(np.linspace(0.2, 1, num_gradients))  # start at 0.2 for lighter shades

    # Combine: first grey for 0, then green gradient
    colors_list = np.vstack([grey, greens])
    cmap = ListedColormap(colors_list)

    # Norm for mapping bins to colors
    norm = BoundaryNorm(bins, cmap.N)
    # ----------------------------
    # Plot
    # ----------------------------
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # ---- Panel 1: Pre-2015 ----
    world.boundary.plot(ax=axes[0], linewidth=0.4, color="black")
    world1.plot(column="Total documents", cmap=cmap, norm=norm, ax=axes[0], edgecolor="none")
    axes[0].set_title("2000-2015", fontsize=16, fontweight="bold")
    axes[0].axis("off")

    # ---- Panel 2: Post-2015 ----
    world.boundary.plot(ax=axes[1], linewidth=0.4, color="black")
    world2.plot(column="Total documents", cmap=cmap, norm=norm, ax=axes[1], edgecolor="none")
    axes[1].set_title("2016-2025", fontsize=16, fontweight="bold")
    axes[1].axis("off")

    # ---- Shared legend/colorbar ----
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])

    '''cbar = fig.colorbar(
        sm,
        ax=axes,
        orientation="horizontal",
        fraction=0.03,   # thickness of the colorbar
        pad=0.50         # move the colorbar further down from axes
    )'''

    # Create colorbar in custom position: full width at the bottom, below the maps
    cbar_ax = fig.add_axes([0.12, 0.05, 0.76, 0.02])  # [left, bottom, width, height]
    cbar = plt.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label("Total Documents", fontsize=12)

    # Optional: human-readable tick labels
    num_ticks = 8
    tick_indices = np.linspace(0, len(bins)-1, num_ticks, dtype=int)
    cbar.set_ticks([bins[i] for i in tick_indices])
    cbar.set_ticklabels([str(bins[i]) for i in tick_indices])



    plt.tight_layout()

    # Save outputs
    fig.savefig(output_png, dpi=300, bbox_inches="tight")
    fig.savefig(output_pdf, bbox_inches="tight")
    plt.close(fig)

# ----------------------------
# CLI entry point
# ----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Create pre/post-2015 global health document maps"
    )
    parser.add_argument("--input", required=True, help="Path to country_year_health_stats.csv")
    parser.add_argument("--png", required=True, help="Output PNG path")
    parser.add_argument("--pdf", required=True, help="Output PDF path")

    args = parser.parse_args()

    create_world_maps(
        input_csv=args.input,
        output_png=args.png,
        output_pdf=args.pdf
    )

if __name__ == "__main__":
    main()
