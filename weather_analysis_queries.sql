-- =============================================================================
--  INDIAN CITIES WEATHER DATA — SQL ANALYSIS QUERIES
--  Table: combined_weather_clean
--  Columns: city, time, year, month, season, decade,
--           tavg, tmin, tmax, dtr, prcp, rainy_day
-- =============================================================================
-- NOTE: These queries run on the exported combined_weather_clean.csv.
--       Load it into SQLite / DuckDB / PostgreSQL / SQL Server as needed.
--       For DuckDB (fastest for CSV): SELECT * FROM 'combined_weather_clean.csv'
-- =============================================================================
-- ── Table 1 : combined_weather_clean ─────────────────────────────────────────
DROP TABLE IF EXISTS combined_weather_clean;

CREATE TABLE combined_weather_clean (
    id          SERIAL          PRIMARY KEY,

    -- Identity / temporal dimensions
    city        VARCHAR(30)     NOT NULL,
    time        DATE            NOT NULL,
    year        SMALLINT        NOT NULL,
    month       SMALLINT        NOT NULL  CHECK (month BETWEEN 1 AND 12),
    season      VARCHAR(15)     NOT NULL
                    CHECK (season IN ('Winter','Pre-Monsoon','Monsoon','Post-Monsoon')),
    decade      SMALLINT        NOT NULL,

    -- Temperature variables  (°C, nullable because of sensor gaps)
    tavg        NUMERIC(5,2),
    tmin        NUMERIC(5,2),
    tmax        NUMERIC(5,2),
    dtr         NUMERIC(5,2),   -- Diurnal Temperature Range = tmax - tmin

    -- Precipitation
    prcp        NUMERIC(7,1),   -- daily precipitation in mm
    rainy_day   SMALLINT        DEFAULT 0
                    CHECK (rainy_day IN (0, 1))  -- 1 if prcp > 1 mm
);

-- Indexes for the most common query patterns
CREATE INDEX idx_cwc_city       ON combined_weather_clean (city);
CREATE INDEX idx_cwc_time       ON combined_weather_clean (time);
CREATE INDEX idx_cwc_city_year  ON combined_weather_clean (city, year);
CREATE INDEX idx_cwc_city_month ON combined_weather_clean (city, month);
CREATE INDEX idx_cwc_season     ON combined_weather_clean (season);
CREATE INDEX idx_cwc_tmax       ON combined_weather_clean (tmax);

-- Load from CSV (adjust path)
COPY combined_weather_clean (city, time, year, month, season, decade,
                              tavg, tmin, tmax, dtr, prcp, rainy_day)
FROM 'D:/outputs/combined_weather_clean.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');


-- ── Table 2 : monthly_aggregates ─────────────────────────────────────────────
DROP TABLE IF EXISTS monthly_aggregates;

CREATE TABLE monthly_aggregates (
    id          SERIAL          PRIMARY KEY,

    city        VARCHAR(30)     NOT NULL,
    year        SMALLINT        NOT NULL,
    month       SMALLINT        NOT NULL  CHECK (month BETWEEN 1 AND 12),
    season      VARCHAR(15)     NOT NULL
                    CHECK (season IN ('Winter','Pre-Monsoon','Monsoon','Post-Monsoon')),

    tavg_mean   NUMERIC(5,2),
    tmax_mean   NUMERIC(5,2),
    tmin_mean   NUMERIC(5,2),
    dtr_mean    NUMERIC(5,2),

    prcp_total  NUMERIC(8,1),
    rainy_days  SMALLINT
);

CREATE INDEX idx_ma_city      ON monthly_aggregates (city);
CREATE INDEX idx_ma_city_year ON monthly_aggregates (city, year);
CREATE INDEX idx_ma_season    ON monthly_aggregates (season);

COPY monthly_aggregates (city, year, month, season,
                          tavg_mean, tmax_mean, tmin_mean, dtr_mean,
                          prcp_total, rainy_days)
FROM 'D:/outputs/monthly_aggregates.csv'
WITH (FORMAT CSV, HEADER TRUE, NULL '');

-- ─────────────────────────────────────────────────────────────────────────────
-- Q1. PROBLEM: Is India's average temperature rising across cities?
--     → Annual warming trend per city
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    city,
    year,
    ROUND(AVG(tavg), 2)        AS annual_avg_temp,
    ROUND(AVG(tmax), 2)        AS annual_avg_tmax,
    ROUND(AVG(tmin), 2)        AS annual_avg_tmin,
    ROUND(MAX(tmax), 1)        AS annual_peak_tmax,
    ROUND(MIN(tmin), 1)        AS annual_coldest_tmin,
    COUNT(*)                   AS data_days
FROM combined_weather_clean
WHERE tavg IS NOT NULL
GROUP BY city, year
ORDER BY city, year;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q2. PROBLEM: Which city has warmed the most over three decades?
--     → Decade-wise comparison of mean Tmax
-- ─────────────────────────────────────────────────────────────────────────────

WITH decade_avg AS (
    SELECT
        city,
        decade,
        ROUND(AVG(tmax), 2) AS avg_tmax,
        ROUND(AVG(tavg), 2) AS avg_tavg,
        ROUND(AVG(tmin), 2) AS avg_tmin
    FROM combined_weather_clean
    WHERE tmax IS NOT NULL
      AND decade IN (1990, 2000, 2010)
    GROUP BY city, decade
),
pivot AS (
    SELECT
        city,
        MAX(CASE WHEN decade = 1990 THEN avg_tmax END) AS tmax_1990s,
        MAX(CASE WHEN decade = 2000 THEN avg_tmax END) AS tmax_2000s,
        MAX(CASE WHEN decade = 2010 THEN avg_tmax END) AS tmax_2010s
    FROM decade_avg
    GROUP BY city
)
SELECT
    city,
    ROUND(tmax_1990s, 2)                       AS tmax_1990s,
    ROUND(tmax_2000s, 2)                       AS tmax_2000s,
    ROUND(tmax_2010s, 2)                       AS tmax_2010s,
    ROUND(tmax_2010s - tmax_1990s, 2)          AS change_1990_to_2010,
    CASE
        WHEN tmax_2010s - tmax_1990s > 1.5 THEN 'Significant Warming'
        WHEN tmax_2010s - tmax_1990s > 0.5 THEN 'Moderate Warming'
        WHEN tmax_2010s - tmax_1990s < 0   THEN 'Cooling'
        ELSE 'Stable'
    END AS warming_status
FROM pivot
ORDER BY change_1990_to_2010 DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q3. PROBLEM: Are extreme heat days (Tmax ≥ 40°C) increasing?
--     → Extreme heat event frequency per city per year
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    city,
    year,
    COUNT(*)                                          AS extreme_heat_days,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER
        (PARTITION BY city), 2)                       AS pct_of_city_total,
    MAX(tmax)                                         AS hottest_day_tmax,
    ROUND(AVG(tmax), 2)                               AS avg_tmax_on_extreme_days
FROM combined_weather_clean
WHERE tmax >= 40
GROUP BY city, year
ORDER BY city, year;

-- Summary: total extreme days by decade
SELECT
    city,
    decade,
    COUNT(*)                    AS extreme_heat_days,
    COUNT(DISTINCT year)        AS years_in_decade,
    ROUND(COUNT(*) * 1.0 /
          COUNT(DISTINCT year), 1)  AS avg_extreme_days_per_year
FROM combined_weather_clean
WHERE tmax >= 40
GROUP BY city, decade
ORDER BY city, decade;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q4. PROBLEM: How does monsoon rainfall vary year to year?
--     → Monsoon season (Jun–Sep) annual rainfall, deviation from mean
-- ─────────────────────────────────────────────────────────────────────────────

WITH monsoon_annual AS (
    SELECT
        city,
        year,
        ROUND(SUM(prcp), 1)   AS monsoon_prcp_mm,
        SUM(rainy_day)        AS monsoon_rainy_days
    FROM combined_weather_clean
    WHERE month BETWEEN 6 AND 9
      AND prcp IS NOT NULL
    GROUP BY city, year
),
stats AS (
    SELECT
        city,
        ROUND(AVG(monsoon_prcp_mm), 1)    AS long_term_mean,
        ROUND(AVG(monsoon_rainy_days), 1) AS avg_rainy_days
    FROM monsoon_annual
    GROUP BY city
)
SELECT
    m.city,
    m.year,
    m.monsoon_prcp_mm,
    m.monsoon_rainy_days,
    s.long_term_mean,
    ROUND(m.monsoon_prcp_mm - s.long_term_mean, 1)          AS deviation_mm,
    ROUND((m.monsoon_prcp_mm - s.long_term_mean)
          / s.long_term_mean * 100, 1)                      AS deviation_pct,
    CASE
        WHEN m.monsoon_prcp_mm > s.long_term_mean * 1.2  THEN 'Excess'
        WHEN m.monsoon_prcp_mm < s.long_term_mean * 0.8  THEN 'Deficit'
        ELSE 'Normal'
    END AS rainfall_category
FROM monsoon_annual m
JOIN stats s ON m.city = s.city
ORDER BY m.city, m.year;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q5. PROBLEM: Seasonal temperature profile — which season drives heat risk?
--     → Seasonal aggregation
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    city,
    season,
    ROUND(AVG(tavg), 2)          AS avg_temp,
    ROUND(AVG(tmax), 2)          AS avg_tmax,
    ROUND(AVG(tmin), 2)          AS avg_tmin,
    ROUND(MAX(tmax), 1)          AS highest_tmax,
    ROUND(MIN(tmin), 1)          AS lowest_tmin,
    ROUND(AVG(dtr), 2)           AS avg_dtr,
    ROUND(SUM(prcp), 1)          AS total_prcp_mm,
    SUM(rainy_day)               AS total_rainy_days
FROM combined_weather_clean
GROUP BY city, season
ORDER BY city,
    CASE season
        WHEN 'Winter'       THEN 1
        WHEN 'Pre-Monsoon'  THEN 2
        WHEN 'Monsoon'      THEN 3
        WHEN 'Post-Monsoon' THEN 4
    END;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q6. PROBLEM: Is the diurnal temperature range (DTR) narrowing?
--     → Narrowing DTR signals urban heat island effect
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    city,
    year,
    ROUND(AVG(dtr), 2)   AS avg_dtr,
    ROUND(MIN(dtr), 2)   AS min_dtr,
    ROUND(MAX(dtr), 2)   AS max_dtr,
    COUNT(*)             AS days_with_dtr
FROM combined_weather_clean
WHERE dtr IS NOT NULL AND dtr > 0
GROUP BY city, year
ORDER BY city, year;

-- Decade-level DTR comparison
SELECT
    city,
    decade,
    ROUND(AVG(dtr), 2) AS avg_dtr,
    COUNT(*)            AS n_days
FROM combined_weather_clean
WHERE dtr IS NOT NULL AND dtr > 0
GROUP BY city, decade
ORDER BY city, decade;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q7. PROBLEM: Which month is the hottest / coldest for each city?
--     → Monthly climate normals (30-year averages)
-- ─────────────────────────────────────────────────────────────────────────────

WITH monthly_normals AS (
    SELECT
        city,
        month,
        ROUND(AVG(tavg), 2)  AS normal_tavg,
        ROUND(AVG(tmax), 2)  AS normal_tmax,
        ROUND(AVG(tmin), 2)  AS normal_tmin,
        ROUND(AVG(prcp), 2)  AS normal_daily_prcp,
        ROUND(SUM(prcp) / COUNT(DISTINCT year), 1) AS avg_monthly_prcp_mm
    FROM combined_weather_clean
    WHERE year BETWEEN 1990 AND 2020
    GROUP BY city, month
),
ranked AS (
    SELECT *,
        RANK() OVER (PARTITION BY city ORDER BY normal_tmax DESC) AS rank_hottest,
        RANK() OVER (PARTITION BY city ORDER BY normal_tmin  ASC)  AS rank_coldest
    FROM monthly_normals
)
SELECT
    city,
    month,
    normal_tavg,
    normal_tmax,
    normal_tmin,
    avg_monthly_prcp_mm,
    rank_hottest,
    rank_coldest,
    CASE WHEN rank_hottest = 1 THEN '🔥 Hottest Month' ELSE '' END AS hottest_flag,
    CASE WHEN rank_coldest = 1 THEN '❄ Coldest Month'  ELSE '' END AS coldest_flag
FROM ranked
ORDER BY city, month;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q8. PROBLEM: Compare climate zones — coastal vs. inland vs. desert
--     → City-level summary for all KPI columns
-- ─────────────────────────────────────────────────────────────────────────────

SELECT
    city,
    CASE city
        WHEN 'Chennai'     THEN 'Coastal'
        WHEN 'Mumbai'      THEN 'Coastal'
        WHEN 'Bhubaneswar' THEN 'Coastal-East'
        WHEN 'Bangalore'   THEN 'Plateau'
        WHEN 'Rajasthan'   THEN 'Arid/Desert'
        WHEN 'Delhi'       THEN 'Semi-Arid Inland'
        WHEN 'Lucknow'     THEN 'Indo-Gangetic Plain'
        WHEN 'Rourkela'    THEN 'Tribal Belt'
    END AS climate_zone,
    ROUND(AVG(tavg), 2)                 AS overall_avg_temp,
    ROUND(AVG(tmax), 2)                 AS overall_avg_tmax,
    ROUND(AVG(tmin), 2)                 AS overall_avg_tmin,
    ROUND(AVG(dtr), 2)                  AS overall_avg_dtr,
    COUNT(CASE WHEN tmax >= 40 THEN 1 END)   AS total_extreme_days,
    ROUND(SUM(prcp) / COUNT(DISTINCT year), 1) AS avg_annual_rainfall_mm,
    ROUND(AVG(rainy_day) * 365, 0)      AS est_rainy_days_per_year,
    COUNT(DISTINCT year)                AS years_of_data
FROM combined_weather_clean
GROUP BY city
ORDER BY overall_avg_temp DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q9. PROBLEM: Rainfall variability — which city has the most erratic rain?
--     → Year-to-year standard deviation of annual rainfall
-- ─────────────────────────────────────────────────────────────────────────────

WITH annual_rain AS (
    SELECT city, year, SUM(prcp) AS ann_prcp
    FROM combined_weather_clean
    WHERE prcp IS NOT NULL
    GROUP BY city, year
)
SELECT
    city,
    ROUND(AVG(ann_prcp), 1)                AS mean_annual_rain,
    ROUND(
        SQRT(AVG((ann_prcp - sub.mean_prcp) * (ann_prcp - sub.mean_prcp))),
    1)                                     AS std_annual_rain,
    ROUND(
        SQRT(AVG((ann_prcp - sub.mean_prcp) * (ann_prcp - sub.mean_prcp)))
        / NULLIF(AVG(ann_prcp), 0) * 100,
    1)                                     AS coeff_variation_pct,
    ROUND(MAX(ann_prcp), 1)                AS max_annual_rain,
    ROUND(MIN(ann_prcp), 1)                AS min_annual_rain
FROM annual_rain
JOIN (
    SELECT city, AVG(ann_prcp) AS mean_prcp
    FROM annual_rain GROUP BY city
) sub USING (city)
GROUP BY city
ORDER BY coeff_variation_pct DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- Q10. PROBLEM: When are heat waves most likely?
--     → Consecutive days with Tmax ≥ 40 (heat wave detection)
-- ─────────────────────────────────────────────────────────────────────────────

-- Flags each day that is part of a 3+-day run of Tmax ≥ 40°C
WITH flagged AS (
    SELECT
        city, time, year, month, tmax,
        CASE WHEN tmax >= 40 THEN 1 ELSE 0 END AS hot_flag
    FROM combined_weather_clean
    WHERE tmax IS NOT NULL
),
runs AS (
    SELECT
        city, time, year, month, tmax, hot_flag,
        ROW_NUMBER() OVER (PARTITION BY city ORDER BY time) -
        ROW_NUMBER() OVER (PARTITION BY city, hot_flag ORDER BY time) AS grp
    FROM flagged
),
heat_waves AS (
    SELECT
        city,
        MIN(time)    AS hw_start,
        MAX(time)    AS hw_end,
        COUNT(*)     AS hw_length_days,
        ROUND(MAX(tmax), 1) AS peak_tmax,
        MIN(year)    AS year
    FROM runs
    WHERE hot_flag = 1
    GROUP BY city, grp
    HAVING COUNT(*) >= 3
)
SELECT *
FROM heat_waves
ORDER BY city, hw_start;
