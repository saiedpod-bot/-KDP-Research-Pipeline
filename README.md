<div align="center">
  <h1> KDP Research Pipeline</h1>
  <p><strong>Production-grade Amazon KDP market intelligence platform with tiered data providers, zero-cost pre-research, and a 0–100 Market Score algorithm.</strong></p>
  <br>
  <p>
    <a href="#-key-features">Features</a> •
    <a href="#-data-providers">Data Providers</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-configuration">Configuration</a> •
    <a href="#-project-structure">Structure</a>
  </p>
  <br>
  <p>
    <img src="https://img.shields.io/badge/Version-3.0-blue?style=flat-square" alt="Version 3.0">
    <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square&logo=python" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Streamlit-1.28+-red?style=flat-square&logo=streamlit" alt="Streamlit">
    <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Cross-platform">
  </p>
</div>

---

##  Key Features

###  Tiered Data Providers
Three interchangeable backends — swap at runtime via `PROVIDER_ACTIVE`:

| Provider | Best For | Speed | Cost | Data Quality |
|---|---|---|---|---|
| **Pangolinfo** | Urgent pre-scrapes | ~3s | 1 credit/query | 40–60 products, medium detail |
| **Apify** | Flexible crawling | 60–120s | ~$0.05/run | Customizable actor-based |
| **Oxylabs** | Deep analysis | ~10s | ~$0.01/query | Rich schema, parse: true |

Providers are swappable at runtime with **zero code changes** via the Settings tab or `PROVIDER_ACTIVE` env var.

###  Intelligent Caching (`src/core/cache.py`)
- SHA-256 hash keyed on `(query + provider_slug)` — each provider caches separately
- `get_or_scrape()` checks `cache/{hash}.json` before calling any API
- Integrated into `execute_with_fallback()` so **all providers benefit automatically**
- Zero API credits consumed on cache hits

###  Task-based Provider Router
- **`urgent`** (autocomplete / pre-search) → Pangolinfo (fastest, cheapest)
- **`deep`** (full analysis) → Oxylabs (richest data)
- **Fallback chain** — if primary fails, automatic retry with next configured provider

###  Pre-Research Engine (`src/core/pre_research.py`)
- **Zero-cost keyword discovery** via Google Suggest API (no credits consumed)
- `expand_keywords()` and `get_niche_suggestions()` — 10+ niche variations per seed term
- Quick Discover panel in the sidebar — select suggestions to auto-fill the pipeline

###  Market Score Algorithm (0–100)
Four-factor scoring engine in `src/core/analyzer.py`:

```
Score = Demand × 35% + Competition × 30% + Pricing × 15% - Dominance Penalty
```

- **Demand** (35%) — average review volume, total market size
- **Competition** (30%) — price variance, review distribution, brand concentration
- **Pricing** (15%) — average price, margin potential
- **Dominance Penalty** (-25%) — top-5 market share, best-seller concentration

Result: 0–100 score with verdict bands (Excellent / Great / Good / Okay / Weak / Poor).

###  Deep Analysis Report
Collapsible expander in the dashboard showing:
- Progress bars for each signal (Demand, Competition, Pricing, Dominance Penalty)
- Weighted contributions with max-score denominators
- Verdict badge (`st.success` / `st.info` / `st.warning` based on score band)

###  Validation Gate
Pipeline blocks unscoped keywords unless the user validates via Quick Discover or checks `Force Analysis` — prevents wasted API credits on exploratory queries.

###  Bilingual Interface (English / Arabic)
Full RTL support for Arabic-speaking KDP authors.

---

##  Data Providers

### Pangolinfo (`PROVIDER_ACTIVE=pangolinfo`)
- Endpoint: `scrapeapi.pangolinfo.com/api/v1/scrape`
- Source: `amzKeyword` — returns 40–60 products per query
- Auth: Bearer token (`PANGOLINFO_TOKEN`)
- Normalized fields: ASIN, Title, Price, Rating, ReviewCount, Sales

### Apify (`PROVIDER_ACTIVE=apify`)
- Actor: `junglee/Amazon-crawler` (ID: `BG3WDrGdteHgZgbPK`)
- REST API: starts actor run, polls until completion, fetches dataset
- Auth: `APIFY_TOKEN` + `APIFY_ACTOR_ID`
- Can take 60–120s on cold start — best for deep analysis

### Oxylabs (`PROVIDER_ACTIVE=oxylabs`)
- Endpoint: `realtime.oxylabs.io/v1/queries`
- Sources: `amazon_search` (keyword search, `parse: true`), `amazon_product` (ASIN deep-dive)
- Auth: Basic Auth (`OXYLABS_USERNAME` + `OXYLABS_PASSWORD`)
- Response structure: `results[0].content.results` is a dict with keys `organic`, `amazons_choices`, `paid`, `suggested`
- Product schema: `asin`, `title`, `price`, `rating` (star float), `reviews_count`, `url_image`, `best_seller`, `is_sponsored`

> Normalizer merges all sections (`organic` + `amazons_choices` + `paid`) into a flat list and maps Oxylabs field names to the unified schema.

---

##  Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core logic & orchestration |
| **UI Framework** | Streamlit 1.28+ | Interactive dashboard |
| **Data** | pandas, SQLite | Analysis & persistence |
| **Scraping API** | Pangolinfo / Apify / Oxylabs | Multi-provider data gathering |
| **Pre-Research** | Google Suggest (free) | Zero-cost keyword discovery |
| **Cache** | Local JSON (SHA-256 hashed) | Prevents redundant API calls |
| **Export** | gspread + google-auth | Google Sheets integration |

---

##  Quick Start

### Prerequisites
- Python 3.10 or higher ([download](https://python.org))
- At least one provider API key (see [Configuration](#configuration))

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/saiedpod-bot/-KDP-Research-Pipeline.git
cd kdp-research-pipeline

# 2. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure your API keys
cp config.ini.example config.ini
# Edit config.ini with your credentials (see Configuration section)
```

### Launch the Dashboard

```bash
streamlit run main.py
```

Your browser will open to `http://localhost:8501`.

---

##  Configuration

### config.ini

```ini
PROVIDER_ACTIVE=pangolinfo

PANGOLINFO_TOKEN=eyJ...

APIFY_TOKEN=apify_api_...
APIFY_ACTOR_ID=BG3WDrGdteHgZgbPK

OXYLABS_USERNAME=your_username
OXYLABS_PASSWORD=your_password

SERPAPI_KEY=your_serpapi_key_here
GOOGLE_SHEET_ID=

AMAZON_DOMAIN=amazon.com

MAX_PAGES=3
MIN_PRICE=7.00
```

| Setting | Required | Default | Description |
|---|---|---|---|
| `PROVIDER_ACTIVE` | **Yes** | `pangolinfo` | Active provider: `pangolinfo`, `apify`, or `oxylabs` |
| `PANGOLINFO_TOKEN` | For Pangolinfo | — | Bearer token from Pangolinfo dashboard |
| `APIFY_TOKEN` | For Apify | — | Apify API token |
| `APIFY_ACTOR_ID` | For Apify | `BG3WDrGdteHgZgbPK` | Amazon Crawler actor ID |
| `OXYLABS_USERNAME` | For Oxylabs | — | Oxylabs username (Basic Auth) |
| `OXYLABS_PASSWORD` | For Oxylabs | — | Oxylabs password (Basic Auth) |
| `SERPAPI_KEY` | Optional | — | Legacy SerpApi key (for tunnel features) |
| `GOOGLE_SHEET_ID` | No | — | Google Sheet ID for export |
| `AMAZON_DOMAIN` | No | `amazon.com` | Marketplace domain |
| `MAX_PAGES` | No | `3` | Search pages (1–20) |
| `MIN_PRICE` | No | `7.00` | Minimum product price filter |

---

##  Project Structure

```
├── main.py                       # Entry point (streamlit run main.py)
├── config.ini                    # User configuration (gitignored)
├── requirements.txt              # Python dependencies
│
├── src/
│   ├── dashboard.py              # Streamlit UI (full interactive dashboard, 3500+ lines)
│   ├── cli.py                    # Command-line interface
│   └── core/
│       ├── __init__.py           # Package exports
│       ├── cache.py              # **[NEW]** Local JSON cache — get_or_scrape(), SHA-256 hashing
│       ├── analyzer.py           # Market Score algorithm (0–100), EOS, UOI, trademark
│       ├── scraper.py            # Provider-agnostic fetcher — delegates to active provider
│       ├── pre_research.py       # **[NEW]** Google Suggest keyword discovery (zero-cost)
│       ├── database.py           # SQLite persistence layer
│       ├── exporter.py           # Google Sheets export
│       ├── config_manager.py     # Configuration resolution chain
│       └── providers/            # **[NEW]** Pluggable provider package
│           ├── __init__.py       # Exports: BaseProvider, BaseScraper, all providers
│           ├── base.py           # Abstract base class + BaseScraper alias
│           ├── registry.py       # Provider registry, factory, task-based router
│           ├── pangolinfo.py     # Pangolinfo API client (Bearer auth, amzKeyword)
│           ├── apify.py          # Apify actor client (REST API, poll-for-completion)
│           └── oxylabs.py        # **[NEW]** Oxylabs client (Basic auth, amazon_search)
│
├── cache/                        # **[NEW]** Auto-created cache directory (gitignored)
├── data/                         # SQLite database, logs (gitignored)
├── output/                       # Exported results (gitignored)
│
└── assets/                       # Icons, images, static resources
```

---

##  Architecture

### Provider-agnostic Pipeline

```
User Query
    │
    ├── Provider Router (get_scraper_for_task)
    │   ├── urgent → Pangolinfo (fast)
    │   └── deep   → Oxylabs  (rich)
    │
    ├── Cache Check (get_or_scrape)
    │   ├── HIT  → return cached JSON
    │   └── MISS → provider.scrape() → save to cache
    │
    ├── Normalize (provider.normalize())
    │   └── Unified schema: ASIN, Title, Price, Rating, ReviewCount, Sales
    │
    ├── Market Score (calculate_market_score())
    │   └── 0–100 score + breakdown + verdict
    │
    └── Display (dashboard.py)
        ├── Intelligence Panel (gauge)
        ├── Deep Analysis Report (progress bars)
        └── Gold-Mine Table
```

### Cache Flow

```
execute_with_fallback(keyword, provider)
    → get_or_scrape(keyword, provider_slug, scrape_fn)
        → get_cached(keyword, provider_slug)
            ├── if cache/{hash}.json exists → return it (0 API credits)
            └── if not → call scrape_fn() → save to cache/{hash}.json → return
```

Each provider has an isolated cache namespace — same query with different providers generates different hashes.

---

##  Development

### Testing a Provider

```bash
# Set active provider
set PROVIDER_ACTIVE=oxylabs

# Run the dashboard
streamlit run main.py
```

Or use the Settings tab in the dashboard to switch providers at runtime.

### Adding a New Provider

1. Create `src/core/providers/new_provider.py`
2. Implement `BaseProvider` ABC (`.scrape()`, `.normalize()`, `.is_configured()`)
3. Register in `registry.py` → `_BUILTIN_PROVIDERS`
4. Add to `__init__.py` exports
5. Add credentials to `config.ini`
6. Caching works automatically via `execute_with_fallback()`

---

##  Security Notice

**⚠️ Protect your API keys.**

1. **`config.ini` is listed in `.gitignore`** — it will never be committed to version control
2. **Never share your `config.ini`**, `credentials.json`, or `.env` files
3. **Use environment variables** as an alternative: `set PROVIDER_ACTIVE=oxylabs`
4. **Revoke compromised keys** immediately via the respective provider dashboards

---

##  License

MIT License — See [LICENSE](LICENSE) for full text.
