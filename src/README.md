

## Step
### Purpose
This script extracts textual content from policy documents available online, supporting PDF and HTML sources, with multiple fallback strategies to maximize successful extraction.

### Inputs
Document URL(s): Web links pointing to policy documents (e.g., PDFs, HTML pages, or document files).

### Processing
The script attempts document retrieval using smart HTTP requests, then applies multiple extraction strategies including direct PDF parsing, OCR for scanned PDFs, HTML text extraction, and browser-based rendering as a final fallback.

### Output
- Extracted document text and metadata, returned as a structured dictionary containing:
  - text: Extracted document content
  - metadata: Information about the extraction method (e.g., embedded PDF, OCR, HTML, browser).

## Step 

<img width="1024" height="1536" alt="image" src="https://github.com/user-attachments/assets/80c2e91e-dd30-4739-a40a-4974d8a56e1c" />

### Purpose

This script extracts, translates, and annotates health-related content from policy and legislative documents. It detects health relevance, adaptation mandates, and institutional roles, and maps matched keywords to predefined health categories.

### Inputs

CSV file containing document metadata, including:

Document URLs (PDFs or web pages)

Document ID

Geography/Country

Year

Topic/Response

Keyword files (.txt) for:

Health terms

Adaptation terms

Health authority/institutional terms

Processing

Document retrieval:

Attempts extraction from primary URL; falls back to secondary URL if needed.

Supports PDFs, HTML pages, and OCR for scanned documents.

Text normalization:

Cleans text by removing non-ASCII characters and placeholders.

Detects language and translates non-English content into English using chunked translation.

Chunking & segmentation:

Splits text into manageable word chunks.

Segments chunks into sentences using spaCy.

Health keyword detection:

Identifies health-related terms in text windows.

Extracts overlapping word windows around keywords to capture context.

Mandate & institutional role detection:

Flags health adaptation mandates using obligation patterns and keywords.

Flags mentions of health authorities or institutional roles.

Keyword categorization:

Maps matched keywords to predefined health categories (e.g., communicable diseases, mental health, nutrition).


### Output

CSV file with one row per document, containing:
- Doc ID, Country, Family ID, ISO3, Year, Response
- Health relevance (1/0)
- Health adaptation mandate (1/0)
- Institutional health role (1/0)
- Matched health keywords
- Health keyword categories
- Notes (e.g., extraction issues, translation warnings)


## Step (Optional)

Purpose

This pipeline annotates health-relevant legislative documents by extracting text from local PDFs, detecting health-related content, obligations, adaptation mandates, and institutional roles, and exporting structured annotations.

Inputs

Local PDFs – Files in PDF_FOLDER named {doc_id}.pdf.

Document metadata CSV – INPUT_DATA containing columns:

Document ID

Geographies

Topic/Response

first_event_year (renamed to Publication Year)

Keyword lists:

health_terms.txt → general health keywords

adaptation_terms.txt → adaptation-specific keywords

health_authority_terms.txt → institutional/authority keywords

Processing Steps

PDF Extraction

Uses pdfplumber for text-based PDFs.

Falls back to OCR via PyMuPDF + pytesseract for scanned PDFs.

Text is translated to English using GoogleTranslator if non-English is detected.

Text Analysis

Splits documents into manageable chunks (CHUNK_SIZE words).

Uses spaCy (en_core_web_sm) for sentence segmentation.

Detects:

Health relevance – presence of health keywords.

Health adaptation mandate – sentences with health + adaptation keywords or legal obligations (using regex).

Institutional health role – presence of health authority keywords.

Extracts windows of text around relevant health keywords for context.

Annotation Generation

Combines results into a structured row with columns:

Doc ID, Country, Year, Response,
Health relevance (1/0),
Health adaptation mandate (1/0),
Institutional health role (1/0),
Extracted health text,
Notes

Handles incremental processing to skip already annotated documents.

Output

Appends each processed row to OUTPUT_FILE in CSV format.

Logs warnings and progress to LOG_FILE.

Configuration

Adjustable parameters:

WINDOW_SIZE – number of words around health keywords to extract.

MIN_OVERLAP_WORDS – minimum overlap when merging windows.

CHUNK_SIZE – number of words per processing chunk.

REL_THRESHOLD – threshold for detecting relative increases (not used here but common in stock plots).

Supports large pipelines with memory cleanup (gc.collect) and logging.

Strengths

Handles scanned PDFs via OCR.

Multi-language translation for non-English documents.

Keyword and obligation-based extraction for targeted health policy analysis.

Incremental processing to resume on failures or partial runs.


## Step
```
python aggregate_by_family.py -i ./annotation/health_annotations_1.csv -o ./annotation/health_annotations_by_family.csv
```
### Purpose



## Step 

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


## Step 

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



## Step 

``` 
python ./src/plot_global_health_categories.py \
 --annotation ./annotation/health_annotations.csv \
 --legis ./data/CCLW_legislative.csv \
 --output ./outputs/figures/global_health_categories.pdf
```
### Purpose
This script generates a **stacked area plot of active health-relevant climate policy documents over time**, showing how different **health categories contribute to the total policy stock**.

### Inputs
- `health_annotations.csv`: Dataset containing **Document ID, health relevance indicator, and health keyword categories**.
- `CCLW_legislative.csv`: Legislative dataset containing **policy timeline events and dates**.

### Processing
The script filters for **health-relevant policies**, determines policy **start and end years from timeline events**, identifies **health category indicators**, and calculates the **active stock of policies per year** by category.

### Output
- `global_health_categories.png` or `global_health_categories.pdf`: A **stacked area chart** showing the yearly evolution of active health-relevant policies by health category, including a line for **total active documents**.



## Step 

```
python ./src/plot_global_response_stackplot.py \
 --annotation ./annotation/health_annotations.csv \
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



## Step 

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



## Step 

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



## Step 

```
python ./src/plot_active_stocks.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --output ./outputs/figures/global_regional_trends_WHO.pdf \
 --group_col WHO
```
### Purpose
This script computes and visualizes active stock trends of health-relevant legislative documents by region, showing the accumulation of active policies over time.

### Inputs
- `health_annotations.csv`: Contains Document ID and health relevance indicator.
- `policy_year_panel.csv`: Expanded panel dataset with Document ID and Year, indicating when each policy is active.

### Processing
The script filters for health-relevant policies, aggregates active documents per region by year using a timeline-based stock logic, and highlights relative yearly increases.

### Output
`regional_stock_trends.pdf`: A line plot per region, showing the active stock of health-relevant policies over time, with markers indicating notable relative growth and a vertical line marking the Paris Agreement (2015).


## Step 

```
python ./src/aggregate_groups.py \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --annotations ./annotation/health_annotations_with_iso3.csv \
  --output ./outputs/dataframes/aggregated_data_file.xlsx \
  --group-cols Country WHO HDI LC \
  --start-year 2000
```

### Purpose
This script aggregates health-relevant climate policy documents over time, accounting for active policy stocks, and summarizes policy features by country and regional groupings.

### Inputs
- ```policy_year_panel.csv```: Panel dataset containing Document ID and Year, indicating when each policy is active.
- ```health_annotations_with_iso3.csv```: Annotated policy metadata including country, response types, health indicators, and grouping variables (e.g., LC, WHO, HDI).

### Processing
The script merges the datasets, filters for health-relevant policies, creates indicators for policy responses and health categories, and aggregates counts by year and specified groupings.

### Output
```aggregated_data_file.xlsx```: An Excel file with multiple sheets containing yearly aggregated counts for:
- Countries and specified regional groupings (LC, WHO, HDI)
- A Global sheet aggregating all countries by year.
