# Amazon KDP Research Pipeline

A modular, fault-tolerant 3-tier research system for Amazon KDP (Kindle Direct Publishing) niche validation. Scrapes Amazon search results via SerpApi, scores products by opportunity, and exports findings to Google Sheets.

## Architecture

```
main.py  (Orchestrator — sequential, error-propagating)
  |
  +-- src/scraper.py   (Tier 1 — Gather)
  |     fetch_all_pages()       — batch pagination via 'start' offset
  |     fetch_amazon_data()     — single-page search
  |     search_and_format()     — convenience wrapper
  |
  +-- src/analyzer.py   (Tier 2 — Analyze)
  |     run_analysis()          — load / filter / score / save
  |     find_low_competition_gems()  — list-based gem filter
  |     find_gems_dataframe()        — DataFrame-based gem filter
  |
  +-- src/exporter.py   (Tier 3 — Export)
        run_export()            — load / authenticate / upload to Sheets
```

**Pipeline contract:** Each stage gates into the next. If Tier 1 fails, Tier 2 never runs. If Tier 2 fails, Tier 3 never runs. Errors propagate with detailed logging.

## Prerequisites

```bash
pip install serpapi requests pandas gspread google-auth
```

| Package | Required | Purpose |
|---------|----------|---------|
| `serpapi` | Yes | Amazon search API |
| `requests` | Yes | HTTP (dependency of serpapi) |
| `pandas` | No (falls back to pure-Python) | Vectorised scoring for large datasets |
| `gspread` | No (Tier 3 only) | Google Sheets write |
| `google-auth` | No (Tier 3 only) | Service account auth |

## Quick Start

### 1. Set your SerpApi key

Create a `.env` file in the project root:

```env
SERPAPI_KEY=your_serpapi_key_here
```

Get a key at [serpapi.com](https://serpapi.com) (free tier: 100 searches/month).

### 2. Quick scan (single page, ~20-50 results)

```bash
python main.py "low fodmap cookbook for kids"
```

### 3. Deep scan (5 pages, 100+ results)

```bash
python main.py "coloring books for adults" --max-pages 5 --min-price 7.00
```

### 4. Full pipeline with Google Sheets export

```bash
python main.py "adhd planner for adults" --max-pages 5 --sheet-id "1abc..."
```

## CLI Reference

```
usage: main.py [-h] [--max-pages MAX_PAGES] [--sheet-id SHEET_ID]
               [--creds CREDS] [--min-price MIN_PRICE] [--no-pandas]
               query

positional arguments:
  query                 Amazon search keyword phrase

options:
  --max-pages MAX_PAGES Pages to fetch (default: 3, use 5+ for 100+ results)
  --sheet-id SHEET_ID   Google Sheet ID for Tier 3 export (omit to skip)
  --creds CREDS         Path to service-account JSON (default: credentials.json)
  --min-price MIN_PRICE Minimum price filter (default: $5.00)
  --no-pandas           Force pure-Python scoring
```

### Research Depth Guide

| Depth | Command | Typical Results | Best For |
|-------|---------|----------------|----------|
| Quick | `--max-pages 1` | 20-50 | Initial niche sniff test |
| Standard | `--max-pages 3` (default) | 50-150 | Regular competitive analysis |
| Deep | `--max-pages 5` | 100-200+ | Saturated niches like "coloring books" |

## Google Sheets Setup (Tier 3)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable the **Google Sheets API**
3. Go to **IAM & Admin** → **Service Accounts** → **Create Service Account**
4. Assign role: **Editor**
5. Create a JSON key → download as `credentials.json`
6. Place `credentials.json` in the project root (it is gitignored)
7. Share your target Google Sheet with the service account email (found in the JSON key as `client_email`)

```bash
# Verify the setup
python main.py "keto cookbook" --sheet-id "1abc123..."
```

**Important:** `credentials.json` is listed in `.gitignore` to prevent accidental commits of private key material.

## Output Files

All generated files land in `output/` (gitignored):

| File | Contents |
|------|----------|
| `raw_{query}.json` | Raw SerpApi response (one or more pages merged) |
| `formatted_{query}.json` | Normalized schema rows: ASIN, Title, Author, Price, BSR, ReviewCount, Rating |
| `ranked_{query}.json` | Scored and sorted rows with SmartScore |
| `ranked_{query}_summary.txt` | Human-readable top-20 table |

## Scoring: SmartScore

```
SmartScore = ReviewCount / (BSR + 1)
```

- High ReviewCount = strong demand / social proof
- Low BSR = high sales velocity
- Dividing by `(BSR + 1)` penalises entrenched competitors
- **Result:** Higher score = higher opportunity

**Known limitation:** BSR is currently set to 0 for all items (requires a product-detail API endpoint). SmartScore currently equals `ReviewCount`. Future Tier 4 will add BSR scraping for real scoring.

## Interpreting "Gold Mine" Results

After analysis, the pipeline prints a `GOLD MINE` table showing the top 5 **Low-Competition Gems**:

```
+==========================================================+
|  GOLD MINE -- Top 5 Low-Competition Opportunities        |
+==========================================================+
| Rank ASIN               Score   Price  Reviews Rating |
|----- -------------- --------- ------- -------- ------ |
|    1 B0DZY2V81Z        0.0000    8.49        0    4.7 |
+==========================================================+
```

### What makes a "Gem"?

A product qualifies when **both** conditions are true:

1. **BSR < 50,000** — The product sells (low Best-Sellers Rank = high velocity)
2. **ReviewCount < 30** — Few reviews = the category is not saturated

A gem with 0 reviews, a 4.7-star initial rating, and a price above $7.00 is a strong signal: the niche has demand but no dominant player. These are the highest-value targets for a new KDP author.

### Caveat: BSR placeholder

Until the product-detail scraper is built, BSR is always 0, which means every item with fewer than 30 reviews qualifies. The gem filter still surfaces the **underserved** part of the equation — look for products with 10-29 reviews and high ratings as validation that the niche converts.

## Project Structure

```
.
+-- main.py                 Orchestrator — sequential stage execution
+-- .env                    SerpApi key (gitignored)
+-- credentials.json        Google service account key (gitignored)
+-- .gitignore
+-- README.md
+-- src/
|   +-- scraper.py          Tier 1 — Data gathering (SerpApi)
|   +-- analyzer.py         Tier 2 — Scoring + gem detection
|   +-- exporter.py         Tier 3 — Google Sheets export
+-- output/                 Generated data (gitignored)
    +-- raw_{query}.json
    +-- formatted_{query}.json
    +-- ranked_{query}.json
    +-- ranked_{query}_summary.txt
```

## Extending the Pipeline

All modules are **additive-only**. To add a new feature:

1. Add a new function to the appropriate `src/` module
2. Wire it into `main.py` without modifying existing stage calls
3. If it's a new Tier, add a new stage block in `run_pipeline()`

For example, to add BSR scraping (Tier 4): create `src/enricher.py` with a `enrich_products(rows)` function that populates `BSR` and `PublicationDate` from Amazon product-detail pages, then insert a stage 1.5 block in `main.py` between the scraper and analyzer calls.
