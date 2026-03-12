#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DATA_START_YEAR = 1963
PLOT_START_YEAR = 2000

MARKERS = ["o", "s", "^", "D", "v", "P", "*", "X", "<", ">"]  # cycle markers if >10 groups

# ------------------------
# Active stock per region
# ------------------------
def compute_active_stock_by_region(annotation_df, panel_df, group_col="LC"):

    # Harmonize IDs
    '''if "Doc ID" in annotation_df.columns:
        annotation_df = annotation_df.rename(columns={"Doc ID": "Document ID"})'''
    
    # Keep health-relevant only
    annotation_df = annotation_df[annotation_df["Health relevance (1/0)"] >= 1].copy()

    # Merge panel and annotation data
    df = panel_df.merge(annotation_df, on="Family ID", how="inner")

    # Resolve overlapping 'Year' columns if needed
    if "Year_x" in df.columns:
        df = df.rename(columns={"Year_x": "Year"})
    if "Year_y" in df.columns:
        df = df.drop(columns=["Year_y"])
    
    df["Year"] = df["Year"].astype(int)

    # Prepare grouping
    groups = df[group_col].dropna().unique()
    max_year = min(df["Year"].max(), 2025)
    years_range = list(range(PLOT_START_YEAR, max_year + 1))

    region_active = {g: [] for g in groups}

    # Compute active stock per year for each group
    for g in groups:
        group_docs = df[df[group_col] == g]["Family ID"].unique()
        active_set = set()
        yearly_totals = []

        for year in years_range:
            # New documents starting this year
            new_docs = set(df.loc[
                (df[group_col] == g) & (df["Year"] == year),
                "Family ID"
            ])
            active_set = active_set.union(new_docs)
            yearly_totals.append(len(active_set))
        
        region_active[g] = yearly_totals

    # Build plotting DataFrame
    plot_df = pd.DataFrame({"Year": years_range})
    for g in groups:
        plot_df[g] = region_active[g]

    return plot_df


# ------------------------
# Plotting function
# ------------------------
def plot_region_trends(plot_df, output_path, group_col="LC"):

    plt.figure(figsize=(14, 7))
    colors = plt.cm.tab10.colors  # up to 10 groups
    groups = [c for c in plot_df.columns if c != "Year"]
    # Determine dynamic vertical offset
    y_max = plot_df[groups].values.max()
    offset = y_max * 0.015   # 3.5% vertical shift
    REL_THRESHOLD = 0.10   # 10% relative increase required

    for i, col in enumerate(groups):
        marker = MARKERS[i % len(MARKERS)]
        plt.plot(
            plot_df["Year"], 
            plot_df[col], 
            marker=marker, 
            linewidth=2.5, 
            label=str(col), 
            color=colors[i % len(colors)]
        )
        

        # Annotate only meaningful relative increases
        for idx in range(1, len(plot_df)):
            x = plot_df["Year"].iloc[idx]
            y = plot_df[col].iloc[idx]
            y_prev = plot_df[col].iloc[idx - 1]

            # Avoid division by zero
            if y_prev == 0:
                continue

            relative_change = (y - y_prev) / y_prev

            if relative_change >= REL_THRESHOLD:
                plt.text(
                    x,
                    y + offset,
                    str(int(y)),
                    fontsize=6,
                    ha="center",
                    va="bottom",
                    alpha=0.9
                )

    plt.axvline(x=2015, linestyle="--", color="black", linewidth=1.8)
    plt.ylim(0, y_max * 1.15)
    plt.text(2015 + 0.2, y_max * 1.05, "Paris Agreement", fontsize=10)

    plt.title(f"Active Health-Relevant Legislative Documents by {group_col} (Timeline Stock)", fontsize=14, fontweight="bold", loc="left")
    plt.xlabel("Year")
    plt.ylabel("Active documents")
    plt.grid(axis="y", linestyle="--", alpha=0.4)
    plt.legend(title=group_col)
    plt.tight_layout()
    plt.savefig(output_path, format="pdf", dpi=300)
    plt.close()


# ------------------------
# CLI
# ------------------------
def main():
    parser = argparse.ArgumentParser(description="Regional active stock trends of health-relevant documents")
    parser.add_argument("--annotation", required=True, help="Path to health annotation CSV")
    parser.add_argument("--panel", required=True, help="Path to policy-year panel CSV")
    parser.add_argument("--group_col", required=True, choices=["LC", "WHO", "HDI"], help="Grouping column for regions")
    parser.add_argument("--output", required=True, help="Output PDF file path")
    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    panel_df = pd.read_csv(args.panel)

    plot_df = compute_active_stock_by_region(annotation_df, panel_df, group_col=args.group_col)
    plot_region_trends(plot_df, args.output, group_col=args.group_col)


if __name__ == "__main__":
    main()