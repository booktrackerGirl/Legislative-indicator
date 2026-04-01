#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ---------------- CONFIG ---------------- #

PLOT_START_YEAR = 2000
PLOT_END_YEAR = 2025

LC_CATEGORIES = ["Africa", "Asia", "Europe", "Latin America", "Oceania", "SIDS"]

WHO_CATEGORIES = [
    "Africa",
    "Americas",
    "Eastern Mediterranean",
    "Europe",
    "South-East Asia",
    "Western Pacific"
]

HDI_CATEGORIES = ["Very High", "High", "Medium", "Low"]

LC_COLORS = plt.cm.tab10.colors
WHO_COLORS = plt.cm.Set2.colors
HDI_COLORS = plt.cm.Pastel1.colors


# ---------------- FUNCTION ---------------- #

def plot_proportions(annotation_df, legis_df, output_path,
                     plot_start_year=PLOT_START_YEAR,
                     plot_end_year=PLOT_END_YEAR):

    annotation_df = annotation_df.copy()
    annotation_df["Response"] = annotation_df["Response"].fillna("")

    # ---------------- EXPAND TIMELINE ---------------- #

    df = legis_df[
        ["Family ID", "Full timeline of events (types)", "Full timeline of events (dates)"]
    ].copy()

    df["event_types"] = df["Full timeline of events (types)"].str.split(";")
    df["event_dates"] = df["Full timeline of events (dates)"].str.split(";")

    df_long = df.explode(["event_types", "event_dates"])
    df_long["event_types"] = df_long["event_types"].astype(str).str.strip()
    df_long["event_dates"] = df_long["event_dates"].astype(str).str.strip()

    df_long["Year"] = df_long["event_dates"].str[:4]
    df_long = df_long[df_long["Year"].str.match(r"^\d{4}$", na=False)]
    df_long["Year"] = df_long["Year"].astype(int)
    df_long = df_long[df_long["Year"] <= plot_end_year]

    # ---------------- EVENTS ---------------- #

    start_events = ["Passed/Approved", "Entered Into Force", "Set", "Net Zero Pledge"]
    end_events = ["Repealed/Replaced", "Closed", "Settled"]

    start_years = df_long[df_long["event_types"].isin(start_events)].groupby("Family ID")["Year"].min()
    end_years = df_long[df_long["event_types"].isin(end_events)].groupby("Family ID")["Year"].max()

    policy_years = pd.concat([start_years, end_years], axis=1)
    policy_years.columns = ["start_year", "end_year"]
    policy_years = policy_years.dropna(subset=["start_year"]).reset_index()

    # ---------------- MERGE ATTRIBUTES ---------------- #

    policy_years = policy_years.merge(
        annotation_df[
            ["Family ID", "Health relevance (1/0)", "LC", "WHO", "HDI"]
        ],
        on="Family ID",
        how="left"
    )

    policy_years["Health relevance (1/0)"] = policy_years["Health relevance (1/0)"].fillna(0)

    policy_years["end_year"] = policy_years["end_year"].apply(
        lambda x: min(x, plot_end_year) if pd.notnull(x) else x
    )

    # ---------------- YEARS ---------------- #

    YEARS = list(range(plot_start_year, plot_end_year + 1))

    # ---------------- ACTIVE SET LOGIC ---------------- #

    active_set = set()
    active_history = []

    for year in YEARS:
        new_docs = set(policy_years.loc[policy_years["start_year"] == year, "Family ID"])
        dropped_docs = set(policy_years.loc[policy_years["end_year"] == year, "Family ID"])

        active_set = active_set.union(new_docs)
        active_set = active_set.difference(dropped_docs)

        active_history.append(active_set.copy())

    # ---------------- GROUP CONFIG ---------------- #

    groups = {
        "Global": None,
        "LC": LC_CATEGORIES,
        "WHO": WHO_CATEGORIES,
        "HDI": HDI_CATEGORIES
    }

    color_maps = {
        "LC": LC_COLORS,
        "WHO": WHO_COLORS,
        "HDI": HDI_COLORS
    }

    results = {}

    # ---------------- COMPUTE PROPORTIONS ---------------- #

    for group_name, categories in groups.items():

        group_results = {}

        for category in (categories if categories else ["Global"]):

            proportions = []

            for i, year in enumerate(YEARS):

                active_set = active_history[i]
                active_df = policy_years[policy_years["Family ID"].isin(active_set)]

                total_global = len(active_df)

                if total_global == 0:
                    proportions.append(0)
                    continue

                if group_name == "Global":
                    subset_df = active_df
                else:
                    subset_df = active_df[active_df[group_name] == category]

                health_count = subset_df["Health relevance (1/0)"].sum()

                proportions.append((health_count / total_global) * 100)

            group_results[category] = proportions

        results[group_name] = group_results

    # ---------------- PLOTTING ---------------- #

    X = np.arange(len(YEARS))

    fig, axes = plt.subplots(2, 2, figsize=(14, 9), sharex=True, sharey=True)
    axes = axes.flatten()

    for ax, (group_name, group_data) in zip(axes, results.items()):

        if group_name == "Global":
            ax.plot(X, group_data["Global"], linewidth=2, label="Global")
        else:
            categories = list(group_data.keys())
            cmap = color_maps[group_name]

            for i, category in enumerate(categories):
                ax.plot(
                    X,
                    group_data[category],
                    linewidth=2,
                    color=cmap[i % len(cmap)],
                    label=category
                )

        ax.set_title(group_name)
        ax.set_ylim(0, 100)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        # X ticks every 5 years
        step = 5 if len(YEARS) > 20 else 2
        tick_years = YEARS[::step]
        tick_indices = [YEARS.index(y) for y in tick_years]

        ax.set_xticks(tick_indices)
        ax.set_xticklabels([str(y) for y in tick_years])

        if 2016 in YEARS:
            idx_2016 = YEARS.index(2016)
            x_2016 = X[idx_2016]

            ax.axvline(x=x_2016, linestyle="--", linewidth=0.5, color="black")

            ax.text(
                x_2016 - 0.5,
                ax.get_ylim()[1] * 0.9,
                "Paris Agreement in force (2016)",
                #rotation=90,
                va="top",
                fontsize=8
            )

        # ---------------- LABELS EVERY 5 YEARS ---------------- #
        label_step = 5

        for i in range(0, len(YEARS), label_step):
            x = X[i]

            for category, vals in group_data.items():
                y = vals[i]
                if y > 0:
                    ax.text(
                        x,
                        y,
                        f"{y:.1f}%",
                        fontsize=7,
                        ha="center",
                        va="bottom"
                    )

        ax.legend(fontsize=8)

    fig.supylabel("Proportion of health-relevant documents (%)")
    fig.supxlabel("Year")
    fig.suptitle(
        "Health-Relevant Share Over Time by Region / Development Group",
        fontsize=14,
        fontweight="bold"
    )

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(output_path, dpi=300)
    plt.close()


# ---------------- CLI ---------------- #

def main():
    parser = argparse.ArgumentParser(description="Proportion plots by LC, WHO, HDI")
    parser.add_argument("--annotation", required=True)
    parser.add_argument("--legis", required=True)
    parser.add_argument("--output", required=True)

    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    legis_df = pd.read_csv(args.legis)

    plot_proportions(annotation_df, legis_df, args.output)


if __name__ == "__main__":
    main()