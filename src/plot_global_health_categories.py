#!/usr/bin/env python3

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# Health categories and colors
# ----------------------------
HEALTH_CATEGORIES = [
    "general_health",
    "mortality_morbidity",
    "injury_trauma",
    "communicable_disease",
    "non_communicable_disease",
    "maternal_child_health",
    "nutrition",
    "mental_health",
    "substance_use",
    "environmental_health",
    "climate_environment",
    "vector_borne_zoonotic",
    "food_waterborne",
    "pathogens_microbiology"
]

CATEGORY_COLORS = {
    "general_health": "#377eb8",
    "communicable_disease": "#ff7f00",
    "non_communicable_disease": "#e41a1c",
    "vector_borne_zoonotic": "#8da0cb",
    "food_waterborne": "#ffd92f",
    "environmental_health": "#66c2a5",
    "nutrition": "#a65628",
    "maternal_child_health": "#ffff33",
    "mental_health": "#f781bf",
    "injury_trauma": "#984ea3",
    "mortality_morbidity": "#4daf4a",
    "pathogens_microbiology": "#e78ac3",
    "substance_use": "#999999",
    "climate_environment": "#fc8d62"
}

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


# ----------------------------
# Main plotting function
# ----------------------------
def plot_health_stackplot(annotation_df, legis_df, output_path, plot_start_year=2000, plot_end_year=2025):

    annotation_df["Health keyword categories"] = annotation_df["Health keyword categories"].fillna("")

    # Keep health-relevant docs only (for main analysis)
    annotation_health_df = annotation_df[annotation_df["Health relevance (1/0)"] >= 1].copy()

    # ----------------------------
    # FILTER legis (health-relevant only)
    # ----------------------------
    legis_df_health = legis_df[legis_df["Family ID"].isin(annotation_health_df["Family ID"])].copy()

    # ----------------------------
    # ALSO keep ALL docs (for total dotted line)
    # ----------------------------
    legis_df_all = legis_df.copy()

    # Expand timeline for health docs
    df = legis_df_health[[
        "Family ID",
        "Full timeline of events (types)",
        "Full timeline of events (dates)"
    ]].copy()

    df["event_types"] = df["Full timeline of events (types)"].str.split(";")
    df["event_dates"] = df["Full timeline of events (dates)"].str.split(";")
    df_long = df.explode(["event_types", "event_dates"])

    df_long["event_types"] = df_long["event_types"].astype(str).str.strip()
    df_long["event_dates"] = df_long["event_dates"].astype(str).str.strip()
    df_long["Year"] = df_long["event_dates"].str[:4]
    df_long = df_long[df_long["Year"].str.match(r"^\d{4}$", na=False)]
    df_long["Year"] = df_long["Year"].astype(int)
    df_long = df_long[df_long["Year"] <= plot_end_year]

    # Define events
    start_events = ["Passed/Approved", "Entered Into Force", "Set", "Net Zero Pledge"]
    end_events = ["Repealed/Replaced", "Closed", "Settled"]

    start_years = df_long[df_long["event_types"].isin(start_events)].groupby("Family ID")["Year"].min()
    end_years = df_long[df_long["event_types"].isin(end_events)].groupby("Family ID")["Year"].max()

    policy_years = pd.concat([start_years, end_years], axis=1)
    policy_years.columns = ["start_year", "end_year"]
    policy_years = policy_years.dropna(subset=["start_year"])
    policy_years["end_year"] = policy_years["end_year"].apply(
        lambda x: min(x, plot_end_year) if pd.notnull(x) else x
    )

    # Merge health categories
    policy_years = policy_years.merge(
        annotation_health_df[["Family ID", "Health keyword categories"]],
        on="Family ID",
        how="left"
    )
    policy_years["Health keyword categories"] = policy_years["Health keyword categories"].fillna("")

    # Create dummies
    for cat in HEALTH_CATEGORIES:
        policy_years[cat] = policy_years["Health keyword categories"].str.contains(cat, case=False, regex=False).astype(int)

    # ----------------------------
    # Build FULL dataset (ALL docs)
    # ----------------------------
    df_all = legis_df_all[[
        "Family ID",
        "Full timeline of events (types)",
        "Full timeline of events (dates)"
    ]].copy()

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
    policy_years_all["end_year"] = policy_years_all["end_year"].apply(
        lambda x: min(x, plot_end_year) if pd.notnull(x) else x
    )

    # ✅ FIX: restore Family ID as column
    policy_years_all = policy_years_all.reset_index()

    # ----------------------------
    # Timeline simulation
    # ----------------------------
    max_year = min(df_long["Year"].max(), plot_end_year)
    YEARS = list(range(plot_start_year, max_year + 1))

    active_set = set()
    active_totals = []
    total_active_set = set()
    total_active_totals = []

    category_totals = {cat: [] for cat in HEALTH_CATEGORIES}

    for year in YEARS:
        # health docs
        new_docs = set(policy_years[policy_years["start_year"] == year]["Family ID"])
        dropped_docs = set(policy_years[policy_years["end_year"] == year]["Family ID"])

        active_set = active_set.union(new_docs)
        active_set = active_set.difference(dropped_docs)

        active_df = policy_years[policy_years["Family ID"].isin(active_set)]
        active_totals.append(len(active_set))

        for cat in HEALTH_CATEGORIES:
            category_totals[cat].append(active_df[cat].sum())

        # total docs (ALL)
        new_docs_all = set(policy_years_all[policy_years_all["start_year"] == year]["Family ID"])
        dropped_docs_all = set(policy_years_all[policy_years_all["end_year"] == year]["Family ID"])

        total_active_set = total_active_set.union(new_docs_all)
        total_active_set = total_active_set.difference(dropped_docs_all)

        total_active_totals.append(len(total_active_set))

    # ----------------------------
    # Build dataframe
    # ----------------------------
    gdata = pd.DataFrame({"Year": YEARS})
    for cat in HEALTH_CATEGORIES:
        gdata[cat] = category_totals[cat]

    gdata["Health docs"] = active_totals
    gdata["Total docs"] = total_active_totals

    # ----------------------------
    # Plot
    # ----------------------------
    X = np.arange(len(YEARS))
    gdata["StackSum"] = gdata[HEALTH_CATEGORIES].sum(axis=1)
    GLOBAL_Y_MAX = max(gdata["StackSum"].max(), gdata["Total docs"].max()) * 1.15

    fig, ax = plt.subplots(figsize=(15, 7))

    stack_arrays = [gdata[col].values for col in HEALTH_CATEGORIES]
    ax.stackplot(
        X,
        stack_arrays,
        colors=[CATEGORY_COLORS[c] for c in HEALTH_CATEGORIES],
        alpha=0.5,
        edgecolor="black",
        linewidth=0.3
    )

    # Solid line = health docs
    line1, = ax.plot(X, gdata["Health docs"], color="black", marker="o", linewidth=2.5, label="Health-relevant documents")

    # Dotted line = total docs
    line2, = ax.plot(X, gdata["Total docs"], color="black", linestyle="--", linewidth=2.5, label="Total documents")

    # Labels on health line
    for xi, val in zip(X, gdata["Health docs"]):
        if val > 0:
            ax.text(
                xi,
                val + 0.01 * GLOBAL_Y_MAX,  # closer to the line
                str(int(val)),
                ha="center",
                fontsize=8
            )
    
    # Label total docs every 5 years (or 4 if you prefer)
    label_step = 5

    for i, (xi, val) in enumerate(zip(X, gdata["Total docs"])):
        if i % label_step == 0 and val > 0:
            
            # marker
            ax.scatter(
                xi,
                val,
                color="black",
                marker="D",
                s=30,
                zorder=3
            )

            # label on top of marker
            ax.text(
                xi,
                val + 0.02 * GLOBAL_Y_MAX,
                str(int(val)),
                ha="center",
                fontsize=8
            )

    # Paris Agreement marker
    if 2015 in YEARS:
        idx_2015 = YEARS.index(2015)
        ax.axvline(x=X[idx_2015], linestyle="--", linewidth=1.5, color="black")
        ax.text(X[idx_2015] + 0.2, 0.9 * GLOBAL_Y_MAX, "Paris Agreement", fontsize=10)

    ax.set_ylim(0, GLOBAL_Y_MAX)
    ax.set_ylabel("Legislative documents")
    ax.set_title("Global Active Health-Relevant Legislative Documents Over Time", loc="left")

    step = 5 if len(YEARS) > 20 else 2
    tick_years = YEARS[::step]
    tick_indices = [YEARS.index(y) for y in tick_years]
    ax.set_xticks(tick_indices)
    ax.set_xticklabels([str(int(y)) for y in tick_years])
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    bar_handles = [
        plt.Rectangle((0, 0), 1, 1, color=CATEGORY_COLORS[c], alpha=0.5)
        for c in HEALTH_CATEGORIES
    ]

    fig.legend(
        handles=bar_handles + [line1, line2],
        labels=[CATEGORY_LABELS[c] for c in HEALTH_CATEGORIES] +
               ["Health-relevant documents", "Total documents"],
        loc="upper left",
        bbox_to_anchor=(0.1, 0.88)
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


# ----------------------------
# CLI
# ----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--annotation", required=True)
    parser.add_argument("--legis", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    panel_df = pd.read_csv(args.legis)

    plot_health_stackplot(annotation_df, panel_df, args.output)


if __name__ == "__main__":
    main()