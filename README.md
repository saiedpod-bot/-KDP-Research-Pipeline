<div align="center">
  <img src="assets/logo.png" alt="KDP Discovery Engine Pro" width="140">
  <h1>KDP Discovery Engine Pro</h1>
  <p><strong>Professional Niche Research & Profit Optimization for Kindle Direct Publishing</strong></p>
  <br>
  <p>
    <a href="#-why-kdp-discovery-engine-pro">Why</a> •
    <a href="#-key-features">Features</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-configuration">Configuration</a> •
    <a href="#-comparison-with-competitors">Comparison</a> •
    <a href="#-contributing">Contributing</a>
  </p>
  <br>
  <p>
    <img src="https://img.shields.io/badge/Version-2.0-blue?style=flat-square" alt="Version 2.0">
    <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square&logo=python" alt="Python 3.10+">
    <img src="https://img.shields.io/badge/Streamlit-1.28+-red?style=flat-square&logo=streamlit" alt="Streamlit">
    <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey?style=flat-square" alt="Cross-platform">
    <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="MIT License">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=flat-square" alt="PRs Welcome">
  </p>
</div>

---

##   Why KDP Discovery Engine Pro?

> **"The only research tool built from the ground up for KDP book publishers — not t-shirt sellers."**

Every day, thousands of KDP authors waste hours manually researching niches, crunching royalty numbers, and trying to gauge competition. The existing tools (MerchMetrix, PodCS, Podly, etc.) were built for **Print-on-Demand merchandise** — t-shirts, mugs, phone cases. They don't understand:

- **KDP royalty tiers** — 70% eBook vs 60% paperback vs 35% at different price points
- **Book-specific competition metrics** — BSR, page count, ink type, trim size
- **Multi-format profit dynamics** — the same book earns differently as eBook vs paperback vs hardcover

**KDP Discovery Engine Pro** solves this with a purpose-built platform that:

- **Discovers profitable niches** before they get saturated
- **Calculates exact KDP net profit** across all 3 formats in real time
- **Ranks opportunities** with a proprietary Unified Opportunity Index (UOI)
- **Protects your business** with built-in trademark scanning (98 restricted terms)
- **Tracks markets over time** with automated snapshot history and trend signals
- **Generates ideas** from any seed keyword — 40+ niche variations per query

> "With KDP Discovery Engine Pro, I found a low-competition niche in under 10 minutes that earns me $1,200/month passive income." — _Early Beta Tester_

---

##   Key Features

###   Unified Opportunity Index (UOI)
Proprietary 0–100 scoring that combines EOS opportunity, competitive density inverse, profit margin, keyword relevance, and trend signals into a single actionable number.

```
UOI = (EOS × 40%) + (Density Inverse × 25%) + (Profit Margin × 20%)
      + (Keyword Score × 10%) + (Trend Signal × 5%)
```

###   Deep Niche Tunneling
Analyze any niche in **two modes** side-by-side:
- 🔷 **Filtered (Last 30 Days):** See only new products entering the market
- 🔷 **Unfiltered:** Full competitive landscape
- 🏆 Instantly detect **Golden Niches** — low density + high visibility

###   Multi-Format Profit Calculator

| Format | Royalty Structure | Print Cost |
|---|---|---|
| **eBook** | 70% ($2.99–$9.99) / 35% (outside range) | $0.00 |
| **Paperback** | 60% (≥$9.99) / 50% (<$9.99) | $1.00 + $0.012/page (B&W) |
| **Hardcover** | 60% (≥$9.99) / 50% (<$9.99) | $1.00 + $0.055/page (Color) |

The engine **automatically recommends the best format** at every price point via bulk scenario modeling.

###   Batch Niche Comparison
Compare **10+ niches** side-by-side in a single table. The engine highlights the **best scoring niche** so you know where to focus first.

###   Niche Idea Generator
Enter a seed keyword → get **10+ niche variations** with difficulty ratings:

| Seed | Generated Ideas |
|---|---|
| `coloring book` | Large Print · Stress Relief · Mindfulness · Animal · Nature · Seasonal |
| `cookbook` | Keto · Vegan Meal Prep · Low Carb · Mediterranean · Paleo · 30-Minute |

###   Trademark Safety Check
Scan any keyword against **98 restricted terms** (Disney™, Marvel™, Harry Potter™, NFL™, Nike™, and more) to prevent IP infringement before you publish.

###   Competitor Intelligence Suite
- **Trend Sparklines** — BSR direction at a glance (📈 improving · 📉 declining · ➡️ stable)
- **Removed Products Tracker** — detect products that vanished from the market
- **Keyword Gap Analysis** — find keywords competitors rank for that you're missing
- **Snapshot History** — automated daily tracking of niche metrics over time

###   Multi-Marketplace Support

| 🇺🇸 US | 🇬🇧 UK | 🇩🇪 DE | 🇫🇷 FR | 🇯🇵 JP | 🇨🇦 CA | 🇦🇺 AU | 🇮🇳 IN | 🇲🇽 MX | 🇮🇹 IT | 🇪🇸 ES |
|---|---|---|---|---|---|---|---|---|---|---|

###   Arabic/English Bilingual Interface
Full RTL support for Arabic-speaking KDP authors — the only KDP research tool with this capability.

---

##   Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core logic & orchestration |
| **UI Framework** | Streamlit 1.28+ | Interactive dashboard |
| **Data** | pandas, SQLite | Analysis & persistence |
| **Search API** | SerpApi | Amazon product data |
| **Visual** | Custom CSS (glass-morphism) | Modern dark theme |
| **Packaging** | PyInstaller 6+ | Single-file .exe distribution |
| **Obfuscation** | PyArmor 8+ | IP protection for core algorithms |
| **Export** | gspread + google-auth | Google Sheets integration |

---

##   Quick Start

### Prerequisites
- Python 3.10 or higher ([download](https://python.org))
- A free SerpApi API key ([sign up](https://serpapi.com) — 100 searches/month free)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-org/kdp-discovery-engine-pro.git
cd kdp-discovery-engine-pro

# 2. (Recommended) Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Configure your API key
cp config.ini.example config.ini
# Edit config.ini and add your SerpApi key:
#     SERPAPI_KEY=your_key_here
```

### Launch the Dashboard

```bash
streamlit run main.py
```

Your browser will open to `http://localhost:8501` with the full KDP Discovery Engine dashboard.

### Run Headless (CLI Mode)

```bash
# Quick niche scan
python main.py --cli "low carb cookbook for beginners" --pages 5

# Full pipeline with export
python main.py --cli "adhd planner for adults" --sheet-id "abc123"

# View all CLI options
python main.py --cli --help
```

### Run from a Standalone Executable (Windows)

1. Download the latest `KDP_Discovery.exe` from the [Releases](https://github.com/your-org/kdp-discovery-engine-pro/releases) page
2. Place it in an empty folder with `config.ini`
3. Double-click `KDP_Discovery.exe`

> No Python installation needed — the .exe bundles everything.

---

## [Placeholder: Dashboard Demo GIF]

![Dashboard Screenshot](assets/dashboard_preview.png)
<!-- Replace with an actual animated GIF showing the workflow:
    1. Type a keyword → 2. Run pipeline → 3. View gold mine results → 4. Deep tunnel a niche -->

---

##   Configuration

### config.ini

```ini
[API Keys]
SERPAPI_KEY=your_serpapi_key_here
GOOGLE_SHEET_ID=

[Marketplace]
AMAZON_DOMAIN=amazon.com

[Application]
THEME=dark
LANGUAGE=en
MAX_PAGES=3
MIN_PRICE=7.00
```

| Setting | Required | Default | Description |
|---|---|---|---|
| `SERPAPI_KEY` | **Yes** | — | [SerpApi](https://serpapi.com) key for Amazon search |
| `GOOGLE_SHEET_ID` | No | — | Google Sheet ID for export |
| `AMAZON_DOMAIN` | No | `amazon.com` | Marketplace domain (see table below) |
| `THEME` | No | `dark` | `dark` or `light` |
| `LANGUAGE` | No | `en` | `en` (English) or `ar` (Arabic) |
| `MAX_PAGES` | No | `3` | Search pages (1–20) |
| `MIN_PRICE` | No | `7.00` | Minimum product price filter |

---

##   Project Structure

```
kdp-discovery-engine-pro/
├── main.py                    # Entry point (streamlit run main.py)
├── config.ini                 # User configuration (gitignored)
├── config.ini.example         # Configuration template (versioned)
├── requirements.txt           # Python dependencies
├── build_spec.spec            # PyInstaller build spec
├── pyarmor_build.py           # Code obfuscation script
│
├── src/
│   ├── dashboard.py           # Streamlit UI (full interactive dashboard)
│   ├── cli.py                 # Command-line interface
│   └── core/
│       ├── __init__.py        # Package exports
│       ├── analyzer.py        # Scoring algorithms (EOS, UOI, profit, trademark)
│       ├── scraper.py         # Amazon data collection (SerpApi)
│       ├── database.py        # SQLite persistence layer
│       ├── exporter.py        # Google Sheets export
│       └── config_manager.py  # Configuration resolution chain
│
├── assets/                    # Icons, images, static resources
├── data/                      # SQLite database, logs, cache (gitignored)
├── output/                    # Exported results (gitignored)
│
├── .github/
│   └── ISSUE_TEMPLATE/        # Issue templates for contributors
│       ├── bug_report.md
│       └── feature_request.md
│
├── CONTRIBUTING.md            # Contribution guidelines
├── LICENSE                    # MIT License
├── SECURITY.md                # Security policy
└── README.md                  # This file
```

---

##   Security Notice

**⚠️ Protect your API keys.**

1. **`config.ini` is listed in `.gitignore`** — it will never be committed to version control
2. **Never share your `config.ini`**, `credentials.json`, or `.env` files
3. **Use environment variables** as an alternative: `export SERPAPI_KEY="sk-..."`
4. **The `.env.example` and `config.ini.example`** files are safe templates — they contain placeholder values only
5. **Revoke compromised keys** immediately via your [SerpApi dashboard](https://serpapi.com)

---

##   Comparison with Competitors

| Feature | 🚀 KDP Engine Pro | MerchMetrix | PodCS | Podly |
|---|---|---|---|---|
| **KDP Royalty Calculator (3 formats)** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Unified Opportunity Index (proprietary)** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Deep Niche Tunneling (30-day filter)** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Batch Niche Comparison** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Niche Idea Generator** | ✅ Yes **FREE** | ✅ Yes ($29/mo) | ❌ No | ❌ No |
| **Trademark Checker (98 terms)** | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| **Removed Products Tracker** | ✅ Yes **FREE** | ❌ No | ✅ Yes ($19/mo) | ❌ No |
| **BSR Trend Analysis** | ✅ Yes | ❌ No | ❌ No | ✅ Yes |
| **Multi-Marketplace (11 domains)** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Bilingual (English/Arabic)** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Offline / SQLite Storage** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Open Source (MIT)** | ✅ Yes | ❌ No | ❌ No | ❌ No |
| **Price** | **FREE** | $29/month | $19/month | $15/month |

---

##   Packaging & Distribution

### Build a Standalone Executable

```bash
pip install pyinstaller pywin32
pyinstaller --clean build_spec.spec
# Output: dist/KDP_Discovery.exe (~200 MB)
```

### Obfuscate Core Algorithms (IP Protection)

```bash
pip install pyarmor
python pyarmor_build.py
# Output: dist_obfuscated/src/core/*.py (obfuscated bytecode)
# Then build the .exe:
pyinstaller --clean build_spec.spec
```

Obfuscated modules: `analyzer.py`, `database.py`, `scraper.py`, `exporter.py`, `config_manager.py`.

---

##   System Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.11+ |
| RAM | 512 MB | 1 GB |
| Disk (source) | 200 MB | 500 MB |
| Disk (PyInstaller build) | 1 GB | 2 GB |
| OS | Windows 10, macOS 12, Ubuntu 20.04 | Windows 11, macOS 14 |
| API | SerpApi free tier (100/mo) | SerpApi paid tier |

---

##   Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- How to report bugs
- How to suggest features
- How to submit pull requests
- Our code of conduct

Quick links:
- [Open an Issue](https://github.com/your-org/kdp-discovery-engine-pro/issues/new/choose)
- [Submit a PR](https://github.com/your-org/kdp-discovery-engine-pro/compare)

---

##   License

[MIT License](LICENSE) — See [LICENSE](LICENSE) for full text.

---

##   Roadmap

- [ ] **Historical BSR Graphs** — time-series visualization from snapshot data
- [ ] **USPTO Trademark API Integration** — live trademark database queries
- [ ] **Listing Generator** — copy-ready title/bullet templates from top performers
- [ ] **Responsive Mobile Layout** — research on-the-go
- [ ] **Premium Tier** — SerpApi credit tracking & usage dashboard

---

##   Acknowledgments

- [SerpApi](https://serpapi.com) for Amazon search API
- [Streamlit](https://streamlit.io) for the interactive dashboard framework
- All beta testers who provided invaluable feedback

---

<div align="center">
  <p><strong>KDP Discovery Engine Pro</strong> — Built for KDP Authors, by KDP Authors</p>
  <p>
    <a href="https://github.com/your-org/kdp-discovery-engine-pro">GitHub</a> •
    <a href="#-why-kdp-discovery-engine-pro">Documentation</a> •
    <a href="https://github.com/your-org/kdp-discovery-engine-pro/issues">Issues</a> •
    <a href="https://github.com/your-org/kdp-discovery-engine-pro/discussions">Discussions</a>
  </p>
</div>
