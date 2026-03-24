#!/usr/bin/env bash

set -e  # stop execution on error

echo "========================================"
echo "Climate-Health Policy Pipeline Starting"
echo "========================================"

# -----------------------------
# Create required directories
# -----------------------------
mkdir -p annotation
mkdir -p outputs/dataframes
mkdir -p outputs/figures


# -----------------------------
# Step 1 — Health relevance extraction
# -----------------------------
# Extracts and annotates health-related content from all documents, detecting:
# - Health relevance
# - Adaptation mandates (optional)
# - Institutional health roles
# Produces a CSV with one row per document including matched keywords and categories
python ./src/health_relevance_pipeline.py


# -----------------------------
# Step 2 — Aggregate by Family ID
# -----------------------------
# Aggregates document-level annotations to Family ID level:
# - Binary indicators set to 1 if any document in the family has it
# - Merges keywords and categories
# - Metadata (Country, ISO3, Year, Response) taken from the first record
python ./src/aggregate_by_family.py \
    -i ./annotation/health_annotations.csv \
    -o ./annotation/health_annotations_family.csv


# -----------------------------
# Step 3 — Merge ISO3 lookup
# -----------------------------
# Adds standardized ISO3 country codes and metadata to the Family-level dataset
python ./src/merge_iso3.py \
    --main_csv ./annotation/health_annotations_family.csv \
    --lookup_csv ./annotation/iso3_lookup.csv \
    --output ./annotation/health_annotations_with_iso3.csv


# -----------------------------
# Step 4 — Create yearly policy panel
# -----------------------------
# Expands each policy across all years it remains active
python ./src/create_yearly_panel.py \
    --input ./data/CCLW_legislative.csv \
    --output ./outputs/dataframes/policy_year_panel.csv


# -----------------------------
# Step 5 — Global world map (2000–2025)
# -----------------------------
# Produces a choropleth map of cumulative health-relevant documents per country
python ./src/create_worldmap_2000.py \
    --input_csv ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
    --output_png ./outputs/figures/health_world_map.png \
    --output_pdf ./outputs/figures/health_world_map.pdf


# -----------------------------
# Step 6 — Pre/Post Paris map
# -----------------------------
# Similar to Step 5, but splits the data into pre-2016 vs post-2015
python ./src/create_world_map.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
    --output_png ./outputs/figures/worldmap_prepost2015.png \
    --output_pdf ./outputs/figures/worldmap_prepost2015.pdf


# -----------------------------
# Step 7 — Institutional health roles map
# -----------------------------
# Maps global distribution of policies that mention institutional health roles
python ./src/map_institutional_health_roles.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
    --output_png ./outputs/figures/institutional_health_roles_map.png \
    --output_pdf ./outputs/figures/institutional_health_roles_map.pdf


# -----------------------------
# Step 8 — Global health category trends
# -----------------------------
# Plots stacked area charts of active health-relevant documents by category over time
python ./src/plot_global_health_categories.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --legis ./data/CCLW_legislative.csv \
    --output ./outputs/figures/global_health_categories.pdf


# -----------------------------
# Step 9 — Global response trends
# -----------------------------
# Plots stacked area charts showing active documents by response type
python ./src/plot_global_response_stackplot.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --legis ./data/CCLW_legislative.csv \
    --output ./outputs/figures/global_policy_stackplot.pdf


# -----------------------------
# Step 10 — Regional response trends
# -----------------------------
# Line plots of active stock trends for each region (LC, WHO, HDI)
python ./src/plot_regional_response_trend.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col LC \
    --output ./outputs/figures/regional_response_trends_LC.pdf

python ./src/plot_regional_response_trend.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col WHO \
    --output ./outputs/figures/regional_response_trends_WHO.pdf

python ./src/plot_regional_response_trend.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col HDI \
    --output ./outputs/figures/regional_response_trends_HDI.pdf


# -----------------------------
# Step 11 — Regional health category trends
# -----------------------------
# Line plots of active stock trends by health category for each region
python ./src/plot_regional_health_category_trend.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col WHO \
    --output ./outputs/figures/regional_health_trends_WHO.pdf

python ./src/plot_regional_health_category_trend.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col HDI \
    --output ./outputs/figures/regional_health_trends_HDI.pdf

python ./src/plot_regional_health_category_trend.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col LC \
    --output ./outputs/figures/regional_health_trends_LC.pdf


# -----------------------------
# Step 12 — Active stock trends
# -----------------------------
# Time series plots of cumulative health-relevant legislative documents
python ./src/plot_active_stocks.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col WHO \
    --output ./outputs/figures/global_regional_trends_WHO.pdf

python ./src/plot_active_stocks.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col HDI \
    --output ./outputs/figures/global_regional_trends_HDI.pdf

python ./src/plot_active_stocks.py \
    --annotation ./annotation/health_annotations_with_iso3.csv \
    --panel ./outputs/dataframes/policy_year_panel.csv \
    --group_col LC \
    --output ./outputs/figures/global_regional_trends_LC.pdf


# -----------------------------
# Step 13 — Regional cascade bars
# -----------------------------
# Clustered bar plots (pre/post 2015) showing Total → Health relevance → Institutional health roles
python ./src/create_regional_health_bars.py \
    --input ./annotation/health_annotations_with_iso3.csv \
    --region HDI \
    --output ./outputs/figures/regional_health_cascade_bars_pre_post_2015_HDI.pdf

python ./src/create_regional_health_bars.py \
    --input ./annotation/health_annotations_with_iso3.csv \
    --region WHO \
    --output ./outputs/figures/regional_health_cascade_bars_pre_post_2015_WHO.pdf

python ./src/create_regional_health_bars.py \
    --input ./annotation/health_annotations_with_iso3.csv \
    --region LC \
    --output ./outputs/figures/regional_health_cascade_bars_pre_post_2015_LC.pdf


# -----------------------------
# Step 14 — Aggregated dataset
# -----------------------------
# Produces a multi-sheet Excel file summarizing health-relevant policies by WHO, HDI, LC
python ./src/aggregate_groups.py \
 --cclw ./data/CCLW_legislative.csv \
 --annotations ./annotation/health_annotations_with_iso3.csv \
 --output ./outputs/dataframes/aggregated_data_file.xlsx \
 --group-cols Country WHO HDI LC \
 --start-year 2000

# -----------------------------
# Step 15 — Health relevance proportions by group
# -----------------------------
# Plots multi-panel line charts showing the proportion (%) of health-relevant documents
# among all active documents over time, broken down by Global, LC, WHO, and HDI groups.
# Each subplot contains multiple lines (one per category), with values labeled every 5 years
# and a vertical marker for the 2015 Paris Agreement.
python ./src/plot_proportion.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --legis ./data/CCLW_legislative.csv \
  --output ./outputs/figures/proportion_plot.pdf

echo "========================================"
echo "Pipeline finished successfully"
echo "Outputs available in /outputs"
echo "========================================"