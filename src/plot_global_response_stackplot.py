#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- CONFIG ---------------- #

RESPONSE_COLS = [
    "Adaptation",
    "Disaster Risk Management",
    "Loss And Damage",
    "Mitigation"
]

COLORS = {
    "Adaptation": "#4daf4a",
    "Disaster Risk Management": "#377eb8",
    "Loss And Damage": "#e41a1c",
    "Mitigation": "#984ea3"
}

DATA_START_YEAR = 1963
PLOT_START_YEAR = 2000
PLOT_END_YEAR = 2025  


# ---------------- PLOTTING FUNCTION ---------------- #

def plot_global_stackplot(annotation_df, legis_df, output_path,
                          plot_start_year=PLOT_START_YEAR, plot_end_year=PLOT_END_YEAR):

    # ---------------- FILTER HEALTH-RELEVANT ---------------- #
    annotation_health = annotation_df[annotation_df["Health relevance (1/0)"] >= 1].copy()
    annotation_health["Response"] = annotation_health["Response"].fillna("")

    legis_df_health = legis_df[legis_df["Family ID"].isin(annotation_health["Family ID"])].copy()

    # ---------------- EXPAND TIMELINE ---------------- #
    df = legis_df_health[
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

    # ---------------- START / END EVENTS ---------------- #
    start_events = ["Passed/Approved", "Entered Into Force", "Set", "Net Zero Pledge"]
    end_events = ["Repealed/Replaced", "Closed", "Settled"]

    start_years = df_long[df_long["event_types"].isin(start_events)].groupby("Family ID")["Year"].min()
    end_years = df_long[df_long["event_types"].isin(end_events)].groupby("Family ID")["Year"].max()

    policy_years = pd.concat([start_years, end_years], axis=1)
    policy_years.columns = ["start_year", "end_year"]
    policy_years = policy_years.dropna(subset=["start_year"])

    # ---------------- MERGE RESPONSE ---------------- #
    policy_years = policy_years.merge(
        annotation_health[["Family ID", "Response"]],
        on="Family ID",
        how="left"
    )
    policy_years["Response"] = policy_years["Response"].fillna("")

    for category in RESPONSE_COLS:
        policy_years[category] = policy_years["Response"].str.contains(
            category, case=False, regex=False
        ).astype(int)

    policy_years["end_year"] = policy_years["end_year"].apply(
        lambda x: min(x, plot_end_year) if pd.notnull(x) else x
    )

    # ---------------- STOCK LOGIC (HEALTH-RELEVANT) ---------------- #
    YEARS = list(range(plot_start_year, plot_end_year + 1))

    active_set = set()
    active_totals = []
    category_totals = {col: [] for col in RESPONSE_COLS}

    for year in YEARS:
        new_docs = set(policy_years.loc[policy_years["start_year"] == year, "Family ID"])
        dropped_docs = set(policy_years.loc[policy_years["end_year"] == year, "Family ID"])

        active_set = active_set.union(new_docs)
        active_set = active_set.difference(dropped_docs)

        active_totals.append(len(active_set))

        active_df = policy_years[policy_years["Family ID"].isin(active_set)]
        for col in RESPONSE_COLS:
            category_totals[col].append(active_df[col].sum())

    # ---------------- STOCK LOGIC (ALL DOCUMENTS) ---------------- #
    annotation_all = annotation_df.copy()
    legis_df_all = legis_df.copy()

    df_all = legis_df_all[
        ["Family ID", "Full timeline of events (types)", "Full timeline of events (dates)"]
    ].copy()

    df_all["event_types"] = df_all["Full timeline of events (types)"].str.split(";")
    df_all["event_dates"] = df_all["Full timeline of events (dates)"].str.split(";")

    df_long_all = df_all.explode(["event_types", "event_dates"])
    df_long_all["event_dates"] = df_long_all["event_dates"].astype(str).str.strip()

    df_long_all["Year"] = df_long_all["event_dates"].str[:4]
    df_long_all = df_long_all[df_long_all["Year"].str.match(r"^\d{4}$", na=False)]
    df_long_all["Year"] = df_long_all["Year"].astype(int)
    df_long_all = df_long_all[df_long_all["Year"] <= plot_end_year]

    start_years_all = df_long_all[df_long_all["event_types"].isin(start_events)].groupby("Family ID")["Year"].min()
    end_years_all = df_long_all[df_long_all["event_types"].isin(end_events)].groupby("Family ID")["Year"].max()

    policy_years_all = pd.concat([start_years_all, end_years_all], axis=1)
    policy_years_all.columns = ["start_year", "end_year"]
    policy_years_all = policy_years_all.dropna(subset=["start_year"])
    policy_years_all = policy_years_all.reset_index()

    policy_years_all["end_year"] = policy_years_all["end_year"].apply(
        lambda x: min(x, plot_end_year) if pd.notnull(x) else x
    )

    total_active_set = set()
    total_active_totals = []

    for year in YEARS:
        new_docs_all = set(policy_years_all.loc[policy_years_all["start_year"] == year, "Family ID"])
        dropped_docs_all = set(policy_years_all.loc[policy_years_all["end_year"] == year, "Family ID"])

        total_active_set = total_active_set.union(new_docs_all)
        total_active_set = total_active_set.difference(dropped_docs_all)

        total_active_totals.append(len(total_active_set))

    # ---------------- BUILD DATAFRAME ---------------- #
    gdata = pd.DataFrame({"Year": YEARS})
    for col in RESPONSE_COLS:
        gdata[col] = category_totals[col]

    gdata["Total health-relevant"] = active_totals
    gdata["Total all documents"] = total_active_totals

    for col in RESPONSE_COLS + ["Total health-relevant", "Total all documents"]:
        gdata[col] = gdata[col].astype(int)

    # ---------------- PLOT ---------------- #
    X = np.arange(len(YEARS))
    gdata["StackSum"] = gdata[RESPONSE_COLS].sum(axis=1)
    GLOBAL_Y_MAX = max(
        gdata["StackSum"].max(),
        gdata["Total all documents"].max()
    ) * 1.15

    fig, ax = plt.subplots(figsize=(12, 6))

    # Stackplot
    stack_arrays = [gdata[col].values for col in RESPONSE_COLS]
    ax.stackplot(
        X,
        stack_arrays,
        colors=[COLORS[c] for c in RESPONSE_COLS],
        alpha=0.5,
        edgecolor="black",
        linewidth=0.3
    )

    # ---------------- HEALTH-RELEVANT TOTAL ---------------- #
    line_health, = ax.plot(
        X,
        gdata["Total health-relevant"],
        color="black",
        marker="o",
        linewidth=2.5,
        label="Health-relevant documents"
    )

    for xi, val in zip(X, gdata["Total health-relevant"]):
        if val > 0:
            ax.text(
                xi,
                val + 0.015 * GLOBAL_Y_MAX,
                str(int(val)),
                ha="center",
                fontsize=8
            )

    # ---------------- ALL DOCUMENTS TOTAL ---------------- #
    line_all, = ax.plot(
        X,
        gdata["Total all documents"],
        color="black",
        linestyle="--",
        linewidth=2.5,
        label="Total documents (all)"
    )

    label_step = 5

    for i, (xi, val) in enumerate(zip(X, gdata["Total all documents"])):
        if i % label_step == 0 and val > 0:

            ax.scatter(
                xi,
                val,
                color="black",
                marker="D",
                s=35,
                zorder=3
            )

            ax.text(
                xi,
                val + 0.02 * GLOBAL_Y_MAX,
                str(int(val)),
                ha="center",
                fontsize=8,
                fontweight="bold"
            )

    # ---------------- PARIS AGREEMENT LINE ---------------- #
    if 2016 in YEARS:
        idx_2016 = YEARS.index(2016)
        ax.axvline(x=X[idx_2016], linestyle="--", linewidth=1.8, color="black")
        ax.text(X[idx_2016] + 0.2, 0.9 * GLOBAL_Y_MAX, "Paris Agreement in force (2016)", va="top", fontsize=10)

    # ---------------- AXES ---------------- #
    ax.set_ylim(0, GLOBAL_Y_MAX)
    ax.set_ylabel("Legislative responses", fontsize=13)
    ax.set_title(
        "Global Active Climate-Health Legislative Documents Over Time",
        fontsize=13,
        fontweight="bold",
        loc="left"
    )

    step = 5 if len(YEARS) > 20 else 2
    tick_years = YEARS[::step]
    tick_indices = [YEARS.index(y) for y in tick_years]
    ax.set_xticks(tick_indices)
    ax.set_xticklabels([str(int(y)) for y in tick_years])

    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # ---------------- LEGEND ---------------- #
    bar_handles = [plt.Rectangle((0, 0), 1, 1, color=COLORS[c], alpha=0.5) for c in RESPONSE_COLS]

    fig.legend(
        handles=bar_handles + [line_health, line_all],
        labels=RESPONSE_COLS + ["Health-relevant documents", "Total documents (all)"],
        loc="upper left",
        bbox_to_anchor=(0.1, 0.88),
        frameon=True
    )

    fig.text(
        0.01,
        0.01,
        f"Note: Data available since {DATA_START_YEAR}; analysis shown from {plot_start_year} to {plot_end_year}.",
        fontsize=11,
        style="italic"
    )

    plt.tight_layout(rect=[0.03, 0.04, 0.97, 0.95])
    plt.savefig(output_path, format="pdf", dpi=300)
    plt.close()


# ---------------- MAIN ---------------- #

def main():
    parser = argparse.ArgumentParser(description="Global stacked area plot using timeline-based stock logic")
    parser.add_argument("--annotation", required=True)
    parser.add_argument("--legis", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    legis_df = pd.read_csv(args.legis)

    plot_global_stackplot(annotation_df, legis_df, args.output)


if __name__ == "__main__":
    main()