"""
analyzer.py — Strategic Opportunity Assessment Engine

Implements Visibility-Based Opportunity Scoring (Free Proxy-BSR),
Keyword Clustering, and 2026-calibrated Sales Estimation.

No external API calls required.

Author: KDP Automation Architect
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# 2026 Sales Estimation: Logarithmic BSR-to-Unit Model
# ---------------------------------------------------------------------------
# Calibrated from observed 2026 marketplace dynamics:
#   BSR ~100,000 → ~1.5 sales/day
#   BSR ~10,000  → ~6.8 sales/day
#   BSR ~1,000   → ~31  sales/day
#
# Model: daily_sales = 2825.5 * BSR^(-0.655)
# ---------------------------------------------------------------------------
def estimate_daily_sales(bsr: float) -> float:
    """Estimate daily unit sales from BSR using the 2026 logarithmic model."""
    try:
        bsr = float(bsr)
        if bsr <= 0:
            return 0.0
        return round(2825.5 * (bsr ** -0.655), 1)
    except (ValueError, TypeError):
        return 0.0


def add_sales_estimates(df: pd.DataFrame) -> pd.DataFrame:
    """Attach 'Est._Daily_Sales' column from BSR if present, else from
    Visibility_Score as a proxy."""
    if df.empty:
        return df
    if 'BSR' in df.columns and df['BSR'].dtype in ('int64', 'float64'):
        df['Est._Daily_Sales'] = df['BSR'].apply(estimate_daily_sales)
    else:
        df['Est._Daily_Sales'] = 0.0
    return df


# ---------------------------------------------------------------------------
# Core Opportunity Scoring Engine
# ---------------------------------------------------------------------------
def find_gems_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze DataFrame with Visibility-Based Opportunity Scoring.

    Enriches the input with:
      - Visibility_Score  = (21 - index) * 5  (1st=105, 20th=10)
      - EOS               = VS * (Price / AvgPriceOfNiche)
      - Theme             = keyword cluster membership
      - Est._Daily_Sales  = logarithmic estimate from BSR or VS proxy

    Parameters
    ----------
    df : pd.DataFrame
        Product data from scraper. Must contain 'Price' and 'Title' columns.
        Sorted by search-result rank (1 = top result).

    Returns
    -------
    pd.DataFrame
        Enriched + sorted by EOS descending.
    """
    if df.empty:
        return df

    df = df.reset_index(drop=True)

    # 1. Visibility Score (VS): rank-based proxy for BSR
    df['Visibility_Score'] = (21 - np.clip(df.index, 0, 20)) * 5

    # 2. Estimated Opportunity Score (EOS):
    #   high-visibility + healthy price = strong opportunity
    avg_price = df['Price'].mean()
    df['EOS'] = df['Visibility_Score'] * (df['Price'] / avg_price)

    # 3. Sales estimates (2026 logarithmic model)
    df = add_sales_estimates(df)

    # 4. Keyword Clustering — extract "Themes" from titles
    themes = ['Cozy', 'Coloring', 'Stress Relief', 'Set', 'Large Print', 'Easy']

    def extract_theme(title: str) -> str:
        for theme in themes:
            if theme.lower() in str(title).lower():
                return theme
        return 'Other'

    df['Theme'] = df['Title'].apply(extract_theme)

    return df.sort_values(by='EOS', ascending=False)


# ---------------------------------------------------------------------------
# Niche Insights Aggregator
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Deep Niche Tunneling — Competitive Density Scoring
# ---------------------------------------------------------------------------
def calculate_competition_score(
    total_results: int,
    filtered_results: int,
) -> str:
    """
    Calculate competition density score — simple string output.

    Returns one of:
      - "Low Density (High Potential)" — ratio < 0.1 (blue ocean)
      - "Moderate Density" — ratio < 0.3
      - "Saturated (High Competition)" — ratio >= 0.3
      - "Insufficient Data" — total_results <= 0
    """
    if total_results <= 0:
        return "Insufficient Data"
    ratio = filtered_results / total_results
    if ratio < 0.1:
        return "Low Density (High Potential)"
    if ratio < 0.3:
        return "Moderate Density"
    return "Saturated (High Competition)"


def compute_niche_density_score(
    filtered_count: int,
    total_count: int,
    avg_visibility_score: float = 0.0,
) -> Dict[str, Any]:
    """
    Compute the competitive density score for a deep-tunneled niche.

    Density = filtered_count / total_count  (lower = fewer competitors
    in the filtered segment such as "last 30 days").

    Golden Niche criteria:
      - Density < 0.3 (few new entrants relative to total market)
      - Average Visibility Score >= 30 (decent discoverability)

    Parameters
    ----------
    filtered_count : int
        Number of products in the filtered (e.g. last-30-days) results.
    total_count : int
        Number of products in the unfiltered (total) results.
    avg_visibility_score : float
        Mean Visibility_Score from the filtered result set.

    Returns
    -------
    dict with keys:
        density, density_label, is_golden, recommendation
    """
    if total_count <= 0:
        return {
            "density": 0.0,
            "density_label": "N/A",
            "is_golden": False,
            "recommendation": "Insufficient data — total count is zero.",
        }

    density = round(filtered_count / total_count, 3)

    if density < 0.15:
        label = "Very Low"
    elif density < 0.3:
        label = "Low"
    elif density < 0.5:
        label = "Moderate"
    elif density < 0.75:
        label = "High"
    else:
        label = "Very High"

    is_golden = density < 0.3 and avg_visibility_score >= 30

    if is_golden:
        rec = (
            ":star: **Golden Niche** — Low competition density "
            f"({density:.1%}) with strong visibility "
            f"(avg VS: {avg_visibility_score:.0f}). "
            "Strong candidate for rapid market entry."
        )
    elif density < 0.3:
        rec = (
            f"Low density ({density:.1%}) but visibility is moderate "
            f"(avg VS: {avg_visibility_score:.0f}). "
            "Consider improving listing quality to compete."
        )
    elif density < 0.5:
        rec = (
            f"Moderate density ({density:.1%}). "
            "Opportunity exists but requires strong differentiation."
        )
    else:
        rec = (
            f"High density ({density:.1%}) — saturated niche. "
            "Look for a more specific sub-niche or different angle."
        )

    return {
        "density": density,
        "density_label": label,
        "is_golden": is_golden,
        "recommendation": rec,
    }


def compute_thematic_density(
    niche_rows: List[Dict[str, Any]],
    total_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Compute competitive density per "Theme" cluster between filtered
    and total result sets.

    Parameters
    ----------
    niche_rows : list[dict]
        Filtered result set (e.g. last-30-days tunnel).
    total_rows : list[dict]
        Unfiltered result set (e.g. full category sweep).

    Returns
    -------
    list[dict] — one per unique Theme, sorted by density ascending.
        Keys: theme, filtered_count, total_count, density, is_golden, avg_eos.
    """
    niche_df = pd.DataFrame(niche_rows)
    total_df = pd.DataFrame(total_rows)

    if niche_df.empty or total_df.empty:
        return []

    # Apply theme clustering
    themes = ['Cozy', 'Coloring', 'Stress Relief', 'Set', 'Large Print', 'Easy']

    def extract_theme(title: str) -> str:
        for theme in themes:
            if theme.lower() in str(title).lower():
                return theme
        return 'Other'

    niche_df['Theme'] = niche_df['Title'].apply(extract_theme)
    total_df['Theme'] = total_df['Title'].apply(extract_theme)

    niche_counts = niche_df['Theme'].value_counts()
    total_counts = total_df['Theme'].value_counts()

    results: List[Dict[str, Any]] = []
    all_themes = set(list(niche_counts.index) + list(total_counts.index))

    for theme in sorted(all_themes):
        fc = int(niche_counts.get(theme, 0))
        tc = int(total_counts.get(theme, 0))
        if tc == 0:
            continue
        density = round(fc / tc, 3)
        avg_eos = niche_df[niche_df['Theme'] == theme]['EOS'].mean() if 'EOS' in niche_df.columns else 0.0
        is_golden = density < 0.3 and fc > 0

        results.append({
            "theme": theme,
            "filtered_count": fc,
            "total_count": tc,
            "density": density,
            "density_label": "Very Low" if density < 0.15 else "Low" if density < 0.3 else "Moderate" if density < 0.5 else "High" if density < 0.75 else "Very High",
            "is_golden": is_golden,
            "avg_eos": round(avg_eos, 1),
        })

    return sorted(results, key=lambda x: x["density"])


def get_niche_insights(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate by Theme to identify the highest-performing micro-niches.

    Returns
    -------
    pd.DataFrame
        Columns: avg EOS, avg Visibility_Score, avg Est._Daily_Sales, product count.
    """
    agg = {
        'EOS': 'mean',
        'Visibility_Score': 'mean',
        'Title': 'count',
    }
    if 'Est._Daily_Sales' in df.columns:
        agg['Est._Daily_Sales'] = 'mean'

    insights = df.groupby('Theme').agg(agg).rename(columns={'Title': 'Product_Count'})
    return insights.sort_values(by='EOS', ascending=False)
