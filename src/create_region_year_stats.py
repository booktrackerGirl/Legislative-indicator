#!/usr/bin/env python3

import argparse
import pandas as pd

EU_COUNTRIES = [
    "Austria","Belgium","Bulgaria","Croatia","Cyprus","Czech Republic","Denmark",
    "Estonia","Finland","France","Germany","Greece","Hungary","Ireland","Italy",
    "Latvia","Lithuania","Luxembourg","Malta","Netherlands","Poland","Portugal",
    "Romania","Slovakia","Slovenia","Spain","Sweden"
]

RESPONSE_CATEGORIES = [
    "Adaptation",
    "Disaster Risk Management",
    "Loss And Damage",
    "Mitigation"
]

# ----------------------------
# UN Region Mapping
# ----------------------------
UN_REGION_MAP = {
    # Africa
    "Algeria": "Africa", "Angola": "Africa", "Benin": "Africa", "Botswana": "Africa",
    "Burkina Faso": "Africa", "Burundi": "Africa", "Cabo Verde": "Africa", "Cameroon": "Africa",
    "Central African Republic": "Africa", "Chad": "Africa", "Comoros": "Africa", "Congo": "Africa",
    "Côte d'Ivoire": "Africa", "Djibouti": "Africa", "Egypt": "Africa", "Equatorial Guinea": "Africa",
    "Eritrea": "Africa", "Eswatini": "Africa", "Ethiopia": "Africa", "Gabon": "Africa",
    "Gambia": "Africa", "Ghana": "Africa", "Guinea": "Africa", "Guinea-Bissau": "Africa",
    "Kenya": "Africa", "Lesotho": "Africa", "Liberia": "Africa", "Libya": "Africa",
    "Madagascar": "Africa", "Malawi": "Africa", "Mali": "Africa", "Mauritania": "Africa",
    "Mauritius": "Africa", "Morocco": "Africa", "Mozambique": "Africa", "Namibia": "Africa",
    "Niger": "Africa", "Nigeria": "Africa", "Rwanda": "Africa", "Sao Tome and Principe": "Africa",
    "Senegal": "Africa", "Seychelles": "Africa", "Sierra Leone": "Africa", "Somalia": "Africa",
    "South Africa": "Africa", "South Sudan": "Africa", "Sudan": "Africa", "Tanzania": "Africa",
    "Togo": "Africa", "Tunisia": "Africa", "Uganda": "Africa", "Zambia": "Africa", "Zimbabwe": "Africa",

    # Asia-Pacific
    "Afghanistan": "Asia-Pacific", "Bahrain": "Asia-Pacific", "Bangladesh": "Asia-Pacific",
    "Bhutan": "Asia-Pacific", "Brunei Darussalam": "Asia-Pacific", "Cambodia": "Asia-Pacific",
    "China": "Asia-Pacific", "Hong Kong": "Asia-Pacific", "Cyprus": "Asia-Pacific", "South Korea": "Asia-Pacific",
    "Fiji": "Asia-Pacific", "India": "Asia-Pacific", "Indonesia": "Asia-Pacific", "Iran": "Asia-Pacific",
    "Iraq": "Asia-Pacific", "Japan": "Asia-Pacific", "Jordan": "Asia-Pacific", "Kazakhstan": "Asia-Pacific",
    "Kiribati": "Asia-Pacific", "Kuwait": "Asia-Pacific", "Kyrgyzstan": "Asia-Pacific",
    "Lao People's Democratic Republic": "Asia-Pacific", "Lebanon": "Asia-Pacific", "Malaysia": "Asia-Pacific",
    "Maldives": "Asia-Pacific", "Marshall Islands": "Asia-Pacific", "Micronesia (Federated States of)": "Asia-Pacific",
    "Mongolia": "Asia-Pacific", "Myanmar": "Asia-Pacific", "Nauru": "Asia-Pacific", "Nepal": "Asia-Pacific",
    "Oman": "Asia-Pacific", "Pakistan": "Asia-Pacific", "Palau": "Asia-Pacific", "Papua New Guinea": "Asia-Pacific",
    "Philippines": "Asia-Pacific", "Qatar": "Asia-Pacific", "North Korea": "Asia-Pacific", "Samoa": "Asia-Pacific",
    "Saudi Arabia": "Asia-Pacific", "Singapore": "Asia-Pacific", "Solomon Islands": "Asia-Pacific",
    "Sri Lanka": "Asia-Pacific", "Syrian Arab Republic": "Asia-Pacific", "Tajikistan": "Asia-Pacific",
    "Thailand": "Asia-Pacific", "Timor-Leste": "Asia-Pacific", "Tonga": "Asia-Pacific", "Turkmenistan": "Asia-Pacific",
    "Tuvalu": "Asia-Pacific", "United Arab Emirates": "Asia-Pacific", "Uzbekistan": "Asia-Pacific",
    "Vanuatu": "Asia-Pacific", "Vietnam": "Asia-Pacific", "Yemen": "Asia-Pacific", "Taiwan": "Asia-Pacific",

    # Eastern Europe
    "Albania": "Eastern Europe", "Armenia": "Eastern Europe", "Azerbaijan": "Eastern Europe",
    "Belarus": "Eastern Europe", "Bosnia and Herzegovina": "Eastern Europe", "Bulgaria": "Eastern Europe",
    "Croatia": "Eastern Europe", "Czechia": "Eastern Europe", "Estonia": "Eastern Europe", "Georgia": "Eastern Europe",
    "Hungary": "Eastern Europe", "Latvia": "Eastern Europe", "Lithuania": "Eastern Europe", "Moldova": "Eastern Europe",
    "Montenegro": "Eastern Europe", "North Macedonia": "Eastern Europe", "Poland": "Eastern Europe", "Romania": "Eastern Europe",
    "Russian Federation": "Eastern Europe", "Serbia": "Eastern Europe", "Slovakia": "Eastern Europe", "Slovenia": "Eastern Europe",
    "Ukraine": "Eastern Europe", "Kosovo": "Eastern Europe",

    # GRULAC
    "Antigua and Barbuda": "GRULAC", "Argentina": "GRULAC", "Bahamas": "GRULAC", "Barbados": "GRULAC",
    "Belize": "GRULAC", "Bolivia": "GRULAC", "Brazil": "GRULAC", "Chile": "GRULAC", "Colombia": "GRULAC",
    "Costa Rica": "GRULAC", "Cuba": "GRULAC", "Dominica": "GRULAC", "Dominican Republic": "GRULAC", "Ecuador": "GRULAC",
    "El Salvador": "GRULAC", "Grenada": "GRULAC", "Guatemala": "GRULAC", "Guyana": "GRULAC", "Haiti": "GRULAC",
    "Honduras": "GRULAC", "Jamaica": "GRULAC", "Mexico": "GRULAC", "Nicaragua": "GRULAC", "Panama": "GRULAC",
    "Paraguay": "GRULAC", "Peru": "GRULAC", "Saint Kitts and Nevis": "GRULAC", "Saint Lucia": "GRULAC",
    "Saint Vincent and the Grenadines": "GRULAC", "Suriname": "GRULAC", "Trinidad and Tobago": "GRULAC",
    "Uruguay": "GRULAC", "Venezuela (Bolivarian Republic of)": "GRULAC", "Venezuela": "GRULAC",

    # WEOG
    "Andorra": "WEOG", "Australia": "WEOG", "Austria": "WEOG", "Belgium": "WEOG", "Canada": "WEOG",
    "Denmark": "WEOG", "Finland": "WEOG", "France": "WEOG", "Germany": "WEOG", "Greece": "WEOG",
    "Iceland": "WEOG", "Ireland": "WEOG", "Israel": "WEOG", "Italy": "WEOG", "Liechtenstein": "WEOG",
    "Luxembourg": "WEOG", "Malta": "WEOG", "Monaco": "WEOG", "Netherlands": "WEOG", "New Zealand": "WEOG",
    "Norway": "WEOG", "Portugal": "WEOG", "San Marino": "WEOG", "Spain": "WEOG", "Sweden": "WEOG",
    "Switzerland": "WEOG", "Türkiye": "WEOG", "United Kingdom": "WEOG", "United States": "WEOG",
    "European Union": None
}

REGION_DISPLAY_NAMES = {
    "Africa": "African",
    "Asia-Pacific": "Asia-Pacific",
    "Eastern Europe": "Eastern European",
    "GRULAC": "Latin American and Caribbean Group (GRULAC)",
    "WEOG": "Western European and Others Group (WEOG)"
}

def create_summary(input_csv, panel_csv, output_csv):

    # -------------------------------------------------
    # Load data
    # -------------------------------------------------
    df = pd.read_csv(input_csv)
    panel = pd.read_csv(panel_csv)

    df = df[df["Notes"] != "Extraction failed"]

    # -------------------------------------------------
    # Harmonise ID columns
    # -------------------------------------------------
    if "Doc ID" in df.columns:
        df = df.rename(columns={"Doc ID": "Document ID"})

    if "year" in panel.columns:
        panel = panel.rename(columns={"year": "Year"})
    elif "Year" not in panel.columns:
        raise ValueError("Panel must contain 'Year' column.")

    # Drop original Year (we use panel Year)
    df = df.drop(columns=["Year"], errors="ignore")

    panel = panel[["Document ID", "Year"]]

    # -------------------------------------------------
    # Merge with expanded panel (cumulative structure)
    # -------------------------------------------------
    df = df.merge(panel, on="Document ID", how="inner")

    # -------------------------------------------------
    # EU expansion
    # -------------------------------------------------
    df_eu = df[df["Country"] == "EU"].copy()
    df_non_eu = df[df["Country"] != "EU"].copy()

    df_eu_expanded = pd.concat(
        [df_eu.assign(Country=c) for c in EU_COUNTRIES],
        ignore_index=True
    )

    df_country = pd.concat([df_non_eu, df_eu_expanded], ignore_index=True)

    # -------------------------------------------------
    # Hong Kong → China
    # -------------------------------------------------
    '''df_hk = df_country[
        df_country["Country"].str.contains("Hong Kong", case=False, na=False)
    ].copy()

    df_hk["Country"] = "China"

    df_country = pd.concat([df_country, df_hk], ignore_index=True)'''

    # Replace Hong Kong with China directly
    df_country.loc[
        df_country["Country"].str.contains("Hong Kong", case=False, na=False),
        "Country"
    ] = "China"

    # -------------------------------------------------
    # Create response dummies
    # -------------------------------------------------
    for category in RESPONSE_CATEGORIES:
        df_country[category] = (
            df_country["Response"]
            .str.contains(category, na=False)
            .astype(int)
        )

    # -------------------------------------------------
    # Create cumulative country-year summary
    # -------------------------------------------------
    df_summary = df_country.groupby(["Country", "Year"], as_index=False).agg(
        **{
            "Total documents": ("Document ID", "nunique"),
            "Health relevance (1/0)": ("Health relevance (1/0)", "sum"),
            "Health adaptation mandate (1/0)": ("Health adaptation mandate (1/0)", "sum"),
            "Institutional health role (1/0)": ("Institutional health role (1/0)", "sum"),
            "Adaptation": ("Adaptation", "sum"),
            "Disaster Risk Management": ("Disaster Risk Management", "sum"),
            "Loss And Damage": ("Loss And Damage", "sum"),
            "Mitigation": ("Mitigation", "sum"),
        }
    ) ## How many active document-year rows exist for that country in that year. That is stock.

    # -------------------------------------------------
    # Map Regions
    # -------------------------------------------------
    df_summary["Region"] = df_summary["Country"].map(UN_REGION_MAP)
    df_summary["Region"] = df_summary["Region"].map(REGION_DISPLAY_NAMES)

    df_summary = df_summary.sort_values(["Country", "Year"]).reset_index(drop=True)

    # -------------------------------------------------
    # Save
    # -------------------------------------------------
    df_summary.to_csv(output_csv, index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Create cumulative country-year summary using expanded panel"
    )
    parser.add_argument("--input", required=True, help="Annotation CSV")
    parser.add_argument("--panel", required=True, help="Expanded yearly panel CSV")
    parser.add_argument("--output", required=True, help="Output CSV path")

    args = parser.parse_args()

    create_summary(
        input_csv=args.input,
        panel_csv=args.panel,
        output_csv=args.output
    )


if __name__ == "__main__":
    main()
