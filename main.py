"""
main.py -- KDP Research Pipeline Orchestrator

Executes all 3 Tiers sequentially with error propagation:
    Tier 1 (scraper) -> Tier 2 (analyzer) -> Tier 3 (exporter)

If any stage fails, the pipeline halts immediately. On success, a
summary is printed with counts from each stage.

Usage:
    python main.py "low fodmap cookbook for kids" --sheet-id "abc123"
    python main.py "adhd planner for adults"          # skip export
    python main.py --help

Author: KDP Automation Architect
"""

import os
import sys
import time
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

# -- Import pipeline modules from core package -------------------------
# Each module runs its .env loader and logging config at import time.
try:
    from core import scraper
    from core import analyzer
    from core import exporter
except ImportError as exc:
    print(f"FATAL: Could not import a pipeline module -- {exc}")
    print("Ensure core/scraper.py, core/analyzer.py, core/exporter.py all exist.")
    sys.exit(1)

# -- Pipeline logger (sits above the module-specific loggers) ----------
logger = logging.getLogger("kdporchestrator")
_log_configured = False


def _setup_logging() -> None:
    """Configure root logging once; modules' basicConfig calls are no-ops after."""
    global _log_configured
    if _log_configured:
        return
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )
    _log_configured = True


# ======================================================================
# Pipeline Orchestrator
# ======================================================================

def run_pipeline(
    query: str,
    sheet_id: Optional[str] = None,
    credentials_path: Optional[str] = None,
    min_price: float = 5.00,
    use_pandas: bool = True,
    max_pages: int = 1,
    enrich_bsr: bool = False,
    max_enrich: int = 20,
    filter_params: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Execute the full KDP research pipeline: scrape -> analyze -> export.

    Parameters
    ----------
    query : str
        Amazon search keyword phrase.
    sheet_id : str, optional
        Google Sheet ID for Tier 3 export. If omitted, export is skipped.
    credentials_path : str, optional
        Path to Google service-account JSON (for Tier 3).
    min_price : float
        Minimum price filter passed to analyzer (default: $5.00).
    use_pandas : bool
        Use Pandas scoring in analyzer if available.
    max_pages : int
        Number of SerpApi result pages to fetch (1 = single page, 3+ = batch).

    Returns
    -------
    bool
        True if the pipeline reached its intended end; False if a stage failed.
    """
    _setup_logging()
    start_wall = time.time()

    # -- Stage 1: Scrape ------------------------------------------------
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE START -- Query: '%s'", query)
    logger.info("=" * 60)
    logger.info("")

    logger.info("-" * 60)
    logger.info("STAGE 1 / 3 -- Scraper (Tier 1)")
    logger.info("-" * 60)

    try:
        if max_pages > 1:
            logger.info("Batch mode enabled -- fetching up to %d pages.", max_pages)
            scraped_rows = scraper.fetch_all_pages(
                query=query,
                max_pages=max_pages,
                api_key=scraper.SERPAPI_KEY,
                domain=scraper.AMAZON_DOMAIN,
                filter_params=filter_params,
            )
            if scraped_rows:
                scraper.save_results(query, {"query": query, "max_pages": max_pages, "organic_results": [], "formatted_rows": scraped_rows}, scraped_rows)
        else:
            scraped_rows = scraper.search_and_format(
                query=query,
                api_key=scraper.SERPAPI_KEY,
                domain=scraper.AMAZON_DOMAIN,
                save=True,
            )
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user during scraping.")
        return False
    except Exception as exc:
        logger.critical("Scraper stage crashed -- %s", exc, exc_info=True)
        return False

    if not scraped_rows:
        logger.error(
            "Scraper returned 0 results for '%s'. "
            "Check the query or your SerpApi key/quota. Halting.",
            query,
        )
        return False

    n_scraped: int = len(scraped_rows)
    logger.info("Scraper stage complete -- %d products collected across %d page(s).", n_scraped, max_pages)

    # -- Stage 2: Analyze ------------------------------------------------
    logger.info("")
    logger.info("-" * 60)
    logger.info("STAGE 2 / 3 -- Analyzer (Tier 2)")
    logger.info("-" * 60)

    try:
        ranked_rows: List[Dict[str, Any]] = analyzer.run_analysis(
            query=query,
            min_price=min_price,
            use_pandas=use_pandas,
        )
    except KeyboardInterrupt:
        logger.warning("Pipeline interrupted by user during analysis.")
        return False
    except Exception as exc:
        logger.critical("Analyzer stage crashed -- %s", exc, exc_info=True)
        return False

    if not ranked_rows:
        logger.error(
            "Analyzer returned 0 opportunities for '%s'. "
            "Check the price filter or input data. Halting.",
            query,
        )
        return False

    n_opportunities: int = len(ranked_rows)
    logger.info("Analyzer stage complete -- %d opportunities scored.", n_opportunities)

    # -- BSR Enrichment (optional, costs credits) --------------------------
    if enrich_bsr:
        logger.info("")
        logger.info("-" * 60)
        logger.info("BSR ENRICHMENT -- fetching real BSR via Product API")
        logger.info("-" * 60)
        logger.info(
            "Enriching up to %d ASIN(s) — costs ~%d SerpApi credit(s).",
            max_enrich, max_enrich,
        )
        try:
            ranked_rows = scraper.batch_enrich_bsr(
                rows=ranked_rows,
                api_key=scraper.SERPAPI_KEY,
                max_asins=max_enrich,
                domain=scraper.AMAZON_DOMAIN,
                delay=1.0,
            )
            n_enriched = sum(1 for r in ranked_rows if r.get("BSR", 0) > 0)
            logger.info(
                "BSR enrichment complete — %d/%d rows have real BSR.",
                n_enriched, min(max_enrich, len(ranked_rows)),
            )
        except Exception as exc:
            logger.warning("BSR enrichment failed: %s", exc)

    # -- Low-Competition Gems analysis (DataFrame variant when pandas available) --
    gems: List[Dict[str, Any]] = []
    try:
        if analyzer.HAS_PANDAS:
            import pandas as _pd
            df = _pd.DataFrame(ranked_rows)
            gems_df = analyzer.find_gems_dataframe(df, bsr_threshold=50000, review_threshold=30)
            gems = gems_df.to_dict(orient="records") if not gems_df.empty else []
        else:
            gems = analyzer.find_low_competition_gems(
                ranked_rows, bsr_threshold=50000, review_threshold=30,
            )
    except Exception as exc:
        logger.warning("Gem analysis fell back to list-based: %s", exc)
        gems = analyzer.find_low_competition_gems(
            ranked_rows, bsr_threshold=50000, review_threshold=30,
        )

    n_gems: int = len(gems)
    logger.info(
        "Low-Competition Gems identified: %d (BSR < 50k, Reviews < 30).",
        n_gems,
    )

    # -- Stage 3: Export (optional) --------------------------------------
    export_ok: bool = False
    if sheet_id:
        logger.info("")
        logger.info("-" * 60)
        logger.info("STAGE 3 / 3 -- Exporter (Tier 3)")
        logger.info("-" * 60)

        try:
            export_ok = exporter.run_export(
                query=query,
                spreadsheet_id=sheet_id,
                sheet_name="KDP_Research",
                credentials_path=credentials_path,
            )
        except KeyboardInterrupt:
            logger.warning("Pipeline interrupted by user during export.")
            return False
        except Exception as exc:
            logger.critical("Exporter stage crashed -- %s", exc, exc_info=True)
            return False

        if not export_ok:
            logger.warning(
                "Export to Google Sheets failed or was skipped. "
                "Scraped and analyzed data is still on disk."
            )
    else:
        logger.info("")
        logger.info("-" * 60)
        logger.info("STAGE 3 / 3 -- Exporter (Tier 3)  SKIPPED (no --sheet-id)")
        logger.info("-" * 60)

    # -- Summary ---------------------------------------------------------
    elapsed = time.time() - start_wall
    logger.info("")
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info("  Query:          %s", query)
    logger.info("  Duration:       %.1f seconds", elapsed)
    logger.info("  Products found: %d", n_scraped)
    logger.info("  Opportunities:  %d", n_opportunities)
    logger.info("  Top ASIN:       %s", ranked_rows[0].get("ASIN", "?") if ranked_rows else "N/A")
    logger.info("  Top Score:      %.4f", ranked_rows[0].get("SmartScore", 0) if ranked_rows else 0)
    if sheet_id:
        logger.info("  Sheets export:  %s", "YES" if export_ok else "FAILED / SKIPPED")
    logger.info("")

    # -- Console-friendly short summary ---------------------------------
    sep = "+" + "-" * 58 + "+"
    print("")
    print(sep)
    print(f"|  KDP Research Pipeline -- Summary{' ' * 26} |")
    print(sep)
    print(f"|  Query:          {query:<42} |")
    print(f"|  Duration:       {elapsed:<6.1f}s{' ' * 37} |")
    print(f"|  Products found: {n_scraped:<4d}{' ' * 29} |")
    print(f"|  Opportunities:  {n_opportunities:<4d}{' ' * 29} |")
    print(f"|  Gems found:     {n_gems:<4d}{' ' * 29} |")
    if ranked_rows:
        top = ranked_rows[0]
        print(f"|  Top pick:       {str(top.get('Title', ''))[:42]:<42} |")
        print(f"|  Top ASIN:       {top.get('ASIN', '?'):<42} |")
        print(f"|  Top Score:      {top.get('SmartScore', 0):<10.4f}{' ' * 29} |")
    if sheet_id:
        status = "Uploaded [OK]" if export_ok else "Failed"
        print(f"|  Sheets export:  {status:<42} |")
    print(sep)
    print("")

    # -- Gold Mine Opportunities -----------------------------------------
    if gems:
        gold_sep = "+" + "=" * 58 + "+"
        print("")
        print(gold_sep)
        print(f"|  GOLD MINE -- Top 5 Low-Competition Opportunities{' ' * 11} |")
        print(gold_sep)
        print(f"|{'Rank':>5} {'ASIN':<14} {'Score':>9} {'Price':>7} {'Reviews':>8} {'Rating':>6} |")
        print(f"|{'-'*5} {'-'*14} {'-'*9} {'-'*7} {'-'*8} {'-'*6} |")
        for i, gem in enumerate(gems[:5], 1):
            asin = gem.get("ASIN", "?")[:12]
            score = gem.get("SmartScore", 0)
            price = gem.get("Price", 0)
            reviews = gem.get("ReviewCount", 0)
            rating = gem.get("Rating", 0)
            print(
                f"|{i:>5} {asin:<14} {score:>9.4f} {price:>7.2f} "
                f"{reviews:>8} {rating:>6.1f} |"
            )
        print(gold_sep)
        print("")
        for i, gem in enumerate(gems[:5], 1):
            title = str(gem.get("Title", ""))[:50]
            print(f"  #{i}: {title}  (ASIN: {gem.get('ASIN', '?')})")
        print("")

    return True


# ======================================================================
# CLI Entry Point
# ======================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="KDP Research Pipeline Orchestrator -- Scrape -> Analyze -> Export",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python main.py "low fodmap cookbook for kids"\n'
            '  python main.py "adhd planner for adults" --sheet-id "abc123..."\n'
            '  python main.py "keto cookbook" --sheet-id "abc123..." --no-pandas\n'
        ),
    )
    parser.add_argument(
        "query",
        type=str,
        help="Amazon search keyword phrase (e.g. 'low fodmap cookbook for kids')",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Number of SerpApi result pages to fetch (default: 3, use 5+ for 100+ results).",
    )
    parser.add_argument(
        "--sheet-id",
        type=str,
        default=os.getenv("GOOGLE_SHEET_ID", ""),
        help=(
            "Google Sheet ID for Tier 3 export. "
            "Also read from GOOGLE_SHEET_ID env var. "
            "Omit to skip the export stage."
        ),
    )
    parser.add_argument(
        "--creds",
        type=str,
        default=None,
        help="Path to Google service-account credentials JSON "
             "(default: project root / credentials.json)",
    )
    parser.add_argument(
        "--min-price",
        type=float,
        default=5.00,
        help="Minimum product price for analyzer filter (default: $5.00)",
    )
    parser.add_argument(
        "--no-pandas",
        action="store_true",
        help="Force pure-Python scoring (skip Pandas even if installed)",
    )
    parser.add_argument(
        "--enrich-bsr",
        action="store_true",
        help="Fetch real Best Sellers Rank via Product API (costs 1 credit per ASIN)",
    )
    parser.add_argument(
        "--max-enrich",
        type=int,
        default=20,
        help="Maximum ASINs to enrich with BSR (default: 20, costs 1 credit each)",
    )
    parser.add_argument(
        "--new-release",
        action="store_true",
        help="Only show products released in the last 30 days (Amazon New Release filter)",
    )

    args = parser.parse_args()

    # Build filter_params dict
    filter_params: Dict[str, str] = {}
    if args.new_release:
        filter_params["rh"] = "p_n_publication_date:1250226011"

    try:
        success = run_pipeline(
            query=args.query,
            sheet_id=args.sheet_id or None,
            credentials_path=args.creds,
            min_price=args.min_price,
            use_pandas=not args.no_pandas,
            max_pages=args.max_pages,
            enrich_bsr=args.enrich_bsr,
            max_enrich=args.max_enrich,
            filter_params=filter_params,
        )
    except KeyboardInterrupt:
        logger.warning("Pipeline terminated by user.")
        success = False

    sys.exit(0 if success else 1)
