#!/usr/bin/env python3
"""
aggregate_docs.py

Usage:
    python aggregate_docs.py input.csv output.csv

This script:
1. Loads a document-level CSV dataset.
2. Removes rows where Notes == "Extraction failed".
3. Converts 'Response' column into binary columns:
   Adaptation, Disaster Risk Management, Loss And Damage, Mitigation
4. Aggregates counts per Country-Year:
   - Total documents
   - Health relevance (1/0)
   - Health adaptation mandate (1/0)
   - Institutional health role (1/0)
   - Counts per response category
5. Maps countries to UN regions.
6. Saves the aggregated summary to a CSV file.
"""

import sys
import pandas as pd

def main():
    # -----------------------------
    # Command-line argument check
    # -----------------------------
    if len(sys.argv) != 3:
        print("Usage: python python_file_with_location.py input_data.csv output_data.csv")
        sys.exit(1)

    input_csv = sys.argv[1]
    output_csv = sys.argv[2]

    # -----------------------------
    # Load CSV dataset
    # -----------------------------
    df_docs = pd.read_csv(input_csv)

    # -----------------------------
    # Remove rows with 'Extraction failed'
    # -----------------------------
    df_docs = df_docs[df_docs['Notes'] != 'Extraction failed']

    # -----------------------------
    # Define response categories and create binary columns
    # -----------------------------
    response_categories = ['Adaptation', 'Disaster Risk Management', 'Loss And Damage', 'Mitigation']

    for category in response_categories:
        df_docs[category] = df_docs['Response'].str.contains(category, na=False).astype(int)

    # -----------------------------
    # Aggregate by Country and Year
    # -----------------------------
    df_summary = df_docs.groupby(['Country', 'Year'], as_index=False).agg(
        **{
            'Total documents': ('Doc ID', 'count'),
            'Health relevance (1/0)': ('Health relevance (1/0)', 'sum'),
            'Health adaptation mandate (1/0)': ('Health adaptation mandate (1/0)', 'sum'),
            'Institutional health role (1/0)': ('Institutional health role (1/0)', 'sum'),
            'Adaptation': ('Adaptation', 'sum'),
            'Disaster Risk Management': ('Disaster Risk Management', 'sum'),
            'Loss And Damage': ('Loss And Damage', 'sum'),
            'Mitigation': ('Mitigation', 'sum')
        }
    )

    # -----------------------------
    # Map countries to UN regions
    # -----------------------------
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

    df_summary['Region'] = df_summary['Country'].map(UN_REGION_MAP)
    df_summary['Region'] = df_summary['Region'].map(REGION_DISPLAY_NAMES)

    # -----------------------------
    # Sort and save CSV
    # -----------------------------
    df_summary = df_summary.sort_values(['Country', 'Year']).reset_index(drop=True)
    df_summary.to_csv(output_csv, index=False)

    print(f"Aggregated summary saved to: {output_csv}")


if __name__ == "__main__":
    main()
