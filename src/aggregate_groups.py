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

RESPONSE_TOPICS = ["Adaptation", "Disaster Risk Management", "Loss And Damage", "Mitigation"]

CATEGORY_LABELS = {
    "general_health": "General health",
    "communicable_disease": "Communicable disease",
    "non_communicable_disease": "Non-communicable disease",
    "vector_borne_zoonotic": "Vector-borne & zoonotic",
    "food_waterborne": "Food & waterborne",
    "environmental_health": "Environmental health",
    "nutrition": "Nutrition",
    "maternal_child_health": "Maternal & child health",
    "mental_health": "Mental health",
    "injury_trauma": "Injury & trauma",
    "mortality_morbidity": "Mortality & morbidity",
    "pathogens_microbiology": "Pathogens & microbiology",
    "substance_use": "Substance use"
}

# -------------------------------
# Aggregation function
# -------------------------------
def aggregate_health_stocks(panel_csv, annotations_csv, output_excel, grouping_columns, start_year=2000):
    # Load CSVs
    panel = pd.read_csv(panel_csv)
    annotations = pd.read_csv(annotations_csv)

    # Rename Doc ID if needed
    '''if "Doc ID" in annotations.columns:
        annotations = annotations.rename(columns={"Doc ID": "Document ID"})'''

    # Fill NaNs
    for col in HEALTH_FEATURES:
        annotations[col] = annotations[col].fillna(0).astype(int)
    annotations["Health keyword categories"] = annotations["Health keyword categories"].fillna("")
    annotations["Response"] = annotations["Response"].fillna("")

    # Merge panel + annotations
    df = panel.merge(annotations, on="Family ID", how="inner")

    # Ensure Year column exists
    if "Year_x" in df.columns:
        df["Year"] = df["Year_x"]
    elif "Year_y" in df.columns:
        df["Year"] = df["Year_y"]
    df = df.drop(columns=[c for c in df.columns if c.endswith("_x") or c.endswith("_y")], errors='ignore')

    # Only health-relevant documents
    df = df[df["Health relevance (1/0)"] == 1]

    # Create dummy columns for responses & health categories (binary per document)
    for cat in CATEGORY_LABELS.keys():
        df[cat] = df["Health keyword categories"].str.contains(cat, case=False, regex=False).astype(int)
    for resp in RESPONSE_TOPICS:
        df[resp] = df["Response"].str.contains(resp, case=False, regex=False).astype(int)

    # Determine years for aggregation
    min_year = max(start_year, df["Year"].min())
    max_year = df["Year"].max()
    years = list(range(min_year, max_year + 1))

    # Excel writer
    with pd.ExcelWriter(output_excel) as writer:
        # -------------------------------
        # Grouped sheets
        # -------------------------------
        for group_col in grouping_columns:
            records = []

            for year in years:
                # Active docs = all docs with Year <= current year
                active_docs = df[df["Year"] <= year].drop_duplicates(subset=["Family ID"])

                # If no docs for a group yet, we still want a row with 0
                group_values = active_docs[group_col].unique()
                all_group_values = list(group_values)  # groups that exist in data
                # also include groups missing for this year
                if df[group_col].dtype == object:
                    all_group_values = df[group_col].dropna().unique()
                for group_value in all_group_values:
                    grp = active_docs[active_docs[group_col] == group_value]
                    rec = {group_col: group_value, "Year": year}
                    for col in HEALTH_FEATURES + RESPONSE_TOPICS + list(CATEGORY_LABELS.keys()):
                        rec[col] = grp[col].sum() if not grp.empty else 0
                    records.append(rec)

            # Convert to DataFrame
            grouped = pd.DataFrame(records)


            # Rename health category columns to user-friendly labels
            grouped = grouped.rename(columns=CATEGORY_LABELS)

            # ✅ Rename health feature columns for readability
            rename_cols = {
                "Health relevance (1/0)": "Health-relevant documents",
                "Health adaptation mandate (1/0)": "Health adaptation mandates",
                "Institutional health role (1/0)": "Institutional health roles"
            }
            grouped = grouped.rename(columns=rename_cols)

            # Rename health category columns to user-friendly labels
            grouped = grouped.rename(columns=CATEGORY_LABELS)

            # Sort by Year and group
            grouped = grouped.sort_values([group_col, "Year"]).reset_index(drop=True)

            # Write to Excel sheet
            grouped.to_excel(writer, sheet_name=group_col[:31], index=False)

        # -------------------------------
        # Global sheet
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
        # ✅ Rename health feature columns for readability
        global_df = global_df.rename(columns=rename_cols)
        global_df = global_df.sort_values("Year").reset_index(drop=True)
        global_df.to_excel(writer, sheet_name="Global", index=False)

    print(f"✅ Aggregated health stocks saved to '{output_excel}'.")


# -------------------------------
# CLI
# -------------------------------
def main():
    parser = argparse.ArgumentParser(description="Aggregate health-relevant policy stocks by groups and year")

    parser.add_argument("--panel", required=True, help="Panel CSV with Family ID and Year")
    parser.add_argument("--annotations", required=True, help="Health annotations CSV")
    parser.add_argument("--output", required=True, help="Output Excel file")
    parser.add_argument("--group-cols", nargs="+", required=True, help="Grouping columns (e.g. Country WHO HDI LC)")
    parser.add_argument("--start-year", type=int, default=2000, help="Start year for aggregation (default=2000)")

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