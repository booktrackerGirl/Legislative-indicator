# Overview
This section describes the role of each script and the corresponding inputs and outputs for them.

## Step 1

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/80c2e91e-dd30-4739-a40a-4974d8a56e1c" />

```
python ./src/health_relevance_pipeline.py
```

### Purpose

This script extracts, translates, and annotates health-related content from policy and legislative documents. It supports PDF and HTML sources, with multiple fallback strategies to maximize successful extraction. It detects health relevance, adaptation mandates, and institutional roles, and maps matched keywords to predefined health categories.

### Inputs
CSV file containing document metadata, including:
- Document URLs (PDFs or web pages)
- Document ID
- Family ID
- Geography/Country
- Year
- Topic/Response

Keyword files (.txt) for:
- Health terms 
- Adaptation terms
- Health authority/institutional terms

### Processing
- Document retrieval:
  - Attempts extraction from primary URL; falls back to secondary URL if needed.
  - Supports PDFs, HTML pages, and OCR for scanned documents.
- Text normalization:
  - Cleans text by removing non-ASCII characters and placeholders.
  - Detects language and translates non-English content into English using chunked translation.
- Chunking & segmentation:
  - Splits text into manageable word chunks.
  - Segments chunks into sentences using spaCy.
- Health keyword detection:
  - Identifies health-related terms in text windows.
  - Extracts overlapping word windows around keywords to capture context.
- Mandate & institutional role detection:
  - Flags health adaptation mandates using obligation patterns and keywords.
  - Flags mentions of health authorities or institutional roles.
- Keyword categorization: Maps matched keywords to predefined health categories (e.g., communicable diseases, mental health, nutrition).


### Output
CSV file with one row per document, containing:
- Doc ID, Country, Family ID, ISO3, Year, Response
- Health relevance (1/0)
- Health adaptation mandate (1/0)
- Institutional health role (1/0)
- Matched health keywords
- Health keyword categories
- Notes (e.g., extraction issues, translation warnings)

## Step 2
```
python aggregate_by_family.py -i ./annotation/health_annotations_1.csv -o ./annotation/health_annotations_by_family.csv
```
### Purpose
This script aggregates **document-level health annotations** to the **Family ID level**, consolidating multiple document entries belonging to the same policy family into a single record.

### Inputs
- **Input CSV (`--input` / `-i`)**: A dataset containing document-level annotations, including *Family ID*, health indicators, and matched health keywords.

### Processing

1. Loads the input dataset and verifies that the **Family ID** column exists.
2. Groups records by **Family ID** to combine multiple document entries within the same family.
3. Aggregates fields as follows:

   * **Binary indicators** (*Health relevance*, *Health adaptation mandate*, *Institutional health role*): set to **1 if any document in the family has value 1**.
   * **Matched health keywords** and **health keyword categories**: merged across documents and deduplicated.
   * **Metadata fields** (Country, ISO3, Year, Response): taken from the **first record** within each family group.
4. Produces a single consolidated row per **Family ID**.

### Output
A **CSV file (`--output` / `-o`)** containing aggregated health annotations at the **Family ID level**, with combined keywords, categories, and family-level indicator values.



## Step 3

```
python merge_iso3.py \
  --main_csv ./annotation/health_annotations.csv \
  --lookup_csv ./annotation/iso3_lookup.csv \
  --output ./annotation/health_annotations_with_iso3.csv
```
### Purpose
This script merges a main dataset with a country lookup table using ISO3 country codes to append standardized country information.

### Inputs
```health_annotations.csv```: Main dataset containing an ISO3 column (e.g., policy annotations).
```iso3_lookup.csv```: Lookup table containing ISO3 codes and corresponding country names or metadata.

### Processing
The script performs a left join on the ISO3 column, appending country information from the lookup table to the main dataset. It also removes duplicate country columns created during the merge and standardizes the column name.

### Output
```health_annotations_with_iso3.csv```: Prints the first few rows of the merged dataset.
Optionally saves the merged dataset as a new CSV file if an output path is provided.


## Step 4

```
python ./src/create_worldmap_2000.py \ --input_csv ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
 --output_png ./outputs/figures/health_world_map.png \
 --output_pdf ./outputs/figures/health_world_map.pdf
```

### Purpose
This script generates a **global choropleth map** showing the cumulative number of **health-relevant legislative documents** by country for the period **2000–2025**.

### Inputs
* `health_annotations.csv`: Document annotation dataset containing **Family ID, ISO3 country codes, and health relevance labels**.
* `policy_year_panel.csv`: Panel dataset containing **Family ID–Year mappings**.
* `WB_GAD_ADM0_complete.shp`: Global country shapefile containing **ISO_A3 country codes** for geographic boundaries.

### Processing
The script merges the annotation and panel datasets to obtain document years, filters documents between **2000–2025**, and keeps only those marked as **health relevant**. Duplicate document–country combinations are removed. Taiwan (`TWN`) is mapped to China (`CHN`), and EU aggregate rows (`EUR`) are excluded. Documents are then **aggregated by ISO3 country code** and merged with the world shapefile using **ISO3 ↔ ISO_A3 matching**.

### Outputs
* `health_world_map.png` & `health_world_map.pdf`: A **global choropleth map** visualizing the distribution of these documents across countries.

**OR**

```
python ./src/create_world_map.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
 --output_png ./outputs/figures/worldmap_prepost2015.png \
 --output_pdf ./outputs/figures/worldmap_prepost2015.pdf 
```
### Purpose
Same as earlier, but the values segregated into two time-periods: before and after Paris Agreement (2015).


## Step 5

```
python ./src/create_yearly_panel.py \
 --input ./data/CCLW_legislative.csv \
 --output ./outputs/dataframes/policy_year_panel.csv
```

### Purpose
Creates a yearly panel dataset of policies by identifying policy start and end years from legislative timeline events and expanding each policy across all years it remains active.

### Inputs
- `legis_df.csv`: Legislative dataset containing Document ID, event types, and event dates describing the policy timeline.

### Processing
The script extracts years from timeline events, determines policy start and end years using predefined event rules (with priority for *Passed/Approved*), applies minor manual corrections, and expands each policy into a Document ID–Year panel representing active policy years.

### Output
-  `policy_year_panel.csv`: A CSV file containing Document ID and Year, indicating the years each policy is active.

## Step 6

``` 
python ./src/plot_global_health_categories.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --legis ./data/CCLW_legislative.csv \
 --output ./outputs/figures/global_health_categories.pdf
```
### Purpose
This script generates a **stacked area plot of active health-relevant climate policy documents over time**, showing how different **health categories contribute to the total policy stock**.

### Inputs
- `health_annotations.csv`: Dataset containing **Family ID, health relevance indicator, and health keyword categories**.
- `CCLW_legislative.csv`: Legislative dataset containing **policy timeline events and dates**.

### Processing
The script filters for **health-relevant policies**, determines policy **start and end years from timeline events**, identifies **health category indicators**, and calculates the **active stock of policies per year** by category.

### Output
- `global_health_categories.png` or `global_health_categories.pdf`: A **stacked area chart** showing the yearly evolution of active health-relevant policies by health category, including a line for **total active documents**.



## Step 7

```
python ./src/plot_global_response_stackplot.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --legis ./data/CCLW_legislative.csv \
 --output ./outputs/figures/global_policy_stackplot.pdf
```
### Purpose
This script creates a **stacked area plot showing the evolution of active climate–health legislative documents by policy response type** over time.

### Inputs
- `health_annotations.csv`: Dataset containing **Document ID, health relevance indicator, and policy response categories**.
- `legis_df.csv`: Legislative dataset containing **policy timeline events and dates**.

### Processing
The script filters **health-relevant policies**, determines **policy start and end years from timeline events**, assigns **response category indicators**, and calculates the **active stock of policies per year** by response type.

### Output
- `global_stackplot.pdf` (or PNG): A **stacked area chart** showing the yearly evolution of active health-relevant legislative documents by **policy response type**, including a line for **total active documents**.


## Step 8

```
python ./src/plot_regional_response_trend.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --group_col LC --output ./outputs/figures/regional_response_trends_LC.pdf
```

### Purpose
This script visualizes **regional trends in active health-relevant legislative documents by response type**, showing how the stock of policies evolves over time across regions.

### Inputs
* `health_annotations.csv`: Contains **Document ID, health relevance indicator, and response types**.
* `policy_year_panel.csv`: Expanded panel dataset with **Document ID and Year** indicating when each policy is active.
* group of choice : [LC, WHO, HDI] regions

### Processing

The script filters for **health-relevant policies**, explodes multiple response types, computes **active stock per year for each response type and region**, and highlights **relative yearly growth**.

### Output
* `regional_response_trends_{group of choice}.pdf`: A **multi-panel line plot** showing active stock trends by response type for each region (LC, WHO, or HDI), with distinct colors, markers, and line styles per region.



## Step 9

```
python ./src/plot_regional_health_category_trend.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --group_col WHO --output ./outputs/figures/regional_health_trends_WHO.pdf
```
### Purpose
This script visualizes **regional trends in active health-relevant legislative documents** by health category, showing how the stock of policies evolves over time across regions.

### Inputs
* `health_annotations.csv`: Contains **Document ID, health relevance indicator, and health keyword categories**.
* `policy_year_panel.csv`: Expanded panel dataset with **Document ID and Year** indicating when each policy is active.

### Processing
The script filters for **health-relevant policies**, assigns **health category indicators**, computes **active stock per year for each health category and region**, and highlights **relative yearly growth**.

### Output
* `regional_health_policy_trends.pdf`: A **multi-panel line plot** showing active stock trends by health category for each region (LC, WHO, or HDI), with distinct colors and markers per region.



## Step 10

```
python ./src/plot_active_stocks.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --output ./outputs/figures/global_regional_trends_WHO.pdf \
 --group_col WHO
```
### Purpose
This script computes and visualizes the cumulative (“active stock”) number of **health-relevant legislative documents** over time, grouped by region or development category. It produces a time-series plot showing how the stock of documents grows from 2000 onward.

### Inputs
- **Annotation CSV (`--annotation`)**: Contains document metadata and a *Health relevance (1/0)* indicator.
- **Policy-year panel CSV (`--panel`)**: Contains document identifiers (Family ID) and associated year information.
- **Grouping column (`--group_col`)**: Category used to group documents (`LC`, `WHO`, or `HDI`).

### Processing
1. Filters documents to include only those marked as health-relevant.
2. Merges annotation and panel datasets using **Family ID**.
3. Groups documents by the selected category (`LC`, `WHO`, or `HDI`).
4. For each year (2000–latest available), calculates the **cumulative number of unique documents** that have appeared up to that year.
5. Generates a line plot showing the active stock of documents over time for each group, with annotations for notable increases and a marker for the **2015 Paris Agreement**.

### Output
A **PDF figure (`--output`)** showing the time-series trends of active health-relevant legislative documents by the chosen grouping.

## Step 11

```
python ./src/aggregate_groups.py \
 --cclw ./data/CCLW_legislative.csv \
 --annotations ./annotation/health_annotations_with_iso3.csv \
 --output ./outputs/dataframes/aggregated_data_file.xlsx \
 --group-cols Country WHO HDI LC \
 --start-year 2000
```

### Purpose
This script aggregates health-relevant climate policy documents over time, accounting for active policy stocks, and summarizes policy features by country and regional groupings.

### Inputs
- ```CCLW_legislative.csv```: CCLW dataset filtered to only include the legislative documents.
- ```health_annotations_with_iso3.csv```: Annotated policy metadata including country, response types, health indicators, and grouping variables (e.g., LC, WHO, HDI).

### Processing
The script merges the datasets, filters for health-relevant policies, creates indicators for policy responses and health categories, and aggregates counts by year and specified groupings.

### Output
```aggregated_data_file.xlsx```: An Excel file with multiple sheets containing yearly aggregated counts for:
- Countries and specified regional groupings (LC, WHO, HDI)
- A Global sheet aggregating all countries by year.

## Step 12
```
python ./src/plot_proportion.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --legis ./data/CCLW_legislative.csv \
  --output ./outputs/figures/proportion_plot.pdf
```

### Purpose
This script generates a multi-panel line plot showing the proportion of health-relevant legislative documents relative to the total number of active documents over time. The figure includes four subplots: Global, LC regions, WHO regions, and HDI categories. Each subplot contains multiple lines representing categories within that grouping, with values expressed as percentages.

### Inputs
`health_annotations_with_iso3.csv`: Annotation dataset containing Family ID, LC, WHO, HDI classifications, and health relevance indicators.
`CCLW_legislative.csv`: Legislative dataset containing Family ID and full event timelines (types and dates).

### Processing
The script expands semicolon-separated event timelines into individual events and extracts years to construct a document lifecycle. Start and end years are identified using predefined event types, and an active document stock is computed over time by adding documents at their start year and removing them at their end year. For each year, the total active documents form the denominator. Health-relevant documents are then aggregated by category (LC, WHO, HDI), and proportions are computed as the share of health-relevant documents in each category relative to the total active documents. The analysis is repeated for each year from 2000 to 2025.

### Outputs
`health_relevance_proportions.pdf`: A 2×2 multi-panel figure showing trends over time for Global, LC, WHO, and HDI groupings. Each subplot contains multiple colored lines for categories within the grouping, percentage values labeled at 5-year intervals, and a vertical dashed line marking the 2015 Paris Agreement.

