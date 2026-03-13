#!/usr/bin/env python3

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import matplotlib.colors as mc

# Colors for each stage
STAGE_COLORS = {
    "Total": "#4D4D4D",        # darker gray
    "Health": "#9467BD",        # rich purple
    "Institutional": "#2CA02C" # green
}

STAGES = [
    ("Total documents", "Total"),
    ("Health relevance (1/0)", "Health"),
    ("Institutional health role (1/0)", "Institutional")
]

LABEL_TO_COLOR_KEY = {
    "Total": "Total",
    "Health": "Health",
    "Institutional": "Institutional"
}

def lighten(color, factor=0.4):
    c = mc.to_rgb(color)
    return tuple(1 - factor * (1 - x) for x in c)

def wrap_label(label, width=12):
    return "\n".join(textwrap.wrap(str(label), width))

# -------------------------------
# Aggregate by chosen grouping
# -------------------------------
def aggregate(df, region_col):
    total = df.groupby(region_col)["Family ID"].nunique().rename("Total documents")
    health = df[df["Health relevance (1/0)"] == 1].groupby(region_col)["Family ID"].nunique().rename("Health relevance (1/0)")
    institutional = df[df["Institutional health role (1/0)"] == 1].groupby(region_col)["Family ID"].nunique().rename("Institutional health role (1/0)")
    out = pd.concat([total, health, institutional], axis=1).fillna(0).reset_index()
    out = out.rename(columns={region_col: "Region"})
    return out

def plot_panel(ax, df, title):
    regions = df["Region"].tolist()
    x = np.arange(len(regions))
    width = 0.22

    for i, (col_name, stage_label) in enumerate(STAGES):
        color_key = LABEL_TO_COLOR_KEY[stage_label]
        base_color = STAGE_COLORS[color_key]
        light_color = lighten(base_color)
        positives = df[col_name].values

        if i == 0:
            negatives = np.zeros_like(positives)
        else:
            prev = df[STAGES[i - 1][0]].values
            negatives = prev - positives

        bars_pos = ax.bar(
            x + i * width,
            positives,
            width,
            color=base_color,
            edgecolor="black",
            linewidth=0.3,
            label=stage_label if ax == ax.figure.axes[0] else None
        )

        # Draw drop-off portion
        ax.bar(
            x + i * width,
            negatives,
            width,
            bottom=positives,
            color=light_color,
            edgecolor="black",
            linewidth=0.3
        )

        # Value labels slightly higher
        for bar, val in zip(bars_pos, positives):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1.5,  # pushed upward
                f"{int(val)}",
                ha="center",
                va="bottom",
                fontsize=8
            )

    ax.set_title(title, fontsize=11, fontweight="bold", pad=15)
    ax.set_xticks(x + width)
    ax.set_xticklabels([wrap_label(r) for r in regions])
    ax.set_ylabel("Number of documents")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

# -------------------------------
# Main
# -------------------------------
def main(input_csv, region_col, output):
    df = pd.read_csv(input_csv)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df[df["Year"] >= 2000].copy()

    # Count each document once per Family ID + region
    df = df.drop_duplicates(subset=["Family ID", region_col])

    pre = aggregate(df[(df["Year"] >= 2000) & (df["Year"] <= 2015)], region_col)
    post = aggregate(df[df["Year"] >= 2016], region_col)

    fig, axes = plt.subplots(1, 2, figsize=(12, 7.2), sharey=True)

    plot_panel(axes[0], pre, "2000–2015")
    plot_panel(axes[1], post, "2016–2025")

    fig.legend(
        title="Policy stage",
        loc="upper center",
        ncol=3,
        bbox_to_anchor=(0.5, 0.92),
        frameon=False
    )

    fig.suptitle(
        "Regional Climate–Health Legislative Presence Before and After the Paris Agreement (2000–2025)",
        fontsize=12,
        y=0.95,
        fontweight="bold"
    )

    fig.text(
        0.5,
        0.1,
        "Each region forms a cluster of three bars: Total documents → Health relevance → Institutional health role.",
        ha="center",
        fontsize=9
    )

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22, top=0.82)
    fig.savefig(output, dpi=300)
    plt.close(fig)

# -------------------------------
# CLI
# -------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Clustered cascade bar charts by region (Family ID aggregation)"
    )

    parser.add_argument("--input", required=True, help="Path to summary CSV")
    parser.add_argument(
        "--region",
        required=True,
        choices=["WHO", "HDI", "LC"],
        help="Choose grouping column"
    )
    parser.add_argument(
        "--output",
        default="regional_health_cascade_bars.pdf",
        help="Output file (pdf/png/svg)"
    )

    args = parser.parse_args()
    main(args.input, args.region, args.output)