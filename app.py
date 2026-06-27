"""
app.py -- Streamlit Dashboard for KDP Research Pipeline

Usage:
    streamlit run app.py

Author: KDP Automation Architect
"""

import os
import sys
import json
import time
import logging
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
from io import StringIO
from datetime import datetime

import pandas as _pd
import streamlit as st

# --- Page config (must be first Streamlit command) -------------------------
st.set_page_config(
    page_title="KDP Research Pipeline",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS for dark-minimalist aesthetic --------------------------------
st.markdown("""
<style>
    /* Main container */
    .main {
        background-color: #0e1117;
    }

    /* Status cards */
    .status-card {
        padding: 0.75rem 1rem;
        border-radius: 8px;
        margin: 0.25rem 0;
        font-size: 0.9rem;
        border-left: 4px solid;
    }
    .status-card.pending {
        background: #1a1d24;
        border-left-color: #555;
        color: #888;
    }
    .status-card.running {
        background: #1a2a3a;
        border-left-color: #2196F3;
        color: #90caf9;
    }
    .status-card.success {
        background: #1a2e1a;
        border-left-color: #4CAF50;
        color: #a5d6a7;
    }
    .status-card.failed {
        background: #2e1a1a;
        border-left-color: #f44336;
        color: #ef9a9a;
    }
    .status-card.skipped {
        background: #1a1d24;
        border-left-color: #777;
        color: #999;
    }

    /* Log area */
    .log-box {
        background: #0a0d14;
        border: 1px solid #2a2d35;
        border-radius: 8px;
        padding: 1rem;
        font-family: "Courier New", Courier, monospace;
        font-size: 0.8rem;
        line-height: 1.5;
        max-height: 360px;
        overflow-y: auto;
        color: #b0b8c8;
    }
    .log-box div {
        border-bottom: 1px solid #1a1d24;
        padding: 2px 0;
    }

    /* Sidebar tweaks */
    .sidebar-input label {
        font-size: 0.8rem;
        color: #888;
    }

    /* Table */
    .stDataFrame {
        font-size: 0.8rem;
    }

    /* Buttons */
    div.stButton > button:first-child {
        width: 100%;
        font-weight: 600;
    }

    /* Metric cards */
    .metric-box {
        background: #1a1d24;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #2a2d35;
    }
    .metric-box .value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #e0e0e0;
    }
    .metric-box .label {
        font-size: 0.75rem;
        color: #777;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Import pipeline modules from core package
# ---------------------------------------------------------------------------
try:
    from core import scraper, analyzer, exporter, database, config_manager
    MODULES_OK = True
except ImportError as exc:
    st.error(f"Pipeline modules could not be imported: {exc}")
    MODULES_OK = False

# ---------------------------------------------------------------------------
# Initialize the SQLite database on every launch
# ---------------------------------------------------------------------------
if MODULES_OK:
    database.init_db()


# ---------------------------------------------------------------------------
# Custom log handler — captures logging into session state
# ---------------------------------------------------------------------------
class SessionLogHandler(logging.Handler):
    """Append log records to a list in st.session_state."""

    def __init__(self, log_key: str = "log_messages"):
        super().__init__()
        self.log_key = log_key

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        if self.log_key in st.session_state:
            st.session_state[self.log_key].append(msg)


def setup_log_capture() -> None:
    """Attach a SessionLogHandler to pipeline loggers."""
    handler = SessionLogHandler("log_messages")
    handler.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(name)s | %(message)s", datefmt="%H:%M:%S")
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.addHandler(handler)

    for name in ("kdpscraper", "kdpanalyzer", "kdpexporter", "kdporchestrator"):
        logger = logging.getLogger(name)
        logger.addHandler(handler)

    # Suppress noisy library loggers
    logging.getLogger("google.auth").setLevel(logging.WARNING)
    logging.getLogger("gspread").setLevel(logging.WARNING)


# ---------------------------------------------------------------------------
# Pipeline runner — yields status updates
# ---------------------------------------------------------------------------
def run_pipeline_dashboard(
    query: str,
    max_pages: int = 3,
    min_price: float = 5.00,
    sheet_id: Optional[str] = None,
    use_pandas: bool = True,
    api_key: Optional[str] = None,
    filter_params: Optional[Dict[str, str]] = None,
    enrich_bsr: bool = False,
    max_enrich: int = 20,
) -> Dict[str, Any]:
    """
    Execute the 3-tier pipeline and return results as a dict.

    Shows live progress via st.progress() and st.status().
    """
    results: Dict[str, Any] = {
        "scraped_count": 0,
        "opportunity_count": 0,
        "gem_count": 0,
        "ranked_rows": [],
        "gems": [],
        "export_ok": False,
        "error": None,
    }

    progress_bar = st.progress(0, text="Pipeline starting...")
    status = st.status("Pipeline running...", expanded=True)

    # -- Stage 1: Scrape --------------------------------------------------
    st.session_state["stage1_status"] = "running"
    try:
        if max_pages > 1:
            stash_log(f"Batch mode: fetching {max_pages} pages ...")
            status.update(label=f"Scraping {max_pages} pages...")

            def page_progress(current: int, total: int) -> None:
                pct = int((current / total) * 55)
                progress_bar.progress(pct, text=f"Scraping page {current}/{total}...")

            scraped_rows = scraper.fetch_all_pages(
                query=query,
                max_pages=max_pages,
                api_key=api_key or scraper.SERPAPI_KEY,
                domain=scraper.AMAZON_DOMAIN,
                filter_params=filter_params,
                progress_callback=page_progress,
            )
            if scraped_rows:
                scraper.save_results(
                    query,
                    {"query": query, "max_pages": max_pages, "organic_results": [], "formatted_rows": scraped_rows},
                    scraped_rows,
                )
        else:
            stash_log("Single-page mode ...")
            scraped_rows = scraper.search_and_format(
                query=query,
                api_key=api_key or scraper.SERPAPI_KEY,
                domain=scraper.AMAZON_DOMAIN,
                save=True,
                filter_params=filter_params,
            )
    except Exception as exc:
        stash_log(f"SCRAPE FAILED: {exc}")
        st.session_state["stage1_status"] = "failed"
        results["error"] = str(exc)
        return results

    if not scraped_rows:
        stash_log("No products found. Halting.")
        st.session_state["stage1_status"] = "failed"
        results["error"] = "No products returned from scraper."
        return results

    results["scraped_count"] = len(scraped_rows)
    stash_log(f"Stage 1 complete — {len(scraped_rows)} products collected.")
    progress_bar.progress(60, text="Analyzing opportunities...")
    status.update(label="Analyzing opportunities...")
    st.session_state["stage1_status"] = "success"

    # -- Stage 2: Analyze (Visibility-Based Opportunity Scoring) ----------
    st.session_state["stage2_status"] = "running"
    try:
        import pandas as _pd_analyze
        df = _pd_analyze.DataFrame(scraped_rows)
        # Filter low-price before scoring
        df["Price"] = _pd_analyze.to_numeric(df.get("Price", 0), errors="coerce").fillna(0)
        df = df[df["Price"] >= min_price].copy()
        if df.empty:
            stash_log("No products after price filter. Halting.")
            st.session_state["stage2_status"] = "failed"
            results["error"] = "No products above minimum price."
            return results
        # Run the opportunity scoring engine
        processed_df = analyzer.find_gems_dataframe(df)
        ranked_rows = processed_df.to_dict(orient="records")
        # Compute low-competition gems from the scored results
        gems = [
            r for r in ranked_rows
            if r.get("ReviewCount", 999) < 30
        ]
    except Exception as exc:
        stash_log(f"ANALYSIS FAILED: {exc}")
        st.session_state["stage2_status"] = "failed"
        results["error"] = str(exc)
        return results

    results["opportunity_count"] = len(ranked_rows)
    results["ranked_rows"] = ranked_rows
    results["gems"] = gems
    results["gem_count"] = len(gems)
    stash_log(f"Stage 2 complete — {len(ranked_rows)} opportunities scored, {len(gems)} gems.")
    progress_bar.progress(80, text="Export stage...")
    status.update(label="Analysis complete.")
    st.session_state["stage2_status"] = "success"

    # -- BSR Enrichment (optional, costs credits) ---------------------------
    if enrich_bsr:
        st.session_state["stage_bsr_status"] = "running"
        stash_log(
            f"BSR enrichment: fetching real BSR for up to {max_enrich} ASIN(s) "
            f"(~{max_enrich} SerpApi credits)..."
        )
        try:
            ranked_rows = scraper.batch_enrich_bsr(
                rows=ranked_rows,
                api_key=api_key or scraper.SERPAPI_KEY,
                max_asins=max_enrich,
                domain=scraper.AMAZON_DOMAIN,
                delay=1.0,
            )
            results["ranked_rows"] = ranked_rows
            stash_log("BSR enrichment complete.")
            st.session_state["stage_bsr_status"] = "success"
        except Exception as exc:
            stash_log(f"BSR enrichment failed: {exc}")
            st.session_state["stage_bsr_status"] = "failed"

    # -- Stage 3: Export (optional) ----------------------------------------
    st.session_state["stage3_status"] = "running"
    if sheet_id:
        stash_log(f"Exporting {len(ranked_rows)} rows to Sheets ...")
        status.update(label="Exporting to Google Sheets...")
        try:
            export_ok = exporter.run_export(
                query=query,
                spreadsheet_id=sheet_id,
                sheet_name="KDP_Research",
            )
            results["export_ok"] = export_ok
            if export_ok:
                stash_log("Export to Google Sheets complete.")
                st.session_state["stage3_status"] = "success"
            else:
                stash_log("Export failed (see logs).")
                st.session_state["stage3_status"] = "failed"
        except Exception as exc:
            stash_log(f"EXPORT FAILED: {exc}")
            st.session_state["stage3_status"] = "failed"
    else:
        stash_log("Export skipped (no Sheet ID).")
        st.session_state["stage3_status"] = "skipped"

    progress_bar.progress(100, text="Pipeline complete!")
    status.update(label="Pipeline complete.", state="complete" if not results["error"] else "error")
    return results


def stash_log(msg: str) -> None:
    """Append a message to the live-log buffer in session state."""
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state["log_messages"].append(f"[{ts}] {msg}")


# ---------------------------------------------------------------------------
# Deep Niche Tunneling — orchestrator
# ---------------------------------------------------------------------------
def run_deep_tunnel_dashboard(
    niche_query: str,
    api_key: str,
    max_pages: int = 3,
) -> Dict[str, Any]:
    """
    Execute a Deep Tunnel search: filtered (last 30 days) + unfiltered,
    score results, compute density, return structured dict.

    Shows live progress via st.status().
    """
    result: Dict[str, Any] = {
        "niche_query": niche_query,
        "filtered_count": 0,
        "unfiltered_count": 0,
        "density_label": "Insufficient Data",
        "is_golden": False,
        "filtered_rows": [],
        "unfiltered_rows": [],
        "gems": [],
        "error": None,
    }

    status = st.status(f"Tunneling Niche: {niche_query}...", expanded=True)
    progress = st.progress(0, text="Starting deep tunnel...")

    try:
        # Step 1: Fetch filtered (last 30 days)
        status.update(label=f"Fetching filtered results for '{niche_query}'...")
        progress.progress(20, text="Fetching filtered (last 30 days)...")
        stash_log(f"Deep tunnel: fetching filtered results for '{niche_query}'...")
        filtered_rows = scraper.deep_tunnel_niche(
            query=niche_query,
            api_key=api_key,
            filter_type='new_30_days',
            max_pages=max_pages,
        )
        result["filtered_count"] = len(filtered_rows)
        stash_log(f"Deep tunnel: {len(filtered_rows)} filtered products.")

        # Step 2: Score filtered results
        progress.progress(45, text="Scoring filtered results...")
        status.update(label="Scoring filtered opportunities...")
        if filtered_rows:
            import pandas as _pd_tunnel
            df_filtered = _pd_tunnel.DataFrame(filtered_rows)
            df_filtered["Price"] = _pd_tunnel.to_numeric(df_filtered.get("Price", 0), errors="coerce").fillna(0)
            scored = analyzer.find_gems_dataframe(df_filtered)
            result["filtered_rows"] = scored.to_dict(orient="records")
            result["gems"] = [r for r in result["filtered_rows"] if r.get("ReviewCount", 999) < 30]

        # Step 3: Fetch unfiltered (same query, no date filter)
        progress.progress(65, text="Fetching unfiltered results...")
        status.update(label="Fetching unfiltered market data...")
        stash_log("Deep tunnel: fetching unfiltered results...")
        unfiltered_rows = scraper.deep_tunnel_niche(
            query=niche_query,
            api_key=api_key,
            filter_type='none',
            max_pages=max_pages,
        )
        result["unfiltered_count"] = len(unfiltered_rows)
        stash_log(f"Deep tunnel: {len(unfiltered_rows)} unfiltered products.")

        # Step 4: Compute competition density
        progress.progress(85, text="Computing competition density...")
        status.update(label="Analyzing competition density...")
        density = analyzer.calculate_competition_score(
            total_results=result["unfiltered_count"],
            filtered_results=result["filtered_count"],
        )
        result["density_label"] = density
        result["is_golden"] = "Low Density" in density

        # Step 5: Save to DB
        data_str = json.dumps({
            "filtered_rows": result["filtered_rows"],
            "unfiltered_rows": result["unfiltered_rows"],
            "filtered_count": result["filtered_count"],
            "unfiltered_count": result["unfiltered_count"],
            "density_label": density,
            "is_golden": result["is_golden"],
        })
        database.save_tunnel_result(niche_query, data_str)

        progress.progress(100, text="Deep tunnel complete!")
        status.update(label=f"Tunnel complete — {density}", state="complete")
        stash_log(f"Deep tunnel complete for '{niche_query}' — {density}.")
    except Exception as exc:
        result["error"] = str(exc)
        status.update(label=f"Tunnel failed: {exc}", state="error")
        stash_log(f"Deep tunnel FAILED: {exc}")

    return result


# ---------------------------------------------------------------------------
# Sidebar inputs
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### :mag: KDP Research Pipeline")
    st.markdown("---")

    # Resolve default query: discovery override > session default > literal default
    _default_query = "coloring books for adults"
    if "search_override" in st.session_state and st.session_state["search_override"]:
        _default_query = st.session_state["search_override"]
        st.session_state["search_override"] = ""  # consume once
    query = st.text_input(
        "Search Query",
        value=_default_query,
        placeholder="e.g. low fodmap cookbook for kids",
        help="Amazon search keyword phrase",
    )

    max_pages = st.number_input(
        "Max Pages",
        min_value=1,
        max_value=20,
        value=3,
        help="Number of SerpApi result pages to fetch (3-5 for deep research)",
    )

    min_price = st.number_input(
        "Min Price ($)",
        min_value=0.0,
        max_value=100.0,
        value=7.00,
        step=0.50,
        help="Filter out products below this price",
    )

    sheet_id = st.text_input(
        "Sheet ID (optional)",
        placeholder="1abc... (leave blank to skip export)",
        help="Google Sheet ID for Tier 3 export",
    )

    st.markdown("---")
    dev_mode = st.checkbox(
        "Developer Mode",
        value=config_manager.get_dev_mode() if MODULES_OK else False,
        help="Show pipeline logs, status cards, and debug info",
    )
    if MODULES_OK:
        config_manager.set_dev_mode(dev_mode)

    st.markdown("---")
    st.markdown("### Filters")

    auto_filter = st.checkbox(
        "Auto-Filter (New Releases)",
        value=st.session_state.get("auto_filter", False),
        help="When enabled, appends 'last 30 days' filter to ALL searches automatically",
    )
    st.session_state["auto_filter"] = auto_filter
    if auto_filter:
        st.markdown(
            "<div style='font-size:0.78rem;color:#4CAF50;margin-bottom:4px;'>"
            ":white_check_mark: Auto-Filter active — only last-30-days results shown</div>",
            unsafe_allow_html=True,
        )

    new_release = st.checkbox(
        "New Release Mode (Last 30 Days)",
        value=st.session_state.get("new_release", False) or auto_filter,
        help="Adds p_n_publication_date:1250226011 refinement to the search",
    )
    st.session_state["new_release"] = new_release

    if new_release:
        st.markdown(
            "<div style='font-size:0.78rem;color:#4CAF50;margin-bottom:4px;'>"
            ":white_check_mark: Filter active — showing only last 30 days</div>",
            unsafe_allow_html=True,
        )

    # Build filter_params dict from toggles
    filter_params = {}
    if new_release:
        filter_params["rh"] = "p_n_publication_date:1250226011"

    st.markdown("### BSR Enrichment")
    enrich_bsr = st.checkbox(
        "Enrich with BSR (costs credits)",
        value=st.session_state.get("enrich_bsr", False),
        help="Fetch real Best Sellers Rank via Product API (1 credit per ASIN). "
             "Enable only for focused analysis.",
    )
    st.session_state["enrich_bsr"] = enrich_bsr
    if enrich_bsr:
        max_enrich = st.number_input(
            "Max ASINs to enrich",
            min_value=1,
            max_value=100,
            value=20,
            help="Limits credit consumption. 20 ASINs = 20 SerpApi credits.",
        )
        st.session_state["max_enrich"] = max_enrich
        st.markdown(
            "<div style='font-size:0.78rem;color:#FF9800;margin-bottom:4px;'>"
            ":warning: Uses 1 credit per ASIN</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    key_status = "configured" if config_manager.get_serpapi_key() != "YOUR_SERPAPI_KEY_HERE" else "MISSING"
    st.markdown(
        f"<div style='font-size:0.75rem;color:#666;'>"
        f"SerpApi key: {key_status}"
        f"</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
tab_names = ["📊 Data Table", "🖼️ Visual Gallery", ":gear: Settings", ":clock3: History"]
tabs = st.tabs(tab_names)

# -- Session state initialisation --------------------------------------------
if "log_messages" not in st.session_state:
    st.session_state["log_messages"] = []
if "stage1_status" not in st.session_state:
    st.session_state["stage1_status"] = "pending"
if "stage2_status" not in st.session_state:
    st.session_state["stage2_status"] = "pending"
if "stage3_status" not in st.session_state:
    st.session_state["stage3_status"] = "pending"
if "stage_bsr_status" not in st.session_state:
    st.session_state["stage_bsr_status"] = "pending"
if "pipeline_results" not in st.session_state:
    st.session_state["pipeline_results"] = None
if "pipeline_running" not in st.session_state:
    st.session_state["pipeline_running"] = False
if "tunnel_results" not in st.session_state:
    st.session_state["tunnel_results"] = None
if "tunnel_niche_name" not in st.session_state:
    st.session_state["tunnel_niche_name"] = ""
if "tunnel_running" not in st.session_state:
    st.session_state["tunnel_running"] = False
if "tunnel_density" not in st.session_state:
    st.session_state["tunnel_density"] = None


# ---------------------------------------------------------------------------
# Results display helper
# ---------------------------------------------------------------------------
def _display_results(results: Optional[Dict[str, Any]], query: str, sheet_id: str, dev_mode: bool) -> None:
    """Render pipeline results: metric cards, gold-mine table, all-ranked table."""
    if not results or results.get("error") or results.get("scraped_count", 0) == 0:
        if results and results.get("error"):
            st.error(f"Pipeline halted: {results['error']}")
        elif not results:
            st.info("Enter a search query and click **Run Pipeline** to begin.")
        return

    # -- Prepare DataFrames ------------------------------------------------
    ranked_rows = results.get("ranked_rows", [])
    all_df = _pd.DataFrame(ranked_rows) if ranked_rows else _pd.DataFrame()

    # Metric cards
    st.markdown("### Results Overview")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        st.markdown(
            f"<div class='metric-box'><div class='value'>{results['scraped_count']}</div><div class='label'>Products Found</div></div>",
            unsafe_allow_html=True,
        )
    with metric_cols[1]:
        st.markdown(
            f"<div class='metric-box'><div class='value'>{results['opportunity_count']}</div><div class='label'>Opportunities</div></div>",
            unsafe_allow_html=True,
        )
    with metric_cols[2]:
        st.markdown(
            f"<div class='metric-box'><div class='value'>{results['gem_count']}</div><div class='label'>Gold Gems</div></div>",
            unsafe_allow_html=True,
        )
    with metric_cols[3]:
        status_icon = ":check:" if results.get("export_ok") else ":fast_forward:"
        export_label = "Exported" if results.get("export_ok") else ("Skipped" if not sheet_id else "Failed")
        st.markdown(
            f"<div class='metric-box'><div class='value'>{status_icon}</div><div class='label'>Export {export_label}</div></div>",
            unsafe_allow_html=True,
        )

    # -- Niche Insights (Top Themes by EOS) ---------------------------------
    if not all_df.empty and "Theme" in all_df.columns and "EOS" in all_df.columns:
        st.markdown("### :bulb: Niche Insights — Top Themes by EOS")
        insights_df = analyzer.get_niche_insights(all_df)
        top3 = insights_df.head(3)
        insight_cols = st.columns(len(top3))
        for col, (theme, row) in zip(insight_cols, top3.iterrows()):
            col.markdown(
                f"<div class='metric-box'>"
                f"<div class='value'>{theme}</div>"
                f"<div class='label'>{int(row['Product_Count'])} products &middot; Avg EOS {row['EOS']:.1f}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # Gold-Mine Table
    if results.get("gems"):
        st.markdown("### :gem: Gold-Mine Opportunities (Ranked by EOS)")
        gems_df = _pd.DataFrame(results["gems"]).copy()
        gems_df["ASIN Link"] = gems_df["ASIN"].apply(
            lambda x: f"https://www.amazon.com/dp/{x}" if x else ""
        )
        display_cols = ["ASIN Link", "Title", "Price", "Visibility_Score", "EOS", "Theme"]
        available = [c for c in display_cols if c in gems_df.columns]
        st.dataframe(
            gems_df[available].head(20),
            use_container_width=True,
            hide_index=True,
            column_config={
                "ASIN Link": st.column_config.LinkColumn("ASIN", display_text=r"https://www.amazon.com/dp/(.*)"),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Visibility_Score": st.column_config.NumberColumn("Vis. Score", format="%.0f"),
                "EOS": st.column_config.NumberColumn("EOS", format="%.1f"),
                "Theme": st.column_config.TextColumn("Theme"),
            },
        )

    # Full Ranked Table
    if results.get("ranked_rows"):
        st.markdown("### All Ranked Products")
        if "Visibility_Score" in all_df.columns:
            all_df["Vis."] = all_df["Visibility_Score"].apply(lambda x: f"{x:.0f}")
        all_cols = ["ASIN Link", "Title", "Price", "Visibility_Score", "EOS", "Theme", "ReviewCount", "Rating"]
        if "SmartScore" in all_df.columns:
            all_cols.append("SmartScore")
        all_avail = [c for c in all_cols if c in all_df.columns]
        with st.expander("Show full ranked table"):
            all_df["ASIN Link"] = all_df["ASIN"].apply(
                lambda x: f"https://www.amazon.com/dp/{x}" if x else ""
            )
            st.dataframe(
                all_df[all_avail],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ASIN Link": st.column_config.LinkColumn("ASIN", display_text=r"https://www.amazon.com/dp/(.*)"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Visibility_Score": st.column_config.NumberColumn("Vis. Score", format="%.0f"),
                    "EOS": st.column_config.NumberColumn("EOS", format="%.1f"),
                    "Theme": st.column_config.TextColumn("Theme"),
                    "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
                    "ReviewCount": st.column_config.NumberColumn("Reviews", format="%d"),
                    "SmartScore": st.column_config.NumberColumn("SmartScore", format="%.4f"),
                },
            )

        json_bytes = json.dumps(ranked_rows, indent=2, ensure_ascii=False).encode("utf-8")
        safe_name = query.lower().replace(" ", "_")[:60]
        st.download_button(
            label="Download Ranked JSON",
            data=json_bytes,
            file_name=f"ranked_{safe_name}.json",
            mime="application/json",
            use_container_width=False,
        )


# ---------------------------------------------------------------------------
# Gallery display helper
# ---------------------------------------------------------------------------
def _display_gallery(
    results: Optional[Dict[str, Any]],
    tunnel_results: Optional[Dict[str, Any]] = None,
) -> None:
    """Render pipeline results as a visual card gallery with thumbnails.

    Falls back to tunnel results if pipeline results are not available.
    """
    rows: List[Dict[str, Any]] = []

    if results and not results.get("error") and results.get("ranked_rows"):
        rows = results["ranked_rows"]
    elif tunnel_results and not tunnel_results.get("error") and tunnel_results.get("filtered_rows"):
        rows = tunnel_results["filtered_rows"]

    if not rows:
        if results and results.get("error"):
            st.error(f"Pipeline halted: {results['error']}")
        elif tunnel_results and tunnel_results.get("error"):
            st.error(f"Deep tunnel failed: {tunnel_results['error']}")
        else:
            st.info("Run a pipeline or deep tunnel from the **Data Table** tab first to see products here.")
        return

    st.markdown(f"### :art: Product Gallery — {len(rows)} products")

    cols = st.columns(4)
    for i, product in enumerate(rows):
        with cols[i % 4]:
            # Thumbnail with fallback
            thumb = product.get("thumbnail", "")
            if thumb:
                st.image(thumb, use_container_width=True)
            else:
                st.markdown(
                    "<div style='background:#1a1d24;border-radius:8px;"
                    "height:160px;display:flex;align-items:center;"
                    "justify-content:center;color:#555;font-size:0.85rem;'>"
                    "No Image Available</div>",
                    unsafe_allow_html=True,
                )

            # Title (shortened)
            title = str(product.get("Title", ""))[:50]
            if len(str(product.get("Title", ""))) > 50:
                title += "…"
            st.markdown(
                f"<div style='font-weight:600;font-size:0.85rem;"
                f"margin:4px 0;line-height:1.3;'>{title}</div>",
                unsafe_allow_html=True,
            )

            # Metadata block
            price = product.get("Price", 0)
            eos = product.get("EOS", 0)
            pub = product.get("PublicationDate", "—")
            bsr = product.get("BSR", 0)
            meta = f"💰 **${float(price):.2f}**" if price else ""
            if eos:
                meta += f" &nbsp;🚀 **{float(eos):.1f}**"
            if pub and pub != "N/A" and pub != "—":
                meta += f" &nbsp;📅 {pub}"
            if bsr:
                meta += f" &nbsp;📈 {int(bsr):,}"
            if meta:
                st.markdown(
                    f"<div style='font-size:0.78rem;color:#aaa;"
                    f"margin:2px 0 6px 0;'>{meta}</div>",
                    unsafe_allow_html=True,
                )

            # Action button
            asin = product.get("ASIN", "")
            if asin and asin != "N/A":
                url = f"https://www.amazon.com/dp/{asin}"
                st.markdown(
                    f"<a href='{url}' target='_blank' "
                    f"style='display:inline-block;background:#2196F3;color:#fff;"
                    f"padding:4px 12px;border-radius:4px;text-decoration:none;"
                    f"font-size:0.78rem;text-align:center;'>View on Amazon</a>",
                    unsafe_allow_html=True,
                )

            # Spacer between cards
            st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)


# =========================================================================
# TAB 0: Data Table
# =========================================================================
tab_dash = tabs[0]

with tab_dash:
    st.markdown("# :rocket: KDP Research Pipeline")
    st.markdown(
        "<div style='color:#777;margin-top:-12px;margin-bottom:20px;'>"
        "Amazon niche validation — scrape / score / export"
        "</div>",
        unsafe_allow_html=True,
    )

    # -- Status cards (visible only in Developer Mode) -------------------------
    if dev_mode:
        st.markdown("### Pipeline Status")
        status_cols = st.columns(3)
        status_labels = [
            ("Tier 1: Scraper", "stage1_status"),
            ("Tier 2: Analyzer", "stage2_status"),
            ("Tier 3: Export", "stage3_status"),
        ]
        for col, (label, key) in zip(status_cols, status_labels):
            status = st.session_state[key]
            emoji = {"pending": " :clock1030:", "running": " :gear:", "success": " :check:", "failed": " :x:", "skipped": " :fast_forward:"}.get(status, "")
            col.markdown(
                f"<div class='status-card {status}'>{emoji} {label}</div>",
                unsafe_allow_html=True,
            )

    # -- Action row ------------------------------------------------------------
    action_cols = st.columns([2, 1, 1])
    run_disabled = st.session_state["pipeline_running"] or not MODULES_OK

    with action_cols[0]:
        run_clicked = st.button(
            "Run Pipeline",
            type="primary",
            disabled=run_disabled,
            use_container_width=True,
        )

    with action_cols[1]:
        if st.button("Clear Log", use_container_width=True):
            st.session_state["log_messages"] = []

    with action_cols[2]:
        if st.button("Reset Status", use_container_width=True):
            for k in ("stage1_status", "stage2_status", "stage3_status"):
                st.session_state[k] = "pending"
            st.session_state["pipeline_results"] = None

    # -- Live log (visible only in Developer Mode) ----------------------------
    if dev_mode:
        st.markdown("### Live Log")
        log_container = st.container()
        log_html = "<div class='log-box'>"
        for line in st.session_state["log_messages"][-40:]:
            log_html += f"<div>{line}</div>"
        log_html += "</div>"
        log_container.markdown(log_html, unsafe_allow_html=True)

    # -- Pipeline execution ---------------------------------------------------
    if MODULES_OK and run_clicked and not st.session_state["pipeline_running"]:
        st.session_state["pipeline_running"] = True
        st.session_state["log_messages"] = []
        st.session_state["stage1_status"] = "pending"
        st.session_state["stage2_status"] = "pending"
        st.session_state["stage3_status"] = "pending"
        st.session_state["pipeline_results"] = None

        api_key = config_manager.get_serpapi_key()
        sheet_id_val = config_manager.get_sheet_id() or sheet_id

        setup_log_capture()

        stash_log(f"Pipeline starting -- query: '{query}', pages: {max_pages}, min price: ${min_price:.2f}")

        start_t = time.time()
        results = run_pipeline_dashboard(
            query=query,
            max_pages=max_pages,
            min_price=min_price,
            sheet_id=sheet_id_val or None,
            use_pandas=True,
            api_key=api_key,
            filter_params=filter_params,
            enrich_bsr=st.session_state.get("enrich_bsr", False),
            max_enrich=st.session_state.get("max_enrich", 20),
        )
        elapsed = time.time() - start_t

        # Save to search history
        if not results.get("error"):
            database.save_search(
                query=query,
                max_pages=max_pages,
                min_price=min_price,
                sheet_id=sheet_id_val,
                results=results,
            )

        st.session_state["pipeline_results"] = results
        st.session_state["pipeline_running"] = False

        if results["error"]:
            stash_log(f"Pipeline FAILED after {elapsed:.1f}s -- {results['error']}")
        else:
            stash_log(f"Pipeline complete in {elapsed:.1f}s.")
        st.rerun()

    # -- Results display -------------------------------------------------------
    _display_results(st.session_state.get("pipeline_results"), query, sheet_id, dev_mode)

    # -- Discovery: Smart Niche Chain -------------------------------------------
    pipeline_data = st.session_state.get("pipeline_results")
    if pipeline_data and not pipeline_data.get("error") and pipeline_data.get("ranked_rows"):
        st.markdown("---")
        st.markdown("### :dna: Smart Niche Discovery")
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
            "Extract categories and co-purchased products from your top results "
            "to find related micro-niches.</div>",
            unsafe_allow_html=True,
        )

        # Clear old discovery when new pipeline runs
        if "last_discovery_query" not in st.session_state:
            st.session_state["last_discovery_query"] = ""
        if "discovery_results" not in st.session_state:
            st.session_state["discovery_results"] = []
        if "discovery_running" not in st.session_state:
            st.session_state["discovery_running"] = False

        disc_cols = st.columns([2, 1])
        with disc_cols[0]:
            discovered_already = st.session_state["discovery_results"] and st.session_state["last_discovery_query"] == query
            disc_label = "Re-discover" if discovered_already else "Discover More"
            disc_disabled = st.session_state["discovery_running"] or not MODULES_OK
            if st.button(disc_label, type="primary", disabled=disc_disabled, use_container_width=True):
                st.session_state["discovery_running"] = True
                st.session_state["discovery_results"] = []
                st.session_state["last_discovery_query"] = query
                st.rerun()

        with disc_cols[1]:
            if st.button("View Discovery Queue", use_container_width=True):
                st.switch_page("app.py")  # will re-run; user can check History tab
                st.session_state["show_queue_inline"] = True
                st.rerun()

        # Run discovery if triggered
        if st.session_state["discovery_running"] and st.session_state["last_discovery_query"] == query:
            stash_log(f"Discovery: extracting niche terms from top products...")
            ranked = pipeline_data.get("ranked_rows", [])
            top_asins = [r.get("ASIN", "") for r in ranked[:5] if r.get("ASIN")]
            api_key = config_manager.get_serpapi_key()

            if not top_asins:
                stash_log("Discovery: no ASINs available.")
                st.session_state["discovery_running"] = False
            elif api_key == "YOUR_SERPAPI_KEY_HERE":
                stash_log("Discovery: no SerpApi key configured.")
                st.warning("Configure a SerpApi key in Settings to use discovery.")
                st.session_state["discovery_running"] = False
            else:
                stash_log(f"Discovery: fetching product details for {len(top_asins)} ASIN(s)...")
                terms = scraper.extract_discovery_terms(
                    query=query,
                    top_asins=top_asins,
                    api_key=api_key,
                    max_asins=3,
                )
                if terms:
                    database.save_discovery_terms(origin_query=query, terms=terms)
                    stash_log(f"Discovery: found {len(terms)} niche suggestions.")
                else:
                    stash_log("Discovery: no new niche terms found.")
                st.session_state["discovery_results"] = terms
                st.session_state["discovery_running"] = False
                st.rerun()

        # Display discovery results
        if st.session_state["discovery_results"] and st.session_state["last_discovery_query"] == query:
            terms = st.session_state["discovery_results"]
            if not terms:
                st.info("No related niches discovered. Try a broader search query.")
            else:
                # Source badges
                source_colors = {
                    "category": ("#4CAF50", "Category"),
                    "bought_together": ("#2196F3", "Bought Together"),
                    "also_bought": ("#FF9800", "Also Bought"),
                }
                st.markdown(f"**{len(terms)} niche suggestions found**")

                for i, t in enumerate(terms[:12]):
                    term = t.get("term", "")
                    source = t.get("source", "auto")
                    score = t.get("score", 0)
                    bg, label = source_colors.get(source, ("#777", source))
                    col1, col2, col3 = st.columns([6, 2, 2])
                    with col1:
                        score_bar = "|" * (score // 10)
                        st.markdown(
                            f"<div style='display:flex;align-items:center;gap:8px;'>"
                            f"<span style='background:{bg};color:#fff;font-size:0.7rem;"
                            f"padding:2px 6px;border-radius:4px;white-space:nowrap;'>{label}</span>"
                            f"<span style='color:#e0e0e0;'>{term}</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    with col2:
                        st.markdown(
                            f"<div style='text-align:center;color:#888;font-size:0.8rem;'>{score}/100</div>",
                            unsafe_allow_html=True,
                        )
                    with col3:
                        safe_term = term.replace("'", "").replace('"', "")
                        btn_key = f"search_disc_{i}_{hash(term) % 10000}"
                        if st.button("Search This", key=btn_key, use_container_width=True):
                            stash_log(f"Discovery: launching search for '{term}'")
                            # Set query in URL params for next run
                            st.query_params["q"] = term
                            st.session_state["search_override"] = term
                            st.rerun()

        # Handle search_override from discovery
        if "search_override" in st.session_state and st.session_state["search_override"]:
            # The rerun will pick this up in the sidebar query input
            pass

    # -- Deep Niche Tunneling ---------------------------------------------------
    st.markdown("---")
    st.markdown("### :tent: Deep Niche Tunneling")
    st.markdown(
        "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
        "Extract a niche from any product, auto-filter by last-30-days, "
        "score with EOS, and measure competition density.</div>",
        unsafe_allow_html=True,
    )

    tunnel_cols = st.columns([3, 1, 1])
    with tunnel_cols[0]:
        tunnel_query = st.text_input(
            "Niche to tunnel (or leave blank to pick from results)",
            placeholder="e.g. low fodmap cookbook for kids",
            label_visibility="collapsed",
        )
    with tunnel_cols[1]:
        tunnel_pages = st.number_input("Pages", min_value=1, max_value=10, value=3, label_visibility="collapsed")
    with tunnel_cols[2]:
        tunnel_disabled = st.session_state["tunnel_running"] or not MODULES_OK
        if st.button("Deep Tunnel :rocket:", type="primary", disabled=tunnel_disabled, use_container_width=True):
            target = tunnel_query.strip() or query.strip()
            if not target:
                st.warning("Enter a niche query first.")
            else:
                st.session_state["tunnel_running"] = True
                st.session_state["tunnel_results"] = None
                st.session_state["tunnel_niche_name"] = target
                st.session_state["tunnel_density"] = None
                st.rerun()

    # Execute tunnel if triggered
    if st.session_state["tunnel_running"] and st.session_state["tunnel_niche_name"]:
        api_key = config_manager.get_serpapi_key()
        if api_key == "YOUR_SERPAPI_KEY_HERE":
            st.error("Configure a SerpApi key in Settings to use Deep Tunneling.")
            st.session_state["tunnel_running"] = False
        else:
            stash_log(f"Deep tunnel: starting for '{st.session_state['tunnel_niche_name']}'...")
            tunnel_result = run_deep_tunnel_dashboard(
                niche_query=st.session_state["tunnel_niche_name"],
                api_key=api_key,
                max_pages=int(tunnel_pages),
            )
            st.session_state["tunnel_results"] = tunnel_result
            st.session_state["tunnel_running"] = False
            st.rerun()

    # Display tunnel results
    tunnel_data = st.session_state.get("tunnel_results")
    if tunnel_data and not tunnel_data.get("error"):
        # -- Density Score card ------------------------------------------------
        density = tunnel_data["density_label"]
        is_golden = tunnel_data.get("is_golden", False)
        if "Low Density" in density:
            density_color = "#4CAF50"
            density_icon = ":large_green_circle:"
        elif "Moderate" in density:
            density_color = "#FF9800"
            density_icon = ":large_yellow_circle:"
        else:
            density_color = "#f44336"
            density_icon = ":red_circle:"

        st.markdown(
            f"<div style='background:#1a1d24;border-radius:8px;padding:1rem;margin:12px 0;"
            f"border-left:4px solid {density_color};'>"
            f"<div style='display:flex;align-items:center;gap:12px;'>"
            f"<span style='font-size:1.5rem;'>{density_icon}</span>"
            f"<div>"
            f"<div style='font-weight:600;font-size:1rem;'>Competition Score: {density}</div>"
            f"<div style='font-size:0.85rem;color:#aaa;'>"
            f"Filtered: {tunnel_data['filtered_count']} products &middot; "
            f"Unfiltered: {tunnel_data['unfiltered_count']} products</div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

        if is_golden:
            st.success(":star: **Golden Niche** — Low competition with strong opportunity potential!")

        # -- Golden List (filtered + scored) -----------------------------------
        filtered = tunnel_data.get("filtered_rows", [])
        gems = tunnel_data.get("gems", [])

        if filtered:
            st.markdown(f"### :gem: Golden List — {len(filtered)} Scored Products (Ranked by EOS)")
            gf_df = _pd.DataFrame(filtered)
            gf_df["ASIN Link"] = gf_df["ASIN"].apply(lambda x: f"https://www.amazon.com/dp/{x}" if x else "")

            display_cols = ["ASIN Link", "Title", "Price", "Visibility_Score", "EOS", "Theme", "ReviewCount", "Rating"]
            avail = [c for c in display_cols if c in gf_df.columns]
            st.dataframe(
                gf_df[avail].head(50),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ASIN Link": st.column_config.LinkColumn("ASIN", display_text=r"https://www.amazon.com/dp/(.*)"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Visibility_Score": st.column_config.NumberColumn("Vis. Score", format="%.0f"),
                    "EOS": st.column_config.NumberColumn("EOS", format="%.1f"),
                    "Theme": st.column_config.TextColumn("Theme"),
                    "Rating": st.column_config.NumberColumn("Rating", format="%.1f"),
                    "ReviewCount": st.column_config.NumberColumn("Reviews", format="%d"),
                },
            )

            # -- CSV Export ----------------------------------------------------
            csv_buffer = StringIO()
            csv_writer = csv.writer(csv_buffer)
            csv_headers = ["ASIN", "Title", "Price", "Visibility_Score", "EOS", "Theme", "ReviewCount", "Rating", "PublicationDate"]
            csv_writer.writerow(csv_headers)
            for row in filtered:
                csv_writer.writerow([
                    row.get("ASIN", ""),
                    row.get("Title", ""),
                    row.get("Price", ""),
                    row.get("Visibility_Score", ""),
                    row.get("EOS", ""),
                    row.get("Theme", ""),
                    row.get("ReviewCount", ""),
                    row.get("Rating", ""),
                    row.get("PublicationDate", ""),
                ])
            safe_name = st.session_state["tunnel_niche_name"].lower().replace(" ", "_")[:40]
            st.download_button(
                label=":inbox_tray: Export Golden List to CSV",
                data=csv_buffer.getvalue(),
                file_name=f"golden_list_{safe_name}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            # -- Gold Gems mini-table -------------------------------------------
            if gems:
                st.markdown(f"**:gem: Gold Gems — {len(gems)} products with < 30 reviews**")
                gem_df = _pd.DataFrame(gems)
                gem_df["ASIN Link"] = gem_df["ASIN"].apply(lambda x: f"https://www.amazon.com/dp/{x}" if x else "")
                gem_cols = ["ASIN Link", "Title", "Price", "EOS", "ReviewCount"]
                gem_avail = [c for c in gem_cols if c in gem_df.columns]
                st.dataframe(
                    gem_df[gem_avail].head(20),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "ASIN Link": st.column_config.LinkColumn("ASIN", display_text=r"https://www.amazon.com/dp/(.*)"),
                        "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                        "EOS": st.column_config.NumberColumn("EOS", format="%.1f"),
                        "ReviewCount": st.column_config.NumberColumn("Reviews", format="%d"),
                    },
                )
        else:
            st.info("No results returned from deep tunnel. Try a broader niche query.")

    elif tunnel_data and tunnel_data.get("error"):
        st.error(f"Deep tunnel failed: {tunnel_data['error']}")


# =========================================================================
# TAB 1: Visual Gallery
# =========================================================================
tab_gallery = tabs[1]

with tab_gallery:
    st.markdown("# :art: Visual Product Gallery")
    st.markdown(
        "<div style='color:#777;margin-top:-12px;margin-bottom:20px;'>"
        "Browse products in a visual card layout with thumbnails</div>",
        unsafe_allow_html=True,
    )
    _display_gallery(st.session_state.get("pipeline_results"), st.session_state.get("tunnel_results"))


# =========================================================================
# TAB 2: Settings
# =========================================================================
tab_settings = tabs[2]

with tab_settings:
    st.markdown("## :gear: Settings")
    st.markdown("Configuration is stored locally in the SQLite database and persists across sessions.")

    st.markdown("### SerpApi Key")
    current_key = config_manager.get_serpapi_key()
    masked = current_key[:8] + "..." + current_key[-4:] if len(current_key) > 12 else ""
    st.markdown(
        f"<div style='font-size:0.85rem;color:#888;margin-bottom:8px;'>"
        f"Current: <code>{masked}</code>" if current_key != "YOUR_SERPAPI_KEY_HERE"
        else "<div style='font-size:0.85rem;color:#e74c3c;'>No key configured.</div>",
        unsafe_allow_html=True,
    )
    new_key = st.text_input(
        "SerpApi Key",
        value="",
        placeholder="Enter your SerpApi key (starts with 641c...)",
        type="password",
        label_visibility="collapsed",
    )
    if st.button("Save SerpApi Key", key="save_key_btn"):
        if new_key.strip():
            config_manager.set_serpapi_key(new_key.strip())
            stash_log("SerpApi key saved to database.")
            st.success("SerpApi key saved!")
            st.rerun()
        else:
            st.warning("Please enter a valid SerpApi key.")

    st.markdown("---")

    st.markdown("### Google Sheets ID")
    current_sid = config_manager.get_sheet_id()
    st.markdown(
        f"<div style='font-size:0.85rem;color:#888;margin-bottom:8px;'>"
        f"Current: <code>{current_sid}</code>" if current_sid
        else "<div style='font-size:0.85rem;color:#888;'>Not configured.</div>",
        unsafe_allow_html=True,
    )
    new_sid = st.text_input(
        "Sheet ID",
        value="",
        placeholder="1abc... (ID from Google Sheets URL)",
        label_visibility="collapsed",
    )
    if st.button("Save Sheet ID", key="save_sid_btn"):
        if new_sid.strip():
            config_manager.set_sheet_id(new_sid.strip())
            stash_log("Google Sheet ID saved to database.")
            st.success("Sheet ID saved!")
            st.rerun()
        else:
            st.warning("Please enter a valid Sheet ID.")

    st.markdown("---")
    st.markdown("### Data Management")
    if st.button("Clear Search History", type="secondary", use_container_width=True):
        conn = database.get_connection()
        conn.execute("DELETE FROM search_history")
        conn.commit()
        conn.close()
        stash_log("Search history cleared.")
        st.success("History cleared!")
        st.rerun()


# =========================================================================
# TAB 3: History
# =========================================================================
tab_history = tabs[3]

with tab_history:
    st.markdown("## :clock3: Past Searches")
    history = database.get_history(limit=50)

    if not history:
        st.info("No search history yet. Run a pipeline from the Dashboard tab.")
    else:
        hist_df = _pd.DataFrame(history)
        display_map = {
            "id": "ID",
            "query": "Query",
            "max_pages": "Pages",
            "min_price": "Price",
            "product_count": "Products",
            "opportunity_count": "Opps",
            "gem_count": "Gems",
            "created_at": "Ran At",
        }
        show_cols = [c for c in display_map if c in hist_df.columns]
        hist_display = hist_df[show_cols].rename(columns=display_map)
        st.dataframe(
            hist_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "ID": st.column_config.NumberColumn("ID", format="%d"),
                "Pages": st.column_config.NumberColumn("Pages", format="%d"),
                "Price": st.column_config.NumberColumn("Min $", format="$%.2f"),
                "Products": st.column_config.NumberColumn("Products", format="%d"),
                "Opps": st.column_config.NumberColumn("Opps", format="%d"),
                "Gems": st.column_config.NumberColumn("Gems", format="%d"),
            },
        )

        st.markdown("### Load Past Result")
        load_cols = st.columns([3, 1])
        with load_cols[0]:
            load_id = st.number_input("Search ID to load", min_value=1, step=1, label_visibility="collapsed", placeholder="Enter search ID...")
        with load_cols[1]:
            if st.button("Load Results", use_container_width=True):
                if load_id:
                    entry = database.get_search_by_id(int(load_id))
                    if entry and entry.get("ranked_rows"):
                        stash_log(f"Loaded search #{load_id}: '{entry['query']}' ({len(entry['ranked_rows'])} products)")
                        st.session_state["pipeline_results"] = {
                            "scraped_count": entry.get("product_count", 0),
                            "opportunity_count": entry.get("opportunity_count", 0),
                            "gem_count": entry.get("gem_count", 0),
                            "ranked_rows": entry["ranked_rows"],
                            "gems": [],
                            "export_ok": False,
                            "error": None,
                        }
                        st.success(f"Loaded search #{load_id} into results.")
                        st.rerun()
                    else:
                        st.error(f"Search #{load_id} not found.")

        st.markdown("### Delete Entry")
        del_cols = st.columns([3, 1])
        with del_cols[0]:
            del_id = st.number_input("Search ID to delete", min_value=1, step=1, label_visibility="collapsed", placeholder="Enter search ID...", key="del_id")
        with del_cols[1]:
            if st.button("Delete", use_container_width=True, type="secondary"):
                if del_id:
                    if database.delete_search(int(del_id)):
                        st.success(f"Deleted search #{del_id}.")
                        st.rerun()
                    else:
                        st.error(f"Could not delete search #{del_id}.")

    # -- Discovery Queue --------------------------------------------------------
    st.markdown("---")
    st.markdown("### :dna: Discovery Queue")
    st.markdown(
        "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
        "Niche suggestions extracted from product-detail pages.</div>",
        unsafe_allow_html=True,
    )

    disc_queue = database.get_discovery_queue(searched=False, limit=20)
    disc_searched = database.get_discovery_queue(searched=True, limit=10)

    if not disc_queue and not disc_searched:
        st.info("No discovery terms yet. Run a pipeline and click 'Discover More'.")
    else:
        if disc_queue:
            st.markdown(f"**Pending ({len(disc_queue)} terms)**")
            q_df = _pd.DataFrame(disc_queue)
            q_display = q_df[["id", "term", "source", "score", "origin_query", "created_at"]]
            st.dataframe(q_display, use_container_width=True, hide_index=True)
        if disc_searched:
            with st.expander(f"Already searched ({len(disc_searched)} terms)"):
                s_df = _pd.DataFrame(disc_searched)
                s_display = s_df[["id", "term", "source", "score", "origin_query", "created_at"]]
                st.dataframe(s_display, use_container_width=True, hide_index=True)

        if st.button("Clear Discovery Queue", type="secondary"):
            database.clear_discovery_queue()
            st.success("Queue cleared.")
            st.rerun()

    # -- Footer ----------------------------------------------------------------
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#444;font-size:0.75rem;'>"
        "KDP Research Pipeline &mdash; SerpApi + Streamlit + SQLite"
        "</div>",
        unsafe_allow_html=True,
    )
