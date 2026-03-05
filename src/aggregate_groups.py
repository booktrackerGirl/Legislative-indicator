#!/usr/bin/env python3

import pandas as pd
import argparse

HEALTH_FEATURES = [
    "Health relevance (1/0)",
    "Health adaptation mandate (1/0)",
    "Institutional health role (1/0)"
]

RESPONSE_TOPICS = ["Adaptation","Disaster Risk Management","Loss And Damage","Mitigation"]

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


def aggregate_by_groupings(panel_csv, annotations_csv, groups_csv, output_excel, grouping_columns):

    panel = pd.read_csv(panel_csv)
    annotations = pd.read_csv(annotations_csv)
    groups = pd.read_csv(groups_csv)

    # Harmonise ID column
    if "Doc ID" in annotations.columns:
        annotations = annotations.rename(columns={"Doc ID": "Document ID"})

    # Ensure numeric fields
    for col in HEALTH_FEATURES:
        annotations[col] = annotations[col].fillna(0).astype(int)

    annotations["Health keyword categories"] = annotations["Health keyword categories"].fillna("")
    annotations["Response"] = annotations["Response"].fillna("")

    # -------------------------------
    # Extract start/end years
    # -------------------------------
    start_events = ["Passed/Approved","Entered Into Force","Set","Net Zero Pledge"]
    end_events = ["Repealed/Replaced","Closed","Settled"]

    panel["start_year"] = None
    panel["end_year"] = None

    for idx, row in panel.iterrows():
        types = str(row.get("Full timeline of events (types)", "")).split(";")
        dates = str(row.get("Full timeline of events (dates)", "")).split(";")

        start_years = [
            int(d[:4]) for t, d in zip(types, dates)
            if t.strip() in start_events and d[:4].isdigit()
        ]

        end_years = [
            int(d[:4]) for t, d in zip(types, dates)
            if t.strip() in end_events and d[:4].isdigit()
        ]

        panel.at[idx, "start_year"] = min(start_years) if start_years else None
        panel.at[idx, "end_year"] = max(end_years) if end_years else None

    panel = panel.dropna(subset=["start_year"])

    # -------------------------------
    # Merge panel + annotations
    # -------------------------------
    df = panel.merge(
        annotations,
        left_on=["Document ID", "Geographies"],
        right_on=["Document ID", "Country"],
        how="inner"
    )

    # -------------------------------
    # Merge grouping metadata
    # -------------------------------
    df = df.merge(
        groups,
        left_on="Country",
        right_on="Country Name to use",
        how="left"
    )

    # -------------------------------
    # Create health & response dummies
    # -------------------------------
    for cat in CATEGORY_LABELS.keys():
        df[cat] = df["Health keyword categories"] \
            .str.contains(cat, case=False, regex=False).astype(int)

    for resp in RESPONSE_TOPICS:
        df[resp] = df["Response"] \
            .str.contains(resp, case=False, regex=False).astype(int)

    # -------------------------------
    # Stock logic
    # -------------------------------
    min_year = int(df["start_year"].min())
    max_year = int(
        max(
            df["start_year"].max(),
            df["end_year"].dropna().max()
        )
    )

    YEARS = list(range(min_year, max_year + 1))
    active_docs = set()

    results = {g: [] for g in grouping_columns}

    for year in YEARS:

        new_docs = set(df[df["start_year"] == year]["Document ID"])
        dropped_docs = set(df[df["end_year"] == year]["Document ID"])

        active_docs = active_docs.union(new_docs).difference(dropped_docs)
        active_df = df[df["Document ID"].isin(active_docs)]

        if year >= 2000:

            for group_col in grouping_columns:

                for group_value, grp in active_df.groupby(group_col):

                    rec = {group_col: group_value, "Year": year, "Total documents": len(grp)}

                    health_grp = grp[grp["Health relevance (1/0)"] == 1]

                    for f in HEALTH_FEATURES:
                        rec[f] = health_grp[f].sum()

                    for t in RESPONSE_TOPICS:
                        rec[t] = health_grp[t].sum()

                    for cat, label in CATEGORY_LABELS.items():
                        rec[label] = health_grp[cat].sum()

                    results[group_col].append(rec)

    # -------------------------------
    # Save
    # -------------------------------
    with pd.ExcelWriter(output_excel) as writer:
        for group_col, records in results.items():
            pd.DataFrame(records).to_excel(
                writer,
                sheet_name=group_col[:31],  # Excel limit
                index=False
            )

    print(f"✅ Aggregated counts saved to '{output_excel}'.")


def main():
    parser = argparse.ArgumentParser(description="Aggregate policy stock by grouping columns")

    parser.add_argument("--panel", required=True, help="Panel CSV")
    parser.add_argument("--annotations", required=True, help="Annotations CSV")
    parser.add_argument("--groups", required=True, help="Grouping metadata CSV")
    parser.add_argument("--output", required=True, help="Output Excel file")

    parser.add_argument(
        "--group-cols",
        nargs="+",
        required=True,
        help="Grouping columns (e.g. ISO3 'LC Grouping' 'WHO Region')"
    )

    args = parser.parse_args()

    aggregate_by_groupings(
        panel_csv=args.panel,
        annotations_csv=args.annotations,
        groups_csv=args.groups,
        output_excel=args.output,
        grouping_columns=args.group_cols
    )


if __name__ == "__main__":
    main()
