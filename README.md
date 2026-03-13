# 🧩 Legislative‑indicator

**Legislative indicator of the Lancet Countdown Report 2026**
A reproducible data pipeline and analytical toolkit to extract, classify, and visualize climate‑health legislative trends globally. The repository integrates OCR/NLP extraction, policy panel construction, annotation, geographic lookup, time‑series processing, and publication‑ready visualizations.

> This project supports research on the intersection of climate policy and health outcomes by building systematic indicators of legislative activity related to health and climate change.

---

## 🧠 Key Objectives

1. **Extract text from climate and health legislation documents** (PDF/HTML/OCR).
2. **Annotate health relevance, adaptation, and institutional roles** using keyword categorization.
3. **Harmonise data at the policy Family ID level** (aggregate multiple documents per policy family).
4. **Build a policy‑year panel** for longitudinal analysis of active legislative documents.
5. **Visualise trends** across regions (WHO groupings, HDI levels, income groups) and globally.
6. **Output aggregated datasets**, figures, and global/regional maps for research reports.

---

## 📁 Repository Structure

```
Legislative‑indicator/
├── annotation/                    # Annotated document outputs
├── data/                          # Raw legislative data
├── outputs/
│   ├── dataframes/               # Expanded panels & aggregated files
│   └── figures/                  # Charts & maps
├── shapefiles/                   # Country boundary shapefiles for maps
├── src/                          # Python analysis scripts
├── keywords/                     # Keyword lists for NLP
├── requirements.txt              # Python dependencies
├── README.md                     # Project overview (this file)
├── LICENSE                       
└── .gitignore
```

---

## ⚙️ Installation

1. Clone the repository

   ```bash
   git clone https://github.com/booktrackerGirl/Legislative-indicator.git
   cd Legislative-indicator
   ```
2. Create Python environment (recommended)

   ```bash
   python3 -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   ```
3. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 Pipeline Overview

The analysis pipeline is designed to run end‑to‑end, generating both **data products** and **figures**. Each script is documented below.

---

## 📌 Step‑by‑Step Scripts

### 1. **Health relevance extraction**

```bash
python ./src/health_relevance_pipeline.py
```

**Purpose:**
Extracts and annotates raw textual content for health relevance, adaptation mandates, and institutional health role mentions using chunked NLP and keyword detection.

**Input:** Document URLs, metadata
**Output:** Annotated CSV of documents

---

### 2. **Aggregate annotations by Family ID**

```bash
python ./src/aggregate_by_family.py \
  -i ./annotation/health_annotations.csv \
  -o ./annotation/health_annotations_family.csv
```

**Purpose:**
Combines multiple document records belonging to the same policy family into a single family‑level record.
Binary indicators are set to 1 if any document in the family is positive.

**Input:** Document annotations
**Output:** Family‑level annotation CSV

---

### 3. **Merge ISO3 country lookup**

```bash
python ./src/merge_iso3.py \
  --main_csv ./annotation/health_annotations_family.csv \
  --lookup_csv ./annotation/iso3_lookup.csv \
  --output ./annotation/health_annotations_with_iso3.csv
```

**Purpose:**
Appends ISO3 country codes and standardised country metadata.

**Output:** Annotated dataset with proper ISO3 codes

---

### 4. **Create yearly policy panel**

```bash
python ./src/create_yearly_panel.py \
  --input ./data/CCLW_legislative.csv \
  --output ./outputs/dataframes/policy_year_panel.csv
```

**Purpose:**
Expands each policy to every year it was active based on timeline events parsed from legislative data.

**Output:** Policy‑year panel

---

## 🗺️ Mapping Scripts

### 5. **Global health‑relevant map (2000–2025)**

```bash
python ./src/create_worldmap_2000.py \
  --input_csv ./annotation/health_annotations_with_iso3.csv \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
  --output_png ./outputs/figures/health_world_map.png \
  --output_pdf ./outputs/figures/health_world_map.pdf
```

**Purpose:** Choropleth of cumulative health‑relevant policies by country.

---

### 6. **Pre/Post Paris Agreement world map**

```bash
python ./src/create_world_map.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
  --output_png ./outputs/figures/worldmap_prepost2015.png \
  --output_pdf ./outputs/figures/worldmap_prepost2015.pdf
```

**Purpose:** Side‑by‑side maps before and after the **2015 Paris Agreement**.

---

### 7. **Institutional health roles world map**

```bash
python ./src/map_institutional_health_roles.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --shapefile ./shapefiles/WB_GAD_ADM0_complete.shp \
  --output_png ./outputs/figures/institutional_health_roles_map.png \
  --output_pdf ./outputs/figures/institutional_health_roles_map.pdf
```

**Purpose:** Maps global distribution of documents mentioning institutional health roles.

---

## 📊 Plotting Scripts

### 8. **Global health category trends**

```bash
python ./src/plot_global_health_categories.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --legis ./data/CCLW_legislative.csv \
  --output ./outputs/figures/global_health_categories.pdf
```

**Output:** Stacked area plot of active policies by health category over time.

---

### 9. **Global response stackplot**

```bash
python ./src/plot_global_response_stackplot.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --legis ./data/CCLW_legislative.csv \
  --output ./outputs/figures/global_policy_stackplot.pdf
```

**Output:** Stacked area chart of active policies by response type over time.

---

### 10. **Regional response trends**

```bash
python ./src/plot_regional_response_trend.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --group_col LC|WHO|HDI \
  --output ./outputs/figures/regional_response_trends_{group}.pdf
```

**Output:** Line charts of active stock trends by response type for each region.

---

### 11. **Regional health category trends**

```bash
python ./src/plot_regional_health_category_trend.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --group_col LC|WHO|HDI \
  --output ./outputs/figures/regional_health_trends_{group}.pdf
```

---

### 12. **Active stock trends**

```bash
python ./src/plot_active_stocks.py \
  --annotation ./annotation/health_annotations_with_iso3.csv \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --group_col LC|WHO|HDI \
  --output ./outputs/figures/global_regional_trends_{group}.pdf
```

---

### 13. **Regional cascade bar charts**

```bash
python ./src/create_regional_health_bars.py \
  --input ./annotation/health_annotations_with_iso3.csv \
  --region LC|WHO|HDI \
  --output ./outputs/figures/regional_health_cascade_bars_pre_post_2015_{group}.pdf
```

Shows a clustered cascade from total documents → health relevance → institutional roles.

---

### 14. **Aggregate to Excel**

```bash
python ./src/aggregate_groups.py \
  --panel ./outputs/dataframes/policy_year_panel.csv \
  --annotations ./annotation/health_annotations_with_iso3.csv \
  --output ./outputs/dataframes/aggregated_data_file.xlsx \
  --group-cols WHO HDI LC \
  --start-year 2000
```

**Output:** Multi‑sheet Excel summarising trends by region.

---
## Run the Analysis Pipeline

Scripts in the `src/` directory are modular and can be executed sequentially:

```
chmod +x src/full_execution_pipeline.sh.sh
./src/full_execution_pipeline.sh.sh
```

Adjust execution depending on your research needs.

## 🧠 Notes

* All pipelines use **Family ID to avoid double counting policies**.
* Time windows usually start in **2000** and extend through **2025**.
* “Pre‑Paris” refers to **2000–2015**; “Post‑Paris” refers to **2016–2025**.

---

## 📄 License

See [LICENSE](https://github.com/booktrackerGirl/Legislative-indicator/blob/master/LICENSE) file for details.
