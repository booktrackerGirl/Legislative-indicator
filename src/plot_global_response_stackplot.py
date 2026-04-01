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

def plot_global_stackplot(annotation_df, legis_df, ax=None,
                          plot_start_year=PLOT_START_YEAR,
                          plot_end_year=PLOT_END_YEAR):

    # Create axis if standalone
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))
        created_fig = True

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

    # ---------------- STOCK LOGIC ---------------- #
    YEARS = list(range(plot_start_year, plot_end_year + 1))

    active_set = set()
    active_totals = []
    category_totals = {col: [] for col in RESPONSE_COLS}

    for year in YEARS:
        new_docs = set(policy_years.loc[policy_years["start_year"] == year, "Family ID"])
        dropped_docs = set(policy_years.loc[policy_years["end_year"] == year, "Family ID"])

        active_set |= new_docs
        active_set -= dropped_docs

        active_totals.append(len(active_set))

        active_df = policy_years[policy_years["Family ID"].isin(active_set)]
        for col in RESPONSE_COLS:
            category_totals[col].append(active_df[col].sum())

    # ---------------- ALL DOCS ---------------- #
    df_all = legis_df.copy()
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
    policy_years_all = policy_years_all.dropna(subset=["start_year"]).reset_index()

    policy_years_all["end_year"] = policy_years_all["end_year"].apply(
        lambda x: min(x, plot_end_year) if pd.notnull(x) else x
    )

    total_active_set = set()
    total_active_totals = []

    for year in YEARS:
        new_docs_all = set(policy_years_all.loc[policy_years_all["start_year"] == year, "Family ID"])
        dropped_docs_all = set(policy_years_all.loc[policy_years_all["end_year"] == year, "Family ID"])

        total_active_set |= new_docs_all
        total_active_set -= dropped_docs_all

        total_active_totals.append(len(total_active_set))

    # ---------------- BUILD DATA ---------------- #
    gdata = pd.DataFrame({"Year": YEARS})
    for col in RESPONSE_COLS:
        gdata[col] = category_totals[col]

    gdata["Total health-relevant"] = active_totals
    gdata["Total all documents"] = total_active_totals

    # ---------------- PLOT ---------------- #
    X = np.arange(len(YEARS))
    gdata["StackSum"] = gdata[RESPONSE_COLS].sum(axis=1)

    GLOBAL_Y_MAX = max(
        gdata["StackSum"].max(),
        gdata["Total all documents"].max()
    ) * 1.15

    # Stackplot
    ax.stackplot(
        X,
        [gdata[col].values for col in RESPONSE_COLS],
        colors=[COLORS[c] for c in RESPONSE_COLS],
        alpha=0.5,
        edgecolor="black",
        linewidth=0.3
    )

    ax.plot(X, gdata["Total health-relevant"], color="black", marker="o", linewidth=2.5)
    ax.plot(X, gdata["Total all documents"], color="black", linestyle="--", linewidth=2.5)

    # Paris Agreement
    if 2016 in YEARS:
        idx = YEARS.index(2016)
        ax.axvline(x=idx, linestyle="--", linewidth=1.5, color="black")

    # Axes
    ax.set_xlim(0, len(YEARS) - 1)
    ax.set_ylim(0, GLOBAL_Y_MAX)
    ax.set_title("Global Active Climate-Health Legislative Documents Over Time", loc="left")
    ax.set_ylabel("Legislative responses")

    ticks = list(range(0, len(YEARS), 5))
    ax.set_xticks(ticks)
    ax.set_xticklabels([str(YEARS[i]) for i in ticks])

    ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Save if standalone
    if created_fig:
        plt.tight_layout()
        fig.savefig(args.output, format="pdf")
        plt.close(fig)

    return GLOBAL_Y_MAX


# ---------------- MAIN ---------------- #

def main():
    parser = argparse.ArgumentParser(description="Global stacked plot")
    parser.add_argument("--annotation", required=True)
    parser.add_argument("--legis", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    legis_df = pd.read_csv(args.legis)

    plot_global_stackplot(annotation_df, legis_df)


if __name__ == "__main__":
    main()