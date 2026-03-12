#!/usr/bin/env bash

set -e  # stop on error

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
echo "Step 1: Running health relevance pipeline..."

python ./src/health_relevance_pipeline.py

echo "Health annotation completed."


# -----------------------------
# Step 2 — Aggregate by Family ID
# -----------------------------
echo "Step 2: Aggregating annotations by Family ID..."

python aggregate_by_family.py \
    -i ./annotation/health_annotations_1.csv \
    -o ./annotation/health_annotations_by_family.csv

echo "Family aggregation completed."


# -----------------------------
# Step 3 — Merge ISO3 country lookup
# -----------------------------
echo "Step 3: Merging ISO3 lookup..."

python ./src/merge_iso3.py \
  --main_csv ./annotation/health_annotations_by_family.csv \
  --lookup_csv ./annotation/iso3_lookup.csv \
  --output ./annotation/health_annotations_with_iso3.csv

echo "ISO3 merge completed."


# -----------------------------
# Step 4 — Create policy-year panel
# -----------------------------
echo "Step 4: Creating yearly policy panel..."

python ./src/create_yearly_panel.py \
 --input ./data/CCLW_legislative.csv \
 --output ./outputs/dataframes/policy_year_panel.csv

echo "Policy panel created."


# -----------------------------
# Step 5 — Global world map
# -----------------------------
echo "Step 5: Creating global world map..."

python ./src/create_worldmap_2000.py \
 --input_csv ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
 --output_png ./outputs/figures/health_world_map.png \
 --output_pdf ./outputs/figures/health_world_map.pdf

echo "World map created."


# -----------------------------
# Step 6 — Pre/Post Paris world map
# -----------------------------
echo "Step 6: Creating pre/post Paris map..."

python ./src/create_world_map.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
 --output_png ./outputs/figures/worldmap_prepost2015.png \
 --output_pdf ./outputs/figures/worldmap_prepost2015.pdf

echo "Pre/Post map created."


# -----------------------------
# Step 7 — Global health categories stackplot
# -----------------------------
echo "Step 7: Plotting global health category trends..."

python ./src/plot_global_health_categories.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --legis ./data/CCLW_legislative.csv \
 --output ./outputs/figures/global_health_categories.pdf

echo "Global health categories plot completed."


# -----------------------------
# Step 8 — Global response stackplot
# -----------------------------
echo "Step 8: Plotting global response trends..."

python ./src/plot_global_response_stackplot.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --legis ./data/CCLW_legislative.csv \
 --output ./outputs/figures/global_policy_stackplot.pdf

echo "Global response stackplot completed."


# -----------------------------
# Step 9 — Regional response trends
# -----------------------------
echo "Step 9: Plotting regional response trends..."

python ./src/plot_regional_response_trend.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --group_col LC \
 --output ./outputs/figures/regional_response_trends_LC.pdf

echo "Regional response trends completed."


# -----------------------------
# Step 10 — Regional health category trends
# -----------------------------
echo "Step 10: Plotting regional health category trends..."

python ./src/plot_regional_health_category_trend.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --group_col WHO \
 --output ./outputs/figures/regional_health_trends_WHO.pdf

echo "Regional health category trends completed."


# -----------------------------
# Step 11 — Active stock trends
# -----------------------------
echo "Step 11: Plotting regional stock trends..."

python ./src/plot_active_stocks.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --group_col WHO \
 --output ./outputs/figures/global_regional_trends_WHO.pdf

echo "Regional stock plot completed."


# -----------------------------
# Step 12 — Aggregated data output
# -----------------------------
echo "Step 12: Creating aggregated dataset..."

python ./src/aggregate_groups.py \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --annotations ./annotation/health_annotations_with_iso3.csv \
  --output ./outputs/dataframes/aggregated_data_file.xlsx \
  --group-cols Country WHO HDI LC \
  --start-year 2000

echo "Aggregated dataset created."


echo "========================================"
echo "Pipeline finished successfully"
echo "Outputs available in /outputs"
echo "========================================"