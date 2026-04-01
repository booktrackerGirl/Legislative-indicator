#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

PLOT_START_YEAR = 2000
REL_THRESHOLD = 0.10
MARKERS = ["o", "s", "^", "D", "v", "P", "*", "X", "<", ">"]
LINESTYLES = ["-", "--", "-.", ":"]

# --- Human-readable labels ---
CATEGORY_LABELS = {
    "general_health": "General Health & Services",
    "mortality_morbidity": "Mortality & Morbidity",
    "injury_trauma": "Injury & Trauma",
    "communicable_disease": "Communicable Diseases",
    "non_communicable_disease": "Non-Communicable Diseases",
    "maternal_child_health": "Maternal & Child Health",
    "nutrition": "Nutrition",
    "mental_health": "Mental Health",
    "substance_use": "Substance Use",
    "environmental_health": "Environmental Health",
    "climate_environment": "Climate & Environment",
    "vector_borne_zoonotic": "Vector-borne & Zoonotic Diseases",
    "food_waterborne": "Food & Waterborne Illnesses",
    "pathogens_microbiology": "Pathogens & Microbiology"
}


# --------------------------------------------------
# Generate globally distinct colors
# --------------------------------------------------
def generate_distinct_colors(n):
    """
    Generate n maximally separated categorical colors.
    Even spacing in HSV space ensures no duplicates.
    """
    hues = np.linspace(0, 1, n, endpoint=False)
    return [mcolors.hsv_to_rgb((h, 0.85, 0.9)) for h in hues]


# --------------------------------------------------
# ACTIVE STOCK (Region × Health Category)
# --------------------------------------------------
def compute_active_stock(annotation_df, panel_df, group_col="LC"):

    '''if "Doc ID" in annotation_df.columns:
        annotation_df = annotation_df.rename(columns={"Doc ID": "Document ID"})'''

    annotation_df = annotation_df[
        annotation_df["Health relevance (1/0)"] >= 1
    ].copy()

    annotation_df = annotation_df.dropna(
        subset=["Health keyword categories"]
    )

    annotation_df["Health keyword categories"] = (
        annotation_df["Health keyword categories"]
        .astype(str)
        .str.split(";")
    )

    annotation_df = annotation_df.explode(
        "Health keyword categories"
    )

    annotation_df["Health keyword categories"] = (
        annotation_df["Health keyword categories"]
        .str.strip()
    )

    df = panel_df.merge(
        annotation_df,
        on="Family ID",
        how="inner"
    )

    if "Year_x" in df.columns:
        df = df.rename(columns={"Year_x": "Year"})
    if "Year_y" in df.columns:
        df = df.drop(columns=["Year_y"])

    df["Year"] = df["Year"].astype(int)

    # Keep fixed conceptual order if available
    health_categories = [
        c for c in CATEGORY_LABELS.keys()
        if c in df["Health keyword categories"].unique()
    ]

    regions = sorted(df[group_col].dropna().unique())

    max_year = min(df["Year"].max(), 2025)
    years_range = list(range(PLOT_START_YEAR, max_year + 1))

    results = {}

    for cat in health_categories:
        results[cat] = {}

        for region in regions:

            subset = df[
                (df["Health keyword categories"] == cat) &
                (df[group_col] == region)
            ]

            active_set = set()
            yearly_stock = []

            for year in years_range:

                new_docs = set(
                    subset.loc[
                        subset["Year"] == year,
                        "Family ID"
                    ]
                )

                active_set |= new_docs
                yearly_stock.append(len(active_set))

            results[cat][region] = yearly_stock

    return results, years_range, health_categories, regions


# --------------------------------------------------
# Plotting
# --------------------------------------------------
def plot_health_trends(results, years, categories, regions, output_path, group_col):

    n = len(categories)
    cols = 4
    rows = int(np.ceil(n / cols))

    fig, axes = plt.subplots(rows, cols, figsize=(20, 4 * rows), sharex=True)
    axes = axes.flatten()

    # ---- GLOBAL UNIQUE COLORS ----
    # Generate a distinct categorical palette for regions
    num_regions = len(regions)
    if num_regions <= 10:
        cmap = plt.get_cmap("tab10")
    else:
        cmap = plt.get_cmap("tab20")

    region_colors = [cmap(i % cmap.N) for i in range(num_regions)]

    for i, cat in enumerate(categories):

        ax = axes[i]

        y_max = max(max(results[cat][r]) for r in regions)
        offset = y_max * 0.02 if y_max > 0 else 0.1

        for j, region in enumerate(regions):

            marker = MARKERS[j % len(MARKERS)]
            linestyle = LINESTYLES[j % len(LINESTYLES)]

            region_color = region_colors[j]

            series = results[cat][region]

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
                if series[k - 1] == 0:
                    continue
                rel_change = (series[k] - series[k - 1]) / series[k - 1]
                if rel_change >= REL_THRESHOLD:
                    ax.text(
                        years[k],
                        series[k] + offset,
                        str(int(series[k])),
                        fontsize=6,
                        ha="center"
                    )

        ax.axvline(2016, linestyle="--", color="black", linewidth=1.2)
        ax.set_ylim(0, y_max * 1.15 if y_max > 0 else 1)

        label = CATEGORY_LABELS.get(cat, cat)

        ax.set_title(
            label,
            fontsize=11,
            fontweight="bold",
            loc="left"
        )

        ax.grid(axis="y", linestyle="--", alpha=0.3)

    # Remove empty axes
    for idx in range(n, len(axes)):
        fig.delaxes(axes[idx])

    # ---- BLACK LEGEND ----
    handles, labels = axes[0].get_legend_handles_labels()

    # No black markers — use the same colors as lines
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

    axes[-1].set_xlabel("Year")
    axes[-2].set_xlabel("Year")

    fig.suptitle(
        f"Active Stock of Health-Relevant Legislative Documents by Health Category and {group_col} Regions",
        fontsize=16,
        fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    plt.savefig(output_path, format="pdf", dpi=300, bbox_inches="tight")
    plt.close()


# --------------------------------------------------
# CLI
# --------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Regional active stock trends by health category"
    )
    parser.add_argument("--annotation", required=True)
    parser.add_argument("--panel", required=True)
    parser.add_argument("--group_col", required=True,
                        choices=["LC", "WHO", "HDI"])
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    panel_df = pd.read_csv(args.panel)

    results, years, categories, regions = compute_active_stock(
        annotation_df,
        panel_df,
        group_col=args.group_col
    )

    plot_health_trends(
        results,
        years,
        categories,
        regions,
        args.output,
        args.group_col
    )


if __name__ == "__main__":
    main()