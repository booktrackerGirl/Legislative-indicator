

```
python merge_iso3.py \
  --main_csv ./annotation/health_annotations.csv \
  --lookup_csv ./annotation/iso3_lookup.csv \
  --output ./annotation/health_annotations_with_iso3.csv
```


```
python ./src/create_yearly_panel.py \
 --input ./data/CCLW_legislative.csv \
 --output ./outputs/dataframes/policy_year_panel.csv
```

``` 
python ./src/plot_global_health_categories.py \
 --annotation ./annotation/health_annotations.csv \
 --legis ./data/CCLW_legislative.csv \
 --output ./outputs/figures/global_health_categories.pdf
```

```
python ./src/plot_global_response_stackplot.py \
 --annotation ./annotation/health_annotations.csv \
 --legis ./data/CCLW_legislative.csv \
 --output ./outputs/figures/global_policy_stackplot.pdf
```

```
python ./src/plot_regional_health_policy.py \
 --annotations ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --output ./outputs/figures/regional_health_policy_trends.pdf \
 --group_col LC
```

```
python ./src/plot_regional_response_trend.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --group_col LC --output ./outputs/figures/regional_response_trends_LC.pdf
```

```
python ./src/plot_regional_health_category_trend.py \
 --annotation ./annotation/health_annotations_with_iso3.csv \
 --panel ./outputs/dataframes/policy_year_panel.csv \
 --group_col WHO --output ./outputs/figures/regional_health_trends_WHO.pdf
```


```
python aggregate_groups.py \
  --panel panel.csv \
  --annotations annotations.csv \
  --groups country_groups.csv \
  --output output.xlsx \
  --group-cols "WHO Region" "HDI Group 2025"
```
