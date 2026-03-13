#!/usr/bin/env python3
import pandas as pd
import argparse

# -------------------------------
# Columns to sum
# -------------------------------
HEALTH_FEATURES = [
    "Health relevance (1/0)",
    "Health adaptation mandate (1/0)",
    "Institutional health role (1/0)"
]

RESPONSE_TOPICS = [
    "Adaptation",
    "Disaster Risk Management",
    "Loss And Damage",
    "Mitigation"
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

# -------------------------------
# Aggregation function
# -------------------------------
def aggregate_health_stocks(panel_csv, annotations_csv, output_excel, grouping_columns, start_year=2000):

    panel = pd.read_csv(panel_csv)
    annotations = pd.read_csv(annotations_csv)

    # Fill missing values
    for col in HEALTH_FEATURES:
        annotations[col] = annotations[col].fillna(0).astype(int)

    annotations["Health keyword categories"] = annotations["Health keyword categories"].fillna("")
    annotations["Response"] = annotations["Response"].fillna("")

    # Merge panel + annotations
    df = panel.merge(annotations, on="Family ID", how="inner")

    # Fix Year column
    if "Year_x" in df.columns:
        df["Year"] = df["Year_x"]
    elif "Year_y" in df.columns:
        df["Year"] = df["Year_y"]

    df = df.drop(columns=[c for c in df.columns if c.endswith("_x") or c.endswith("_y")], errors="ignore")

    # Only health-relevant documents
    df = df[df["Health relevance (1/0)"] == 1]

    # -------------------------------
    # Create dummy variables
    # -------------------------------
    for cat in CATEGORY_LABELS.keys():
        df[cat] = df["Health keyword categories"].str.contains(cat, case=False, regex=False).astype(int)

    for resp in RESPONSE_TOPICS:
        df[resp] = df["Response"].str.contains(resp, case=False, regex=False).astype(int)

    # -------------------------------
    # Separate EU documents
    # -------------------------------
    EU_LABELS = ["European Union", "EU"]

    df_eu = df[df["Country"].isin(EU_LABELS)].copy()
    df_non_eu = df[~df["Country"].isin(EU_LABELS)].copy()

    # Determine year range
    min_year = max(start_year, df["Year"].min())
    max_year = df["Year"].max()
    years = list(range(min_year, max_year + 1))

    rename_cols = {
        "Health relevance (1/0)": "Health-relevant documents",
        "Health adaptation mandate (1/0)": "Health adaptation mandates",
        "Institutional health role (1/0)": "Institutional health roles"
    }

    with pd.ExcelWriter(output_excel) as writer:

        # -------------------------------
        # Grouped sheets (NON-EU only)
        # -------------------------------
        for group_col in grouping_columns:

            records = []

            for year in years:

                active_docs = df_non_eu[df_non_eu["Year"] <= year].drop_duplicates(subset=["Family ID"])
                all_group_values = df_non_eu[group_col].dropna().unique()

                for group_value in all_group_values:

                    grp = active_docs[active_docs[group_col] == group_value]

                    rec = {group_col: group_value, "Year": year}

                    for col in HEALTH_FEATURES + RESPONSE_TOPICS + list(CATEGORY_LABELS.keys()):
                        rec[col] = grp[col].sum() if not grp.empty else 0

                    records.append(rec)

            grouped = pd.DataFrame(records)

            grouped = grouped.rename(columns=CATEGORY_LABELS)
            grouped = grouped.rename(columns=rename_cols)

            grouped = grouped.sort_values([group_col, "Year"]).reset_index(drop=True)

            grouped.to_excel(writer, sheet_name=group_col[:31], index=False)

        # -------------------------------
        # EU sheet
        # -------------------------------
        eu_records = []

        for year in years:

            active_docs = df_eu[df_eu["Year"] <= year].drop_duplicates(subset=["Family ID"])

            rec = {"Region": "European Union", "Year": year}

            for col in HEALTH_FEATURES + RESPONSE_TOPICS + list(CATEGORY_LABELS.keys()):
                rec[col] = active_docs[col].sum()

            eu_records.append(rec)

        eu_df = pd.DataFrame(eu_records)

        eu_df = eu_df.rename(columns=CATEGORY_LABELS)
        eu_df = eu_df.rename(columns=rename_cols)

        eu_df = eu_df.sort_values("Year").reset_index(drop=True)

        eu_df.to_excel(writer, sheet_name="EU", index=False)

        # -------------------------------
        # Global sheet (INCLUDING EU)
        # -------------------------------
        global_records = []

        for year in years:

            active_docs = df[df["Year"] <= year].drop_duplicates(subset=["Family ID"])

            rec = {"Year": year}

            for col in HEALTH_FEATURES + RESPONSE_TOPICS + list(CATEGORY_LABELS.keys()):
                rec[col] = active_docs[col].sum()

            global_records.append(rec)

        global_df = pd.DataFrame(global_records)

        global_df = global_df.rename(columns=CATEGORY_LABELS)
        global_df = global_df.rename(columns=rename_cols)

        global_df = global_df.sort_values("Year").reset_index(drop=True)

        global_df.to_excel(writer, sheet_name="Global", index=False)

    print(f"✅ Aggregated health stocks saved to '{output_excel}'.")


# -------------------------------
# CLI
# -------------------------------
def main():

    parser = argparse.ArgumentParser(
        description="Aggregate health-relevant policy stocks by groups and year"
    )

    parser.add_argument("--panel", required=True)
    parser.add_argument("--annotations", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--group-cols", nargs="+", required=True)
    parser.add_argument("--start-year", type=int, default=2000)

    args = parser.parse_args()

    aggregate_health_stocks(
        panel_csv=args.panel,
        annotations_csv=args.annotations,
        output_excel=args.output,
        grouping_columns=args.group_cols,
        start_year=args.start_year
    )


if __name__ == "__main__":
    main()