#!/usr/bin/env python3

import argparse
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np

# ----------------------------
# Harmonize country names
# ----------------------------
def harmonize_country_names(df):
    df = df[df["ISO3"] != "EUR"].copy()  # remove EU
    df.loc[df["ISO3"] == "TWN", "ISO3"] = "CHN"  # map Taiwan to China
    df["ISO3"] = df["ISO3"].str.strip().str.upper()
    return df

# ----------------------------
# Compute cumulative active stock per year
# ----------------------------
def compute_active_stock(annotations, panel):
    """
    Computes cumulative active stock of health-relevant documents per country.
    Counts each document only once using panel data.
    """
    # Standardize column
    '''if "Doc ID" in annotations.columns:
        annotations = annotations.rename(columns={"Doc ID": "Document ID"})'''
    
    # Merge panel
    df = annotations.merge(panel, on="Family ID", how="left", suffixes=("", "_panel"))
    
    # Use Year from panel if available
    if "Year_panel" in df.columns:
        df["Year"] = df["Year_panel"]
    elif "Year" not in df.columns:
        raise ValueError("No 'Year' column found after merging panel data.")
    
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df[df["Year"].notna()]

    # Filter health-relevant and drop duplicates
    df = df[df["Health relevance (1/0)"] >= 1]
    df = df.drop_duplicates(subset=["Family ID", "ISO3"])
    df = harmonize_country_names(df)

    # Determine year range for cumulative counting
    start_year = int(df["Year"].min())  # could be before 2000
    end_year = int(df["Year"].max())
    years = list(range(start_year, end_year + 1))

    countries = df["ISO3"].unique()
    cum_dict = {c: [] for c in countries}

    for c in countries:
        active_docs = set()
        country_docs = df[df["ISO3"] == c]
        for y in years:
            # Include documents that started <= year
            new_docs = set(country_docs[country_docs["Year"] <= y]["Family ID"])
            active_docs.update(new_docs)
            cum_dict[c].append(len(active_docs))

    cum_df = pd.DataFrame({"Year": years})
    cum_cols = pd.DataFrame(cum_dict, index=years)
    cum_df = pd.concat([cum_df, cum_cols.reset_index(drop=True)], axis=1)

    return cum_df

# ----------------------------
# Aggregate by display period
# ----------------------------
def aggregate_period(cum_df, start_year, end_year):
    period_df = cum_df[(cum_df["Year"] >= start_year) & (cum_df["Year"] <= end_year)]
    # Take last year as cumulative total
    agg = period_df.iloc[-1, 1:].reset_index()
    agg.columns = ["ISO3", "Total documents"]
    return agg

# ----------------------------
# Plot map
# ----------------------------
def plot_world_map(shapefile, agg_df, title, ax, cmap, norm):
    gdf = gpd.read_file(shapefile)
    agg_df["ISO3"] = agg_df["ISO3"].str.strip()
    gdf["ISO_A3"] = gdf["ISO_A3"].str.strip().str.upper()

    merged = gdf.merge(agg_df, how="left", left_on="ISO_A3", right_on="ISO3")
    merged["Total documents"] = merged["Total documents"].fillna(0)

    merged.plot(column="Total documents",
                cmap=cmap,
                norm=norm,
                edgecolor="black",
                linewidth=0.2,
                ax=ax,
                legend=False)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_facecolor("#dceaf6")

# ----------------------------
# Main function
# ----------------------------
def main(annotations_csv, panel_csv, shapefile, output_png, output_pdf):
    annotations = pd.read_csv(annotations_csv)
    panel = pd.read_csv(panel_csv)

    # Compute cumulative stock
    cum_df = compute_active_stock(annotations, panel)

    # Aggregate for display period (from 2000 onward)
    agg_df = aggregate_period(cum_df, start_year=2000, end_year=2025)

    # Color scheme
    vmax = agg_df["Total documents"].max()
    low_bins = list(range(0, min(vmax, 20)+1))
    high_bins = list(range(21, int(vmax)+5, max(1,int(vmax/10))))
    bins = sorted(list(set(low_bins + high_bins)))

    grey = [0.8, 0.8, 0.8, 1]
    greens = plt.cm.Greens(np.linspace(0.2, 1, len(bins)-1))
    colors_list = np.vstack([grey, greens])
    cmap = ListedColormap(colors_list)
    norm = BoundaryNorm(bins, cmap.N)

    # Plot
    fig, ax = plt.subplots(figsize=(16, 9))
    plot_world_map(shapefile, agg_df, "Global Active Health-Relevant Legislative Documents (2000–2025)", ax, cmap, norm)

    # Colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.05, pad=0.04)
    cbar.set_label("Total Documents", fontsize=12)

    plt.tight_layout()
    fig.savefig(output_png, dpi=300, bbox_inches="tight")
    fig.savefig(output_pdf, bbox_inches="tight")
    plt.close()
    print(f"Map saved as {output_png} and {output_pdf}")

# ----------------------------
# CLI
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--panel", required=True)
    parser.add_argument("--shapefile", required=True)
    parser.add_argument("--output_png", required=True)
    parser.add_argument("--output_pdf", required=True)
    args = parser.parse_args()

    main(args.input_csv, args.panel, args.shapefile, args.output_png, args.output_pdf)