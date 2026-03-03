import argparse
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import textwrap
import matplotlib.colors as mc

# Colors for each stage (consistent across regions)
STAGE_COLORS = {
    "Total": "#4D4D4D",          # darker gray
    "Health": "#1F77B4",         # saturated blue
    "Adaptation": "#2CA02C",     # vivid green
    "Institutional": "#9467BD"   # rich purple
}

# Descriptive stage labels
STAGES = [
    ("Total documents", "Total"),
    ("Health relevance (1/0)", "Presence of relevant health-related content"),
    ("Health adaptation mandate (1/0)", "Adaptation mandates addressing health risks"),
    ("Institutional health role (1/0)", "Mentions of health institutions/roles"),
]

# Map descriptive label back to short color key
LABEL_TO_COLOR_KEY = {
    "Total": "Total",
    "Presence of relevant health-related content": "Health",
    "Adaptation mandates addressing health risks": "Adaptation",
    "Mentions of health institutions/roles": "Institutional"
}

def lighten(color, factor=0.4):
    """Lighten a hex color"""
    c = mc.to_rgb(color)
    return tuple(1 - factor * (1 - x) for x in c)

def wrap_label(label, width=12):
    """Wrap long region labels for X-axis"""
    return "\n".join(textwrap.wrap(label, width))

def aggregate(df):
    """Aggregate counts by region"""
    return df.groupby("Region", as_index=False).agg({
        "Total documents": "sum",
        "Health relevance (1/0)": "sum",
        "Health adaptation mandate (1/0)": "sum",
        "Institutional health role (1/0)": "sum"
    })

def plot_panel(ax, df, title):
    regions = df["Region"].tolist()
    x = np.arange(len(regions))
    width = 0.18

    for i, (col_name, stage_label) in enumerate(STAGES):
        # Map descriptive label to color key
        color_key = LABEL_TO_COLOR_KEY[stage_label]
        base_color = STAGE_COLORS[color_key]
        light_color = lighten(base_color)

        positives = df[col_name].values

        if i == 0:
            negatives = np.zeros_like(positives)
            denominators = positives
        else:
            prev = df[STAGES[i - 1][0]].values
            negatives = prev - positives
            denominators = prev

        # Draw positive portion
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

        # Add value labels on top of bars
        for bar, val in zip(bars_pos, positives):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.5,
                f"{int(val)}",
                ha="center",
                va="bottom",
                fontsize=8
            )

    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels([wrap_label(r) for r in regions])
    ax.set_ylabel("Number of documents")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

def main(input_csv, output):
    df = pd.read_csv(input_csv)
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    # Keep only 2000+ years
    df = df[df["Year"] >= 2000].copy()

    # Split pre/post 2015
    # Pre-Paris: 2000–2015
    pre = aggregate(df[(df["Year"] >= 2000) & (df["Year"] <= 2015)])
    # Post-Paris: 2016 onwards
    post = aggregate(df[df["Year"] >= 2016])

    fig, axes = plt.subplots(1, 2, figsize=(20, 12), sharey=True)

    plot_panel(axes[0], pre, "2000-2015")
    plot_panel(axes[1], post, "2016 and after")

    # Legend
    fig.legend(
        title="Policy stage",
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, 0.92),
        frameon=False
    )

    # Main title
    fig.suptitle(
        "Aggregated Regional Climate–Health Legislative Presence Before and After the Paris Agreement (2000–2025)",
        fontsize=20,
        y=0.95,
        fontweight="bold"
    )

    # Figure caption
    fig.text(
        0.5, 0.1,
        "Each region forms a cluster of four bars: Total documents → Health relevance → "
        "Health adaptation mandate → Institutional health role.\n"
        "Darker segments indicate documents reaching the stage; lighter segments indicate drop-off from the previous stage.",
        ha="center",
        fontsize=9
    )

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22, top=0.82)


    fig.savefig(output, dpi=300)
    plt.close(fig)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Static clustered cascade bar charts (pre/post 2015) with descriptive stage labels"
    )
    parser.add_argument("--input", required=True, help="Path to df_summary CSV")
    parser.add_argument(
        "--output",
        default="regional_health_cascade_bars_pre_post_2015.pdf",
        help="Output file (pdf/png/svg)"
    )

    args = parser.parse_args()
    main(args.input, args.output)
