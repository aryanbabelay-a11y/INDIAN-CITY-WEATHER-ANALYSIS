"""
=============================================================================
  INDIAN CITIES WEATHER ANALYSIS (1990–2022)
  Exploratory Data Analysis & Climate Trend Study
  Cities: Bangalore, Chennai, Delhi, Lucknow, Mumbai,
          Rajasthan (Jodhpur), Bhubaneswar, Rourkela
=============================================================================
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# 0. CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
sns.set_theme(style="darkgrid", palette="muted")
plt.rcParams.update({'figure.dpi': 130, 'font.size': 11})

DATA_PATHS = {
    'Bangalore'  : 'D:/Bangalore_1990_2022_BangaloreCity.csv',
    'Chennai'    : 'D:/Chennai_1990_2022_Madras.csv',
    'Delhi'      : 'D:/Delhi_NCR_1990_2022_Safdarjung.csv',
    'Lucknow'    : 'D:/Lucknow_1990_2022.csv',
    'Mumbai'     : 'D:/Mumbai_1990_2022_Santacruz.csv',
    'Rajasthan'  : 'D:/Rajasthan_1990_2022_Jodhpur.csv',
    'Bhubaneswar': 'D:/weather_Bhubhneshwar_1990_2022.csv',
    'Rourkela'   : 'D:/weather_Rourkela_2021_2022.csv',
}
GEO_PATH = 'data/Station_GeoLocation_Longitute_Latitude_Elevation_EPSG_4326.csv'

CITY_COLORS = {
    'Bangalore'  : '#E76F51',
    'Chennai'    : '#F4A261',
    'Delhi'      : '#2A9D8F',
    'Lucknow'    : '#264653',
    'Mumbai'     : '#E9C46A',
    'Rajasthan'  : '#A8DADC',
    'Bhubaneswar': '#457B9D',
    'Rourkela'   : '#1D3557',
}

# ─────────────────────────────────────────────────────────────────────────────
# 1. DATA LOADING & CLEANING
# ─────────────────────────────────────────────────────────────────────────────

def load_and_clean(path: str, city: str) -> pd.DataFrame:
    """Load a city CSV, parse dates, derive extra columns."""
    df = pd.read_csv(path)

    # Robust date parsing (handles DD-MM-YYYY and YYYY-MM-DD)
    df['time'] = pd.to_datetime(df['time'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['time'])
    df = df.sort_values('time').reset_index(drop=True)

    # Tag the city
    df['city'] = city

    # Temporal features
    df['year']    = df['time'].dt.year
    df['month']   = df['time'].dt.month
    df['season']  = df['month'].map({
        12:'Winter', 1:'Winter', 2:'Winter',
        3:'Pre-Monsoon', 4:'Pre-Monsoon', 5:'Pre-Monsoon',
        6:'Monsoon', 7:'Monsoon', 8:'Monsoon', 9:'Monsoon',
        10:'Post-Monsoon', 11:'Post-Monsoon'
    })
    df['decade']  = (df['year'] // 10) * 10

    # Fill missing tavg from (tmin+tmax)/2 where possible
    mask = df['tavg'].isna() & df['tmin'].notna() & df['tmax'].notna()
    df.loc[mask, 'tavg'] = (df.loc[mask, 'tmin'] + df.loc[mask, 'tmax']) / 2

    # Diurnal temperature range
    df['dtr'] = df['tmax'] - df['tmin']

    # Rainy-day flag (prcp > 1 mm)
    if 'prcp' in df.columns:
        df['rainy_day'] = (df['prcp'] > 1).astype(int)

    return df


def load_all() -> tuple[dict, pd.DataFrame]:
    """Return dict of per-city DataFrames and a single combined DataFrame."""
    city_dfs = {}
    for city, path in DATA_PATHS.items():
        try:
            city_dfs[city] = load_and_clean(path, city)
            print(f"  ✓ {city:15s} — {len(city_dfs[city]):,} rows loaded")
        except FileNotFoundError:
            print(f"  ✗ {city:15s} — file not found at: {path}")

    combined = pd.concat(city_dfs.values(), ignore_index=True)
    return city_dfs, combined


print("=" * 60)
print("  LOADING DATA")
print("=" * 60)
city_dfs, combined = load_all()


# ─────────────────────────────────────────────────────────────────────────────
# 2. BASIC STATISTICS OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────

print("\n" + "=" * 60)
print("  SUMMARY STATISTICS PER CITY")
print("=" * 60)

summary_rows = []
for city, df in city_dfs.items():
    row = {
        'City'           : city,
        'Records'        : len(df),
        'Year Range'     : f"{df['year'].min()}–{df['year'].max()}",
        'Avg Temp (°C)'  : round(df['tavg'].mean(), 1),
        'Max Temp Ever'  : round(df['tmax'].max(), 1),
        'Min Temp Ever'  : round(df['tmin'].min(), 1),
        'Total Precip mm': round(df['prcp'].sum(), 0),
        'Null % (tavg)'  : round(df['tavg'].isna().mean() * 100, 1),
    }
    summary_rows.append(row)

summary_df = pd.DataFrame(summary_rows)
print(summary_df.to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# 3. MISSING DATA HEATMAP
# ─────────────────────────────────────────────────────────────────────────────

def plot_missing_heatmap(city_dfs):
    cols_of_interest = ['tavg', 'tmin', 'tmax', 'prcp']
    null_pct = pd.DataFrame({
        city: [df[c].isna().mean() * 100 if c in df.columns else 100
               for c in cols_of_interest]
        for city, df in city_dfs.items()
    }, index=cols_of_interest)

    fig, ax = plt.subplots(figsize=(11, 4))
    sns.heatmap(null_pct, annot=True, fmt='.1f', cmap='YlOrRd',
                linewidths=0.5, ax=ax, vmin=0, vmax=60,
                cbar_kws={'label': 'Missing %'})
    ax.set_title('Missing Data (%) by City & Variable', fontsize=14, pad=12)
    ax.set_xlabel('')
    plt.tight_layout()
    plt.savefig('outputs/01_missing_data_heatmap.png')
    plt.show()
    print("  → Saved: outputs/01_missing_data_heatmap.png")


# ─────────────────────────────────────────────────────────────────────────────
# 4. ANNUAL TEMPERATURE TREND  (Climate Change Signal)
# ─────────────────────────────────────────────────────────────────────────────

def plot_annual_temp_trend(city_dfs):
    """Line plot of annual average temperature with OLS trend lines."""
    # Only long-record cities
    long_cities = [c for c, d in city_dfs.items() if d['year'].max() - d['year'].min() >= 10]

    annual = {}
    for city in long_cities:
        df = city_dfs[city]
        annual[city] = df.groupby('year')['tavg'].mean().reset_index()
        annual[city]['city'] = city

    fig, axes = plt.subplots(4, 2, figsize=(16, 16), sharex=False)
    axes = axes.flatten()

    for i, city in enumerate(long_cities):
        ax = axes[i]
        a = annual[city].dropna()
        ax.plot(a['year'], a['tavg'], color=CITY_COLORS[city], lw=1.5, alpha=0.8)

        # Trend line
        slope, intercept, r, p, _ = stats.linregress(a['year'], a['tavg'])
        trend_y = slope * a['year'] + intercept
        ax.plot(a['year'], trend_y, '--', color='crimson', lw=1.5,
                label=f'Trend: {slope*10:+.2f}°C/decade  (p={p:.3f})')
        ax.fill_between(a['year'], a['tavg'], trend_y, alpha=0.15, color=CITY_COLORS[city])

        ax.set_title(city, fontsize=12)
        ax.set_ylabel('Avg Temp (°C)')
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3)

    for j in range(len(long_cities), len(axes)):
        axes[j].set_visible(False)

    fig.suptitle('Annual Average Temperature Trend (1990–2022)', fontsize=15, y=1.01)
    plt.tight_layout()
    plt.savefig('outputs/02_annual_temp_trend.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/02_annual_temp_trend.png")


# ─────────────────────────────────────────────────────────────────────────────
# 5. SEASONAL TEMPERATURE BOX PLOTS
# ─────────────────────────────────────────────────────────────────────────────

def plot_seasonal_temperature(combined):
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    season_order = ['Winter', 'Pre-Monsoon', 'Monsoon', 'Post-Monsoon']
    long_cities  = [c for c in combined['city'].unique() if c != 'Rourkela']
    data_subset  = combined[combined['city'].isin(long_cities)]

    # Tmax by season
    sns.boxplot(data=data_subset, x='season', y='tmax', hue='city',
                order=season_order, ax=axes[0], palette=CITY_COLORS,
                linewidth=0.8, fliersize=1)
    axes[0].set_title('Max Temperature by Season & City')
    axes[0].set_xlabel('Season')
    axes[0].set_ylabel('Tmax (°C)')
    axes[0].legend(fontsize=7, ncol=2)

    # Avg temp by month (heatmap style)
    pivot = data_subset.groupby(['city', 'month'])['tavg'].mean().unstack()
    sns.heatmap(pivot, cmap='RdYlBu_r', annot=True, fmt='.1f',
                linewidths=0.4, ax=axes[1],
                cbar_kws={'label': 'Avg Temp (°C)'})
    axes[1].set_title('Monthly Mean Temperature Heatmap')
    axes[1].set_xlabel('Month')
    axes[1].set_ylabel('')
    axes[1].set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun',
                              'Jul','Aug','Sep','Oct','Nov','Dec'])

    plt.suptitle('Seasonal & Monthly Temperature Patterns', fontsize=14)
    plt.tight_layout()
    plt.savefig('outputs/03_seasonal_temperature.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/03_seasonal_temperature.png")


# ─────────────────────────────────────────────────────────────────────────────
# 6. PRECIPITATION ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def plot_precipitation(city_dfs):
    long_cities = [c for c, d in city_dfs.items() if d['year'].max() - d['year'].min() >= 10]

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # (a) Annual total precipitation over years
    ax = axes[0]
    for city in long_cities:
        ann = city_dfs[city].groupby('year')['prcp'].sum()
        ax.plot(ann.index, ann.values, color=CITY_COLORS[city], lw=1.3, label=city, alpha=0.85)
    ax.set_title('Annual Total Precipitation (mm)')
    ax.set_ylabel('Precipitation (mm)')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # (b) Monthly average precipitation (bar grouped)
    monthly_prcp = pd.DataFrame({
        city: city_dfs[city].groupby('month')['prcp'].mean()
        for city in long_cities
    })
    monthly_prcp.plot(kind='bar', ax=axes[1], color=list(CITY_COLORS.values()),
                      width=0.75, edgecolor='none')
    axes[1].set_title('Average Monthly Precipitation (mm)')
    axes[1].set_xlabel('Month')
    axes[1].set_ylabel('Avg Daily Precip (mm)')
    axes[1].set_xticklabels(['J','F','M','A','M','J','J','A','S','O','N','D'], rotation=0)
    axes[1].legend(fontsize=8)

    # (c) Rainy days per year
    ax = axes[2]
    for city in long_cities:
        rain = city_dfs[city].groupby('year')['rainy_day'].sum()
        ax.plot(rain.index, rain.values, color=CITY_COLORS[city], lw=1.3, label=city, alpha=0.85)
    ax.set_title('Rainy Days per Year (prcp > 1mm)')
    ax.set_ylabel('Rainy Days')
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    plt.suptitle('Precipitation Analysis', fontsize=14)
    plt.tight_layout()
    plt.savefig('outputs/04_precipitation_analysis.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/04_precipitation_analysis.png")


# ─────────────────────────────────────────────────────────────────────────────
# 7. EXTREME HEAT EVENTS (Days with Tmax ≥ 40°C)
# ─────────────────────────────────────────────────────────────────────────────

def plot_extreme_heat(city_dfs):
    threshold = 40
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Count extreme days per year per city
    extreme_counts = {}
    for city, df in city_dfs.items():
        if df['year'].max() - df['year'].min() < 5:
            continue
        cnt = df[df['tmax'] >= threshold].groupby('year').size()
        extreme_counts[city] = cnt

    extreme_df = pd.DataFrame(extreme_counts).fillna(0)

    # Stacked area
    extreme_df.plot(kind='area', stacked=False, ax=axes[0],
                    color=list(CITY_COLORS.values()), alpha=0.65, linewidth=1.2)
    axes[0].set_title(f'Days with Tmax ≥ {threshold}°C per Year')
    axes[0].set_ylabel('Count of Extreme Heat Days')
    axes[0].legend(fontsize=8)

    # Decade comparison
    decade_extreme = {}
    for city, df in city_dfs.items():
        if df['year'].max() - df['year'].min() < 5:
            continue
        d = df[df['tmax'] >= threshold].groupby('decade').size().reset_index()
        d.columns = ['decade', 'count']
        d['city'] = city
        decade_extreme[city] = d

    decade_all = pd.concat(decade_extreme.values(), ignore_index=True)
    pivot = decade_all.pivot(index='decade', columns='city', values='count').fillna(0)
    pivot.plot(kind='bar', ax=axes[1], color=list(CITY_COLORS.values()),
               edgecolor='white', width=0.7)
    axes[1].set_title(f'Extreme Heat Days by Decade (Tmax ≥ {threshold}°C)')
    axes[1].set_xlabel('Decade')
    axes[1].set_ylabel('Total Days')
    axes[1].set_xticklabels(pivot.index.astype(str), rotation=0)
    axes[1].legend(fontsize=8)

    plt.suptitle('Extreme Heat Event Analysis', fontsize=14)
    plt.tight_layout()
    plt.savefig('outputs/05_extreme_heat_events.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/05_extreme_heat_events.png")


# ─────────────────────────────────────────────────────────────────────────────
# 8. DIURNAL TEMPERATURE RANGE (DTR) — URBANISATION PROXY
# ─────────────────────────────────────────────────────────────────────────────

def plot_dtr(city_dfs):
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Annual mean DTR over time
    for city, df in city_dfs.items():
        if df['year'].max() - df['year'].min() < 5:
            continue
        ann_dtr = df.groupby('year')['dtr'].mean()
        axes[0].plot(ann_dtr.index, ann_dtr.values,
                     color=CITY_COLORS[city], lw=1.4, label=city)
    axes[0].set_title('Annual Mean Diurnal Temperature Range (DTR)')
    axes[0].set_ylabel('DTR (°C)')
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    # DTR distribution violin
    long = combined[combined['city'] != 'Rourkela'].dropna(subset=['dtr'])
    city_order = long.groupby('city')['dtr'].mean().sort_values().index.tolist()
    sns.violinplot(data=long, x='city', y='dtr', order=city_order,
                   palette=CITY_COLORS, ax=axes[1], cut=0)
    axes[1].set_title('Diurnal Temperature Range Distribution by City')
    axes[1].set_ylabel('DTR (°C)')
    axes[1].set_xlabel('')
    axes[1].tick_params(axis='x', rotation=30)

    plt.suptitle('Diurnal Temperature Range (Urbanisation / Land-Use Proxy)', fontsize=14)
    plt.tight_layout()
    plt.savefig('outputs/06_diurnal_temperature_range.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/06_diurnal_temperature_range.png")


# ─────────────────────────────────────────────────────────────────────────────
# 9. MONSOON PERFORMANCE ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────

def plot_monsoon_analysis(city_dfs):
    monsoon_months = [6, 7, 8, 9]
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    # Annual monsoon precipitation
    monsoon_prcp = {}
    for city, df in city_dfs.items():
        if df['year'].max() - df['year'].min() < 5:
            continue
        m = df[df['month'].isin(monsoon_months)].groupby('year')['prcp'].sum()
        monsoon_prcp[city] = m

    mdf = pd.DataFrame(monsoon_prcp)
    mdf.plot(ax=axes[0], color=list(CITY_COLORS.values()), lw=1.4, alpha=0.85)
    axes[0].set_title('Annual Monsoon Season Precipitation (Jun–Sep)')
    axes[0].set_ylabel('Total Precipitation (mm)')
    axes[0].legend(fontsize=8)
    axes[0].grid(True, alpha=0.3)

    # % of annual rain from monsoon
    pct_data = {}
    for city, df in city_dfs.items():
        if df['year'].max() - df['year'].min() < 5:
            continue
        ann = df.groupby('year')['prcp'].sum()
        mon = df[df['month'].isin(monsoon_months)].groupby('year')['prcp'].sum()
        pct_data[city] = (mon / ann * 100).mean()

    pd.Series(pct_data).sort_values().plot(
        kind='barh', ax=axes[1],
        color=[CITY_COLORS[c] for c in pd.Series(pct_data).sort_values().index]
    )
    axes[1].set_title('% of Annual Rainfall from Monsoon Season')
    axes[1].set_xlabel('% of Annual Precipitation')
    axes[1].grid(axis='x', alpha=0.4)

    plt.suptitle('Monsoon Rainfall Analysis', fontsize=14)
    plt.tight_layout()
    plt.savefig('outputs/07_monsoon_analysis.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/07_monsoon_analysis.png")


# ─────────────────────────────────────────────────────────────────────────────
# 10. CORRELATION HEATMAP (within Bhubaneswar — full variables)
# ─────────────────────────────────────────────────────────────────────────────

def plot_bhubaneswar_correlation(city_dfs):
    df = city_dfs['Bhubaneswar'].copy()
    # Select only numeric, non-trivially-null columns
    num_cols = ['tavg', 'tmin', 'tmax', 'prcp', 'wdir', 'wspd', 'pres', 'dtr']
    num_cols = [c for c in num_cols if c in df.columns]
    corr = df[num_cols].corr()

    fig, ax = plt.subplots(figsize=(9, 7))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, linewidths=0.5, ax=ax, vmin=-1, vmax=1)
    ax.set_title('Variable Correlation — Bhubaneswar Station\n(only station with wind/pressure data)',
                 fontsize=12)
    plt.tight_layout()
    plt.savefig('outputs/08_bhubaneswar_correlation.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/08_bhubaneswar_correlation.png")


# ─────────────────────────────────────────────────────────────────────────────
# 11. CITY COMPARISON RADAR / SPIDER CHART
# ─────────────────────────────────────────────────────────────────────────────

def plot_city_radar(city_dfs):
    long_cities = [c for c, d in city_dfs.items() if d['year'].max() - d['year'].min() >= 10]

    metrics = {
        'Avg Temp'    : lambda df: df['tavg'].mean(),
        'Temp Range'  : lambda df: df['tmax'].mean() - df['tmin'].mean(),
        'Annual Rain' : lambda df: df['prcp'].sum() / df['year'].nunique(),
        'Extreme Days': lambda df: (df['tmax'] >= 40).sum() / df['year'].nunique(),
        'DTR'         : lambda df: df['dtr'].mean(),
    }

    scores = {}
    for city in long_cities:
        scores[city] = {m: fn(city_dfs[city]) for m, fn in metrics.items()}

    score_df = pd.DataFrame(scores).T
    # Normalise to 0–1
    norm_df = (score_df - score_df.min()) / (score_df.max() - score_df.min())

    categories = list(norm_df.columns)
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for city in long_cities:
        vals = norm_df.loc[city].tolist() + [norm_df.loc[city].tolist()[0]]
        ax.plot(angles, vals, lw=2, label=city, color=CITY_COLORS[city])
        ax.fill(angles, vals, alpha=0.1, color=CITY_COLORS[city])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0.25', '0.50', '0.75', '1.0'], fontsize=8)
    ax.set_title('City Climate Profile (Normalised)', fontsize=13, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=9)

    plt.tight_layout()
    plt.savefig('outputs/09_city_radar_chart.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/09_city_radar_chart.png")


# ─────────────────────────────────────────────────────────────────────────────
# 12. DECADE-OVER-DECADE TEMPERATURE SHIFT
# ─────────────────────────────────────────────────────────────────────────────

def plot_decade_shift(city_dfs):
    """Compare mean Tmax in 1990s vs 2010s for each city."""
    results = []
    for city, df in city_dfs.items():
        if df['year'].max() < 2010:
            continue
        t90 = df[df['decade'] == 1990]['tmax'].mean()
        t10 = df[df['decade'] == 2010]['tmax'].mean()
        results.append({'City': city, '1990s': t90, '2010s': t10, 'Delta': t10 - t90})

    rdf = pd.DataFrame(results).sort_values('Delta', ascending=False)

    fig, axes = plt.subplots(1, 2, figsize=(15, 6))

    # Side-by-side bar
    x = np.arange(len(rdf))
    width = 0.35
    axes[0].bar(x - width/2, rdf['1990s'], width, label='1990s',
                color='steelblue', alpha=0.85)
    axes[0].bar(x + width/2, rdf['2010s'], width, label='2010s',
                color='tomato', alpha=0.85)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(rdf['City'], rotation=30)
    axes[0].set_ylabel('Mean Tmax (°C)')
    axes[0].set_title('Mean Tmax: 1990s vs 2010s')
    axes[0].legend()

    # Delta bar
    colors = ['green' if v < 0 else 'crimson' for v in rdf['Delta']]
    axes[1].bar(rdf['City'], rdf['Delta'], color=colors, alpha=0.85)
    axes[1].axhline(0, color='black', lw=0.8)
    axes[1].set_ylabel('Tmax Change (°C)')
    axes[1].set_title('Tmax Increase: 2010s minus 1990s')
    axes[1].tick_params(axis='x', rotation=30)

    for i, (_, row) in enumerate(rdf.iterrows()):
        axes[1].text(i, row['Delta'] + 0.05, f"{row['Delta']:+.2f}°C",
                     ha='center', fontsize=9)

    plt.suptitle('Decade-Over-Decade Temperature Shift', fontsize=14)
    plt.tight_layout()
    plt.savefig('outputs/10_decade_shift.png', bbox_inches='tight')
    plt.show()
    print("  → Saved: outputs/10_decade_shift.png")


# ─────────────────────────────────────────────────────────────────────────────
# 13. STATISTICAL SIGNIFICANCE — Mann-Kendall Trend Test
# ─────────────────────────────────────────────────────────────────────────────

def run_trend_tests(city_dfs):
    """Mann-Kendall-style trend test using scipy's linregress + p-value."""
    print("\n" + "=" * 60)
    print("  ANNUAL TEMPERATURE TREND — LINEAR REGRESSION (p-value)")
    print("=" * 60)
    print(f"{'City':15s} {'Variable':8s} {'Slope (°C/yr)':>14s} {'p-value':>10s} {'Trend':>12s}")
    print("-" * 60)

    for city, df in city_dfs.items():
        if df['year'].max() - df['year'].min() < 10:
            continue
        for var in ['tavg', 'tmax', 'tmin']:
            ann = df.groupby('year')[var].mean().dropna()
            if len(ann) < 5:
                continue
            slope, _, _, p, _ = stats.linregress(ann.index, ann.values)
            sig = '↑ WARMING' if (slope > 0 and p < 0.05) else ('↓ COOLING' if (slope < 0 and p < 0.05) else 'No sig trend')
            print(f"  {city:13s} {var:8s} {slope:+14.4f} {p:10.4f} {sig:>12s}")


# ─────────────────────────────────────────────────────────────────────────────
# 14. EXPORT COMBINED CLEAN DATASET (for SQL / Power BI)
# ─────────────────────────────────────────────────────────────────────────────

def export_combined(combined):
    out = combined[['city', 'time', 'year', 'month', 'season', 'decade',
                    'tavg', 'tmin', 'tmax', 'dtr', 'prcp', 'rainy_day']].copy()
    out.to_csv('outputs/combined_weather_clean.csv', index=False)
    print("\n  ✓ Combined clean dataset → outputs/combined_weather_clean.csv")
    print(f"    Shape: {out.shape}")

    # Also export monthly aggregates (Power BI optimised)
    monthly = out.groupby(['city', 'year', 'month', 'season']).agg(
        tavg_mean=('tavg', 'mean'),
        tmax_mean=('tmax', 'mean'),
        tmin_mean=('tmin', 'mean'),
        dtr_mean=('dtr', 'mean'),
        prcp_total=('prcp', 'sum'),
        rainy_days=('rainy_day', 'sum'),
    ).reset_index()
    monthly.to_csv('outputs/monthly_aggregates.csv', index=False)
    print("  ✓ Monthly aggregates → outputs/monthly_aggregates.csv")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────

import os
os.makedirs('outputs', exist_ok=True)

print("\nRunning all visualisations …\n")
plot_missing_heatmap(city_dfs)
plot_annual_temp_trend(city_dfs)
plot_seasonal_temperature(combined)
plot_precipitation(city_dfs)
plot_extreme_heat(city_dfs)
plot_dtr(city_dfs)
plot_monsoon_analysis(city_dfs)
plot_bhubaneswar_correlation(city_dfs)
plot_city_radar(city_dfs)
plot_decade_shift(city_dfs)
run_trend_tests(city_dfs)
export_combined(combined)

print("\n✅  All analyses complete. Check the outputs/ folder.")
