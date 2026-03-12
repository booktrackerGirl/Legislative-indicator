#!/usr/bin/env python3
import pandas as pd
import argparse

# ===============================
# ARGUMENT PARSER
# ===============================
parser = argparse.ArgumentParser(description="Aggregate health annotations by Family ID")
parser.add_argument("-i", "--input", required=True, help="Input CSV file path")
parser.add_argument("-o", "--output", required=True, help="Output CSV file path")
args = parser.parse_args()

# ===============================
# LOAD DATA
# ===============================
df = pd.read_csv(args.input)

# Ensure 'Family ID' exists
if 'Family ID' not in df.columns:
    raise ValueError("Input CSV must have 'Family ID' column")

# ===============================
# AGGREGATE FUNCTION
# ===============================
def aggregate_family(group):
    # Combine health keywords without duplicates
    combined_terms = set()
    for terms in group["Matched health keywords"].dropna():
        combined_terms.update(terms.split(";"))
    combined_terms = ";".join(sorted(t for t in combined_terms if t))

    # Combine health categories
    combined_categories = set()
    if "Health keyword categories" in group.columns:
        for cats in group["Health keyword categories"].dropna():
            combined_categories.update(cats.split(";"))
        combined_categories = ";".join(sorted(c for c in combined_categories if c))

    # Binary fields: take 1 if any Doc ID has 1
    health_relevance = int(group["Health relevance (1/0)"].max())
    health_mandate = int(group["Health adaptation mandate (1/0)"].max())
    institutional_role = int(group["Institutional health role (1/0)"].max())

    # Representative values from first row
    first_row = group.iloc[0]
    return pd.Series({
        "Family ID": first_row["Family ID"],
        "Country": first_row.get("Country", ""),
        "ISO3": first_row.get("ISO3", ""),
        "Year": first_row.get("Year", ""),
        "Response": first_row.get("Response", ""),
        "Health relevance (1/0)": health_relevance,
        "Health adaptation mandate (1/0)": health_mandate,
        "Institutional health role (1/0)": institutional_role,
        "Matched health keywords": combined_terms,
        "Health keyword categories": combined_categories,
        "Notes": "Aggregated from multiple Doc IDs"
    })

# ===============================
# AGGREGATE BY FAMILY ID
# ===============================
df_family = df.groupby("Family ID").agg({
    "Country": "first",
    "ISO3": "first",
    "Year": "first",
    "Response": "first",
    "Health relevance (1/0)": "max",
    "Health adaptation mandate (1/0)": "max",
    "Institutional health role (1/0)": "max",
    "Matched health keywords": lambda x: ";".join(sorted(set(";".join(x.dropna()).split(";")))),
    "Health keyword categories": lambda x: ";".join(sorted(set(";".join(x.dropna()).split(";")))),
}).reset_index()

# ===============================
# SAVE OUTPUT
# ===============================
df_family.to_csv(args.output, index=False)
print(f"✔ Aggregated output saved to: {args.output}")