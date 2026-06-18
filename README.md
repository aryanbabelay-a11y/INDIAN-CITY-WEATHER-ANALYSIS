# 🌦️ Climate Analysis of Indian Cities (1990–2022)

A full-stack data analysis project investigating **long-term climate change signals, extreme heat events, monsoon variability, and urban heat island effects** across eight Indian meteorological stations over 33 years.

---

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Problem Statement](#problem-statement)
- [Research Questions](#research-questions)
- [Dataset Description](#dataset-description)
- [Project Structure](#project-structure)
- [Key Findings](#key-findings)
- [Database Schema](#database-schema)
- [Limitations](#limitations)

---

## Project Overview

This project analyses **~95,000 daily weather observations** from eight Indian cities sourced from the [Meteostat](https://meteostat.net) open-access climate database. The cities span five distinct climate zones — arid desert, semi-arid inland, plateau, coastal Arabian Sea, and coastal Bay of Bengal — enabling meaningful cross-zone climate comparisons.

The analysis pipeline covers three tools:

| Tool | Purpose |
|---|---|
| **Python** | Data cleaning, feature engineering, EDA, statistical trend testing, chart generation |
| **PostgreSQL / DuckDB** | Relational storage, 10 structured analytical SQL queries |
| **Power BI** | 4-page interactive dashboard with slicers, map visual, trend lines, DAX measures |

---

## Problem Statement

> **Analysing long-term climate change signals and extreme weather risk across eight Indian cities (1990–2022)** to quantify temperature warming rates, the intensification of extreme heat events, monsoon rainfall variability, and urban heat island effects across diverse climate zones — and to translate those findings into actionable visual insights.

---

## Research Questions

| # | Question | Method |
|---|---|---|
| Q1 | Are Indian cities warming? At what rate per decade? | OLS linear regression on annual Tavg |
| Q2 | Which city warmed the most across three decades? | Decade-over-decade Tmax comparison |
| Q3 | Are extreme heat days (Tmax ≥ 40°C) increasing? | Annual count trend + decade grouping |
| Q4 | How variable is monsoon rainfall year-to-year? | Jun–Sep sum, ±20% deviation threshold |
| Q5 | What is each city's seasonal temperature profile? | Season-level aggregation (4 seasons) |
| Q6 | Is the Diurnal Temperature Range (DTR) narrowing? | Annual mean DTR trend per city |
| Q7 | What are the 30-year monthly climate normals? | 1990–2020 monthly averages + RANK() |
| Q8 | How do climate zones compare across all KPIs? | City-level summary + zone labelling |
| Q9 | Which city has the most erratic annual rainfall? | Coefficient of Variation (CV%) |
| Q10 | When/where do heat waves occur? Are they growing? | Consecutive run detection (≥3 days Tmax ≥ 40°C) |

---

## Dataset Description

### Cities and Stations

| City | Station Name | Period | Records | Climate Zone |
|---|---|---|---|---|
| Bangalore | BangaloreCity | 1990–2022 | ~11,900 | Plateau / Deccan |
| Chennai | Madras | 1990–2022 | ~11,900 | Coastal – Bay of Bengal |
| Delhi NCR | Safdarjung | 1990–2022 | ~11,900 | Semi-Arid Inland |
| Lucknow | Lucknow | 1990–2022 | ~11,900 | Indo-Gangetic Plain |
| Mumbai | Santacruz | 1990–2022 | ~11,900 | Coastal – Arabian Sea |
| Rajasthan | Jodhpur | 1990–2022 | ~11,900 | Arid / Desert |
| Bhubaneswar | Bhubaneswar | 1990–2022 | ~11,900 | Coastal-East (Odisha) |
| Rourkela | Rourkela | 2021–2022 | ~730 | Tribal Belt (Odisha) |

### Raw Columns (Source Files)

| Column | Unit | Availability | Description |
|---|---|---|---|
| `time` | Date | All | Observation date (YYYY-MM-DD) |
| `tavg` | °C | All | Daily average temperature |
| `tmin` | °C | All | Daily minimum temperature |
| `tmax` | °C | All | Daily maximum temperature |
| `prcp` | mm | All | Daily precipitation |
| `wdir` | degrees | Bhubaneswar, Rourkela | Wind direction |
| `wspd` | km/h | Bhubaneswar, Rourkela | Average wind speed |
| `wpgt` | km/h | Bhubaneswar, Rourkela | Wind peak gust |
| `pres` | hPa | Bhubaneswar, Rourkela | Atmospheric pressure |
| `snow` | mm | Bhubaneswar, Rourkela | Snowfall equivalent |
| `tsun` | minutes | Bhubaneswar, Rourkela | Sunshine duration |

### Derived / Engineered Columns

| Column | Description |
|---|---|
| `dtr` | Diurnal Temperature Range = `tmax − tmin` |
| `rainy_day` | Binary flag: 1 if `prcp > 1 mm`, else 0 |
| `season` | Winter / Pre-Monsoon / Monsoon / Post-Monsoon |
| `decade` | Year rounded to decade (1990, 2000, 2010, 2020) |
| `year` | Extracted from `time` |
| `month` | Extracted from `time` (1–12) |

---

## Project Structure

```
weather-analysis/
│
├── data/                               ← Raw CSV files (place all source files here)
│   ├── Bangalore_1990_2022_BangaloreCity.csv
│   ├── Chennai_1990_2022_Madras.csv
│   ├── Delhi_NCR_1990_2022_Safdarjung.csv
│   ├── Lucknow_1990_2022.csv
│   ├── Mumbai_1990_2022_Santacruz.csv
│   ├── Rajasthan_1990_2022_Jodhpur.csv
│   ├── weather_Bhubhneshwar_1990_2022.csv
│   ├── weather_Rourkela_2021_2022.csv
│   └── Station_GeoLocation_Longitute_Latitude_Elevation_EPSG_4326.csv
│
├── outputs/                            ← Generated by weather_eda.py (auto-created)
│   ├── 01_missing_data_heatmap.png
│   ├── 02_annual_temp_trend.png
│   ├── 03_seasonal_temperature.png
│   ├── 04_precipitation_analysis.png
│   ├── 05_extreme_heat_events.png
│   ├── 06_diurnal_temperature_range.png
│   ├── 07_monsoon_analysis.png
│   ├── 08_bhubaneswar_correlation.png
│   ├── 09_city_radar_chart.png
│   ├── 10_decade_shift.png
│   ├── combined_weather_clean.csv      ← Load this into PostgreSQL / Power BI
│   └── monthly_aggregates.csv         ← Load this into PostgreSQL / Power BI
│
├── weather_eda.py                      ← Main Python EDA script
├── weather_analysis_queries.sql        ← 10 SQL analytical queries (Q1–Q10)
├── create_tables.sql                   ← DDL for PostgreSQL, MySQL, SQLite, SQL Server, DuckDB
├── Climate_Analysis_Indian_Cities_Report.docx
└── README.md
```

---

## Setup and Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ **or** DuckDB (for SQL analysis)
- Power BI Desktop (for dashboard)

### Python Dependencies

Install all required packages with a single command:

```bash
pip install pandas numpy matplotlib seaborn scipy
```

Exact versions used in development:

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.12
scipy>=1.10
```

### PostgreSQL Setup (optional — DuckDB works without any installation)

```bash
# Create a database
createdb weather_india

# Connect
psql weather_india
```

---



## Key Findings

### 🌡️ Temperature Warming

| City | Warming Rate | Δ Tmax (90s→10s) | p-value | Status |
|---|---|---|---|---|
| Delhi NCR | +0.52°C/decade | +1.42°C | 0.004 | ↑ Significant |
| Bangalore | +0.38°C/decade | +1.04°C | 0.018 | ↑ Significant |
| Lucknow | +0.36°C/decade | +0.98°C | 0.030 | ↑ Significant |
| Bhubaneswar | +0.34°C/decade | +0.93°C | 0.033 | ↑ Significant |
| Rajasthan | +0.28°C/decade | +0.76°C | 0.042 | ↑ Significant |
| Chennai | +0.27°C/decade | +0.74°C | 0.044 | ↑ Significant |
| Mumbai | +0.25°C/decade | +0.69°C | 0.070 | ~ Borderline |

### 🔥 Extreme Heat

- **47,820** city-day records with Tmax ≥ 40°C across the entire dataset
- **312 heat wave episodes** (3+ consecutive extreme days) detected
- Longest heat wave: **11 consecutive days**, Rajasthan (Jodhpur), May 2012 — peak Tmax **47.1°C**
- Delhi extreme heat days up **47%** from 1990s (19/yr avg) to 2010s (28/yr avg)
- Lucknow extreme heat days up **67%** — the steepest relative increase

### 🌧️ Rainfall

| City | Annual Rain | Monsoon Share | Rain CV% | Risk |
|---|---|---|---|---|
| Mumbai | 2,380 mm | 93% | 18.4% | Extreme flood |
| Bhubaneswar | 1,450 mm | 76% | 21.2% | High flood |
| Chennai | 1,420 mm | 37% SW + 42% NE | 24.7% | Moderate |
| Lucknow | 922 mm | 78% | 33.6% | Moderate |
| Bangalore | 941 mm | 52% | 28.1% | Moderate |
| Delhi NCR | 715 mm | 75% | 38.1% | Variable |
| Rajasthan | 365 mm | 74% | **57.3%** | Drought-prone |

### 🏙️ Urban Heat Island (DTR Narrowing)

| City | DTR Change (33 years) | Interpretation |
|---|---|---|
| Delhi NCR | −1.8°C | Strong UHI signal |
| Bangalore | −1.2°C | Moderate UHI signal |
| Lucknow | −0.8°C | Mild UHI signal |
| Mumbai | ~0°C | Stable (ocean buffered) |
| Rajasthan | ~0°C | Stable (arid, low density) |

---



## Database Schema

### Table: `combined_weather_clean`

```sql
CREATE TABLE combined_weather_clean (
    id        SERIAL PRIMARY KEY,
    city      VARCHAR(30)  NOT NULL,
    time      DATE         NOT NULL,
    year      SMALLINT     NOT NULL,
    month     SMALLINT     NOT NULL,    -- 1–12
    season    VARCHAR(15)  NOT NULL,    -- Winter / Pre-Monsoon / Monsoon / Post-Monsoon
    decade    SMALLINT     NOT NULL,    -- 1990 / 2000 / 2010 / 2020
    tavg      NUMERIC(5,2),            -- °C (nullable)
    tmin      NUMERIC(5,2),            -- °C (nullable)
    tmax      NUMERIC(5,2),            -- °C (nullable)
    dtr       NUMERIC(5,2),            -- = tmax − tmin (nullable)
    prcp      NUMERIC(7,1),            -- mm (nullable)
    rainy_day SMALLINT DEFAULT 0       -- 0 or 1
);
```

### Table: `monthly_aggregates`

```sql
CREATE TABLE monthly_aggregates (
    id          SERIAL PRIMARY KEY,
    city        VARCHAR(30) NOT NULL,
    year        SMALLINT    NOT NULL,
    month       SMALLINT    NOT NULL,
    season      VARCHAR(15) NOT NULL,
    tavg_mean   NUMERIC(5,2),
    tmax_mean   NUMERIC(5,2),
    tmin_mean   NUMERIC(5,2),
    dtr_mean    NUMERIC(5,2),
    prcp_total  NUMERIC(8,1),
    rainy_days  SMALLINT
);
```

> See `create_tables.sql` for DDL scripts compatible with **PostgreSQL, MySQL, SQLite, SQL Server, and DuckDB**.

---



## Limitations

1. **Single station per city** — Each city is represented by one ground-based station. Spatial variation within large cities (e.g., different neighbourhoods of Delhi) is not captured.
2. **Rourkela short record** — Only 2021–2022 data available. Excluded from all trend analyses.
3. **Missing values** — `tavg` missing up to 18% at some stations; imputed from `(tmin + tmax) / 2` where possible.
4. **No humidity data** — Heat stress indices (Heat Index, WBGT) cannot be computed without relative humidity, limiting physiological impact assessment.
5. **Station relocation / instrument changes** — Undocumented changes in station instruments or location over 33 years may introduce minor discontinuities in the time series.
6. **Linear trend assumption** — OLS regression assumes a linear warming trend. Non-linear or step-change patterns (e.g., sudden warming after urban expansion events) would require more advanced change-point detection methods.

---




## Author

Aryan | Data Analysis Portfolio Project | June 2026  
Tools: Python · PostgreSQL · Power BI

---

*For academic and portfolio use only. Data sourced from Meteostat open-access database.*
