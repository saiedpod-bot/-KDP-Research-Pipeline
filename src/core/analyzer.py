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


# ---------------------------------------------------------------------------
# 1. Profit Calculator — net profit per book after Amazon fees & printing
# ---------------------------------------------------------------------------
def calculate_profit(
    price: float,
    page_count: int = 200,
    is_ebook: bool = False,
    ink_type: str = 'bw',
) -> Dict[str, Any]:
    """
    Estimate net profit for a KDP paperback/ebook.

    Amazon KDP 2026 royalty structure:
      - eBook (70%): $2.99–$9.99 minus ~$0.15 delivery
      - Paperback (60%): >=$9.99
      - Paperback (50%): <$9.99

    Printing cost (B&W): $1.00 + $0.012/page
    Printing cost (Color): $1.00 + $0.055/page

    Returns dict with keys: price, royalty_rate, royalty, print_cost,
    delivery_fee, net_profit, profit_margin_pct.
    """
    if price <= 0:
        return {"net_profit": 0.0, "profit_margin_pct": 0.0}

    if is_ebook:
        royalty_rate = 0.70 if 2.99 <= price <= 9.99 else 0.35
        delivery_fee = max(0.15, price * 0.01)
        print_cost = 0.0
    else:
        royalty_rate = 0.60 if price >= 9.99 else 0.50
        delivery_fee = 0.0
        if ink_type == 'color':
            print_cost = 1.00 + (max(page_count, 24) * 0.055)
        else:
            print_cost = 1.00 + (max(page_count, 24) * 0.012)

    royalty = price * royalty_rate
    net_profit = round(royalty - delivery_fee - print_cost, 2)
    profit_margin_pct = round((net_profit / price) * 100, 1) if price > 0 else 0.0

    return {
        "price": price,
        "royalty_rate": royalty_rate,
        "royalty": round(royalty, 2),
        "print_cost": round(print_cost, 2),
        "delivery_fee": round(delivery_fee, 2),
        "net_profit": net_profit,
        "profit_margin_pct": profit_margin_pct,
    }


def add_profit_columns(df: pd.DataFrame, page_count: int = 200) -> pd.DataFrame:
    """Attach Net_Profit and Profit_Margin_% columns to a scored DataFrame."""
    if df.empty or "Price" not in df.columns:
        return df
    profits = df["Price"].apply(
        lambda p: calculate_profit(float(p), page_count=page_count)
    )
    df["Net_Profit"] = profits.apply(lambda x: x["net_profit"])
    df["Profit_Margin_%"] = profits.apply(lambda x: x["profit_margin_pct"])
    return df


# ---------------------------------------------------------------------------
# 2. Keyword Explorer — extract keywords & find gaps
# ---------------------------------------------------------------------------
def extract_keywords_from_titles(titles: List[str]) -> List[Dict[str, Any]]:
    """
    Extract meaningful keywords from a list of product titles.

    Returns list of {keyword, count, frequency} sorted by frequency descending.
    """
    import re
    from collections import Counter

    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'for', 'of', 'to', 'in', 'is',
        'it', 'with', 'on', 'at', 'by', 'this', 'that', 'not', 'are',
        'was', 'but', 'all', 'be', 'has', 'have', 'from', 'their',
        'your', 'our', 'its', 'book', 'books', 'more',
    }
    words: List[str] = []
    phrases: List[str] = []

    for title in titles:
        title_lower = str(title).lower()
        # Individual words (filtered)
        tokens = re.findall(r'[a-z]+', title_lower)
        filtered = [t for t in tokens if t not in stop_words and len(t) > 2]
        words.extend(filtered)
        # Two-word phrases
        for i in range(len(filtered) - 1):
            phrases.append(f"{filtered[i]} {filtered[i+1]}")

    word_counts = Counter(words)
    phrase_counts = Counter(phrases)

    total = len(titles) if titles else 1
    results: List[Dict[str, Any]] = []

    # Top single words
    for word, count in word_counts.most_common(30):
        results.append({
            "keyword": word,
            "type": "word",
            "count": count,
            "frequency": round(count / total, 2),
        })

    # Top phrases
    for phrase, count in phrase_counts.most_common(20):
        results.append({
            "keyword": phrase,
            "type": "phrase",
            "count": count,
            "frequency": round(count / total, 2),
        })

    return sorted(results, key=lambda x: x["count"], reverse=True)


def find_keyword_gaps(
    competitor_titles: List[str],
    opportunity_titles: List[str],
) -> List[Dict[str, Any]]:
    """
    Find keywords present in competitor titles but missing or rare
    in opportunity (new entrant) titles.

    Returns list of gap keywords sorted by gap_score descending.
    """
    comp_words: Dict[str, int] = {}
    opp_words: Dict[str, int] = {}

    import re
    for title in competitor_titles:
        for w in re.findall(r'[a-z]+', str(title).lower()):
            if len(w) > 2:
                comp_words[w] = comp_words.get(w, 0) + 1

    for title in opportunity_titles:
        for w in re.findall(r'[a-z]+', str(title).lower()):
            if len(w) > 2:
                opp_words[w] = opp_words.get(w, 0) + 1

    total_comp = len(competitor_titles) or 1
    total_opp = len(opportunity_titles) or 1

    gaps: List[Dict[str, Any]] = []
    for word, comp_count in comp_words.items():
        opp_count = opp_words.get(word, 0)
        comp_freq = comp_count / total_comp
        opp_freq = opp_count / total_opp
        gap_score = round(comp_freq - opp_freq, 3)
        if gap_score > 0.1:
            gaps.append({
                "keyword": word,
                "competitor_freq": round(comp_freq, 2),
                "opportunity_freq": round(opp_freq, 2),
                "gap_score": gap_score,
            })

    return sorted(gaps, key=lambda x: x["gap_score"], reverse=True)[:20]


# ---------------------------------------------------------------------------
# 5. Unified Opportunity Index (UOI) — single 0–100 score
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# AI-Powered Niche Idea Generator (like MerchMetrix's Idea Generator)
# ---------------------------------------------------------------------------
def generate_niche_ideas(keyword: str, max_ideas: int = 10) -> List[Dict[str, Any]]:
    """
    Generate related niche ideas from a seed keyword using pattern expansion.

    Uses prefix/suffix expansion, category cross-matching, and theme
    combinations to produce actionable micro-niche ideas.

    Parameters
    ----------
    keyword : str
        Seed keyword (e.g. "coloring book").
    max_ideas : int
        Maximum number of ideas to return.

    Returns
    -------
    list[dict]
        Each with keys: idea, angle, reason, difficulty.
    """
    ideas: List[Dict[str, Any]] = []
    kw = keyword.lower().strip()

    # --- Prefix/suffix expansion patterns ---
    prefixes = [
        "large print", "easy", "simple", "beginner", "adult",
        "kids", "seniors", "women", "men", "professional",
    ]
    suffixes = [
        "for adults", "for beginners", "for kids", "for seniors",
        "for women", "for men", "made easy", "101", "journal",
        "workbook", "planner", "cookbook", "guide", "manual",
    ]
    themes = [
        "stress relief", "anxiety", "mindfulness", "self care",
        "christmas", "halloween", "holiday", "gifts",
        "animals", "nature", "travel", "space", "ocean",
        "vegan", "keto", "paleo", "low carb", "mediterranean",
        "anti inflammatory", "gluten free", "sugar free",
    ]
    angles = [
        "budget friendly", "quick", "30 minute", "5 ingredient",
        "one pot", "meal prep", "family sized", "single serving",
        "low content", "high content", "illustrated", "annotated",
    ]

    # 1. Prefix + keyword
    for prefix in prefixes:
        idea = f"{prefix} {kw}"
        if len(ideas) < max_ideas:
            ideas.append({
                "idea": idea.title(),
                "angle": f"Prefix '{prefix}' targets a specific audience segment",
                "reason": f"'{prefix}' narrows the market and reduces competition",
                "difficulty": "Low" if prefix in ("large print", "easy", "beginner") else "Medium",
            })

    # 2. Keyword + suffix
    for suffix in suffixes:
        idea = f"{kw} {suffix}"
        if len(ideas) < max_ideas:
            ideas.append({
                "idea": idea.title(),
                "angle": f"Suffix '{suffix}' adds specificity",
                "reason": f"'{suffix}' phrases have lower search volume but higher conversion",
                "difficulty": "Low" if suffix in ("101", "for beginners", "made easy") else "Medium",
            })

    # 3. Theme cross-matches
    for theme in themes:
        if len(ideas) >= max_ideas:
            break
        idea = f"{theme} {kw}"
        ideas.append({
            "idea": idea.title(),
            "angle": f"Theme '{theme}' taps into trending interest",
            "reason": f"'{theme}' is a growing sub-niche with engaged buyers",
            "difficulty": "Medium",
        })
        if len(ideas) >= max_ideas:
            break
        idea2 = f"{kw} {theme}"
        ideas.append({
            "idea": idea2.title(),
            "angle": f"Descriptive '{theme}' modifier",
            "reason": f"Combines broad appeal with niche targeting",
            "difficulty": "Medium",
        })

    # 4. Angle combinations
    for angle in angles:
        if len(ideas) >= max_ideas:
            break
        idea = f"{angle} {kw}"
        ideas.append({
            "idea": idea.title(),
            "angle": f"Value prop '{angle}' drives purchase intent",
            "reason": f"'{angle}' signals practical benefit to the buyer",
            "difficulty": "Low",
        })

    return ideas[:max_ideas]


# ---------------------------------------------------------------------------
# Trademark Safety Check Integration (like every POD tool has)
# ---------------------------------------------------------------------------
TRADEMARKED_TERMS = [
    # Major KDP trademarked/restricted terms
    "disney", "marvel", "dc comics", "harry potter", "star wars",
    "nfl", "nba", "mlb", "nhl", "fifa", "olympic",
    "coca cola", "pepsi", "nike", "adidas", "puma", "gucci",
    "louis vuitton", "channel", "versace", "prada", "fendi",
    "hello kitty", "sanrio", "pokemon", "nintendo", "sega",
    "minecraft", "fortnite", "roblox", "among us",
    "barbie", "lego", "hot wheels", "transformers",
    "paw patrol", "peppa pig", "bluey", "cocomelon",
    "santa claus", "elvis presley", "michael jackson",
    "taylor swift", "beyonce", "beatles", "rolling stones",
    "kfc", "mcdonald's", "starbucks", "wendys",
    "angsar", "i love", "ivy", "case",
    "kdp", "amazon", "kindle", "audible",
    "instant pot", "air fryer", "nutribullet", "ninja",
    "bible", "quran", "torah",  # religious texts - careful
    "wedding",  # restricted for certain uses
    "medical", "doctor", "nurse",  # medical claims restriction
    "american flag",  # specific usage rules
    "university of", "college of",  # educational institutions
    "harvard", "yale", "stanford", "mit", "oxford", "cambridge",
    "wwf", "unicef", "red cross",  # charitable orgs
    "fbi", "cia", "white house", "pentagon",  # government
    "the office", "friends", "seinfeld", "sopranos",
    "game of thrones", "stranger things", "squid game",
    "yellowstone", "better call saul", "breaking bad",
    "lord of the rings", "star trek", "doctor who",
]


def check_trademark(keyword: str) -> Dict[str, Any]:
    """
    Check a keyword or phrase against curated trademarked/restricted terms.

    Returns dict with:
      - is_safe: bool (True if no trademark issues found)
      - flagged_terms: list of flagged substrings
      - risk_level: "safe", "warning", or "high"
      - message: human-readable recommendation
    """
    kw_lower = keyword.lower().strip()
    flagged: List[str] = []

    for term in TRADEMARKED_TERMS:
        if term in kw_lower:
            flagged.append(term)

    if not flagged:
        return {
            "is_safe": True,
            "flagged_terms": [],
            "risk_level": "safe",
            "message": "No trademarked terms detected. This keyword appears safe to use.",
        }

    risk_level = "high" if len(flagged) > 1 else "warning"
    msg_parts = [
        f"Flagged term(s): {', '.join(flagged)}.",
    ]
    if risk_level == "high":
        msg_parts.append(
            "HIGH RISK: Multiple trademarked terms detected. "
            "Strongly recommend choosing alternative keywords."
        )
    else:
        msg_parts.append(
            f"'{flagged[0]}' is a trademarked or restricted term. "
            "Avoid using it in titles, descriptions, or backend keywords."
        )

    return {
        "is_safe": False,
        "flagged_terms": flagged,
        "risk_level": risk_level,
        "message": " ".join(msg_parts),
    }


# ---------------------------------------------------------------------------
# BSR Trend Sparklines (like Podly's product graphs)
# ---------------------------------------------------------------------------
def compute_bsr_trend_icon(
    current_bsr: Optional[float],
    historical_bsrs: Optional[List[float]] = None,
) -> str:
    """
    Compute a text-based trend indicator from BSR history.

    Parameters
    ----------
    current_bsr : float or None
        Current BSR value (lower is better).
    historical_bsrs : list[float] or None
        Previous BSR values (most recent first).

    Returns
    -------
    str
        Trend emoji/indicator: ":chart_with_upwards_trend:" (improving, BSR down),
        ":chart_with_downwards_trend:" (declining, BSR up),
        ":left_right_arrow:" (stable), or ":grey_question:" (unknown).
    """
    if current_bsr is None or current_bsr <= 0:
        return ":grey_question:"

    if not historical_bsrs or len(historical_bsrs) < 1:
        return ":left_right_arrow:"

    # Filter valid BSR values
    valid = [b for b in historical_bsrs if b and b > 0]
    if not valid:
        return ":left_right_arrow:"

    avg_historical = sum(valid) / len(valid)
    change_pct = (current_bsr - avg_historical) / avg_historical

    # BSR lower = better rank = improving trend
    if change_pct < -0.15:
        return ":chart_with_upwards_trend:"  # Improving (BSR dropped)
    elif change_pct > 0.15:
        return ":chart_with_downwards_trend:"  # Declining (BSR rose)
    else:
        return ":left_right_arrow:"  # Stable


def compute_niche_trend(
    snapshot_history: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Determine overall niche trend from snapshot history.

    Returns dict with keys: direction (up/stable/down), icon, description.
    """
    if not snapshot_history or len(snapshot_history) < 2:
        return {
            "direction": "stable",
            "icon": ":left_right_arrow:",
            "description": "Insufficient data to determine trend.",
        }

    sorted_snaps = sorted(snapshot_history, key=lambda x: x.get("snapshot_date", ""))
    latest = sorted_snaps[-1]
    prior = sorted_snaps[-2]

    latest_count = int(latest.get("product_count", 0))
    prior_count = int(prior.get("product_count", 0))

    if prior_count == 0:
        return {"direction": "stable", "icon": ":left_right_arrow:", "description": "No prior data."}

    growth = (latest_count - prior_count) / prior_count

    if growth > 0.3:
        return {
            "direction": "up",
            "icon": ":chart_with_upwards_trend:",
            "description": f"Growing fast ({growth*100:.0f}% more products) — rising competition.",
        }
    elif growth > 0.1:
        return {
            "direction": "up",
            "icon": ":chart_with_upwards_trend:",
            "description": f"Slight growth ({growth*100:.0f}%) — monitor carefully.",
        }
    elif growth > -0.1:
        return {
            "direction": "stable",
            "icon": ":left_right_arrow:",
            "description": f"Stable ({growth*100:.1f}% change) — steady opportunity.",
        }
    else:
        return {
            "direction": "down",
            "icon": ":chart_with_downwards_trend:",
            "description": f"Shrinking ({growth*100:.0f}%) — fewer competitors entering.",
        }


def get_product_bsr_history(
    product_asin: str,
    snapshot_history: List[Dict[str, Any]],
) -> List[float]:
    """
    Extract historical BSR-like values for a product from snapshots.
    Uses avg_visibility as a BSR proxy when real BSR is unavailable.
    """
    values = []
    for snap in snapshot_history:
        vis = snap.get("avg_visibility", 0)
        if vis > 0:
            # Invert: higher visibility = lower (better) BSR
            values.append(max(1, 100 - vis))
    return values


def compute_unified_opportunity_index(
    eos: float,
    density: float = 0.0,
    profit_margin: float = 0.0,
    keyword_score: float = 0.5,
    trend_signal: float = 0.5,
) -> float:
    """
    Combine all opportunity factors into one 0–100 index.

    UOI = (EOS_normalized × 40) + ((1 - Density) × 25)
          + (ProfitMargin_normalized × 20) + (Keyword × 10) + (Trend × 5)
    """
    # Normalize EOS (typical range 0–200, cap at 150)
    eos_norm = min(eos / 150.0, 1.0)

    # Density: lower is better (0% = 1.0, 100% = 0.0)
    density_norm = max(1.0 - density, 0.0)

    # Profit margin: 0–50% range
    profit_norm = min(profit_margin / 50.0, 1.0)

    uoi = (eos_norm * 40) + (density_norm * 25) + (profit_norm * 20) + (keyword_score * 10) + (trend_signal * 5)
    return round(min(uoi, 100.0), 1)


def add_uoi_column(df: pd.DataFrame, density: float = 0.0) -> pd.DataFrame:
    """Attach UOI column to a scored + profit DataFrame."""
    if df.empty:
        return df
    df["UOI"] = df.apply(
        lambda row: compute_unified_opportunity_index(
            eos=row.get("EOS", 0) or 0,
            density=density,
            profit_margin=row.get("Profit_Margin_%", 0) or 0,
            keyword_score=0.5,  # placeholder — updated by keyword explorer
            trend_signal=0.5,   # placeholder — updated by niche tracker
        ),
        axis=1,
    )
    return df


# ---------------------------------------------------------------------------
# 3. Niche Tracker — trend signal computation
# ---------------------------------------------------------------------------
def compute_trend_signal(
    current_count: int,
    previous_count: int,
) -> float:
    """
    Compute a 0.0–1.0 trend signal from historical data.

    If product count is growing fast → low signal (more competition coming).
    If stable or shrinking → high signal (niche not saturating).
    """
    if previous_count <= 0:
        return 0.5  # neutral
    growth = (current_count - previous_count) / previous_count
    if growth > 0.5:
        return 0.2  # fast growing → weak signal
    if growth > 0.2:
        return 0.5  # moderate growth → neutral
    if growth > -0.1:
        return 0.8  # stable → strong signal
    return 0.9  # shrinking → very strong signal


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


# ---------------------------------------------------------------------------
# Niche Scoring Intelligence Module — Market Quality Score (0–100)
# ---------------------------------------------------------------------------
# Weights:
#   Demand (35%)       — BSR / Review Velocity / Review Count fallback
#   Competition (30%)  — median review count of top 10 (lower = better)
#   Pricing (15%)      — closeness to $5.99–$9.99 sweet spot
#   Indie/Recency (10%)— recent pub date + indie author signals
#   Dominance (-25%)   — penalty if top 3 hold > 60% of reviews/revenue
# ---------------------------------------------------------------------------


def _estimate_demand_score(competitors: List[Dict[str, Any]]) -> float:
    """
    Demand sub-score (0–100) based on BSR or review velocity.

    Strategy:
      1. If >= 50% of products have BSR > 0, use BSR-based score.
      2. Else fallback to review-count-based score.
    """
    bsr_values = [c.get("BSR", 0) or 0 for c in competitors if c.get("BSR", 0) or 0 > 0]
    if bsr_values and len(bsr_values) >= len(competitors) * 0.5:
        avg_bsr = sum(bsr_values) / len(bsr_values)
        # BSR model: lower BSR = higher demand
        # BSR 1 → 100, BSR 100k → 0
        score = max(0, 100 - (avg_bsr / 1000))
        return round(min(score, 100), 1)

    # Fallback: review count as demand proxy
    review_counts = [
        c.get("ReviewCount", 0) or 0
        for c in competitors
        if c.get("ReviewCount", 0) or 0 > 0
    ]
    if review_counts:
        avg_reviews = sum(review_counts) / len(review_counts)
        # 0 reviews → 0, 1000+ reviews → 100
        score = min(avg_reviews / 10, 100)
        return round(score, 1)

    return 10.0  # very low signal, slight positive for untested niche


def _estimate_competition_score(competitors: List[Dict[str, Any]]) -> float:
    """
    Competition sub-score (0–100) based on median review count of top 10.

    Lower median reviews = less competition = higher score.

    Calibration:
      median <= 10   → 100 (blue ocean)
      median <= 50   → 85
      median <= 100  → 70
      median <= 300  → 50
      median <= 1000 → 30
      median > 1000  → 10
    """
    top10 = competitors[:10]
    review_counts = sorted([
        c.get("ReviewCount", 0) or 0
        for c in top10
    ])
    if not review_counts:
        return 50.0

    mid = len(review_counts) // 2
    median = review_counts[mid] if len(review_counts) % 2 else (review_counts[mid - 1] + review_counts[mid]) / 2

    if median <= 10:
        return 100.0
    if median <= 50:
        return 85.0
    if median <= 100:
        return 70.0
    if median <= 300:
        return 50.0
    if median <= 1000:
        return 30.0
    return 10.0


def _estimate_pricing_score(competitors: List[Dict[str, Any]]) -> float:
    """
    Pricing sub-score (0–100) based on proximity to $5.99–$9.99 sweet spot.

    Scores how many products fall in the KDP sweet-spot price range.
    """
    prices = [
        c.get("Price", 0) or 0
        for c in competitors
        if (c.get("Price", 0) or 0) > 0
    ]
    if not prices:
        return 30.0

    in_sweet_spot = sum(1 for p in prices if 5.99 <= p <= 9.99)
    ratio = in_sweet_spot / len(prices)

    avg_price = sum(prices) / len(prices)
    price_penalty = 0.0
    if avg_price < 5.99:
        price_penalty = 10.0
    elif avg_price > 15.0:
        price_penalty = 20.0

    score = (ratio * 100) - price_penalty
    return round(max(0, min(score, 100)), 1)


def _estimate_recency_bonus(competitors: List[Dict[str, Any]]) -> float:
    """
    Indie/Recency bonus sub-score (0–100).

    Awards points for:
      - Products with recent publication dates (last 2 years).
      - Authors that appear to be indie (no corporate suffixes).
    """
    from datetime import datetime
    current_year = datetime.now().year

    recent_count = 0
    indie_count = 0
    total = len(competitors) or 1

    corporate_indicators = {"inc", "llc", "ltd", "press", "publishing", "house", "studio", "media", "group", "corporation", "enterprises"}

    for c in competitors:
        pub = c.get("PublicationDate", "")
        if pub:
            try:
                # Try to extract year
                year = None
                if len(pub) == 4 and pub.isdigit():
                    year = int(pub)
                elif "-" in pub:
                    year = int(pub.split("-")[0])
                if year and year >= current_year - 2:
                    recent_count += 1
            except (ValueError, IndexError):
                pass

        author = str(c.get("Author", "")).lower()
        if author and author != "unknown":
            words = set(author.replace(",", "").split())
            if not words & corporate_indicators:
                indie_count += 1

    recent_ratio = recent_count / total
    indie_ratio = indie_count / total

    score = (recent_ratio * 60) + (indie_ratio * 40)
    return round(min(score, 100), 1)


def _estimate_dominance_penalty(competitors: List[Dict[str, Any]]) -> float:
    """
    Dominance penalty (0–25) subtracted from total score.

    If top 3 products hold > 60% of total reviews → apply penalty.
    Penalty scales linearly from 0 (at 60%) to 25 (at 100%).

    Skips penalty when too few competitors exist (< 4 products),
    as concentration is meaningless with limited data.
    """
    if len(competitors) < 4:
        return 0.0

    review_counts = [
        c.get("ReviewCount", 0) or 0
        for c in competitors
    ]
    total_reviews = sum(review_counts)
    if total_reviews <= 0:
        return 0.0

    top3_reviews = sum(sorted(review_counts, reverse=True)[:3])
    concentration = top3_reviews / total_reviews

    if concentration <= 0.60:
        return 0.0
    penalty = ((concentration - 0.60) / 0.40) * 25
    return round(min(penalty, 25), 1)


def calculate_niche_score(
    competitors_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute the Market Quality Score (0–100) for a niche.

    Parameters
    ----------
    competitors_data : list[dict]
        Product rows from the scraper. Each dict should contain:
        ASIN, Title, Author, Price, BSR, ReviewCount, Rating, PublicationDate.

    Returns
    -------
    dict with keys:
        total_score       — Market Quality Score (0–100)
        verdict           — label from get_niche_verdict()
        signals: {
            demand_score,
            competition_score,
            pricing_score,
            recency_bonus,
            dominance_penalty,
        }
        weights: {
            demand_weight,
            competition_weight,
            pricing_weight,
            recency_weight,
            dominance_weight,
        }
        contribution: {
            demand_contrib,
            competition_contrib,
            pricing_contrib,
            recency_contrib,
            dominance_contrib,
        }
        product_count,
    """
    if not competitors_data:
        return {
            "total_score": 0,
            "verdict": "Insufficient Data",
            "signals": {},
            "weights": {},
            "contribution": {},
            "product_count": 0,
        }

    # Weights
    weights = {
        "demand": 0.35,
        "competition": 0.30,
        "pricing": 0.15,
        "recency": 0.10,
        "dominance": -0.25,
    }

    # Raw signals (each 0–100)
    demand = _estimate_demand_score(competitors_data)
    competition = _estimate_competition_score(competitors_data)
    pricing = _estimate_pricing_score(competitors_data)
    recency = _estimate_recency_bonus(competitors_data)
    penalty = _estimate_dominance_penalty(competitors_data)

    signals = {
        "demand_score": demand,
        "competition_score": competition,
        "pricing_score": pricing,
        "recency_bonus": recency,
        "dominance_penalty": penalty,
    }

    # Weighted contributions
    contribution = {
        "demand_contrib": round(demand * weights["demand"], 2),
        "competition_contrib": round(competition * weights["competition"], 2),
        "pricing_contrib": round(pricing * weights["pricing"], 2),
        "recency_contrib": round(recency * weights["recency"], 2),
        "dominance_contrib": round(-penalty * abs(weights["dominance"]), 2),
    }

    total_score = sum(contribution.values())
    total_score = round(max(0, min(total_score, 100)), 1)

    return {
        "total_score": total_score,
        "verdict": get_niche_verdict(total_score),
        "signals": signals,
        "weights": weights,
        "contribution": contribution,
        "product_count": len(competitors_data),
    }


def get_niche_verdict(score: float) -> str:
    """
    Map a numeric Market Quality Score to a human-readable verdict band.

    Bands:
      Excellent: 85+
      Great:     70+
      Good:      55+
      Okay:      40+
      Weak:      25+
      Poor:      <25
    """
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Great"
    if score >= 55:
        return "Good"
    if score >= 40:
        return "Okay"
    if score >= 25:
        return "Weak"
    return "Poor"


# ---------------------------------------------------------------------------
# Empty-Result Diagnostics & Query Broadening
# ---------------------------------------------------------------------------
_COMMON_STOP_WORDS: set = {
    "a", "an", "the", "for", "and", "or", "of", "to", "in", "with",
    "book", "books", "guide", "guides", "ideas", "idea", "tips",
}

_QUERY_BROADENING_RULES: List[tuple] = [
    # (word to remove, reason label)
    ("for beginners", "broader audience"),
    ("for kids", "broader audience"),
    ("for adults", "broader audience"),
    ("for women", "remove niche audience"),
    ("for men", "remove niche audience"),
    ("for seniors", "remove niche audience"),
    ("beginners", "remove level specifier"),
    ("easy", "remove qualifier"),
    ("simple", "remove qualifier"),
    ("large print", "more general search"),
    ("complete", "less specific"),
    ("ultimate", "less specific"),
    ("essential", "less specific"),
    ("guide", "remove generic word"),
    ("ideas", "remove generic word"),
    ("tips", "remove generic word"),
]


def suggest_broader_queries(query: str) -> List[Dict[str, Any]]:
    """
    Generate broader search suggestions when a query returns no results.

    Uses a multi-strategy approach:
    1. Remove qualifying phrases (for beginners, for adults, etc.)
    2. Remove trailing generic words (guide, ideas, tips)
    3. Split compound terms and try sub-combinations
    4. Remove stop words progressively

    Parameters
    ----------
    query : str
        The search query that returned no results.

    Returns
    -------
    List[Dict[str, Any]]
        Each dict: {query, strategy, reason}
    """
    suggestions: List[Dict[str, Any]] = []
    seen: set = set()
    lower: str = query.lower().strip()

    def _add(q: str, strategy: str, reason: str) -> None:
        key = q.strip().lower()
        if key and key != lower and key not in seen:
            seen.add(key)
            suggestions.append({"query": q.strip(), "strategy": strategy, "reason": reason})

    # Strategy 1: Remove qualifying phrases
    for phrase, reason in _QUERY_BROADENING_RULES:
        if phrase in lower:
            broad = lower.replace(phrase, "").strip()
            # Clean up double spaces
            broad = " ".join(broad.split())
            if broad:
                _add(broad, "broaden by phrase", reason)

    # Strategy 2: Remove last word(s) progressively (for long-tail queries)
    words = lower.split()
    if len(words) >= 3:
        for n in range(len(words) - 1, 1, -1):
            shortened = " ".join(words[:n])
            _add(shortened, "shorten query", "remove trailing specificity")

    # Strategy 3: Try sub-combinations of 2-word pairs (for compound niches)
    if len(words) >= 4:
        for i in range(len(words)):
            for j in range(i + 2, len(words) + 1):
                subset = words[i:j]
                if 2 <= len(subset) <= len(words) - 1:
                    candidate = " ".join(subset)
                    _add(candidate, "extract sub-niche", "try a narrower combination")

    # Strategy 4: Remove stop words progressively
    filtered = [w for w in words if w not in _COMMON_STOP_WORDS]
    if len(filtered) < len(words) and len(filtered) >= 2:
        _add(" ".join(filtered), "remove filler words", "remove common words")

    # Strategy 5: Suggest removing the last word iteratively
    if len(words) >= 3:
        for i in range(len(words) - 1, 1, -1):
            candidate = " ".join(words[:i])
            _add(candidate, "progressive truncation", "try a shorter query")

    return suggestions[:10]  # max 10 suggestions


def get_empty_result_diagnosis(
    query: str,
    has_api_key: bool = True,
    filter_new_release: bool = False,
    min_price: float = 7.0,
) -> Dict[str, Any]:
    """
    Diagnose why a search returned no results and provide actionable advice.

    Parameters
    ----------
    query : str
        The search query that returned no results.
    has_api_key : bool
        Whether a valid API key is configured.
    filter_new_release : bool
        Whether the new-release (last 30 days) filter was active.
    min_price : float
        The minimum price filter that was applied.

    Returns
    -------
    Dict[str, Any]
        {possible_causes: List[str], suggestions: List[Dict], advice: str}
    """
    causes: List[str] = []
    advice_parts: List[str] = []
    suggestions = suggest_broader_queries(query)

    # Cause 1: API key
    if not has_api_key:
        causes.append("No valid SerpApi key configured. The scraper cannot fetch Amazon data.")
        advice_parts.append("Add your SerpApi key in config.ini (get a free key at https://serpapi.com).")

    # Cause 2: New-release filter too restrictive
    if filter_new_release:
        causes.append("The 'New Release (Last 30 Days)' filter is active. Very few books meet this criterion for highly specific niches.")
        advice_parts.append("Turn off 'Auto-Filter (New Releases)' to see all products, not just last 30 days.")

    # Cause 3: Query too specific
    word_count = len(query.strip().split())
    if word_count >= 4:
        causes.append(f"The query has {word_count} words, which is very specific. Amazon may not have exact matches.")
        advice_parts.append("Try a broader search with fewer keywords.")

    # Cause 4: Page count too low
    causes.append("Amazon's algorithm may not index niche combinations deeply for very specific queries.")

    if suggestions:
        cause_text = "Try one of these broader search suggestions:"
        causes.append(cause_text)

    diagnosis = {
        "possible_causes": causes,
        "suggestions": suggestions,
        "query_words": word_count,
        "advice": " ".join(advice_parts) if advice_parts else "Try broadening your search query.",
    }

    return diagnosis
