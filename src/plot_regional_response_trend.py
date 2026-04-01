#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import math

PLOT_START_YEAR = 2000
REL_THRESHOLD = 0.10
MARKERS = ["o", "s", "^", "D", "v", "P", "*", "X", "<", ">"]
LINESTYLES = ["-", "--", "-.", ":"]

# --------------------------------------------------
# ACTIVE STOCK (Region × Response)
# --------------------------------------------------
def compute_active_stock(annotation_df, panel_df, group_col="LC"):

    '''if "Doc ID" in annotation_df.columns:
        annotation_df = annotation_df.rename(columns={"Doc ID": "Document ID"})'''

    # Keep health-relevant
    annotation_df = annotation_df[annotation_df["Health relevance (1/0)"] >= 1].copy()

    # Explode multiple response types
    annotation_df = annotation_df.dropna(subset=["Response"])
    annotation_df["Response"] = annotation_df["Response"].astype(str).str.split(";")
    annotation_df = annotation_df.explode("Response")
    annotation_df["Response"] = annotation_df["Response"].str.strip()

    df = panel_df.merge(annotation_df, on="Family ID", how="inner")

    if "Year_x" in df.columns:
        df = df.rename(columns={"Year_x": "Year"})
    if "Year_y" in df.columns:
        df = df.drop(columns=["Year_y"])

    df["Year"] = df["Year"].astype(int)

    response_types = sorted(df["Response"].unique())
    regions = sorted(df[group_col].dropna().unique())

    max_year = min(df["Year"].max(), 2025)
    years_range = list(range(PLOT_START_YEAR, max_year + 1))

    results = {}
    for resp in response_types:
        results[resp] = {}
        for region in regions:
            subset = df[(df["Response"] == resp) & (df[group_col] == region)]
            active_set = set()
            yearly_stock = []
            for year in years_range:
                new_docs = set(subset.loc[subset["Year"] == year, "Family ID"])
                active_set |= new_docs
                yearly_stock.append(len(active_set))
            results[resp][region] = yearly_stock

    return results, years_range, response_types, regions

# --------------------------------------------------
# PLOTTING FUNCTION
# --------------------------------------------------
def plot_response_trends(results, years, responses, regions, output_path, group_col):

    n = len(responses)
    cols = 2
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(10*cols, 5*rows), sharex=True)
    axes = axes.flatten()

    # ---- REGION COLORS USING tab10/tab20 ----
    num_regions = len(regions)
    cmap = plt.get_cmap("tab10") if num_regions <= 10 else plt.get_cmap("tab20")
    region_colors = [cmap(i % cmap.N) for i in range(num_regions)]

    for i, resp in enumerate(responses):

        ax = axes[i]

        y_max = max(max(results[resp][r]) for r in regions)
        offset = y_max * 0.02 if y_max > 0 else 0.1

        for j, region in enumerate(regions):

            marker = MARKERS[j % len(MARKERS)]
            linestyle = LINESTYLES[j % len(LINESTYLES)]
            region_color = region_colors[j]
            series = results[resp][region]

            ax.plot(
                years,
                series,
                marker=marker,
                linewidth=2,
                linestyle=linestyle,
                label=str(region),
                color=region_color
            )

            # Relative growth annotation
            for k in range(1, len(series)):
                if series[k-1] == 0:
                    continue
                rel_change = (series[k] - series[k-1]) / series[k-1]
                if rel_change >= REL_THRESHOLD:
                    ax.text(years[k], series[k]+offset, str(int(series[k])), fontsize=6, ha="center")

        ax.axvline(2016, linestyle="--", color="black", linewidth=1.2)
        ax.set_ylim(0, y_max*1.15 if y_max > 0 else 1)
        ax.set_title(f"{resp}", fontsize=12, fontweight="bold", loc="left")
        ax.grid(axis="y", linestyle="--", alpha=0.3)

    # Remove unused axes
    for idx in range(n, len(axes)):
        fig.delaxes(axes[idx])

    # ---- LEGEND ----
    handles, labels = axes[0].get_legend_handles_labels()
    new_handles = [
        plt.Line2D([], [], marker=MARKERS[i % len(MARKERS)],
                   linestyle=LINESTYLES[i % len(LINESTYLES)],
                   color=region_colors[i],
                   markerfacecolor=region_colors[i],
                   markeredgecolor=region_colors[i],
                   linewidth=1.8)
        for i in range(len(labels))
    ]

    fig.legend(
        new_handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=min(len(regions), 6),
        title=group_col,
        frameon=True
    )

    for ax in axes[-cols:]:
        ax.set_xlabel("Year")

    fig.suptitle(
        f"Active Stock of Health-Relevant Legislative Documents by Response Type and {group_col} Regions",
        fontsize=16, fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(output_path, format="pdf", dpi=300, bbox_inches="tight")
    plt.close()

# --------------------------------------------------
# CLI
# --------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Regional active stock trends by Response type")
    parser.add_argument("--annotation", required=True)
    parser.add_argument("--panel", required=True)
    parser.add_argument("--group_col", required=True, choices=["LC","WHO","HDI"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    panel_df = pd.read_csv(args.panel)

    results, years, responses, regions = compute_active_stock(annotation_df, panel_df, group_col=args.group_col)
    plot_response_trends(results, years, responses, regions, args.output, args.group_col)

if __name__ == "__main__":
    main()