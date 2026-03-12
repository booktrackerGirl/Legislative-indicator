#!/usr/bin/env python3
import pandas as pd
import argparse

def main(main_csv, lookup_csv, output_csv=None):
    # Load data
    main_df = pd.read_csv(main_csv)
    lookup_df = pd.read_csv(lookup_csv)

    # Merge on ISO3
    merged_df = main_df.merge(lookup_df, on="ISO3", how="left")

    # Drop duplicate country column and rename
    merged_df = merged_df.drop(columns=["Country_y"]).rename(columns={"Country_x": "Country"})

    # Show result
    print(merged_df.head())

    # Optionally save to CSV
    if output_csv:
        merged_df.to_csv(output_csv, index=False)
        print(f"\nMerged dataframe saved to: {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge main CSV with ISO3 lookup CSV")
    parser.add_argument("--main_csv", help="Path to main CSV file (e.g., health_annotations.csv)")
    parser.add_argument("--lookup_csv", help="Path to ISO3 lookup CSV file (e.g., iso3_lookup.csv)")
    parser.add_argument("--output", "-o", help="Optional output CSV file path")

    args = parser.parse_args()
    main(args.main_csv, args.lookup_csv, args.output)