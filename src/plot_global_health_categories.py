#!/usr/bin/env python3

import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# Health categories and colors
# ----------------------------
# --- Health categories list ---
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
    "general_health": "#377eb8",           # blue
    "communicable_disease": "#ff7f00",     # orange
    "non_communicable_disease": "#e41a1c", # red
    "vector_borne_zoonotic": "#8da0cb",    # light blue
    "food_waterborne": "#ffd92f",          # yellow
    "environmental_health": "#66c2a5",     # teal
    "nutrition": "#a65628",                # brown
    "maternal_child_health": "#ffff33",    # bright yellow
    "mental_health": "#f781bf",            # pink
    "injury_trauma": "#984ea3",            # purple
    "mortality_morbidity": "#4daf4a",      # green
    "pathogens_microbiology": "#e78ac3",   # magenta
    "substance_use": "#999999",            # gray
    "climate_environment": "#fc8d62"       # coral / climate-related
}

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


# ----------------------------
# Main plotting function
# ----------------------------
def plot_health_stackplot(annotation_df, legis_df, output_path, plot_start_year=2000, plot_end_year=2025):
    # Harmonize columns
    '''if "Doc ID" in annotation_df.columns:
        annotation_df = annotation_df.rename(columns={"Doc ID": "Document ID"})'''
    annotation_df["Health keyword categories"] = annotation_df["Health keyword categories"].fillna("")

    # Keep health-relevant docs
    annotation_df = annotation_df[annotation_df["Health relevance (1/0)"] >= 1].copy()

    legis_df = legis_df[legis_df["Family ID"].isin(annotation_df["Family ID"])].copy()

    # Expand timeline events
    df = legis_df[[
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
    # Keep only events up to plot_end_year
    df_long = df_long[df_long["Year"] <= plot_end_year]

    # Define start & end events
    start_events = ["Passed/Approved", "Entered Into Force", "Set", "Net Zero Pledge"]
    end_events = ["Repealed/Replaced", "Closed", "Settled"]

    start_years = df_long[df_long["event_types"].isin(start_events)].groupby("Family ID")["Year"].min()
    end_years = df_long[df_long["event_types"].isin(end_events)].groupby("Family ID")["Year"].max()

    policy_years = pd.concat([start_years, end_years], axis=1)
    policy_years.columns = ["start_year", "end_year"]
    policy_years = policy_years.dropna(subset=["start_year"])
    policy_years["end_year"] = policy_years["end_year"].apply(lambda x: min(x, plot_end_year) if pd.notnull(x) else x)

    # Merge health keyword info
    policy_years = policy_years.merge(
        annotation_df[["Family ID", "Health keyword categories"]],
        on="Family ID",
        how="left"
    )
    policy_years["Health keyword categories"] = policy_years["Health keyword categories"].fillna("")

    # Create health dummies
    for cat in HEALTH_CATEGORIES:
        policy_years[cat] = policy_years["Health keyword categories"].str.contains(cat, case=False, regex=False).astype(int)

    # Timeline-based stock logic
    max_year = min(df_long["Year"].max(), plot_end_year)
    YEARS = list(range(plot_start_year, max_year + 1))
    active_set = set()
    active_totals = []
    category_totals = {cat: [] for cat in HEALTH_CATEGORIES}

    for year in YEARS:
        new_docs = set(policy_years[policy_years["start_year"] == year]["Family ID"])
        dropped_docs = set(policy_years[policy_years["end_year"] == year]["Family ID"])

        active_set = active_set.union(new_docs)
        active_set = active_set.difference(dropped_docs)

        active_totals.append(len(active_set))
        active_df = policy_years[policy_years["Family ID"].isin(active_set)]

        for cat in HEALTH_CATEGORIES:
            category_totals[cat].append(active_df[cat].sum())

    # Build plotting dataframe
    gdata = pd.DataFrame({"Year": YEARS})
    for cat in HEALTH_CATEGORIES:
        gdata[cat] = category_totals[cat]
    gdata["Total documents"] = active_totals

    # Plot
    X = np.arange(len(YEARS))
    gdata["StackSum"] = gdata[HEALTH_CATEGORIES].sum(axis=1)
    GLOBAL_Y_MAX = max(gdata["StackSum"].max(), gdata["Total documents"].max()) * 1.15

    fig, ax = plt.subplots(figsize=(15, 7))
    stack_arrays = [gdata[col].values for col in HEALTH_CATEGORIES]
    ax.stackplot(X, stack_arrays, colors=[CATEGORY_COLORS[c] for c in HEALTH_CATEGORIES], alpha=0.5, edgecolor="black", linewidth=0.3)
    line, = ax.plot(X, gdata["Total documents"], color="black", marker="o", linewidth=2.7, label="Total health-relevant documents")

    # Add text
    for xi, val in zip(X, gdata["Total documents"]):
        if val > 0:
            ax.text(xi, val + 0.03 * GLOBAL_Y_MAX, str(int(val)), ha="center", va="bottom", fontsize=8, fontweight="bold")

    # Highlight Paris Agreement
    if 2015 in YEARS:
        idx_2015 = YEARS.index(2015)
        ax.axvline(x=X[idx_2015], linestyle="--", linewidth=1.8, color="black")
        ax.text(X[idx_2015]+0.2, 0.9*GLOBAL_Y_MAX, "Paris Agreement", va="top", fontsize=10)

    ax.set_ylim(0, GLOBAL_Y_MAX)
    ax.set_ylabel("Legislative documents", fontsize=13)
    ax.set_title("Global Active Health-Relevant Legislative Documents Over Time", fontsize=13, fontweight="bold", loc="left")

    step = 5 if len(YEARS) > 20 else 2
    tick_years = YEARS[::step]
    tick_indices = [YEARS.index(y) for y in tick_years]
    ax.set_xticks(tick_indices)
    ax.set_xticklabels([str(int(y)) for y in tick_years])
    ax.grid(axis="y", linestyle="--", alpha=0.4)

    bar_handles = [plt.Rectangle((0,0),1,1,color=CATEGORY_COLORS[c],alpha=0.5) for c in HEALTH_CATEGORIES]
    fig.legend(handles=bar_handles+[line], labels=[CATEGORY_LABELS[c] for c in HEALTH_CATEGORIES]+["Total health-relevant documents"], loc="upper left", bbox_to_anchor=(0.1,0.88), frameon=True)

    fig.text(0.01, 0.01, "Note: Analysis shown from {} onward.".format(plot_start_year), fontsize=11, style="italic")
    plt.tight_layout(rect=[0.03, 0.04, 0.97, 0.95])
    plt.savefig(output_path, dpi=300)
    plt.close()

# ----------------------------
# CLI
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="Health categories stackplot with timeline-based active documents")
    parser.add_argument("--annotation", required=True, help="CSV with health keyword annotations")
    parser.add_argument("--legis", required=True, help="CSV with legislative panel info (start/end years)")
    parser.add_argument("--output", required=True, help="Output file (PDF/PNG)")
    args = parser.parse_args()

    annotation_df = pd.read_csv(args.annotation)
    panel_df = pd.read_csv(args.legis)

    plot_health_stackplot(annotation_df, panel_df, args.output)

if __name__ == "__main__":
    main()