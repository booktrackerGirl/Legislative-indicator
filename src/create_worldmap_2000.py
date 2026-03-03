#!/usr/bin/env python3

import argparse
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt


# -----------------------------
# EU ISO-3 codes (for expansion)
# -----------------------------
EU_ISO3 = [
    "AUT","BEL","BGR","HRV","CYP","CZE","DNK","EST","FIN","FRA",
    "DEU","GRC","HUN","IRL","ITA","LVA","LTU","LUX","MLT",
    "NLD","POL","PRT","ROU","SVK","SVN","ESP","SWE"
]


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def main(args):

    print("Generating aggregated global statistics...")

    # -----------------------------
    # LOAD DATA
    # -----------------------------
    annotations = pd.read_csv(args.input_csv)
    panel = pd.read_csv(args.panel)
    iso_lookup = pd.read_csv(args.iso_codes)

    # Standardize column names in ISO table
    iso_lookup = iso_lookup.rename(columns={
        "ISO2": "ISO_A2",
        "ISO3": "ISO_A3"
    })

    # Rename columns if needed
    if "Doc ID" in annotations.columns:
        annotations = annotations.rename(columns={"Doc ID": "Document ID"})
    if "year" in panel.columns:
        panel = panel.rename(columns={"year": "Year"})

    # -----------------------------
    # MERGE PANEL
    # -----------------------------
    df = annotations.merge(panel, on="Document ID", how="left", suffixes=("", "_panel"))

    if "Year_panel" in df.columns:
        df["Year"] = df["Year_panel"]

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df = df[df["Year"].notna()]
    df = df[(df["Year"] >= 2000) & (df["Year"] <= 2025)]

    # -----------------------------
    # EXPAND EU DOCUMENTS (ISO3 level)
    # -----------------------------
    eu_docs = df[df["ISO_A3"] == "EU"]
    non_eu_docs = df[df["ISO_A3"] != "EU"]

    expanded_rows = []

    for _, row in eu_docs.iterrows():
        for iso3 in EU_ISO3:
            new_row = row.copy()
            new_row["ISO_A3"] = iso3
            expanded_rows.append(new_row)

    expanded_df = pd.DataFrame(expanded_rows)
    df = pd.concat([non_eu_docs, expanded_df], ignore_index=True)

    # -----------------------------
    # KEEP ONLY HEALTH RELEVANT
    # -----------------------------
    df = df[df["Health relevance (1/0)"] == 1]

    # -----------------------------
    # REMOVE DUPLICATES
    # -----------------------------
    df = df.drop_duplicates(subset=["Document ID", "ISO_A3"])

    # -----------------------------
    # CONVERT ISO3 → ISO2
    # -----------------------------
    df = df.merge(
        iso_lookup[["ISO_A3", "ISO_A2"]],
        on="ISO_A3",
        how="left"
    )

    df = df[df["ISO_A2"].notna()]

    # -----------------------------
    # AGGREGATE USING ISO2
    # -----------------------------
    aggregated = (
        df.groupby("ISO_A2")
        .size()
        .reset_index(name="Health relevance")
    )

    aggregated.to_csv(args.output_csv, index=False)
    print(f"Aggregated CSV saved as: {args.output_csv}")

    # -----------------------------
    # LOAD SHAPEFILE (ISO2)
    # -----------------------------
    gdf = gpd.read_file(args.shapefile)

    # Ensure shapefile has ISO_A2 column
    if "ISO_A2" not in gdf.columns:
        raise ValueError("Shapefile must contain ISO_A2 column.")

    merged = gdf.merge(
        aggregated,
        on="ISO_A2",
        how="left"
    )

    # -----------------------------
    # PLOT
    # -----------------------------
    fig, ax = plt.subplots(figsize=(16, 9))

    ax.set_facecolor("#dceaf6")

    merged.plot(
        column="Health relevance",
        cmap="OrRd",
        edgecolor="black",
        linewidth=0.2,
        legend=True,
        legend_kwds={
            "shrink": 0.6,
            "aspect": 25,
            "pad": 0.02
        },
        ax=ax
    )

    ax.set_xticks([])
    ax.set_yticks([])

    ax.set_title(
        "Cumulative Health-Relevant Legislative Documents (2000–2025)",
        fontsize=15
    )

    plt.tight_layout()

    plt.savefig(args.output_png, dpi=300, bbox_inches="tight")
    plt.savefig(args.output_pdf, bbox_inches="tight")
    plt.close()

    print(f"Map saved as {args.output_png} and {args.output_pdf}")
    print("Done.")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--input_csv", required=True)
    parser.add_argument("--panel", required=True)
    parser.add_argument("--iso_codes", required=True,
                        help="ISO mapping CSV from iban.com")
    parser.add_argument("--shapefile", required=True)
    parser.add_argument("--output_csv", required=True)
    parser.add_argument("--output_png", required=True)
    parser.add_argument("--output_pdf", required=True)

    args = parser.parse_args()
    main(args)