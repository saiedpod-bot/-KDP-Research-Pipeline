"""
dashboard.py -- Streamlit Dashboard for KDP Discovery Engine Pro

Usage:
    streamlit run main.py

Author: KDP Automation Architect
"""

import os
import sys
import json
import time
import logging
import csv
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path
from io import StringIO
from datetime import datetime

# --- Ensure src/ is on the path for 'from core import ...' ---
_src_path = Path(__file__).resolve().parent
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

import pandas as _pd
import streamlit as st

# --- Page config (must be first Streamlit command) -------------------------
st.set_page_config(
    page_title="KDP Research Pipeline",
    page_icon=":rocket:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS — modern interactive glass-morphism design --------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    /* Main container — subtle animated gradient */
    .main {
        background: linear-gradient(135deg, #0a0e17 0%, #0f1629 50%, #0a0e17 100%);
        background-attachment: fixed;
    }
    .stApp {
        background: transparent;
    }

    /* Animated gradient glow on header area */
    .gradient-glow {
        position: relative;
        overflow: hidden;
    }
    .gradient-glow::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle at 30% 50%, rgba(99,102,241,0.08) 0%, transparent 50%),
                    radial-gradient(circle at 70% 50%, rgba(168,85,247,0.06) 0%, transparent 50%);
        animation: aurora 15s ease-in-out infinite alternate;
        pointer-events: none;
    }
    @keyframes aurora {
        0% { transform: translate(0, 0) rotate(0deg); }
        50% { transform: translate(-5%, 3%) rotate(5deg); }
        100% { transform: translate(5%, -3%) rotate(-5deg); }
    }

    /* Glass card — used for metrics, sections */
    .glass-card {
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.25rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .glass-card:hover {
        background: rgba(255,255,255,0.06);
        border-color: rgba(255,255,255,0.12);
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    }
    .glass-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.03), transparent);
        transition: left 0.6s ease;
    }
    .glass-card:hover::after {
        left: 100%;
    }

    /* Pulse ring for golden/important items */
    .pulse-ring {
        position: relative;
    }
    .pulse-ring::before {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 20px;
        border: 2px solid rgba(250,204,21,0.3);
        animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    @keyframes pulse-ring {
        0%, 100% { opacity: 0.3; transform: scale(1); }
        50% { opacity: 1; transform: scale(1.03); }
    }

    /* Status cards — modernized */
    .status-card {
        padding: 0.75rem 1rem;
        border-radius: 12px;
        margin: 0.25rem 0;
        font-size: 0.85rem;
        font-weight: 500;
        border-left: 4px solid;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    .status-card.pending {
        background: rgba(85,85,85,0.1);
        border-left-color: #555;
        color: #888;
    }
    .status-card.running {
        background: rgba(33,150,243,0.1);
        border-left-color: #2196F3;
        color: #90caf9;
        box-shadow: 0 0 20px rgba(33,150,243,0.1);
    }
    .status-card.success {
        background: rgba(76,175,80,0.1);
        border-left-color: #4CAF50;
        color: #a5d6a7;
    }
    .status-card.failed {
        background: rgba(244,67,54,0.1);
        border-left-color: #f44336;
        color: #ef9a9a;
    }
    .status-card.skipped {
        background: rgba(119,119,119,0.08);
        border-left-color: #777;
        color: #999;
    }

    /* Log area — terminal aesthetic */
    .log-box {
        background: #05080f;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 1rem;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.78rem;
        line-height: 1.7;
        max-height: 360px;
        overflow-y: auto;
        color: #b0b8c8;
        box-shadow: inset 0 0 30px rgba(0,0,0,0.5);
    }
    .log-box div {
        border-bottom: 1px solid rgba(255,255,255,0.03);
        padding: 3px 0;
        opacity: 0.85;
        transition: opacity 0.2s;
    }
    .log-box div:hover { opacity: 1; }

    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.02);
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(255,255,255,0.08);
        border-radius: 3px;
        transition: background 0.3s;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255,255,255,0.15);
    }

    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: rgba(10,14,23,0.95);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255,255,255,0.05);
    }

    /* Buttons — glass morphism with glow */
    div.stButton > button:first-child {
        width: 100%;
        font-weight: 600;
        border-radius: 10px;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.04);
        color: #e0e0e0;
        padding: 0.5rem 1rem;
        font-size: 0.85rem;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        backdrop-filter: blur(10px);
        letter-spacing: 0.3px;
    }
    div.stButton > button:first-child:hover {
        background: rgba(255,255,255,0.1);
        border-color: rgba(255,255,255,0.2);
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    div.stButton > button:first-child:active {
        transform: translateY(0);
    }

    /* Primary button — gradient accent */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        border: none;
        color: white;
        font-weight: 700;
        box-shadow: 0 4px 20px rgba(99,102,241,0.25);
    }
    div.stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 30px rgba(99,102,241,0.4);
        transform: translateY(-2px);
    }

    /* Metric cards — glass with glow */
    .metric-box {
        background: rgba(255,255,255,0.03);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 16px;
        padding: 1.25rem 0.75rem;
        text-align: center;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    .metric-box:hover {
        border-color: rgba(99,102,241,0.2);
        transform: translateY(-3px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }
    .metric-box .value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #f0f0f0; /* fallback for screen readers */
        background: linear-gradient(135deg, #f0f0f0, #a0a0f0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: -0.5px;
    }
    .metric-box .label {
        font-size: 0.7rem;
        color: rgba(255,255,255,0.4);
        text-transform: uppercase;
        letter-spacing: 0.8px;
        font-weight: 600;
        margin-top: 4px;
    }
    .metric-box::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent);
    }

    /* Tables — clean modern */
    .stDataFrame {
        font-size: 0.8rem;
    }
    .stDataFrame [data-testid="StyledDataFrameDataCell"] {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
    }
    .stDataFrame thead tr th {
        background: rgba(255,255,255,0.03) !important;
        border-bottom: 1px solid rgba(255,255,255,0.06) !important;
        font-weight: 600 !important;
        color: rgba(255,255,255,0.6) !important;
        text-transform: uppercase;
        font-size: 0.7rem !important;
        letter-spacing: 0.5px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: rgba(255,255,255,0.02);
        border-radius: 12px;
        padding: 4px;
        border: 1px solid rgba(255,255,255,0.04);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 0.8rem;
        color: rgba(255,255,255,0.4);
        transition: all 0.25s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: rgba(255,255,255,0.8);
        background: rgba(255,255,255,0.04);
    }
    .stTabs [aria-selected="true"] {
        background: rgba(99,102,241,0.15) !important;
        color: #a5b4fc !important;
        box-shadow: 0 2px 10px rgba(99,102,241,0.1);
    }

    /* Input fields — dark glass */
    .stTextInput input, .stNumberInput input, .stSelectbox > div {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
        font-size: 0.85rem !important;
        transition: all 0.25s ease;
    }
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: rgba(99,102,241,0.4) !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    }

    /* Checkbox */
    .stCheckbox label {
        color: rgba(255,255,255,0.6) !important;
        font-size: 0.82rem;
    }
    .stCheckbox [data-testid="baseweb-checkbox"] input:checked + span {
        background: #6366f1 !important;
        border-color: #6366f1 !important;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.02) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        color: rgba(255,255,255,0.7) !important;
        transition: all 0.2s ease;
    }
    .streamlit-expanderHeader:hover {
        background: rgba(255,255,255,0.04) !important;
        border-color: rgba(255,255,255,0.08) !important;
    }

    /* Info/Success/Warning/Error boxes */
    .stAlert {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
        backdrop-filter: blur(10px);
    }

    /* Section dividers */
    h1, h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.3px;
    }
    h1 {
        background: linear-gradient(135deg, #f0f0f0, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.8rem !important;
        color: #f0f0f0; /* fallback for screen readers / forced colors */
    }
    h2 {
        color: rgba(255,255,255,0.9) !important;
        font-size: 1.3rem !important;
    }
    h3 {
        color: rgba(255,255,255,0.8) !important;
        font-size: 1.1rem !important;
    }

    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #10b981, #059669) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(16,185,129,0.2) !important;
    }
    .stDownloadButton button:hover {
        box-shadow: 0 6px 25px rgba(16,185,129,0.35) !important;
        transform: translateY(-1px);
    }

    /* Spinner */
    .stSpinner > div {
        border-color: #6366f1 transparent transparent transparent !important;
    }

    /* Section separator */
    .section-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(99,102,241,0.2), transparent);
        margin: 1.5rem 0;
        border: none;
    }

    /* High-Contrast Mode (triggered by body attr) */
    body[data-high-contrast="true"] .metric-box .value,
    body[data-high-contrast="true"] h1 {
        -webkit-text-fill-color: #ffffff !important;
        color: #ffffff !important;
        background: none !important;
    }
    body[data-high-contrast="true"] .glass-card,
    body[data-high-contrast="true"] .metric-box {
        background: rgba(0,0,0,0.6) !important;
        border-color: rgba(255,255,255,0.3) !important;
        backdrop-filter: none !important;
    }
    body[data-high-contrast="true"] .log-box {
        background: #000 !important;
        color: #0f0 !important;
        border-color: #fff !important;
    }
    body[data-high-contrast="true"] .stTabs [data-baseweb="tab"] {
        color: #fff !important;
    }
    body[data-high-contrast="true"] .stTabs [aria-selected="true"] {
        background: rgba(255,255,255,0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# High-contrast mode toggle (controlled via session state)
if st.session_state.get("high_contrast", False):
    st.markdown(
        "<script>document.body.setAttribute('data-high-contrast', 'true');</script>",
        unsafe_allow_html=True,
    )


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
# Welcome Screen
# ---------------------------------------------------------------------------
def show_welcome_screen():
    """Render the landing hero when no pipeline has run yet."""
    st.markdown("""
    <div class="gradient-glow" style="padding: 3rem 2rem; border-radius: 24px; margin-bottom: 1.5rem;">
        <h1 style="font-size: 3rem; font-weight: 800; letter-spacing: -1px; margin: 0; line-height: 1.2;">
            🚀 KDP Discovery Engine<br><span style="font-size:1.6rem;font-weight:400;color:#94a3b8;">Intelligence Core</span>
        </h1>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns([3, 2])
    with cols[0]:
        st.markdown("""
        أهلاً بك في نظام الذكاء الاصطناعي لتحليل أسواق KDP.

        **كيف يعمل النظام؟**
        1. **الاستطلاع:** نقوم بجلب بيانات لحظية من Amazon عبر Pangolinfo API.
        2. **التحليل:** يقوم محركنا (The Brain) بحساب "درجة النيش" (Niche Score) بناءً على التنافسية، الطلب، وتوزيع المبيعات.
        3. **التنفيذ:** نحول الفرص الذهبية إلى ملفات تصميم جاهزة للرفع على Canva بضغطة زر.

        ---
        ### 💡 نصيحة احترافية:
        * ابحث عن نيشات بدرجة **(70+)** لضمان سرعة الانتشار.
        * استخدم ميزة **Bulk CSV** لتحويل أفكارك إلى كتب جاهزة في دقائق.
        """)

    with cols[1]:
        st.markdown("#### لوحة مؤشرات الأداء")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Pangolinfo Status", "Connected ✅")
        with c2:
            st.metric("Design Engine", "Ready 🎨")


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
    domain: str = "amazon.com",
    amazon_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the 3-tier pipeline and return results as a dict.

    If *amazon_url* is provided, the scraper bypasses SerpApi keyword search
    and scrapes the full Amazon URL directly (useful when keyword search
    returns 0 results but Amazon shows products).

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

    # -- Validate Pangolinfo token before spending credits ------------------
    stash_log("Validating Pangolinfo token...")
    pangolinfo_token = os.environ.get("PANGOLINFO_TOKEN") or scraper.PANGOLINFO_TOKEN
    if not pangolinfo_token:
        stash_log("PANGOLINFO_TOKEN missing.")
        st.session_state["stage1_status"] = "failed"
        results["error"] = (
            "**Pangolinfo token not configured.** "
            "Set PANGOLINFO_TOKEN in config.ini or .env file."
        )
        return results
    stash_log("Pangolinfo token found.")

    # -- Stage 1: Scrape via Pangolinfo ------------------------------------
    st.session_state["stage1_status"] = "running"
    try:
        stash_log(f"Searching Pangolinfo for: {query[:80]}...")
        status.update(label="Searching Pangolinfo...")
        progress_bar.progress(10, text="Fetching Amazon data...")
        raw = scraper.fetch_category_url(keyword=query, marketplace="amz_us")
        if raw is None:
            stash_log("Pangolinfo scrape returned None.")
            scraped_rows = []
        elif isinstance(raw, dict) and "error" in raw:
            stash_log(f"Pangolinfo error: {raw['error']}")
            results["error"] = raw["error"]
            scraped_rows = []
        else:
            scraped_rows = scraper.normalize_pangolinfo_results(raw)
            if scraped_rows:
                scraper.save_results(query, raw, scraped_rows)
            stash_log(f"Pangolinfo scrape: {len(scraped_rows)} products found.")
    except Exception as exc:
        stash_log(f"SCRAPE FAILED: {exc}")
        st.session_state["stage1_status"] = "failed"
        results["error"] = str(exc)
        return results

    if not scraped_rows:
        stash_log("No products found. Halting.")
        st.session_state["stage1_status"] = "failed"
        # Diagnose why
        has_key = bool(api_key) and api_key != "YOUR_SERPAPI_KEY_HERE"
        diagnosis = analyzer.get_empty_result_diagnosis(
            query=query,
            has_api_key=has_key,
            filter_new_release=bool(filter_params and "rh" in filter_params),
            min_price=min_price,
        )
        # If API key was validated but returned 0, mention URL paste option
        if amazon_url:
            results["error"] = (
                "Amazon URL scrape returned no products. "
                "The URL may be invalid or Amazon changed its page structure. "
                "Try a different URL or enable Demo Mode."
            )
        else:
            results["error"] = (
                "No products returned from scraper. "
                "Try pasting the Amazon URL directly (expand 'Paste Amazon URL directly' above). "
                "Or enable Demo Mode to explore the tool without an API key."
            )
        results["empty_diagnosis"] = diagnosis
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
            results["error"] = f"No products above ${min_price:.2f} minimum price."
            results["empty_diagnosis"] = {
                "possible_causes": [
                    f"The minimum price filter (${min_price:.2f}) eliminated all products.",
                    "All scraped products were priced below the minimum threshold.",
                ],
                "suggestions": [
                    {"query": str(round(min_price * 0.7, 2)), "strategy": "lower price", "reason": "reduce minimum price"},
                    {"query": "0", "strategy": "remove filter", "reason": "remove price filter entirely"},
                ],
                "advice": f"Try lowering the minimum price below ${min_price:.2f}, or set it to $0 to see all products.",
            }
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

    # Attach Profit columns + UOI
    try:
        processed_df = analyzer.add_profit_columns(processed_df)
        density_val = results.get("density", 0.0)
        processed_df = analyzer.add_uoi_column(processed_df, density=density_val)
        ranked_rows = processed_df.to_dict(orient="records")
        results["ranked_rows"] = ranked_rows
    except Exception as exc:
        stash_log(f"Profit/UOI enrichment note: {exc}")

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
                domain=domain,
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
    domain: str = "amazon.com",
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
            domain=domain,
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
            domain=domain,
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

        # Save a snapshot for trend tracking
        filtered_for_snap = result.get("filtered_rows", [])
        if filtered_for_snap:
            import statistics
            prices = [r.get("Price", 0) or 0 for r in filtered_for_snap]
            eoss = [r.get("EOS", 0) or 0 for r in filtered_for_snap]
            viss = [r.get("Visibility_Score", 0) or 0 for r in filtered_for_snap]
            profs = [r.get("Net_Profit", 0) or 0 for r in filtered_for_snap]
            titles = [r.get("Title", "") for r in filtered_for_snap]
            top_kw = json.dumps([k["keyword"] for k in analyzer.extract_keywords_from_titles(titles)[:10]])
            database.save_niche_snapshot(
                query=niche_query,
                product_count=len(filtered_for_snap),
                avg_price=round(statistics.mean(prices), 2),
                avg_eos=round(statistics.mean(eoss), 1),
                avg_visibility=round(statistics.mean(viss), 1),
                avg_profit=round(statistics.mean(profs), 2),
                gem_count=len(result.get("gems", [])),
                top_keywords=top_kw,
            )

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

    # -- Quick Start mode: hides advanced settings from beginners --------------
    quick_start = st.checkbox(
        "Quick Start Mode (Recommended)",
        value=st.session_state.get("quick_start", True),
        help="Simplified view — hides advanced settings. Uncheck for full control.",
    )
    st.session_state["quick_start"] = quick_start

    query = st.text_input(
        "Search Query",
        value=_default_query,
        placeholder="e.g. yoga anatomy coloring book",
        help="Type what you'd search on Amazon — try 'coloring books for adults' or 'keto cookbook for beginners'",
    )

    # -- Amazon URL Paste (bypasses SerpApi keyword search if SerpApi returns 0) -
    with st.expander(":link: Paste Amazon URL directly (if keyword search fails)", expanded=False):
        st.markdown(
            "<div style='color:#888;font-size:0.82rem;margin-bottom:6px;'>"
            "If the keyword search above returns 0 results but Amazon shows products, "
            "paste the Amazon URL here instead. The tool will scrape it directly.</div>",
            unsafe_allow_html=True,
        )
        amazon_url = st.text_input(
            "Amazon Search URL",
            placeholder="https://www.amazon.com/s?k=yoga+anatomy+coloring+book&i=stripbooks",
            label_visibility="collapsed",
            key="amazon_url_paste",
        )
        st.caption(
            "Copy the URL from your browser after searching on Amazon, paste it above, "
            "then click **Analyze Niche** below."
        )

    # -- Market domain selector (multi-marketplace support) --------------------
    domain_options = {
        "amazon.com": "🇺🇸 US",
        "amazon.co.uk": "🇬🇧 UK",
        "amazon.de": "🇩🇪 Germany",
        "amazon.fr": "🇫🇷 France",
        "amazon.co.jp": "🇯🇵 Japan",
        "amazon.ca": "🇨🇦 Canada",
        "amazon.com.au": "🇦🇺 Australia",
        "amazon.in": "🇮🇳 India",
        "amazon.com.mx": "🇲🇽 Mexico",
        "amazon.it": "🇮🇹 Italy",
        "amazon.es": "🇪🇸 Spain",
    }
    current_domain = config_manager.get("amazon_domain", "amazon.com") if MODULES_OK else "amazon.com"
    domain_label = st.selectbox(
        "Marketplace",
        options=list(domain_options.keys()),
        format_func=lambda d: domain_options.get(d, d),
        index=list(domain_options.keys()).index(current_domain)
            if current_domain in domain_options else 0,
        help="Select Amazon marketplace to search. Currency & defaults adjust automatically.",
    )
    if MODULES_OK and domain_label != current_domain:
        config_manager.set("amazon_domain", domain_label)

    # Show advanced settings only when Quick Start is OFF
    filter_params: Dict[str, str] = {}

    if not quick_start:
        max_pages = st.number_input(
            "Max Pages",
            min_value=1,
            max_value=20,
            value=3,
            help="Number of SerpApi result pages to fetch (3-5 for deep research). Each page ≈ 20 products.",
        )

        min_price = st.number_input(
            "Min Price ($)",
            min_value=0.0,
            max_value=100.0,
            value=7.00,
            step=0.50,
            help="Filter out products below this price. $7+ typically indicates quality books.",
        )

        sheet_id = st.text_input(
            "Sheet ID (optional)",
            placeholder="1abc... (leave blank to skip export)",
            help="Google Sheet ID for Tier 3 export — only needed if you use Google Sheets.",
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
            help='Show only books released in the last 30 days. Great for finding fresh trends.',
        )
        st.session_state["auto_filter"] = auto_filter
        if auto_filter:
            filter_params["rh"] = "p_n_publication_date:1250226011"

        new_release = st.checkbox(
            "New Release Mode (Last 30 Days)",
            value=st.session_state.get("new_release", False) or auto_filter,
            help="Only show books published in the last 30 days — catches emerging trends early.",
        )
        st.session_state["new_release"] = new_release
        if new_release:
            filter_params["rh"] = "p_n_publication_date:1250226011"

        st.markdown("### BSR Enrichment")
        enrich_bsr = st.checkbox(
            "Enrich with BSR (costs credits)",
            value=st.session_state.get("enrich_bsr", False),
            help="Fetch real Best Sellers Rank via Product API (1 credit per ASIN). "
                 "Enable only for focused analysis on a short list.",
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
    else:
        # Quick Start defaults — sensible for beginners
        max_pages = 2
        min_price = 7.00
        sheet_id = ""
        dev_mode = False
        auto_filter = False
        new_release = False
        enrich_bsr = False
        max_enrich = 0

    st.markdown("---")

    # -- Sample data mode (no API key needed) ----------------------------------
    use_sample_data = st.checkbox(
        "Demo Mode (no API key needed)",
        value=st.session_state.get("use_sample_data", False),
        help="Load pre-collected sample data so you can explore all features without configuring an API key.",
    )
    st.session_state["use_sample_data"] = use_sample_data

    if use_sample_data:
        st.markdown(
            "<div style='font-size:0.78rem;color:#4CAF50;margin-bottom:4px;'>"
            ":white_check_mark: Demo mode active — using sample data. "
            "Configure a SerpApi key in Settings for live searches.</div>",
            unsafe_allow_html=True,
        )
        if MODULES_OK:
            config_manager.set_serpapi_key("SAMPLE_MODE")

    # High contrast toggle (always visible)
    high_contrast = st.checkbox(
        "High Contrast Mode",
        value=st.session_state.get("high_contrast", False),
        help="Increases contrast for better readability. Recommended for accessibility.",
    )
    st.session_state["high_contrast"] = high_contrast

    # Pangolinfo token status
    pangolinfo_token = os.environ.get("PANGOLINFO_TOKEN") or (scraper.PANGOLINFO_TOKEN if MODULES_OK else "")
    if pangolinfo_token:
        status_color = "#4CAF50"
        status_text = "Connected ✅"
    else:
        status_color = "#FF9800"
        status_text = "Not configured — add PANGOLINFO_TOKEN in .env"

    st.markdown(
        f"<div style='font-size:0.75rem;color:{status_color};'>"
        f":key: Pangolinfo: {status_text}</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
if not st.session_state.get("pipeline_results"):
    show_welcome_screen()

tab_names = [
    "📊 Data Table",
    "🧭 Opportunity Explorer",
    "🖼️ Visual Gallery",
    "🎨 Design Studio",
    ":gear: Settings",
    ":clock3: History",
]
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
if "kw_suggestions" not in st.session_state:
    st.session_state["kw_suggestions"] = []
if "kw_gaps" not in st.session_state:
    st.session_state["kw_gaps"] = []
if "category_browser_open" not in st.session_state:
    st.session_state["category_browser_open"] = False
if "niche_tracker_query" not in st.session_state:
    st.session_state["niche_tracker_query"] = ""
if "niche_tracker_history" not in st.session_state:
    st.session_state["niche_tracker_history"] = []
if "quick_start" not in st.session_state:
    st.session_state["quick_start"] = True
if "use_sample_data" not in st.session_state:
    st.session_state["use_sample_data"] = False
if "batch_results" not in st.session_state:
    st.session_state["batch_results"] = []
if "high_contrast" not in st.session_state:
    st.session_state["high_contrast"] = False


# ---------------------------------------------------------------------------
# Results display helper
# ---------------------------------------------------------------------------
def _display_results(results: Optional[Dict[str, Any]], query: str, sheet_id: str, dev_mode: bool) -> None:
    """Render pipeline results: metric cards, gold-mine table, all-ranked table."""
    if not results or results.get("error") or results.get("scraped_count", 0) == 0:
        if results and results.get("error"):
            st.error(f"Pipeline halted: {results['error']}")
            # Show diagnosis if available
            diagnosis = results.get("empty_diagnosis")
            if diagnosis:
                with st.container():
                    st.markdown("### :mag: Why did this happen?")
                    for cause in diagnosis.get("possible_causes", []):
                        st.markdown(f"- {cause}")
                    suggestions = diagnosis.get("suggestions", [])
                    if suggestions:
                        st.markdown("#### :bulb: Try one of these broader searches:")
                        cols = st.columns(min(3, len(suggestions)))
                        for i, sug in enumerate(suggestions[:6]):
                            col = cols[i % len(cols)]
                            query_text = sug["query"]
                            col.markdown(
                                f"<div style='background:#1e2538;"
                                f"border:1px solid #2a3355;border-radius:8px;"
                                f"padding:8px 12px;margin:4px 0;font-size:0.85rem;'>"
                                f"<span style='color:#4CAF50;font-weight:600;'>{query_text}</span>"
                                f"<br><span style='color:#888;font-size:0.75rem;'>{sug['reason']}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )
                    if diagnosis.get("advice"):
                        st.info(diagnosis["advice"])
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

    # -- Intelligence Panel: Market Score (Pangolinfo-optimized) ---------------
    if ranked_rows:
        market = analyzer.calculate_market_score(ranked_rows)
        st.markdown("### :bar_chart: Intelligence Panel — Niche Score")

        gauge_cols = st.columns([3, 2])
        with gauge_cols[0]:
            score = market["score"]
            band = market["band"]
            color = "#4CAF50" if score >= 70 else "#FF9800" if score >= 40 else "#F44336"
            st.markdown(
                f"<div style='text-align:center;padding:12px;'>"
                f"<div style='font-size:2.8rem;font-weight:800;color:{color};'>{score}</div>"
                f"<div style='font-size:1.1rem;color:#aaa;margin-top:-6px;'>{band}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.progress(score / 100)
            st.caption(market["verdict"])

        with gauge_cols[1]:
            bd = market["breakdown"]
            st.markdown(
                f"<div style='font-size:0.85rem;'>"
                f"<div><span style='color:#4CAF50;'>▬</span> Demand: <b>{bd['demand']:.0f}</b> ({bd['demand_weight']} → <b>{bd['demand_contrib']:.0f}</b>)</div>"
                f"<div><span style='color:#2196F3;'>▬</span> Competition: <b>{bd['competition']:.0f}</b> ({bd['competition_weight']} → <b>{bd['competition_contrib']:.0f}</b>)</div>"
                f"<div><span style='color:#FF9800;'>▬</span> Pricing: <b>{bd['pricing']:.0f}</b> ({bd['pricing_weight']} → <b>{bd['pricing_contrib']:.0f}</b>)</div>"
                f"<div><span style='color:#F44336;'>▬</span> Dominance Penalty: <b>-{bd['dominance_penalty']:.0f}</b> ({bd['dominance_weight']} → <b>{bd['dominance_contrib']:.0f}</b>)</div>"
                f"<div style='margin-top:6px;font-size:0.75rem;color:#666;'>Products scored: {bd['product_count']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # -- Score Legend (educational tooltips) ------------------------------------
    with st.expander(":green_book: What do these scores mean?"):
        st.markdown("""
        | Score | What it measures | Good range | Plain English |
        |---|---|---|---|
        | **EOS** (Estimated Opportunity) | Visibility × Price relative to niche | 50–150+ | Higher = better opportunity. Combines how visible a product is with its price point. |
        | **Visibility Score** | Search rank proxy (1st = 100, 20th = 10) | 30–100 | How high a product ranks in search results. Higher is more visible to buyers. |
        | **UOI** (Unified Opportunity Index) | Combines EOS, competition, profit, keywords & trend | 50–100 | Single 0-100 score. 70+ = excellent opportunity. Factors in everything! |
        | **Net Profit** | Price − Amazon fees − printing cost | $2–$8+ | What you actually earn per sale after all costs. |
        | **Gold Gems** | Products with < 30 reviews | — | Low-competition products. If you make a similar book, you can compete without fighting hundreds of reviews. |
        | **Density** | Filtered count ÷ unfiltered count | 0%–30% | Lower = fewer competitors in your target segment. Under 30% is considered "low competition." |
        """)

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
        # Add trend indicator from snapshot history
        snap_history = database.get_snapshot_history(query, limit=3)
        if snap_history:
            niche_trend = analyzer.compute_niche_trend(snap_history)
            gems_df["Trend"] = niche_trend["icon"]
        else:
            gems_df["Trend"] = ":left_right_arrow:"
        display_cols = ["Trend", "ASIN Link", "Title", "Price", "Net_Profit", "Profit_Margin_%", "UOI", "Visibility_Score", "EOS", "Theme"]
        available = [c for c in display_cols if c in gems_df.columns]
        st.dataframe(
            gems_df[available].head(20),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Trend": st.column_config.TextColumn("Trend"),
                "ASIN Link": st.column_config.LinkColumn("ASIN", display_text=r"https://www.amazon.com/dp/(.*)"),
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Net_Profit": st.column_config.NumberColumn("Net Profit", format="$%.2f"),
                "Profit_Margin_%": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                "UOI": st.column_config.NumberColumn("UOI", format="%.1f"),
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
        snap_history_trend = database.get_snapshot_history(query, limit=3)
        if snap_history_trend:
            niche_trend_all = analyzer.compute_niche_trend(snap_history_trend)
            all_df["Trend"] = niche_trend_all["icon"]
        else:
            all_df["Trend"] = ":left_right_arrow:"
        all_cols = ["Trend", "ASIN Link", "Title", "Price", "Net_Profit", "Profit_Margin_%", "UOI", "Visibility_Score", "EOS", "Theme", "ReviewCount", "Rating"]
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
                    "Trend": st.column_config.TextColumn("Trend"),
                    "ASIN Link": st.column_config.LinkColumn("ASIN", display_text=r"https://www.amazon.com/dp/(.*)"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Net_Profit": st.column_config.NumberColumn("Net Profit", format="$%.2f"),
                    "Profit_Margin_%": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                    "UOI": st.column_config.NumberColumn("UOI", format="%.1f"),
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

        # Full CSV Export with all columns
        if not all_df.empty:
            all_export_cols = [
                "ASIN", "Title", "Author", "Price", "BSR", "ReviewCount", "Rating",
                "Net_Profit", "Profit_Margin_%", "UOI", "Visibility_Score", "EOS",
                "Theme", "Est._Daily_Sales", "PublicationDate",
            ]
            export_avail = [c for c in all_export_cols if c in all_df.columns]
            csv_full = all_df[export_avail].to_csv(index=False)
            st.download_button(
                label=":inbox_tray: Full Export (all columns CSV)",
                data=csv_full,
                file_name=f"full_export_{safe_name}.csv",
                mime="text/csv",
                use_container_width=False,
            )

    # -- What to do next (plain-language recommendation) -----------------------
    if results.get("gem_count", 0) > 0:
        top_gem = results["gems"][0] if results.get("gems") else None
        st.markdown("### :compass: What to do next")
        if top_gem:
            gem_title = top_gem.get("Title", "this product")
            gem_eos = top_gem.get("EOS", 0)
            gem_reviews = top_gem.get("ReviewCount", 0)
            gem_profit = top_gem.get("Net_Profit", 0)
            st.info(
                f"**Start here:** **\"{gem_title}\"** has a strong EOS of **{gem_eos:.0f}**, "
                f"only **{int(gem_reviews)} reviews**, and estimated profit of **${gem_profit:.2f}/sale**. "
                f"Consider publishing a similar book with a unique angle — better cover, "
                f"more pages, or targeting a specific sub-audience. "
                f"Then use the **Keyword Explorer** tab to find what keywords your competitors are ranking for."
            )
        else:
            st.info(
                f"We found **{results['gem_count']} gold gems** with low competition. "
                f"Scroll up to see them in the Gold-Mine table. "
                f"Choose one with high EOS (>50) and low reviews (<30) for your first launch."
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
                st.image(thumb, use_column_width=True)
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
            vs = product.get("Visibility_Score", 0)
            theme = product.get("Theme", "—")
            rating = product.get("Rating", 0)
            reviews = product.get("ReviewCount", 0)
            pub = product.get("PublicationDate", "—")
            bsr = product.get("BSR", 0)

            meta = f"💰 **${float(price):.2f}**" if price else ""
            if eos:
                meta += f" &nbsp;🚀 **{float(eos):.1f}**"
            if vs:
                meta += f" &nbsp;📊 **{float(vs):.0f}**"
            st.markdown(
                f"<div style='font-size:0.8rem;color:#ccc;"
                f"margin:2px 0;'>{meta}</div>",
                unsafe_allow_html=True,
            )

            meta2 = ""
            if rating:
                meta2 += f"⭐ {float(rating):.1f}"
            if reviews:
                meta2 += f" &nbsp;💬 {int(reviews)}"
            if theme and theme != "—":
                meta2 += f" &nbsp;🏷️ {theme}"
            if meta2:
                st.markdown(
                    f"<div style='font-size:0.75rem;color:#888;"
                    f"margin:2px 0 6px 0;'>{meta2}</div>",
                    unsafe_allow_html=True,
                )

            if pub and pub not in ("N/A", "—", ""):
                st.markdown(
                    f"<div style='font-size:0.7rem;color:#666;"
                    f"margin:0 0 4px 0;'>📅 {pub}</div>",
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

        start_t = time.time()
        if use_sample_data:
            stash_log("Demo mode: loading sample data...")
            import pandas as _pd_demo
            sample = [
                {"ASIN": "B0DEMO001", "Title": "Cozy Coloring Book for Adults: Stress Relief Patterns", "Author": "Sarah Design", "Price": 9.99, "Rating": 4.5, "ReviewCount": 12, "PublicationDate": "2026-01-15"},
                {"ASIN": "B0DEMO002", "Title": "Cozy Coloring Book: Easy Large Print Designs for Relaxation", "Author": "Emma Artist", "Price": 8.99, "Rating": 4.7, "ReviewCount": 5, "PublicationDate": "2026-03-01"},
                {"ASIN": "B0DEMO003", "Title": "Low Carb Cookbook for Beginners: 500 Easy Recipes", "Author": "Chef Keto", "Price": 14.99, "Rating": 4.3, "ReviewCount": 28, "PublicationDate": "2025-11-20"},
                {"ASIN": "B0DEMO004", "Title": "Keto Diet Cookbook for Women Over 50", "Author": "Dr. Wellness", "Price": 12.99, "Rating": 4.6, "ReviewCount": 8, "PublicationDate": "2026-02-14"},
                {"ASIN": "B0DEMO005", "Title": "Stress Relief Coloring Book: Mandalas for Adults", "Author": "Mindful Art", "Price": 7.99, "Rating": 4.2, "ReviewCount": 45, "PublicationDate": "2025-09-10"},
                {"ASIN": "B0DEMO006", "Title": "Large Print Easy Crossword Puzzles for Seniors", "Author": "Brain Games", "Price": 11.99, "Rating": 4.8, "ReviewCount": 3, "PublicationDate": "2026-04-01"},
                {"ASIN": "B0DEMO007", "Title": "Vegan Meal Prep Cookbook: Plant-Based Recipes", "Author": "Green Kitchen", "Price": 13.99, "Rating": 4.4, "ReviewCount": 18, "PublicationDate": "2025-12-05"},
                {"ASIN": "B0DEMO008", "Title": "Low Carb High Fat Diet: Complete Guide for Beginners", "Author": "Dr. Keto", "Price": 16.99, "Rating": 4.1, "ReviewCount": 35, "PublicationDate": "2025-08-15"},
                {"ASIN": "B0DEMO009", "Title": "Easy Keto Recipes: 30-Minute Meals for Busy People", "Author": "Quick Chef", "Price": 10.99, "Rating": 4.5, "ReviewCount": 9, "PublicationDate": "2026-03-20"},
                {"ASIN": "B0DEMO010", "Title": "Mindfulness Coloring Book for Adults: Relax and Unwind", "Author": "Zen Art", "Price": 8.99, "Rating": 4.3, "ReviewCount": 22, "PublicationDate": "2025-10-01"},
                {"ASIN": "B0DEMO011", "Title": "Paleo Diet Cookbook: Grain-Free Recipes for Health", "Author": "Cave Kitchen", "Price": 15.99, "Rating": 4.0, "ReviewCount": 15, "PublicationDate": "2026-01-28"},
                {"ASIN": "B0DEMO012", "Title": "Mediterranean Diet Cookbook for Beginners", "Author": "Olive Chef", "Price": 12.99, "Rating": 4.6, "ReviewCount": 7, "PublicationDate": "2026-04-10"},
            ]
            df_demo = _pd_demo.DataFrame(sample)
            df_demo = analyzer.find_gems_dataframe(df_demo)
            df_demo = analyzer.add_profit_columns(df_demo)
            df_demo = analyzer.add_uoi_column(df_demo, density=0.15)
            ranked = df_demo.to_dict(orient="records")
            results = {
                "scraped_count": len(ranked),
                "opportunity_count": len(ranked),
                "gem_count": sum(1 for r in ranked if r.get("ReviewCount", 999) < 30),
                "ranked_rows": ranked,
                "gems": [r for r in ranked if r.get("ReviewCount", 999) < 30],
                "export_ok": False,
                "error": None,
            }
            stash_log(f"Demo data loaded — {results['scraped_count']} products, {results['gem_count']} gold gems.")
        else:
            stash_log(f"Pipeline starting -- query: '{query}', pages: {max_pages}, min price: ${min_price:.2f}")
            amazon_url = st.session_state.get("amazon_url_paste", "").strip()
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
                domain=domain_label,
                amazon_url=amazon_url or None,
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
                domain=domain_label,
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

            display_cols = ["ASIN Link", "Title", "Price", "Net_Profit", "Profit_Margin_%", "UOI", "Visibility_Score", "EOS", "Theme", "ReviewCount", "Rating"]
            avail = [c for c in display_cols if c in gf_df.columns]
            st.dataframe(
                gf_df[avail].head(50),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ASIN Link": st.column_config.LinkColumn("ASIN", display_text=r"https://www.amazon.com/dp/(.*)"),
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Net_Profit": st.column_config.NumberColumn("Net Profit", format="$%.2f"),
                    "Profit_Margin_%": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                    "UOI": st.column_config.NumberColumn("UOI", format="%.1f"),
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
            # Show diagnostic suggestions
            niche_q = st.session_state.get("tunnel_niche_name", "")
            if niche_q:
                diagnosis = analyzer.get_empty_result_diagnosis(niche_q, has_api_key=True)
                suggestions = diagnosis.get("suggestions", [])
                if suggestions:
                    st.markdown("#### :bulb: Broader niche suggestions:")
                    cols = st.columns(3)
                    for i, sug in enumerate(suggestions[:6]):
                        with cols[i % 3]:
                            st.markdown(
                                f"<div style='background:#1e2538;"
                                f"border:1px solid #2a3355;border-radius:8px;"
                                f"padding:8px 12px;margin:4px 0;font-size:0.85rem;'>"
                                f"<span style='color:#4CAF50;font-weight:600;'>{sug['query']}</span>"
                                f"<br><span style='color:#888;font-size:0.75rem;'>{sug['reason']}</span>"
                                f"</div>",
                                unsafe_allow_html=True,
                            )

    # -- Recently Removed Products (like PodCS) --------------------------------
        if tunnel_data and not tunnel_data.get("error"):
            niche_q = st.session_state.get("tunnel_niche_name", "")
            if niche_q:
                removed = database.get_removed_products(niche_q)
                if removed:
                    with st.expander(f":recycle: Recently Removed Products ({len(removed)} found)"):
                        st.markdown(
                            "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
                            "Products that existed in previous snapshots but are no longer available. "
                            "These may have been deleted, gone out of stock, or lost the Buy Box. "
                            "Consider re-creating high-performing removed designs.</div>",
                            unsafe_allow_html=True,
                        )
                        rem_df = _pd.DataFrame(removed)
                        st.dataframe(
                            rem_df[["asin", "title", "last_price", "last_seen", "removed_after"]],
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "asin": st.column_config.TextColumn("ASIN"),
                                "title": st.column_config.TextColumn("Title"),
                                "last_price": st.column_config.NumberColumn("Last Price", format="$%.2f"),
                                "last_seen": st.column_config.TextColumn("Last Seen"),
                                "removed_after": st.column_config.TextColumn("Removed After"),
                            },
                        )
                        rem_csv = rem_df.to_csv(index=False)
                        st.download_button(
                            label=":inbox_tray: Download Removed Products CSV",
                            data=rem_csv,
                            file_name=f"removed_{niche_q[:30]}.csv",
                            mime="text/csv",
                            use_container_width=True,
                        )

    elif tunnel_data and tunnel_data.get("error"):
        st.error(f"Deep tunnel failed: {tunnel_data['error']}")


# =========================================================================
# TAB 1: Opportunity Explorer
# =========================================================================
tab_explorer = tabs[1]

with tab_explorer:
    st.markdown("# :compass: Opportunity Explorer")
    st.markdown(
        "<div style='color:#777;margin-top:-12px;margin-bottom:20px;'>"
        "Profit, Keywords, Categories & Trend Tracking</div>",
        unsafe_allow_html=True,
    )

    explorer_tabs = st.tabs([
        ":moneybag: Profit Calculator",
        ":key: Keyword Explorer",
        ":card_index_dividers: Category Browser",
        ":chart_with_upwards_trend: Niche Tracker",
    ])

    # -----------------------------------------------------------------------
    # Explorer Tab A: Profit Calculator
    # -----------------------------------------------------------------------
    with explorer_tabs[0]:
        st.markdown("### KDP Profit Calculator")
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
            "Estimate net profit per book after Amazon fees & printing costs (2026 rates).</div>",
            unsafe_allow_html=True,
        )

        pc = st.columns([1, 1, 1])
        with pc[0]:
            pc_price = st.number_input("Sale Price ($)", min_value=0.99, max_value=200.0, value=9.99, step=0.50)
        with pc[1]:
            pc_pages = st.number_input("Page Count", min_value=24, max_value=1200, value=200, step=10)
        with pc[2]:
            pc_type = st.selectbox("Format", ["Paperback (B&W)", "Paperback (Color)", "eBook"], index=0)

        is_ebook = pc_type == "eBook"
        ink_type = "color" if pc_type == "Paperback (Color)" else "bw"

        pc_result = analyzer.calculate_profit(
            price=pc_price,
            page_count=pc_pages,
            is_ebook=is_ebook,
            ink_type=ink_type,
        )

        # Profit breakdown cards
        pm_cols = st.columns(4)
        with pm_cols[0]:
            st.metric("Royalty Rate", f"{pc_result['royalty_rate']*100:.0f}%")
        with pm_cols[1]:
            st.metric("Printing + Delivery", f"${pc_result['print_cost'] + pc_result['delivery_fee']:.2f}")
        with pm_cols[2]:
            st.metric("Net Profit", f"${pc_result['net_profit']:.2f}",
                      delta=f"${pc_result['net_profit'] - 0:.2f}")
        with pm_cols[3]:
            margin_color = "normal" if pc_result['profit_margin_pct'] >= 30 else "inverse" if pc_result['profit_margin_pct'] < 15 else "normal"
            st.metric("Profit Margin", f"{pc_result['profit_margin_pct']:.1f}%")

        # Bulk calculator
        with st.expander("Bulk pricing chart (evaluate multiple prices)"):
            prices = list(range(5, 35, 2))
            bulk_data = []
            for p in prices:
                r = analyzer.calculate_profit(float(p), page_count=pc_pages, is_ebook=is_ebook, ink_type=ink_type)
                bulk_data.append({"Price": p, "Net Profit": r["net_profit"], "Margin %": r["profit_margin_pct"]})
            bulk_df = _pd.DataFrame(bulk_data)
            st.dataframe(bulk_df, use_container_width=True, hide_index=True,
                         column_config={
                             "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                             "Net Profit": st.column_config.NumberColumn("Net Profit", format="$%.2f"),
                             "Margin %": st.column_config.NumberColumn("Margin %", format="%.1f%%"),
                         })
            st.caption("Shows how net profit scales with different sale prices.")

        # Apply to current results
        if st.session_state.get("pipeline_results") and st.session_state["pipeline_results"].get("ranked_rows"):
            if st.button("Apply Profit Calculator to Current Results", use_container_width=True):
                rows = st.session_state["pipeline_results"]["ranked_rows"]
                df = _pd.DataFrame(rows)
                df = analyzer.add_profit_columns(df, page_count=pc_pages)
                st.session_state["pipeline_results"]["ranked_rows"] = df.to_dict(orient="records")
                stash_log(f"Profit columns applied (page count: {pc_pages}).")
                st.success(f"Profit columns added! Check the Data Table tab.")
                st.rerun()

    # -----------------------------------------------------------------------
    # Explorer Tab B: Keyword Explorer
    # -----------------------------------------------------------------------
    with explorer_tabs[1]:
        st.markdown("### Keyword Explorer")
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
            "Discover high-value keywords from competitor titles & Amazon suggestions.</div>",
            unsafe_allow_html=True,
        )

        kw_cols = st.columns([3, 1])
        with kw_cols[0]:
            kw_query = st.text_input("Keyword to explore", placeholder="e.g. low carb cookbook", label_visibility="collapsed")
        with kw_cols[1]:
            kw_go = st.button("Explore Keywords", type="primary", use_container_width=True)

        if kw_go and kw_query.strip():
            with st.spinner("Fetching Amazon suggestions & analyzing competitor keywords..."):
                # Amazon suggestions (free API)
                suggestions = scraper.fetch_amazon_suggestions(kw_query.strip(), limit=10)
                st.session_state["kw_suggestions"] = suggestions

                # Extract keywords from current results
                pipeline_data = st.session_state.get("pipeline_results")
                tunnel_data = st.session_state.get("tunnel_results")
                titles = []
                if pipeline_data and pipeline_data.get("ranked_rows"):
                    titles.extend(r.get("Title", "") for r in pipeline_data["ranked_rows"])
                if tunnel_data and tunnel_data.get("filtered_rows"):
                    titles.extend(r.get("Title", "") for r in tunnel_data["filtered_rows"])

                keywords = analyzer.extract_keywords_from_titles(titles) if titles else []
                st.session_state["kw_gaps"] = keywords

                stash_log(f"Keyword explorer: {len(suggestions)} suggestions, {len(keywords)} extracted keywords.")

        # Display Amazon suggestions
        if st.session_state["kw_suggestions"]:
            st.markdown("#### Amazon Search Suggestions")
            suggs = st.session_state["kw_suggestions"]
            sugg_cols = st.columns(2)
            for i, s in enumerate(suggs):
                with sugg_cols[i % 2]:
                    if st.button(f"🔍 {s}", key=f"sugg_{i}", use_container_width=True):
                        st.session_state["search_override"] = s
                        st.rerun()

        # Display extracted keywords
        if st.session_state["kw_gaps"]:
            st.markdown("#### Keywords from Competitor Titles")
            kw_df = _pd.DataFrame(st.session_state["kw_gaps"])
            st.dataframe(
                kw_df[["keyword", "type", "count", "frequency"]].head(30),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "keyword": st.column_config.TextColumn("Keyword"),
                    "type": st.column_config.TextColumn("Type"),
                    "count": st.column_config.NumberColumn("Occurrences", format="%d"),
                    "frequency": st.column_config.NumberColumn("Frequency", format="%.0%"),
                },
            )

        # Keyword gap analysis
        st.markdown("#### Keyword Gap Analysis")
        gap_cols = st.columns([3, 1, 1])
        with gap_cols[0]:
            gap_comp_query = st.text_input("Competitor niche (e.g. high-traffic niche)", placeholder="competitive niche name", label_visibility="collapsed")
        with gap_cols[1]:
            gap_opp_query = st.text_input("Your niche (opportunity)", placeholder="your target niche", label_visibility="collapsed")
        with gap_cols[2]:
            gap_go = st.button("Find Gaps", use_container_width=True)

        if gap_go and gap_comp_query and gap_opp_query:
            with st.spinner("Analyzing keyword gaps..."):
                # Get competitor titles from DB history for the competitor niche
                comp_snap = database.get_latest_snapshot(gap_comp_query.strip())
                opp_snap = database.get_latest_snapshot(gap_opp_query.strip())

                comp_titles = []
                opp_titles = []
                if comp_snap and comp_snap.get("top_keywords"):
                    comp_titles = json.loads(comp_snap["top_keywords"])
                if opp_snap and opp_snap.get("top_keywords"):
                    opp_titles = json.loads(opp_snap["top_keywords"])

                if comp_titles and opp_titles:
                    gaps = analyzer.find_keyword_gaps(comp_titles, opp_titles)
                    if gaps:
                        st.markdown("**Keywords competitors use but you're missing:**")
                        gap_df = _pd.DataFrame(gaps)
                        st.dataframe(gap_df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No significant gaps found (gap_score > 0.1).")
                else:
                    st.info("Run Deep Tunnels on both niches first to build keyword profiles.")

    # -----------------------------------------------------------------------
    # Explorer Tab C: Category Browser
    # -----------------------------------------------------------------------
    with explorer_tabs[2]:
        st.markdown("### Amazon KDP Category Browser")
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
            "Browse Amazon book categories and find underserved sub-categories.</div>",
            unsafe_allow_html=True,
        )

        categories = scraper.fetch_category_tree()
        if categories:
            # Build a tree view
            cat_df = _pd.DataFrame(categories)
            st.dataframe(
                cat_df[["id", "name", "parent_id"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.TextColumn("Browse Node ID"),
                    "name": st.column_config.TextColumn("Category Name"),
                    "parent_id": st.column_config.TextColumn("Parent ID"),
                },
            )
            st.caption(f"{len(categories)} top-level book categories. Use the Browse Node ID in Amazon URL filters.")

            # Quick analysis: pick a category to analyze
            st.markdown("#### Analyze Category Potential")
            cat_choice = st.selectbox(
                "Select a category to explore",
                options=[c["name"] for c in categories],
                index=0,
            )
            if st.button("Search This Category", use_container_width=True):
                chosen = next((c for c in categories if c["name"] == cat_choice), None)
                if chosen:
                    search_term = f"{chosen['name']} books"
                    st.session_state["search_override"] = search_term
                    stash_log(f"Category browser: launching search for '{search_term}'")
                    st.rerun()

    # -----------------------------------------------------------------------
    # Explorer Tab D: Niche Tracker & Batch Comparison
    # -----------------------------------------------------------------------
    with explorer_tabs[3]:
        st.markdown("### Niche Trend Tracker")
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
            "Track niche metrics week-over-week to spot trends early.</div>",
            unsafe_allow_html=True,
        )

        nt_cols = st.columns([3, 1])
        with nt_cols[0]:
            nt_query = st.text_input("Niche query to track", placeholder="e.g. keto cookbook", label_visibility="collapsed")
        with nt_cols[1]:
            nt_go = st.button("Track Niche", type="primary", use_container_width=True)

        if nt_go and nt_query.strip():
            q = nt_query.strip()
            history = database.get_snapshot_history(q, limit=10)
            st.session_state["niche_tracker_query"] = q
            st.session_state["niche_tracker_history"] = history

        # Display history
        nt_query_active = st.session_state.get("niche_tracker_query", "")
        nt_history = st.session_state.get("niche_tracker_history", [])

        if nt_query_active and nt_history:
            st.markdown(f"**Tracking: {nt_query_active}** — {len(nt_history)} snapshot(s)")

            hist_df = _pd.DataFrame(nt_history)
            if not hist_df.empty:
                hist_df["snapshot_date"] = _pd.to_datetime(hist_df["snapshot_date"])
                hist_df = hist_df.sort_values("snapshot_date")

                # Week-over-week metrics
                st.dataframe(
                    hist_df[["snapshot_date", "product_count", "avg_price", "avg_eos", "avg_profit", "gem_count"]],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "snapshot_date": st.column_config.DateColumn("Date"),
                        "product_count": st.column_config.NumberColumn("Products", format="%d"),
                        "avg_price": st.column_config.NumberColumn("Avg Price", format="$%.2f"),
                        "avg_eos": st.column_config.NumberColumn("Avg EOS", format="%.1f"),
                        "avg_profit": st.column_config.NumberColumn("Avg Profit", format="$%.2f"),
                        "gem_count": st.column_config.NumberColumn("Gems", format="%d"),
                    },
                )

                # WoW comparison
                if len(hist_df) >= 2:
                    st.markdown("#### Week-over-Week Comparison")
                    latest = hist_df.iloc[-1]
                    previous = hist_df.iloc[-2]

                    wow_cols = st.columns(4)
                    with wow_cols[0]:
                        prod_change = latest["product_count"] - previous["product_count"]
                        st.metric("Product Count", int(latest["product_count"]),
                                  delta=f"{prod_change:+d}" if prod_change != 0 else "—")
                    with wow_cols[1]:
                        eos_change = latest["avg_eos"] - previous["avg_eos"]
                        st.metric("Avg EOS", f"{latest['avg_eos']:.1f}",
                                  delta=f"{eos_change:+.1f}" if abs(eos_change) > 0.1 else "—")
                    with wow_cols[2]:
                        profit_change = latest["avg_profit"] - previous["avg_profit"]
                        st.metric("Avg Profit", f"${latest['avg_profit']:.2f}",
                                  delta=f"${profit_change:+.2f}" if abs(profit_change) > 0.01 else "—")
                    with wow_cols[3]:
                        gem_change = int(latest["gem_count"]) - int(previous["gem_count"])
                        st.metric("Gems", int(latest["gem_count"]),
                                  delta=f"{gem_change:+d}" if gem_change != 0 else "—")

                    # Trend signal
                    trend = analyzer.compute_trend_signal(
                        int(latest["product_count"]),
                        int(previous["product_count"]),
                    )
                    signal_map = {0.2: "⚠️ Fast Growing (Low Signal)", 0.5: "→ Moderate Growth",
                                  0.8: "✅ Stable (Strong Signal)", 0.9: "✅ Shrinking (Best Signal)"}
                    st.info(f"**Trend Signal:** {signal_map.get(trend, f'{trend:.1f}')}")
        elif nt_query_active and not nt_history:
            st.info(f"No snapshots yet for '{nt_query_active}'. Run a Deep Tunnel on this niche first to create snapshots.")

        # Manually trigger a snapshot from current results
        pipeline_data = st.session_state.get("pipeline_results")
        if pipeline_data and pipeline_data.get("ranked_rows") and not pipeline_data.get("error"):
            if st.button("Save Current Results as Snapshot", use_container_width=True):
                rows = pipeline_data["ranked_rows"]
                titles = [r.get("Title", "") for r in rows]
                prices = [r.get("Price", 0) or 0 for r in rows]
                eoss = [r.get("EOS", 0) or 0 for r in rows]
                viss = [r.get("Visibility_Score", 0) or 0 for r in rows]
                profs = [r.get("Net_Profit", 0) or 0 for r in rows]
                import statistics
                top_kw = json.dumps([k["keyword"] for k in analyzer.extract_keywords_from_titles(titles)[:10]])
                snap_id = database.save_niche_snapshot(
                    query=query,
                    product_count=len(rows),
                    avg_price=round(statistics.mean(prices), 2),
                    avg_eos=round(statistics.mean(eoss), 1),
                    avg_visibility=round(statistics.mean(viss), 1),
                    avg_profit=round(statistics.mean(profs), 2),
                    gem_count=len(pipeline_data.get("gems", [])),
                    top_keywords=top_kw,
                )
                if snap_id:
                    stash_log(f"Niche snapshot saved (ID: {snap_id}) for query '{query}'.")
                    st.success(f"Snapshot saved! Go to Niche Tracker to view history.")
                else:
                    st.error("Failed to save snapshot.")

    # -----------------------------------------------------------------------
    # Explorer Tab E: Niche Idea Generator (like MerchMetrix)
    # -----------------------------------------------------------------------
    with st.expander(":bulb: Niche Idea Generator"):
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
            "Generate 10+ related micro-niche ideas from a seed keyword. "
            "Uses prefix/suffix expansion, theme cross-matching, and angle combinations.</div>",
            unsafe_allow_html=True,
        )
        ng_cols = st.columns([3, 1])
        with ng_cols[0]:
            ng_keyword = st.text_input(
                "Seed keyword",
                placeholder="e.g. coloring book, keto cookbook",
                label_visibility="collapsed",
                key="niche_gen_input",
            )
        with ng_cols[1]:
            ng_go = st.button("Generate Ideas", type="primary", use_container_width=True, key="niche_gen_btn")

        if ng_go and ng_keyword.strip():
            ideas = analyzer.generate_niche_ideas(ng_keyword.strip(), max_ideas=12)
            st.markdown(f"**{len(ideas)} niche ideas generated from '{ng_keyword}'**")
            for idx, idea in enumerate(ideas):
                diff_color = {"Low": "#4CAF50", "Medium": "#FF9800", "High": "#f44336"}.get(
                    idea["difficulty"], "#888"
                )
                st.markdown(
                    f"<div style='background:rgba(255,255,255,0.03);border-radius:8px;"
                    f"padding:10px 14px;margin:6px 0;border-left:3px solid {diff_color};'>"
                    f"<div style='display:flex;align-items:center;gap:8px;'>"
                    f"<span style='font-weight:600;font-size:1rem;'>{idea['idea']}</span>"
                    f"<span style='background:{diff_color};color:#fff;font-size:0.7rem;"
                    f"padding:2px 8px;border-radius:10px;'>{idea['difficulty']}</span>"
                    f"</div>"
                    f"<div style='font-size:0.8rem;color:#aaa;margin-top:4px;'>{idea['angle']}</div>"
                    f"<div style='font-size:0.75rem;color:#777;'>{idea['reason']}</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                if st.button(f"Search '{idea['idea']}'", key=f"ng_search_{idx}", use_container_width=True):
                    st.session_state["search_override"] = idea["idea"]
                    st.rerun()

    # -----------------------------------------------------------------------
    # Explorer Tab F: Trademark Safety Checker
    # -----------------------------------------------------------------------
    with st.expander(":warning: Trademark Safety Check"):
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
            "Check keywords for trademarked or restricted terms before publishing. "
            "Curated list of common KDP trademark risks.</div>",
            unsafe_allow_html=True,
        )
        tm_cols = st.columns([3, 1])
        with tm_cols[0]:
            tm_keyword = st.text_input(
                "Keyword to check",
                placeholder="e.g. keto cookbook for beginners",
                label_visibility="collapsed",
                key="tm_input",
            )
        with tm_cols[1]:
            tm_go = st.button("Check Trademark", type="primary", use_container_width=True, key="tm_btn")

        if tm_go and tm_keyword.strip():
            result = analyzer.check_trademark(tm_keyword.strip())
            if result["is_safe"]:
                st.success(result["message"])
            elif result["risk_level"] == "high":
                st.error(result["message"])
            else:
                st.warning(result["message"])

        # Auto-scan top keywords from current results
        pipeline_data_tm = st.session_state.get("pipeline_results")
        if pipeline_data_tm and pipeline_data_tm.get("ranked_rows"):
            if st.button("Auto-Scan Current Results for Trademark Risks", use_container_width=True, key="tm_auto"):
                titles = [r.get("Title", "") for r in pipeline_data_tm["ranked_rows"][:20]]
                flagged_any = False
                for title in titles:
                    result = analyzer.check_trademark(title)
                    if not result["is_safe"]:
                        flagged_any = True
                        risk_icon = ":red_circle:" if result["risk_level"] == "high" else ":warning:"
                        st.markdown(
                            f"<div style='font-size:0.85rem;margin:4px 0;'>"
                            f"{risk_icon} <strong>{title[:60]}</strong> — "
                            f"{', '.join(result['flagged_terms'])}</div>",
                            unsafe_allow_html=True,
                        )
                if not flagged_any:
                    st.success("No trademark issues detected in the top 20 products.")

    # -----------------------------------------------------------------------
    # Explorer Tab G: Multi-Format Profit Comparison (KDP specific)
    # -----------------------------------------------------------------------
    with st.expander(":money_with_wings: Multi-Format Profit Comparison"):
        st.markdown(
            "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
            "Compare net profit across paperback, hardcover, and eBook formats side-by-side. "
            "Find the most profitable format for each price point.</div>",
            unsafe_allow_html=True,
        )
        mf_cols = st.columns([1, 1, 1])
        with mf_cols[0]:
            mf_price = st.number_input(
                "Sale Price ($)", min_value=0.99, max_value=200.0, value=9.99, step=0.50,
                key="mf_price",
            )
        with mf_cols[1]:
            mf_pages = st.number_input(
                "Page Count", min_value=24, max_value=1200, value=200, step=10,
                key="mf_pages",
            )
        with mf_cols[2]:
            mf_ink = st.selectbox(
                "Ink Type", ["B&W", "Color"], index=0, key="mf_ink",
            )

        ink = "color" if mf_ink == "Color" else "bw"

        # Calculate for all formats
        formats = {
            "Paperback": analyzer.calculate_profit(mf_price, mf_pages, is_ebook=False, ink_type=ink),
            "eBook": analyzer.calculate_profit(mf_price, mf_pages, is_ebook=True, ink_type=ink),
            "Hardcover": analyzer.calculate_profit(mf_price, mf_pages, is_ebook=False, ink_type=ink),
        }

        # Adjust hardcover costs (higher printing)
        hc = formats["Hardcover"]
        hc_print = hc.get("print_cost", 0) + 2.00  # Hardcover premium
        hc_net = round(hc.get("royalty", 0) - hc_print, 2)
        hc_margin = round((hc_net / mf_price) * 100, 1) if mf_price > 0 else 0
        formats["Hardcover"]["print_cost"] = round(hc.get("print_cost", 0) + 2.00, 2)
        formats["Hardcover"]["net_profit"] = hc_net
        formats["Hardcover"]["profit_margin_pct"] = hc_margin

        # Display comparison table
        comp_data = []
        for fmt_name, fmt_data in formats.items():
            comp_data.append({
                "Format": fmt_name,
                "Royalty Rate": f"{fmt_data['royalty_rate']*100:.0f}%",
                "Royalty": fmt_data["royalty"],
                "Print Cost": fmt_data["print_cost"],
                "Delivery": fmt_data["delivery_fee"],
                "Net Profit": fmt_data["net_profit"],
                "Margin %": fmt_data["profit_margin_pct"],
            })

        comp_df = _pd.DataFrame(comp_data)
        st.dataframe(
            comp_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Format": st.column_config.TextColumn("Format"),
                "Royalty Rate": st.column_config.TextColumn("Royalty Rate"),
                "Royalty": st.column_config.NumberColumn("Royalty", format="$%.2f"),
                "Print Cost": st.column_config.NumberColumn("Print Cost", format="$%.2f"),
                "Delivery": st.column_config.NumberColumn("Delivery", format="$%.2f"),
                "Net Profit": st.column_config.NumberColumn("Net Profit", format="$%.2f"),
                "Margin %": st.column_config.NumberColumn("Margin %%", format="%.1f%%"),
            },
        )

        # Best format recommendation
        best_format = max(comp_data, key=lambda r: r["Net Profit"])
        st.success(
            f":trophy: **Best Format: {best_format['Format']}** "
            f"— Net Profit: ${best_format['Net Profit']:.2f} "
            f"({best_format['Margin %']:.1f}% margin at ${mf_price:.2f})"
        )

        # Bulk scenario: show best format per price point (bulk modeling)
        st.markdown("**Bulk Scenario — Best Format per Price**")
        prices_range = list(range(3, 31, 2))
        bulk_rows = []
        for p in prices_range:
            pb = analyzer.calculate_profit(float(p), mf_pages, is_ebook=False, ink_type=ink)
            eb = analyzer.calculate_profit(float(p), mf_pages, is_ebook=True, ink_type=ink)
            hc_b = analyzer.calculate_profit(float(p), mf_pages, is_ebook=False, ink_type=ink)
            hc_print_b = hc_b.get("print_cost", 0) + 2.00
            hc_net_b = round(hc_b.get("royalty", 0) - hc_print_b, 2)

            format_profits = [
                ("Paperback", pb["net_profit"]),
                ("eBook", eb["net_profit"]),
                ("Hardcover", hc_net_b),
            ]
            best = max(format_profits, key=lambda r: r[1])
            bulk_rows.append({
                "Price": p,
                "Paperback $": pb["net_profit"],
                "eBook $": eb["net_profit"],
                "Hardcover $": hc_net_b,
                "Best Format": best[0],
                "Best Profit $": best[1],
            })
        bulk_df = _pd.DataFrame(bulk_rows)
        st.dataframe(
            bulk_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                "Paperback $": st.column_config.NumberColumn("Paperback", format="$%.2f"),
                "eBook $": st.column_config.NumberColumn("eBook", format="$%.2f"),
                "Hardcover $": st.column_config.NumberColumn("Hardcover", format="$%.2f"),
                "Best Format": st.column_config.TextColumn("Best Format"),
                "Best Profit $": st.column_config.NumberColumn("Best Profit", format="$%.2f"),
            },
        )
        st.caption("Shows which format maximizes profit at each price point.")

    # Batch Multi-Query Comparison (at bottom of Explorer tab)
    st.markdown("---")
    st.markdown("### :bar_chart: Batch Niche Comparison")
    st.markdown(
        "<div style='color:#777;font-size:0.85rem;margin-bottom:8px;'>"
        "Run the same pipeline across multiple queries and compare results side-by-side.</div>",
        unsafe_allow_html=True,
    )
    batch_input = st.text_area(
        "Enter one query per line",
        placeholder="keto cookbook\nlow carb cookbook\npaleo diet book\nvegan cookbook\nmediterranean diet",
        height=100,
        label_visibility="collapsed",
    )
    batch_cols = st.columns([1, 2])
    with batch_cols[0]:
        batch_go = st.button("Run Batch Comparison", type="primary", use_container_width=True)
    with batch_cols[1]:
        if st.button("Clear Batch Results", use_container_width=True):
            st.session_state["batch_results"] = []

    if batch_go and batch_input.strip():
        queries = [q.strip() for q in batch_input.split("\\n") if q.strip()]
        if len(queries) < 2:
            st.warning("Enter at least 2 queries (one per line).")
        else:
            st.session_state["batch_results"] = []
            batch_progress = st.progress(0, text=f"Running batch: 0/{len(queries)}")
            api_key = config_manager.get_serpapi_key()
            for i, q in enumerate(queries):
                stash_log(f"Batch: running '{q}' ({i+1}/{len(queries)})...")
                try:
                    # Quick single-page scrape + score
                    rows = scraper.search_and_format(
                        query=q,
                        api_key=api_key,
                        domain=domain_label,
                        save=False,
                        filter_params=filter_params if not quick_start else {},
                    )
                    if rows:
                        import pandas as _pd_batch
                        df = _pd_batch.DataFrame(rows)
                        df["Price"] = _pd_batch.to_numeric(df.get("Price", 0), errors="coerce").fillna(0)
                        df = analyzer.find_gems_dataframe(df)
                        df = analyzer.add_profit_columns(df)
                        scored = df.to_dict(orient="records")
                        gem_count = sum(1 for r in scored if r.get("ReviewCount", 999) < 30)
                        avg_eos = _pd_batch.to_numeric(df.get("EOS", 0), errors="coerce").mean()
                        avg_profit = _pd_batch.to_numeric(df.get("Net_Profit", 0), errors="coerce").mean()
                        st.session_state["batch_results"].append({
                            "query": q,
                            "products": len(scored),
                            "gems": gem_count,
                            "avg_eos": round(avg_eos, 1),
                            "avg_profit": round(avg_profit, 2),
                            "error": None,
                        })
                    else:
                        st.session_state["batch_results"].append({
                            "query": q, "products": 0, "gems": 0,
                            "avg_eos": 0, "avg_profit": 0,
                            "error": "No results",
                        })
                except Exception as exc:
                    st.session_state["batch_results"].append({
                        "query": q, "products": 0, "gems": 0,
                        "avg_eos": 0, "avg_profit": 0,
                        "error": str(exc),
                    })
                batch_progress.progress((i + 1) / len(queries), text=f"Running batch: {i+1}/{len(queries)}")
            batch_progress.progress(1.0, text="Batch complete!")
            stash_log(f"Batch comparison complete — {len(queries)} queries processed.")
            st.rerun()

    # Display batch results
    if st.session_state["batch_results"]:
        batch_df = _pd.DataFrame(st.session_state["batch_results"])
        st.markdown(f"**Batch Results** — {len(batch_df)} queries")
        st.dataframe(
            batch_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "query": st.column_config.TextColumn("Query"),
                "products": st.column_config.NumberColumn("Products", format="%d"),
                "gems": st.column_config.NumberColumn("Gold Gems", format="%d"),
                "avg_eos": st.column_config.NumberColumn("Avg EOS", format="%.1f"),
                "avg_profit": st.column_config.NumberColumn("Avg Profit", format="$%.2f"),
                "error": st.column_config.TextColumn("Error"),
            },
        )
        # Highlight best niche
        valid = [r for r in st.session_state["batch_results"] if not r.get("error")]
        if valid:
            best = max(valid, key=lambda r: r.get("avg_eos", 0) * 0.6 + r.get("gems", 0) * 10)
            st.success(
                f":trophy: **Best niche: \"{best['query']}\"** "
                f"— {best['gems']} gold gems, avg EOS {best['avg_eos']}, "
                f"avg profit ${best['avg_profit']:.2f}"
            )


# =========================================================================
# TAB 2: Visual Gallery
# =========================================================================
tab_gallery = tabs[2]

with tab_gallery:
    st.markdown("# :art: Visual Product Gallery")
    st.markdown(
        "<div style='color:#777;margin-top:-12px;margin-bottom:20px;'>"
        "Browse products in a visual card layout with thumbnails</div>",
        unsafe_allow_html=True,
    )
    _display_gallery(st.session_state.get("pipeline_results"), st.session_state.get("tunnel_results"))


# =========================================================================
# TAB 3: Design Studio (simplified with Imagen integration)
# =========================================================================
tab_design = tabs[3]

with tab_design:
    st.markdown("# :art: Design Intelligence Studio")
    st.markdown(
        "<div style='color:#777;margin-top:-12px;margin-bottom:20px;'>"
        "AI art prompts, image generation, design resources — all in one place</div>",
        unsafe_allow_html=True,
    )

    # Import design engine
    try:
        from core import design_engine
        HAS_DESIGN = True
    except ImportError:
        HAS_DESIGN = False
        st.error("Design engine not available. Ensure src/core/design_engine.py exists.")

    # Import Canva integration (optional)
    try:
        from core import canva_integration
        HAS_CANVA = True
    except ImportError:
        HAS_CANVA = False

    if HAS_DESIGN:
        design_tabs = st.tabs(["🎨 Prompt & Image Generator", "🔗 Design Resources", "🤖 AI Assistant"])

        # ------------------------------------------------------------------
        # TAB A: Unified Prompt Generator + Image Generation
        # ------------------------------------------------------------------
        with design_tabs[0]:
            st.markdown("### 🎯 AI Art Prompt & Image Generator")
            st.markdown(
                "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
                "Generate prompts for Midjourney / Stable Diffusion, or generate images directly via Google Imagen.</div>",
                unsafe_allow_html=True,
            )

            pg_cols = st.columns([2, 1, 1])

            with pg_cols[0]:
                pg_niche = st.text_input(
                    "Niche / Subject",
                    placeholder="e.g. yoga anatomy, keto cookbook, mandala patterns",
                    help="The main topic of your book",
                    key="pg_niche_simple",
                )

            with pg_cols[1]:
                pg_style = st.selectbox(
                    "Book Style",
                    options=design_engine.get_style_options(),
                    index=0,
                    key="pg_style_simple",
                )

            with pg_cols[2]:
                pg_age = st.selectbox(
                    "Age Group",
                    options=design_engine.get_age_options(),
                    index=5,
                    key="pg_age_simple",
                )

            pg_cols2 = st.columns([1, 1, 1])

            with pg_cols2[0]:
                pg_complexity = st.selectbox(
                    "Complexity",
                    options=design_engine.get_complexity_options(),
                    index=1,
                    key="pg_complexity_simple",
                )

            with pg_cols2[1]:
                pg_platform = st.selectbox(
                    "Platform",
                    options=["midjourney", "stablediffusion", "imagen"],
                    index=0,
                    key="pg_platform_simple",
                    help="Midjourney/SD = text prompts | Imagen = generate actual images",
                )

            with pg_cols2[2]:
                pg_page_type = st.radio(
                    "Page Type",
                    options=["Interior Page", "Cover"],
                    index=0,
                    horizontal=True,
                    key="pg_page_type_simple",
                )

            # --- Generate Buttons ---
            btn_cols = st.columns([1, 1, 1])

            with btn_cols[0]:
                gen_clicked = st.button(
                    "Generate Prompt",
                    type="primary",
                    use_container_width=True,
                    key="gen_prompt_simple",
                )

            with btn_cols[1]:
                generate_image = st.button(
                    "Generate Image Now",
                    type="secondary",
                    use_container_width=True,
                    key="gen_image_simple",
                    disabled=(pg_platform != "imagen"),
                    help="Only available when Platform is 'imagen'",
                )

            with btn_cols[2]:
                if HAS_CANVA:
                    _canva_url = canva_integration.get_template_url(pg_style)
                    if _canva_url:
                        st.markdown(
                            f"<a href='{_canva_url}' target='_blank' "
                            f"style='display:block;text-align:center;padding:8px;"
                            f"background:#1a3a3a;border:1px solid #00C4CC;"
                            f"border-radius:8px;color:#fff;text-decoration:none;'>"
                            f"Open Canva</a>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.caption("Set Canva URL in config.ini")
                else:
                    st.caption("")

            # --- Google Cloud settings for Imagen ---
            if pg_platform == "imagen":
                with st.expander(":cloud: Imagen Settings", expanded=False):
                    st.markdown(
                        "<div style='color:#888;font-size:0.8rem;margin-bottom:8px;'>"
                        "Enter your Google Cloud credentials for Imagen image generation. "
                        f"Cost: ~<b>${design_engine._IMAGEN_PRICE_PER_IMAGE:.3f}</b> per image.</div>",
                        unsafe_allow_html=True,
                    )
                    gc_cols = st.columns(2)
                    with gc_cols[0]:
                        gc_api_key = st.text_input(
                            "Google API Key",
                            type="password",
                            placeholder="AIza... or AQ...",
                            key="gc_api_key",
                            help="API key from Google Cloud Console → APIs & Services → Credentials",
                        )
                    with gc_cols[1]:
                        gc_project = st.text_input(
                            "Project ID",
                            placeholder="my-gcp-project",
                            key="gc_project",
                            help="Your Google Cloud project ID (not the name)",
                        )

                    gc_cols2 = st.columns(2)
                    with gc_cols2[0]:
                        gc_model = st.selectbox(
                            "Model",
                            options=design_engine.get_imagen_models(),
                            index=0,
                            key="gc_model",
                        )
                    with gc_cols2[1]:
                        gc_aspect = st.selectbox(
                            "Aspect Ratio",
                            options=design_engine.get_imagen_aspect_ratios(),
                            index=0,
                            key="gc_aspect",
                        )

            # --- Handle Generate Prompt ---
            if gen_clicked:
                if not pg_niche.strip():
                    st.warning("Please enter a niche or subject.")
                else:
                    with st.spinner("Constructing optimized prompt..."):
                        result = design_engine.generate_prompt(
                            niche=pg_niche.strip(),
                            age_group=pg_age,
                            style=pg_style,
                            complexity=pg_complexity,
                            platform=pg_platform,
                            interior_page=(pg_page_type == "Interior Page"),
                        )

                    st.markdown("---")
                    st.markdown("### :clipboard: Generated Prompt")

                    st.markdown("**Full Prompt:**")
                    st.code(result["full_prompt"], language="text")

                    st.markdown("**Cover Variant:**")
                    st.code(result["cover_prompt"], language="text")

                    with st.expander(":mag: Breakdown"):
                        st.markdown(f"""
                        | Component | Value |
                        |---|---|
                        | **Subject** | `{pg_niche}` |
                        | **Style** | `{result['style']}` |
                        | **Age** | `{result['age_group']}` |
                        | **Complexity** | `{result['complexity']}` |
                        | **Platform** | `{result['platform']}` |
                        """)
                        if result.get("cost_estimate"):
                            st.markdown(f"| **Cost/Image** | `${result['cost_estimate']:.3f} |")

                    st.success("Prompt ready! Copy and paste into your AI art tool.")

            # --- Handle Generate Image (Imagen) ---
            if generate_image:
                if not pg_niche.strip():
                    st.warning("Please enter a niche or subject.")
                elif not gc_api_key.strip() or not gc_project.strip():
                    st.warning("Enter Google API Key and Project ID in Imagen Settings.")
                else:
                    with st.spinner("Generating prompt..."):
                        result = design_engine.generate_prompt(
                            niche=pg_niche.strip(),
                            age_group=pg_age,
                            style=pg_style,
                            complexity=pg_complexity,
                            platform="imagen",
                            interior_page=(pg_page_type == "Interior Page"),
                        )
                    prompt_text = result["prompt"]

                    st.markdown("---")
                    st.markdown("### :frame_with_picture: Generating Image…")
                    st.code(prompt_text, language="text")
                    st.caption(f"Estimated cost: ${design_engine._IMAGEN_PRICE_PER_IMAGE:.3f}")

                    img_result = design_engine.generate_image(
                        prompt=prompt_text,
                        api_key=gc_api_key.strip(),
                        project=gc_project.strip(),
                        model=gc_model,
                        sample_count=1,
                        aspect_ratio=gc_aspect,
                    )

                    if img_result and "images" in img_result:
                        for i, b64 in enumerate(img_result["images"]):
                            st.image(
                                base64.b64decode(b64),
                                caption=f"Image {i + 1} — Cost: ${img_result.get('cost', 0):.3f}",
                                use_column_width=True,
                            )
                        st.success(
                            f"Generated {img_result['count']} image(s) — Total cost: "
                            f"**${img_result.get('cost', 0):.3f}**"
                        )

                        # Download button for the first image
                        st.download_button(
                            label="Download Image (PNG)",
                            data=base64.b64decode(img_result["images"][0]),
                            file_name=f"{pg_niche.strip().lower().replace(' ', '_')}_imagen.png",
                            mime="image/png",
                            key="dl_imagen_img",
                        )
                    else:
                        err = img_result.get("error", "Unknown error") if img_result else "No response"
                        st.error(f"Image generation failed: {err}")

        # ------------------------------------------------------------------
        # TAB B: Design Resources + Canva
        # ------------------------------------------------------------------
        with design_tabs[1]:
            st.markdown("### 🔗 Design Resources")
            st.markdown(
                "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
                "Search external platforms for design assets, templates, and inspiration.</div>",
                unsafe_allow_html=True,
            )

            dr_keywords = st.text_input(
                "Search Keywords",
                placeholder="e.g. yoga coloring book cover",
                key="dr_keywords_simple",
            )

            if dr_keywords.strip():
                st.markdown("#### Quick Links")
                links_cols = st.columns(3)

                for idx, (fn, label, icon) in enumerate([
                    (design_engine.build_creative_fabrica_link, "Creative Fabrica", "🎨"),
                    (design_engine.build_canva_link, "Canva Templates", "🖌️"),
                    (design_engine.build_amazon_link, "Amazon Bestsellers", "📚"),
                ]):
                    link = fn(dr_keywords.strip())
                    with links_cols[idx]:
                        st.markdown(
                            f"<a href='{link['url']}' target='_blank' "
                            f"style='display:block;background:#1e2538;border:1px solid #2a3355;"
                            f"border-radius:10px;padding:16px;text-align:center;text-decoration:none;"
                            f"transition:0.2s;'>"
                            f"<div style='font-size:1.8rem;margin-bottom:6px;'>{icon}</div>"
                            f"<div style='color:#4CAF50;font-weight:600;font-size:0.95rem;'>{link['label']}</div>"
                            f"<div style='color:#888;font-size:0.75rem;margin-top:4px;'>{link['description']}</div>"
                            f"</a>",
                            unsafe_allow_html=True,
                        )

                st.markdown("---")
                st.markdown(
                    "<div style='color:#888;font-size:0.8rem;'>"
                    ":bulb: Use Creative Fabrica for commercial graphics. "
                    "Use Canva for quick mockups. Use Amazon to research covers in your niche."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info("Enter keywords above to enable search links.")

            # --- Canva Bulk CSV ---
            st.markdown("---")
            st.markdown("### :bridge_at_night: Canva Bulk Import")
            st.markdown(
                "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
                "Generate a bulk import CSV for Canva Bulk Create.</div>",
                unsafe_allow_html=True,
            )

            canva_cols = st.columns([1, 1])

            with canva_cols[0]:
                csv_urls_input = st.text_area(
                    "Image URLs (one per line)",
                    placeholder="https://example.com/image1.jpg\nhttps://example.com/image2.jpg",
                    height=90,
                    key="csv_urls_simple",
                )
                csv_urls = [u.strip() for u in csv_urls_input.splitlines() if u.strip()]

                if st.button(
                    "Generate Bulk CSV",
                    type="secondary",
                    use_container_width=True,
                    key="gen_csv_simple",
                ):
                    if not csv_urls:
                        st.warning("Enter at least one image URL.")
                    else:
                        from core.exporter import generate_canva_bulk_csv
                        csv_path = generate_canva_bulk_csv(csv_urls)
                        if csv_path:
                            with open(csv_path, "rb") as f:
                                st.download_button(
                                    label="Download canva_bulk_import.csv",
                                    data=f,
                                    file_name="canva_bulk_import.csv",
                                    mime="text/csv",
                                    use_container_width=True,
                                    key="dl_csv_simple",
                                )
                            st.success("CSV ready! Upload to Canva → Bulk Create.")
                        else:
                            st.error("Failed to generate CSV.")

            with canva_cols[1]:
                manifest_book = st.text_input(
                    "Book Title (for manifest)",
                    placeholder="e.g. Mandala Magic",
                    key="manifest_simple",
                )
                if manifest_book.strip() and csv_urls and HAS_CANVA:
                    manifest_trim = "8.5x11"
                    entries = canva_integration.generate_image_entries_from_prompts(
                        niche=manifest_book.strip(),
                        num_pages=len(csv_urls),
                        image_urls=csv_urls,
                    )
                    manifest_csv = canva_integration.generate_design_manifest(
                        entries,
                        book_title=manifest_book.strip(),
                        trim_size=manifest_trim,
                    )
                    st.download_button(
                        label="Download Design Manifest CSV",
                        data=manifest_csv,
                        file_name=f"{manifest_book.strip().lower().replace(' ', '_')}_manifest.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="dl_manifest_simple",
                    )

        # ------------------------------------------------------------------
        # TAB C: AI Assistant (OpenAI Integration)
        # ------------------------------------------------------------------
        with design_tabs[2]:
            st.markdown("### 🤖 AI Prompt Assistant")
            st.markdown(
                "<div style='color:#777;font-size:0.85rem;margin-bottom:12px;'>"
                "Use OpenAI to generate or enhance prompts, descriptions, and book metadata. "
                "Requires an OpenAI API key (optional, separate from SerpApi).</div>",
                unsafe_allow_html=True,
            )

            # OpenAI key input
            oai_key = st.text_input(
                "OpenAI API Key",
                type="password",
                placeholder="sk-... (optional — get one at platform.openai.com)",
                help="Your OpenAI API key. Stored only for this session.",
                key="oai_key_input",
            )

            oai_model = st.selectbox(
                "Model",
                options=["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                index=0,
                key="oai_model",
            )

            oai_task = st.selectbox(
                "Task",
                options=[
                    "Write a KDP book description",
                    "Generate Midjourney prompt variations",
                    "Improve/enhance an existing prompt",
                    "Generate SEO keywords for this niche",
                    "Write a compelling book title",
                ],
                index=0,
                key="oai_task",
            )

            oai_context = st.text_area(
                "Context / Details",
                placeholder="Describe your book, niche, target audience, or paste an existing prompt...",
                height=120,
                key="oai_context",
            )

            if st.button("Generate with AI", type="primary", use_container_width=True, key="oai_gen_btn"):
                if not oai_key.strip():
                    st.warning("Please enter an OpenAI API key to use this feature.")
                elif not oai_context.strip():
                    st.warning("Please provide context about your book or niche.")
                else:
                    # Build system prompt based on task
                    system_prompts = {
                        "Write a KDP book description": (
                            "You are a professional KDP copywriter. Write compelling, SEO-optimized "
                            "book descriptions for Amazon KDP. Use persuasive language, bullet points "
                            "for key features, and include relevant keywords naturally."
                        ),
                        "Generate Midjourney prompt variations": (
                            "You are an expert prompt engineer for Midjourney v6. Generate 3 creative "
                            "variations of the given prompt. Each should include subject, style, lighting, "
                            "composition, and parameters (--ar 8.5:11 --v 6.0). Be specific and artistic."
                        ),
                        "Improve/enhance an existing prompt": (
                            "You are a professional AI prompt engineer. Review the user's prompt and "
                            "suggest improvements: add more specific descriptors, better lighting terms, "
                            "composition adjustments, and stylistic enhancements."
                        ),
                        "Generate SEO keywords for this niche": (
                            "You are an Amazon KDP keyword researcher. Generate 7 high-volume, "
                            "low-competition keyword phrases for Amazon search. Include both short-tail "
                            "and long-tail keywords. Explain why each keyword has potential."
                        ),
                        "Write a compelling book title": (
                            "You are a professional book title consultant for Amazon KDP. Generate 5 "
                            "compelling title options for the user's niche. Each should be searchable, "
                            "clickable, and differentiated from competitors. Explain the strategy."
                        ),
                    }

                    system_msg = system_prompts.get(oai_task, "You are a helpful AI assistant for KDP publishing.")
                    user_msg = oai_context.strip()

                    with st.spinner(f"Calling OpenAI {oai_model}..."):
                        response = design_engine.generate_with_openai(
                            system_prompt=system_msg,
                            user_message=user_msg,
                            api_key=oai_key.strip(),
                            model=oai_model,
                        )

                    if response and response.get("content"):
                        st.markdown("---")
                        st.markdown("### :robot_face: AI Response")
                        st.markdown(response["content"])

                        if response.get("model"):
                            st.caption(f"Model: {response['model']}")
                    elif response and response.get("error"):
                        st.error(f"AI generation failed: {response['error']}")
                    else:
                        st.error("No response received from AI. Check your API key and try again.")

    st.markdown("---")
    st.markdown(
        "<div style='text-align:center;color:#444;font-size:0.75rem;'>"
        "Design Intelligence Studio &mdash; Midjourney + Stable Diffusion + OpenAI"
        "</div>",
        unsafe_allow_html=True,
    )


# =========================================================================
# TAB 4: Settings
# =========================================================================
tab_settings = tabs[4]

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
# TAB 5: History
# =========================================================================
tab_history = tabs[5]

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
