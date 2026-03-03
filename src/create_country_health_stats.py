#!/usr/bin/env python3

import argparse
import pandas as pd
from collections import Counter


EU_COUNTRIES = [
    "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic","Denmark",
    "Estonia","Finland","France","Germany","Greece","Hungary","Ireland","Italy",
    "Latvia","Lithuania","Luxembourg","Malta","Netherlands","Poland","Portugal",
    "Romania","Slovakia","Slovenia","Spain","Sweden"
]

FEATURE_COLS = [
    "Health relevance (1/0)",
    "Health adaptation mandate (1/0)",
    "Institutional health role (1/0)"
]


def create_country_year_health_stats(
    input_csv,
    panel_csv,
    output_csv,
    multilabel_col="Response",
    year_col="Year"
):
    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    df = pd.read_csv(input_csv)
    panel = pd.read_csv(panel_csv)

    df = df[df['Notes'] != 'Extraction failed']

    # ------------------------------------------------------------------
    # Merge with yearly policy panel
    # ------------------------------------------------------------------

    panel = pd.read_csv(panel_csv)

    # Ensure ID column matches
    if "Doc ID" in df.columns:
        df = df.rename(columns={"Doc ID": "Document ID"})

    # Ensure panel has correct year column
    if "year" in panel.columns:
        panel = panel.rename(columns={"year": "Year"})
    elif "Year" not in panel.columns:
        raise ValueError("Panel file must contain 'Year' or 'year' column.")

    # Drop original Year from annotation (important!)
    df = df.drop(columns=["Year"], errors="ignore")

    # Keep only required panel columns
    panel = panel[["Document ID", "Year"]]


    # ------------------------------------------------------------------
    # MERGE WITH EXPANDED PANEL (THIS CREATES CUMULATIVE STRUCTURE)
    # ------------------------------------------------------------------
    df = df.merge(
        panel.rename(columns={"Year": year_col}),
        on="Document ID",
        how="inner"
    )

    # Ensure numeric binary features
    for c in FEATURE_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # ------------------------------------------------------------------
    # EU expansion
    # ------------------------------------------------------------------
    df_eu = df[df["Country"] == "EU"].copy()
    df_non_eu = df[df["Country"] != "EU"].copy()

    df_eu_expanded = pd.concat(
        [df_eu.assign(Country=c) for c in EU_COUNTRIES],
        ignore_index=True
    )

    df_country = pd.concat(
        [df_non_eu, df_eu_expanded],
        ignore_index=True
    )

    # ------------------------------------------------------------------
    # Hong Kong → China
    # ------------------------------------------------------------------
    '''df_hk = df_country[
        df_country["Country"].str.contains("Hong Kong", case=False, na=False)
    ].copy()

    df_hk["Country"] = "China"

    df_country = pd.concat([df_country, df_hk], ignore_index=True)'''

    df_country.loc[
        df_country["Country"].str.contains("Hong Kong", case=False, na=False),
        "Country"
    ] = "China"

    # ------------------------------------------------------------------
    # Filter to health-relevant documents
    # ------------------------------------------------------------------
    df_health = df_country[df_country["Health relevance (1/0)"] == 1].copy()

    # Deduplicate after EU expansion to avoid double-counting documents
    df_health = df_health.drop_duplicates(subset=["Document ID", "Country", year_col])

    # ------------------------------------------------------------------
    # Country-year totals (NOW USING PANEL YEAR)
    # ------------------------------------------------------------------
    country_year_totals = (
        df_health
        .groupby(["Country", year_col])
        .size()
        .reset_index(name="Total documents")
    ) # this is stocking up cumulative counts by country-year, which is what we want for the maps   Stockₜ = count of policies where panel contains (policy, t)

    # ------------------------------------------------------------------
    # Sum binary health features
    # ------------------------------------------------------------------
    country_year_features = (
        df_health
        .groupby(["Country", year_col])[FEATURE_COLS]
        .sum()
        .reset_index()
    )

    # ------------------------------------------------------------------
    # Topic counts by country-year
    # ------------------------------------------------------------------
    topic_records = []

    for (country, year), group in df_health.groupby(["Country", year_col]):
        all_topics = []
        for cell in group[multilabel_col].dropna():
            all_topics.extend(
                [t.strip() for t in cell.split(";") if t.strip()]
            )

        counts = Counter(all_topics)
        for topic, count in counts.items():
            topic_records.append({
                "Country": country,
                year_col: year,
                topic: count
            })

    country_year_topics = pd.DataFrame(topic_records)

    country_year_topics_wide = (
        country_year_topics
        .pivot_table(index=["Country", year_col], aggfunc="sum")
        .reset_index()
    )

    # ------------------------------------------------------------------
    # Final merge
    # ------------------------------------------------------------------
    country_year_stats = (
        country_year_totals
        .merge(country_year_features, on=["Country", year_col], how="left")
        .merge(country_year_topics_wide, on=["Country", year_col], how="left")
    )

    country_year_stats.to_csv(output_csv, index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Create cumulative country-year health statistics using expanded panel"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to combined annotation CSV"
    )
    parser.add_argument(
        "--panel",
        required=True,
        help="Path to expanded yearly panel CSV"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output country-year health stats CSV"
    )

    args = parser.parse_args()

    create_country_year_health_stats(
        input_csv=args.input,
        panel_csv=args.panel,
        output_csv=args.output
    )


if __name__ == "__main__":
    main()
