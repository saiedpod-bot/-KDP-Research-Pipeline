<div align="center">
  <img src="assets/logo.png" alt="KDP Research Pipeline" width="140">
  <h1> KDP Research Pipeline</h1>
  <p><strong>Production-grade Amazon KDP Market Intelligence Platform</strong><br>
  Tiered data providers · Zero-cost pre-research · 0–100 Market Score · Intelligent Caching</p>
  <br>
  <p>
    <a href="#-why-kdp-research-pipeline">Why</a> •
    <a href="#-key-features">Features</a> •
    <a href="#-data-providers">Providers</a> •
    <a href="#-tech-stack">Stack</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-configuration">Config</a> •
    <a href="#-architecture">Architecture</a> •
    <a href="#-comparison">Comparison</a>
  </p>
  <br>
  <p>
    <img src="https://img.shields.io/badge/Version-3.0--beta-blue?style=flat-square" alt="Version 3.0">
    <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square&logo=python" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Streamlit-1.28+-red?style=flat-square&logo=streamlit" alt="Streamlit">
    <img src="https://img.shields.io/badge/Data_Providers-3-green?style=flat-square" alt="3 Data Providers">
    <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square" alt="MIT License">
    <img src="https://img.shields.io/badge/Platform-Windows%20|%20macOS%20|%20Linux-9cf?style=flat-square" alt="Cross-platform">
  </p>
</div>

---

##  Why KDP Research Pipeline?

> **"The first KDP research tool with swappable data providers — built for serious Amazon book publishers."**

Most niche research tools are built for t-shirt sellers and generic POD merchandise. They don't understand:

- **KDP royalty math** — 70% eBook vs 60% paperback vs 35% hardcover at specific price bands
- **Book-native metrics** — BSR, review velocity, page count, print cost per page
- **Multi-format dynamics** — the same title earns differently in each format
- **Arabic-speaking authors** — no other tool offers full RTL Arabic support

**KDP Research Pipeline** solves this with a modular, production-grade platform:

- **3 interchangeable data providers** (Pangolinfo / Apify / Oxylabs) — swap at runtime, zero code changes
- **Zero-cost pre-research** via Google Suggest — explore niches before spending API credits
- **Intelligent local caching** — SHA-256 hashed, per-provider isolation, zero redundant API calls
- **Market Score 0–100** — demand, competition, pricing, and dominance in a single actionable number
- **Validation gate** — prevents wasted credits on unscoped keywords
- **Bilingual EN/AR** — full RTL support including Arabic UI labels

> "I found a low-competition niche in under 10 minutes that earns $1,200/month passive income." — _Beta Tester_

---

##  Key Features

###  Tiered Data Providers

| Provider | Speed | Cost | Products/Query | Best For |
|---|---|---|---|---|
| **Pangolinfo** | ~3s | 1 credit/query | 40–60 | Urgent pre-scrapes, quick validation |
| **Apify** | 60–120s | ~$0.05/run | 40–80 | Deep crawling, custom actors |
| **Oxylabs** | ~10s | ~$0.01/query | 48–62 | Rich data with parse: true |

Providers are **hot-swappable** via the Settings tab or `PROVIDER_ACTIVE` env var — no code changes, no restarts.

###  Intelligent Caching
- **`get_or_scrape(query, provider_slug, scrape_fn)`** — checks `cache/{sha256_hash}.json` first
- Per-provider isolation — same query with different providers = different cache keys
- Integrated into `execute_with_fallback()` so **every provider gets caching for free**
- Zero API credits consumed on cache hits — ideal for repeated analysis

###  Pre-Research Engine (`core/pre_research.py`)
- **Google Suggest API** — completely free, no API key required
- `get_niche_suggestions("coloring book")` → 15+ niche variations
- Quick Discover panel in the dashboard sidebar — select a suggestion to auto-fill the pipeline
- Saves costly provider credits for validated queries only

###  Market Score Algorithm (0–100)

```
Score = Demand × 35% + Competition × 30% + Pricing × 15% - Dominance_Penalty
```

| Component | Weight | What It Measures |
|---|---|---|
| **Demand Score** | 35% | Average reviews, total market size, sales velocity |
| **Competition Score** | 30% | Price variance, review distribution, brand concentration |
| **Pricing Score** | 15% | Average price point, margin headroom |
| **Dominance Penalty** | -25% | Top-5 market share, best-seller badge density |

**Verdict bands:** Excellent (85+) · Great (70+) · Good (55+) · Okay (40+) · Weak (25+) · Poor

###  Deep Analysis Report
Collapsible expander in the dashboard:
- Progress bars with max-score denominators (Demand 35/35, Competition 30/30, etc.)
- Weighted contribution for each signal
- Verdict badge — `st.success` (Excellent/Great), `st.info` (Good/Okay), `st.warning` (Weak/Poor)

###  Validation Gate
The pipeline blocks execution unless the keyword is:
1. **Validated** via Quick Discover (click "Select" on a suggestion), OR
2. **Force Analysis** checkbox is checked

This prevents wasting API credits on exploratory or mistyped queries.

###  Unified Opportunity Index (UOI)
Proprietary 0–100 scoring combining EOS, density inverse, profit margin, keyword relevance, and trend:

```
UOI = (EOS × 40%) + (Density Inverse × 25%) + (Profit Margin × 20%)
      + (Keyword Score × 10%) + (Trend Signal × 5%)
```

###  Additional Capabilities
- **Deep Niche Tunneling** — filtered (last 30 days) vs unfiltered mode side-by-side
- **Multi-Format Profit Calculator** — eBook / paperback / hardcover with KDP royalty math
- **Batch Niche Comparison** — compare 10+ niches in a single table
- **Trademark Checker** — 98 restricted terms (Disney, Marvel, Harry Potter, NFL, Nike...)
- **Competitor Intelligence** — BSR trends, removed products tracker, keyword gap analysis
- **Snapshot History** — automated daily tracking with SQLite persistence
- **11 Marketplaces** — US, UK, DE, FR, JP, CA, AU, IN, MX, IT, ES
- **Arabic/English Bilingual** — full RTL support

---

##  Data Providers

### Pangolinfo
| Property | Value |
|---|---|
| Endpoint | `https://scrapeapi.pangolinfo.com/api/v1/scrape` |
| Source | `amzKeyword` |
| Auth | Bearer token (`PANGOLINFO_TOKEN`) |
| Products | 40–60 per query |
| Speed | ~3 seconds |
| Cost | 1 credit/query |

### Apify
| Property | Value |
|---|---|
| Actor | `junglee/Amazon-crawler` |
| Actor ID | `BG3WDrGdteHgZgbPK` |
| Auth | `APIFY_TOKEN` + `APIFY_ACTOR_ID` |
| Products | 40–80 per run |
| Speed | 60–120 seconds (cold start) |
| Cost | ~$0.05/run |

### Oxylabs
| Property | Value |
|---|---|
| Endpoint | `https://realtime.oxylabs.io/v1/queries` |
| Sources | `amazon_search` (keyword), `amazon_product` (ASIN) |
| Auth | Basic Auth (`OXYLABS_USERNAME` + `OXYLABS_PASSWORD`) |
| Products | 48–62 per query |
| Speed | ~10 seconds |
| Cost | ~$0.01/query |
| Feature | `parse: true` for structured data |

> **Oxylabs response structure:** `results[0].content.results` is a **dict** with keys `organic`, `amazons_choices`, `paid`, `suggested`. The normalizer merges all sections and maps Oxylabs field names (`rating` → star rating, `reviews_count` → review count) into the unified schema.

---

##  Architecture

```
User Query
    │
    ├── Provider Router (get_scraper_for_task)
    │   ├── "urgent"  ──→ Pangolinfo (fastest)
    │   ├── "deep"    ──→ Oxylabs  (richest)
    │   └── fallback chain on failure
    │
    ├── Cache Check (get_or_scrape)
    │   ├── HIT  ──→ return cached JSON (0 credits)
    │   └── MISS ──→ provider.scrape() → save → return
    │
    ├── Normalize (provider.normalize())
    │   └── Unified schema: ASIN, Title, Price, Rating, ReviewCount
    │
    ├── Market Score (calculate_market_score)
    │   └── 0–100 score + breakdown + verdict
    │
    └── Dashboard UI
        ├── Intelligence Panel (gauge + gauge)
        ├── Deep Analysis Report (progress bars + verdict badge)
        ├── Gold-Mine Table (ranked opportunities)
        └── Export (Google Sheets / JSON)
```

### Cache Key Derivation

```
hash = SHA256("{query}|{provider_slug}")[:16]
cache_path = cache/{hash}.json
```

Different providers → different hashes, even for the same keyword.

---

##  Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core logic |
| **UI** | Streamlit 1.28+ | Interactive dashboard |
| **Data** | pandas, NumPy, SQLite | Analysis & persistence |
| **Providers** | Pangolinfo · Apify · Oxylabs | Amazon product data |
| **Pre-Research** | Google Suggest (free) | Zero-cost keyword discovery |
| **Cache** | Local JSON + SHA-256 | Prevents redundant API calls |
| **Export** | gspread + google-auth | Google Sheets |
| **Auth** | python-dotenv, configparser | Credential management |

---

##  Quick Start

### Prerequisites
- Python 3.10+ ([download](https://python.org))
- At least one provider API key (see [Configuration](#configuration))

### Installation

```bash
# 1. Clone
git clone https://github.com/saiedpod-bot/-KDP-Research-Pipeline.git
cd -KDP-Research-Pipeline

# 2. Virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure
cp config.ini.example config.ini
# Edit config.ini with your provider credentials
```

### Launch

```bash
streamlit run main.py
```

Opens at `http://localhost:8501`.

### CLI Mode

```bash
# Quick scan
python main.py --cli "coloring books for adults" --pages 3

# With Google Sheets export
python main.py --cli "keto cookbook 2025" --sheet-id "abc123..."

python main.py --cli --help
```

---

##  Configuration

### config.ini

```ini
# ── Active Provider ──────────────────────────────────────────
PROVIDER_ACTIVE=pangolinfo

# ── Pangolinfo ───────────────────────────────────────────────
PANGOLINFO_TOKEN=eyJ...

# ── Apify ────────────────────────────────────────────────────
APIFY_TOKEN=apify_api_...
APIFY_ACTOR_ID=BG3WDrGdteHgZgbPK

# ── Oxylabs ──────────────────────────────────────────────────
OXYLABS_USERNAME=your_oxylabs_username
OXYLABS_PASSWORD=your_oxylabs_password

# ── SerpApi (legacy — for tunnel features) ───────────────────
SERPAPI_KEY=your_serpapi_key_here

# ── Google Sheets ────────────────────────────────────────────
GOOGLE_SHEET_ID=

# ── Marketplace ──────────────────────────────────────────────
AMAZON_DOMAIN=amazon.com

# ── Pipeline ─────────────────────────────────────────────────
MAX_PAGES=3
MIN_PRICE=7.00
```

### Settings Reference

| Setting | Required | Default | Description |
|---|---|---|---|
| **`PROVIDER_ACTIVE`** | Yes | `pangolinfo` | Active provider: `pangolinfo`, `apify`, or `oxylabs` |
| **`PANGOLINFO_TOKEN`** | For Pangolinfo | — | Bearer token from Pangolinfo dashboard |
| **`APIFY_TOKEN`** | For Apify | — | Apify API token |
| **`APIFY_ACTOR_ID`** | For Apify | `BG3WDrGdteHgZgbPK` | Amazon Crawler actor ID |
| **`OXYLABS_USERNAME`** | For Oxylabs | — | Oxylabs username (Basic Auth) |
| **`OXYLABS_PASSWORD`** | For Oxylabs | — | Oxylabs password (Basic Auth) |
| `SERPAPI_KEY` | Optional | — | Legacy SerpApi key |
| `GOOGLE_SHEET_ID` | No | — | Google Sheet ID for export |
| `AMAZON_DOMAIN` | No | `amazon.com` | Marketplace domain |
| `MAX_PAGES` | No | `3` | Search pages (1–20) |
| `MIN_PRICE` | No | `7.00` | Minimum product price filter |

---

##  Project Structure

```
├── main.py                          # Streamlit entry point
├── config.ini                       # User credentials (gitignored)
├── config.ini.example               # Template (versioned)
├── requirements.txt                 # Python dependencies
│
├── src/
│   ├── dashboard.py                 # Streamlit UI (~3500 lines)
│   ├── cli.py                       # Command-line interface
│   └── core/
│       ├── __init__.py              # Package exports
│       ├── cache.py                 # **[NEW]** get_or_scrape, SHA-256 JSON cache
│       ├── analyzer.py              # Market Score 0–100, EOS, UOI, trademark
│       ├── scraper.py               # Provider-agnostic fetch + normalize
│       ├── pre_research.py          # **[NEW]** Google Suggest (zero-cost)
│       ├── database.py              # SQLite persistence
│       ├── exporter.py              # Google Sheets export
│       ├── config_manager.py        # Config resolution
│       ├── design_engine.py         # AI design tools
│       └── providers/               # **[NEW]** Pluggable providers
│           ├── __init__.py          # BaseScraper alias, all exports
│           ├── base.py              # Abstract base class
│           ├── registry.py          # **[NEW]** Task router + fallback chain
│           ├── pangolinfo.py        # Pangolinfo API client
│           ├── apify.py             # Apify actor client
│           └── oxylabs.py           # **[NEW]** Oxylabs client
│
├── cache/                           # **[NEW]** Auto-created (gitignored)
├── data/                            # SQLite DB, logs (gitignored)
├── output/                          # Exports (gitignored)
│
└── assets/                          # Images, static resources
```

---

##  Security

**⚠️ Protect your API credentials at all times.**

- **`config.ini` is gitignored** — never committed to version control
- **Never share** `config.ini`, `credentials.json`, `.env`, or any file containing real tokens
- **Use environment variables** as an alternative:
  ```bash
  # PowerShell
  $env:PROVIDER_ACTIVE = "oxylabs"
  $env:OXYLABS_USERNAME = "your_username"
  $env:OXYLABS_PASSWORD = "your_password"

  # bash
  export PROVIDER_ACTIVE=oxylabs
  export OXYLABS_USERNAME=your_username
  export OXYLABS_PASSWORD=your_password
  ```
- **`config.ini.example`** contains placeholders only — use it as a template
- **Revoke compromised keys** immediately via the respective provider dashboards
- **Cache files** (`cache/*.json`) contain scraped product data — delete them if they contain sensitive information

### Provider Security Notes

| Provider | Auth Method | Credentials Location |
|---|---|---|
| Pangolinfo | Bearer token in `Authorization` header | `PANGOLINFO_TOKEN` in `config.ini` or env |
| Apify | API token in REST API calls | `APIFY_TOKEN` in `config.ini` or env |
| Oxylabs | Basic Auth (base64-encoded) | `OXYLABS_USERNAME` + `OXYLABS_PASSWORD` in `config.ini` or env |

---

##  Comparison with Competitors

| Feature | KDP Research Pipeline | MerchMetrix | PodCS | Podly | Titan |
|---|---|---|---|---|---|
| **Swappable Providers** | ✅ 3 providers | ❌ Fixed | ❌ Fixed | ❌ Fixed | ❌ Fixed |
| **Intelligent Caching** | ✅ SHA-256 hashed | ❌ No | ❌ No | ❌ No | ❌ No |
| **Zero-Cost Pre-Research** | ✅ Google Suggest | ❌ No | ❌ No | ❌ No | ❌ No |
| **Market Score (0–100)** | ✅ 4-factor | ✅ Basic | ❌ No | ❌ No | ❌ No |
| **KDP Royalty Calculator** | ✅ 3 formats | ❌ No | ❌ No | ❌ No | ❌ No |
| **Deep Niche Tunneling** | ✅ 30-day filter | ❌ No | ❌ No | ❌ No | ❌ No |
| **Batch Niche Comparison** | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| **Trademark Checker** | ✅ 98 terms | ✅ Yes | ✅ Yes | ❌ No | ❌ No |
| **Removed Products Tracker** | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| **BSR Trends** | ✅ Sparklines | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **11 Marketplaces** | ✅ US–ES | ❌ No | ❌ No | ❌ No | ❌ No |
| **Bilingual EN/AR** | ✅ Full RTL | ❌ No | ❌ No | ❌ No | ❌ No |
| **Offline Storage** | ✅ SQLite | ❌ No | ❌ No | ❌ No | ❌ No |
| **Open Source** | ✅ MIT | ❌ No | ❌ No | ❌ No | ❌ No |
| **Price** | **FREE** | $29/mo | $19/mo | $15/mo | $49/mo |

---

##  Roadmap

- [ ] **Historical BSR Graphs** — time-series visualization from snapshot data
- [ ] **USPTO Trademark API** — live trademark database queries
- [ ] **AI Listing Generator** — GPT-powered title/bullet templates
- [ ] **Responsive Mobile Layout** — research on-the-go
- [ ] **Provider Credit Dashboard** — usage tracking per provider
- [ ] **Multi-user Mode** — team accounts with role-based access
- [ ] **API Rate Limiter** — automatic throttling per provider

---

##  Development

### Adding a New Provider

1. Create `src/core/providers/new_provider.py`
2. Implement `BaseProvider` ABC:
   - `.scrape(keyword, marketplace, max_retries)` → raw dict
   - `.normalize(raw)` → unified schema list
   - `.is_configured()` → bool
   - `.name`, `.slug` properties
3. Register in `registry.py` → `_BUILTIN_PROVIDERS`
4. Export from `providers/__init__.py`
5. Add credentials to `config.ini`
6. Caching works automatically via `execute_with_fallback()`

### Testing

```bash
# Test a specific provider
$env:PROVIDER_ACTIVE = "oxylabs"
streamlit run main.py

# Or run headless
python -c "from core.providers.registry import execute_with_fallback; r = execute_with_fallback('coloring book', 'com', 'deep'); print('OK' if r and 'error' not in r else 'FAIL')"
```

---

##  FAQ

**Q: Do I need all three providers?**
No. Start with one. Pangolinfo is the easiest to set up (single token). Oxylabs gives the richest data.

**Q: Does the cache expire?**
No — cache is permanent. Delete `cache/*.json` to force a fresh scrape, or use the "Clear Cache" button (not yet in UI, run `python -c "from core.cache import clear_cache; clear_cache()"`).

**Q: Can I use this without any paid provider?**
Yes — the Google Suggest pre-research (Quick Discover) is completely free. For deep analysis, you need at least one configured provider.

**Q: Is my API key safe?**
Yes — `config.ini` is gitignored. Keys are never sent to GitHub. Use environment variables for extra security.

**Q: What marketplace domains are supported?**
`amazon.com` (US), `amazon.co.uk` (UK), `amazon.de` (DE), `amazon.fr` (FR), `amazon.co.jp` (JP), `amazon.ca` (CA), `amazon.com.au` (AU), `amazon.in` (IN), `amazon.com.mx` (MX), `amazon.it` (IT), `amazon.es` (ES).

---

##  License

[MIT License](LICENSE) — free to use, modify, and distribute. See [LICENSE](LICENSE) for full terms.

---

##  Acknowledgments

- [Pangolinfo](https://pangolinfo.com) — Amazon scrape API
- [Apify](https://apify.com) — Web scraping platform & Amazon Crawler actor
- [Oxylabs](https://oxylabs.io) — Proxy & scraping infrastructure
- [Streamlit](https://streamlit.io) — Dashboard framework
- [Google Suggest](https://google.com) — Free keyword discovery API
- All beta testers who provided invaluable feedback

---

<div align="center">
  <p><strong>KDP Research Pipeline</strong> — Built for KDP authors, by KDP authors</p>
  <p>
    <a href="https://github.com/saiedpod-bot/-KDP-Research-Pipeline">GitHub</a> •
    <a href="#-why-kdp-research-pipeline">Documentation</a> •
    <a href="https://github.com/saiedpod-bot/-KDP-Research-Pipeline/issues">Issues</a> •
    <a href="https://github.com/saiedpod-bot/-KDP-Research-Pipeline/discussions">Discussions</a>
  </p>
  <br>
  <p>
    <img src="https://img.shields.io/badge/Version-3.0--beta-blue?style=flat-square">
    <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square&logo=python">
    <img src="https://img.shields.io/badge/Streamlit-1.28+-red?style=flat-square&logo=streamlit">
    <img src="https://img.shields.io/badge/Data_Providers-3-green?style=flat-square">
    <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square">
  </p>
</div>
