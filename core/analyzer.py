"""
analyzer.py — Tier 2: Data Analysis & Smart Scoring Module

Part of the Amazon KDP Research Pipeline.
Consumes formatted output from scraper.py, applies scoring/filtering logic,
and returns ranked results for export (Tier 3).

Additive-only module: extend with new scoring functions, never rewrite existing.

Dependencies:
    pip install pandas  (optional — falls back to pure-Python sorting)

Author: KDP Automation Architect
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Path(__file__).parent / "analyzer.log", mode="a"),
    ],
)
logger = logging.getLogger("kdpanalyzer")

# ---------------------------------------------------------------------------
# Paths — aligned with scraper.py's PROJECT_ROOT convention
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
OUTPUT_DIR: Path = PROJECT_ROOT / "output"


# ---------------------------------------------------------------------------
# Loader: read formatted JSON files produced by scraper.py
# ---------------------------------------------------------------------------
def load_formatted_data(
    query: Optional[str] = None,
    file_path: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load formatted product data from disk.

    Parameters
    ----------
    query : str, optional
        Search query used in scraper (derives filename automatically).
    file_path : str, optional
        Direct path to a formatted JSON file (overrides *query*).

    Returns
    -------
    list[dict]
        List of product rows, or empty list if the file cannot be loaded.
    """
    try:
        # Determine file path
        if file_path:
            path = Path(file_path)
        elif query:
            safe_name: str = query.lower().replace(" ", "_")[:60]
            path = OUTPUT_DIR / f"formatted_{safe_name}.json"
        else:
            logger.error("Either 'query' or 'file_path' must be provided.")
            return []

        if not path.exists():
            logger.error("Formatted data file not found: %s", path)
            return []

        with open(path, "r", encoding="utf-8") as fh:
            data: List[Dict[str, Any]] = json.load(fh)

        logger.info("Loaded %d rows from %s", len(data), path)
        return data

    except json.JSONDecodeError as exc:
        logger.error("Invalid JSON in %s: %s", path, exc)
        return []
    except Exception as exc:
        logger.error("Failed to load formatted data: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Filter: remove low-margin products
# ---------------------------------------------------------------------------
def filter_low_price(
    rows: List[Dict[str, Any]],
    min_price: float = 5.00,
) -> List[Dict[str, Any]]:
    """
    Remove products whose Price is below *min_price*.

    Low-price books leave razor-thin margins after KDP printing costs.
    Parameters
    ----------
    rows : list[dict]
        Product rows to filter.
    min_price : float
        Minimum acceptable price (default: $5.00).

    Returns
    -------
    list[dict]
        Filtered rows.
    """
    filtered: List[Dict[str, Any]] = []
    removed_count: int = 0

    try:
        for row in rows:
            try:
                price = float(row.get("Price", 0))
                if price >= min_price:
                    filtered.append(row)
                else:
                    removed_count += 1
            except (ValueError, TypeError):
                # If price cannot be parsed, keep the row (consumer beware)
                filtered.append(row)

        if removed_count:
            logger.info(
                "Price filter (< $%.2f) removed %d / %d rows.",
                min_price,
                removed_count,
                len(rows),
            )
        return filtered

    except Exception as exc:
        logger.error("Price filter failed: %s", exc)
        return rows


# ---------------------------------------------------------------------------
# Scorer: compute opportunity score
# ---------------------------------------------------------------------------
def calculate_score(row: Dict[str, Any]) -> float:
    """
    Compute the Smart Score for a single product row.

    Formula:
        Score = ReviewCount / (BSR + 1)

    Rationale
    ---------
    - High ReviewCount signals strong demand / social proof.
    - Low BSR (Best-Sellers Rank) signals high sales velocity.
    - Dividing by (BSR + 1) avoids division-by-zero when BSR is 0 (placeholder).
    - A higher score means higher demand with less entrenched competition.

    Returns
    -------
    float
        The computed score (≥ 0).
    """
    try:
        reviews = int(row.get("ReviewCount", 0))
        bsr = int(row.get("BSR", 0))
        return reviews / (bsr + 1)
    except (ValueError, TypeError) as exc:
        logger.warning("Score calc failed for ASIN %s: %s", row.get("ASIN", "?"), exc)
        return 0.0


def score_and_sort(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Attach a 'SmartScore' field to each row, then sort descending by score.

    Parameters
    ----------
    rows : list[dict]
        Product rows (post-filter).

    Returns
    -------
    list[dict]
        Same rows with a 'SmartScore' key, sorted high → low.
    """
    try:
        for row in rows:
            try:
                row["SmartScore"] = round(calculate_score(row), 4)
            except Exception as exc:
                logger.warning("Could not score row %s: %s", row.get("ASIN", "?"), exc)
                row["SmartScore"] = 0.0

        # Sort descending
        ranked = sorted(rows, key=lambda r: r.get("SmartScore", 0), reverse=True)

        logger.info(
            "Scored and sorted %d rows. Top score: %.4f",
            len(ranked),
            ranked[0]["SmartScore"] if ranked else 0,
        )
        return ranked

    except Exception as exc:
        logger.error("Scoring pipeline failed: %s", exc)
        return rows


# ---------------------------------------------------------------------------
# Pandas variant — faster for large datasets
# ---------------------------------------------------------------------------
def score_and_sort_pandas(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Same as score_and_sort() but uses Pandas for vectorised computation.

    Falls back to the pure-Python version if Pandas is not installed.
    """
    if not HAS_PANDAS:
        logger.warning("Pandas not available — falling back to pure-Python scoring.")
        return score_and_sort(rows)

    try:
        df = pd.DataFrame(rows)

        # Fill missing numeric fields
        df["ReviewCount"] = pd.to_numeric(df.get("ReviewCount", 0), errors="coerce").fillna(0)
        df["BSR"] = pd.to_numeric(df.get("BSR", 0), errors="coerce").fillna(0)

        # Filter low-price
        df["Price"] = pd.to_numeric(df.get("Price", 0), errors="coerce").fillna(0)
        df = df[df["Price"] >= 5.00]

        # Score
        df["SmartScore"] = df["ReviewCount"] / (df["BSR"] + 1)

        # Sort
        df = df.sort_values("SmartScore", ascending=False).reset_index(drop=True)

        logger.info(
            "Pandas scored & sorted %d rows. Top score: %.4f",
            len(df),
            df.iloc[0]["SmartScore"] if not df.empty else 0,
        )
        return df.to_dict(orient="records")

    except Exception as exc:
        logger.error("Pandas scoring failed — falling back: %s", exc)
        return score_and_sort(rows)


# ---------------------------------------------------------------------------
# Saver: write ranked results back to disk
# ---------------------------------------------------------------------------
def save_ranked_results(
    rows: List[Dict[str, Any]],
    query: str,
) -> None:
    """
    Write the scored-and-sorted result set to the output directory.

    Produces two files:
        - ranked_{query}.json       (full rows with SmartScore)
        - ranked_{query}_summary.txt (human-readable top-20 table)
    """
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name: str = query.lower().replace(" ", "_")[:60]

        # Full JSON
        json_path = OUTPUT_DIR / f"ranked_{safe_name}.json"
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2, ensure_ascii=False)
        logger.info("Ranked results saved -> %s", json_path)

        # Text summary (top 20)
        txt_path = OUTPUT_DIR / f"ranked_{safe_name}_summary.txt"
        with open(txt_path, "w", encoding="utf-8") as fh:
            header = f"{'Rank':<6} {'ASIN':<15} {'Title':<55} {'Price':>8} {'Score':>10} {'★':>5} {'Reviews':>8}"
            fh.write("=" * len(header) + "\n")
            fh.write(f"KDP Research Pipeline — Ranked Results: {query}\n")
            fh.write("=" * len(header) + "\n")
            fh.write(header + "\n")
            fh.write("-" * len(header) + "\n")
            for i, r in enumerate(rows[:20], 1):
                title = r["Title"][:52] + ".." if len(r["Title"]) > 52 else r["Title"]
                fh.write(
                    f"{i:<6} {r.get('ASIN', '?'):<15} {title:<55} "
                    f"{r.get('Price', 0):>8.2f} {r.get('SmartScore', 0):>10.4f} "
                    f"{r.get('Rating', 0):>5.1f} {r.get('ReviewCount', 0):>8}\n"
            )
        logger.info("Summary table saved -> %s", txt_path)

    except Exception as exc:
        logger.error("Failed to save ranked results: %s", exc)


# ---------------------------------------------------------------------------
# Low-Competition Gems: identify underserved opportunities
# ---------------------------------------------------------------------------
def find_low_competition_gems(
    rows: List[Dict[str, Any]],
    bsr_threshold: int = 50000,
    review_threshold: int = 30,
) -> List[Dict[str, Any]]:
    """
    Identify **Low-Competition Gems** — products with solid demand but
    minimal entrenched competition.

    A product qualifies when both conditions are true:
        1. BSR < *bsr_threshold*     (low Best-Sellers Rank → high velocity)
        2. ReviewCount < *review_threshold*  (few reviews → open door)

    **Known limitation**: The current scraper sets BSR=0 for all items
    (product-detail scraping is a future Tier).  Until then, every item
    whose ReviewCount < threshold will match, which still surfaces the
    *underserved* factor of the equation.

    Parameters
    ----------
    rows : list[dict]
        Scored product rows (must include ``SmartScore``).
    bsr_threshold : int
        Maximum BSR to qualify (default: 50,000).
    review_threshold : int
        Maximum review count to qualify (default: 30).

    Returns
    -------
    list[dict]
        Qualifying rows, sorted by SmartScore descending.
    """
    gems: List[Dict[str, Any]] = []

    try:
        for row in rows:
            try:
                bsr = int(row.get("BSR", 0))
                reviews = int(row.get("ReviewCount", 0))
            except (ValueError, TypeError):
                continue

            if bsr < bsr_threshold and reviews < review_threshold:
                gems.append(row)

        gems.sort(key=lambda r: r.get("SmartScore", 0), reverse=True)

        logger.info(
            "Low-Competition Gems — %d / %d rows qualify "
            "(BSR < %d, Reviews < %d).",
            len(gems),
            len(rows),
            bsr_threshold,
            review_threshold,
        )
        return gems

    except Exception as exc:
        logger.error("Low-competition gem search failed: %s", exc)
        return []


def find_gems_dataframe(
    df: "pd.DataFrame",
    bsr_threshold: int = 50000,
    review_threshold: int = 30,
) -> "pd.DataFrame":
    """
    DataFrame-based gem finder for Batch mode analysis.

    Filters a scored DataFrame to rows where:
      - BSR < *bsr_threshold*
      - ReviewCount < *review_threshold*

    Parameters
    ----------
    df : pd.DataFrame
        Scored DataFrame (must contain 'BSR', 'ReviewCount', 'SmartScore').
    bsr_threshold : int
        Maximum BSR to qualify (default: 50,000).
    review_threshold : int
        Maximum review count to qualify (default: 30).

    Returns
    -------
    pd.DataFrame
        Filtered DataFrame, sorted by SmartScore descending.
    """
    if not HAS_PANDAS:
        logger.warning(
            "Pandas not available — cannot use DataFrame gem finder. "
            "Returning empty DataFrame."
        )
        import pandas as _empty_pd
        return _empty_pd.DataFrame()

    try:
        before = len(df)
        gems_df = df[
            (df["BSR"] < bsr_threshold) & (df["ReviewCount"] < review_threshold)
        ].copy()
        gems_df = gems_df.sort_values("SmartScore", ascending=False)
        logger.info(
            "find_gems_dataframe — %d / %d rows qualify "
            "(BSR < %d, Reviews < %d).",
            len(gems_df),
            before,
            bsr_threshold,
            review_threshold,
        )
        return gems_df

    except Exception as exc:
        logger.error("DataFrame gem finder failed: %s", exc)
        return df.head(0) if not df.empty else df


# ---------------------------------------------------------------------------
# Full pipeline: load -> filter -> score -> save
# ---------------------------------------------------------------------------
def run_analysis(
    query: str,
    min_price: float = 5.00,
    use_pandas: bool = True,
) -> List[Dict[str, Any]]:
    """
    Execute the full analysis pipeline for a given search query.

    Steps
    -----
    1. Load formatted data produced by scraper.py.
    2. Apply price filter (remove < $5.00).
    3. Compute SmartScore = ReviewCount / (BSR + 1).
    4. Sort descending by score.
    5. Save ranked results to disk.

    Parameters
    ----------
    query : str
        The same search query used by scraper.py.
    min_price : float
        Minimum price threshold (default: $5.00).
    use_pandas : bool
        Use Pandas for scoring if available (default: True).

    Returns
    -------
    list[dict]
        Ranked product rows with SmartScore attached.
    """
    logger.info("=" * 60)
    logger.info("KDP Research Pipeline — Tier 2: Analyze")
    logger.info("Query: %s", query)
    logger.info("=" * 60)

    # Step 1 — load
    raw_rows: List[Dict[str, Any]] = load_formatted_data(query=query)
    if not raw_rows:
        logger.error("No data to analyze for query '%s'. Run scraper.py first.", query)
        return []

    # Step 2 — filter
    filtered: List[Dict[str, Any]] = filter_low_price(raw_rows, min_price=min_price)

    # Step 3 — score & sort
    if use_pandas and HAS_PANDAS:
        ranked: List[Dict[str, Any]] = score_and_sort_pandas(filtered)
    else:
        ranked: List[Dict[str, Any]] = score_and_sort(filtered)

    # Step 4 — save
    save_ranked_results(ranked, query)

    return ranked


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Tier 2: Amazon KDP Data Analyzer")
    parser.add_argument("query", type=str, help="Search query matching a scraper output file")
    parser.add_argument("--min-price", type=float, default=5.00, help="Minimum price filter (default: $5.00)")
    parser.add_argument("--no-pandas", action="store_true", help="Force pure-Python scoring even if Pandas is installed")

    args = parser.parse_args()

    results = run_analysis(
        query=args.query,
        min_price=args.min_price,
        use_pandas=not args.no_pandas,
    )

    # Pretty-print top 10
    print("\n")
    print(f"{'Rank':<6} {'ASIN':<15} {'Title':<55} {'Price':>8} {'Score':>10} {'★':>5} {'Reviews':>8}")
    print("-" * 112)
    for i, r in enumerate(results[:10], 1):
        title = r["Title"][:52] + ".." if len(r["Title"]) > 52 else r["Title"]
        print(
            f"{i:<6} {r.get('ASIN', '?'):<15} {title:<55} "
            f"{r.get('Price', 0):>8.2f} {r.get('SmartScore', 0):>10.4f} "
            f"{r.get('Rating', 0):>5.1f} {r.get('ReviewCount', 0):>8}"
        )

    print(f"\nAnalyzed {len(results)} products.")
