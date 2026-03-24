#!/usr/bin/env python3

import pandas as pd
import argparse

PLOT_END_YEAR = 2025

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

RESPONSE_TOPICS = [
    "Adaptation",
    "Disaster Risk Management",
    "Loss And Damage",
    "Mitigation"
]


# -------------------------------
# Lifecycle (IDENTICAL to stackplot)
# -------------------------------
def build_policy_years(legis_df):

    df = legis_df.copy()

    df["event_types"] = df["Full timeline of events (types)"].fillna("").str.split(";")
    df["event_dates"] = df["Full timeline of events (dates)"].fillna("").str.split(";")

    df = df.explode(["event_types", "event_dates"])

    df["event_types"] = df["event_types"].astype(str).str.strip()
    df["event_dates"] = df["event_dates"].astype(str).str.strip()

    df["Year"] = df["event_dates"].str[:4]
    df = df[df["Year"].str.match(r"^\d{4}$", na=False)]
    df["Year"] = df["Year"].astype(int)
    df = df[df["Year"] <= PLOT_END_YEAR]

    start_events = ["Passed/Approved", "Entered Into Force", "Set", "Net Zero Pledge"]
    end_events = ["Repealed/Replaced", "Closed", "Settled"]

    start_years = df[df["event_types"].isin(start_events)].groupby("Family ID")["Year"].min()
    end_years = df[df["event_types"].isin(end_events)].groupby("Family ID")["Year"].max()

    policy_years = pd.concat([start_years, end_years], axis=1)
    policy_years.columns = ["start_year", "end_year"]

    policy_years = policy_years.dropna(subset=["start_year"])
    policy_years["end_year"] = policy_years["end_year"].apply(
        lambda x: min(x, PLOT_END_YEAR) if pd.notnull(x) else x
    )

    return policy_years.reset_index()


# -------------------------------
# Active stock (IDENTICAL LOGIC)
# -------------------------------
def simulate_active(df_meta, policy_years, start_year):

    YEARS = list(range(start_year, PLOT_END_YEAR + 1))

    active_set = set()
    total_active_set = set()

    records = []

    for year in YEARS:

        # --- lifecycle updates ---
        new_docs = set(policy_years[policy_years["start_year"] == year]["Family ID"])
        dropped_docs = set(policy_years[policy_years["end_year"] == year]["Family ID"])

        active_set |= new_docs
        active_set -= dropped_docs

        total_active_set |= new_docs
        total_active_set -= dropped_docs

        active_df = df_meta[df_meta["Family ID"].isin(active_set)]

        # ✅ CRITICAL: prevent duplicate inflation
        active_df = active_df.drop_duplicates(subset=["Family ID"])

        rec = {"Year": year}

        # --- totals ---
        rec["Total documents"] = len(total_active_set)

        rec["Health-relevant documents"] = active_df[
            active_df["Health relevance (1/0)"] == 1
        ]["Family ID"].nunique()

        rec["Institutional health roles"] = active_df[
            active_df["Institutional health role (1/0)"] == 1
        ]["Family ID"].nunique()

        # --- categories ---
        for cat in HEALTH_CATEGORIES:
            rec[cat] = active_df[cat].sum()

        # --- response topics ---
        for topic in RESPONSE_TOPICS:
            rec[topic] = active_df["Response"].str.contains(topic, case=False, na=False).sum()

        records.append(rec)

    return pd.DataFrame(records)


# -------------------------------
# MAIN
# -------------------------------
def aggregate(cclw_csv, annotations_csv, output_excel, grouping_columns, start_year=2000):

    legis = pd.read_csv(cclw_csv)
    ann = pd.read_csv(annotations_csv)

    # --- clean ---
    ann["Health keyword categories"] = ann["Health keyword categories"].fillna("")
    ann["Response"] = ann["Response"].fillna("")
    ann["Health relevance (1/0)"] = ann["Health relevance (1/0)"].fillna(0).astype(int)
    ann["Institutional health role (1/0)"] = ann["Institutional health role (1/0)"].fillna(0).astype(int)

    # --- category dummies ---
    for cat in HEALTH_CATEGORIES:
        ann[cat] = ann["Health keyword categories"].str.contains(cat, case=False, regex=False).astype(int)

    df = legis.merge(ann, on="Family ID", how="inner")

    # lifecycle
    policy_years = build_policy_years(legis)

    # EU split
    EU_LABELS = ["European Union", "EU"]
    df_eu = df[df["Country"].isin(EU_LABELS)]
    df_non_eu = df[~df["Country"].isin(EU_LABELS)]

    # -------------------------------
    # WRITE OUTPUT
    # -------------------------------
    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:

        # GLOBAL
        global_df = simulate_active(df, policy_years, start_year)
        global_df.rename(columns=CATEGORY_LABELS).to_excel(writer, sheet_name="Global", index=False)

        # EU
        eu_ids = set(df_eu["Family ID"])
        eu_policy = policy_years[policy_years["Family ID"].isin(eu_ids)]

        eu_df = simulate_active(df_eu, eu_policy, start_year)
        eu_df.rename(columns=CATEGORY_LABELS).to_excel(writer, sheet_name="EU", index=False)

        # NON-EU GROUPS
        for col in grouping_columns:

            if col not in df_non_eu.columns:
                continue

            records = []

            for group_value in df_non_eu[col].dropna().unique():

                subset = df_non_eu[df_non_eu[col] == group_value]
                ids = set(subset["Family ID"])

                subset_policy = policy_years[policy_years["Family ID"].isin(ids)]

                out = simulate_active(subset, subset_policy, start_year)
                out[col] = group_value

                records.append(out)

            if records:
                pd.concat(records).to_excel(writer, sheet_name=col[:31], index=False)

    print(f"✅ DONE (stackplot-consistent): {output_excel}")


# -------------------------------
# CLI
# -------------------------------
def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--cclw", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--group-cols", nargs="+", required=True)
    parser.add_argument("--start-year", type=int, default=2000)

    args = parser.parse_args()

    aggregate(
        args.cclw,
        args.annotations,
        args.output,
        args.group_cols,
        args.start_year
    )


if __name__ == "__main__":
    main()