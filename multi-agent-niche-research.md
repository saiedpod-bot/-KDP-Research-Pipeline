# Multi-Agent Orchestration: KDP Niche Research

## System Overview

This is a multi-agent orchestration system for KDP niche research. Each agent is a specialized autonomous unit with a specific role, toolset, and output. The **Orchestrator Agent** manages the workflow, passing outputs between agents, validating results, and compiling the final deliverable. Agents run sequentially where dependencies exist and in parallel where they don't.

---

## Agent Roles & Workflow

```
Orchestrator (Agent-0)
    │
    ├── Agent-1: Market Scanner       ─┐
    ├── Agent-2: Keyword Analyst      ─┤── (parallel: Phase 1)
    ├── Agent-3: Competition Analyzer ─┘
    │
    ├── Agent-4: Profitability Assessor (Phase 2, depends on Agent-1 + Agent-3)
    │
    ├── Agent-5: Trend & Seasonality  (Phase 3, parallel with Phase 2)
    │
    ├── Agent-6: Opportunity Scorer   (Phase 4, depends on all prior agents)
    │
    └── Agent-0: Final Synthesis + Report
```

---

## Agent-0: Orchestrator

**Role:** Manages the entire workflow. Receives the user's initial niche idea or broad genre. Validates outputs at each stage. Resolves conflicts between agent findings. Compiles final recommendation report.

**Input:**
- User's niche idea, genre preference, experience level, budget, goals

**Workflow:**
1. Parse user input → extract genre, format (eBook/print), fiction/nonfiction, target audience
2. Dispatch Agent-1, Agent-2, Agent-3 in parallel
3. Collect outputs → validate data coherence → pass to Agent-4 and Agent-5
4. Collect Agent-4 + Agent-5 outputs → pass to Agent-6
5. Receive Opportunity Score → compile final report
6. Present to user with actionable next steps

**Output:**
- Final Niche Research Report (structured: summary, data, recommendation, action plan)

---

## Agent-1: Market Scanner

**Role:** Scans Amazon's KDP marketplace to identify potential niches and validate market viability.

**Skill: Amazon Marketplace Analysis**

**Process:**
1. Start from user's genre/niche idea
2. Search Amazon using the niche keyword phrase
3. For each relevant book in search results, extract:
   - Title, Author, BSR (Best Sellers Rank), Category path, Price, Format (eBook/paperback/hardcover), Page count, Publication date, Rating count, Average rating
4. Identify top 20 bestsellers in the niche
5. Check if BSR < 50,000 for at least 3 books (viability threshold)
6. Determine if competition count is < 10,000 results
7. Flag if niche is publisher-dominated (more than 50% of top 20 are from Big 5 publishers)

**Input:** Genre/niche phrase, target marketplace (default: Amazon.com)
**Output:** Market data table, viability flags, category paths, BSR distribution

---

## Agent-2: Keyword Analyst

**Role:** Researches keyword demand for the niche using Amazon autocomplete and keyword tools.

**Skill: Search Data Analysis**

**Process:**
1. Take the primary niche keyword phrase
2. Check Amazon search autocomplete: type the phrase and record all suggested completions
3. Research related keywords using: Publisher Rocket, Helium 10, or manual Amazon search analysis
4. Categorize keywords into:
   - **Head terms** (high volume, high competition) — single broad words
   - **Body terms** (medium volume, medium competition) — 2-3 word phrases
   - **Long-tail terms** (low volume, low competition) — 4+ word specific phrases
5. Identify which keywords appear in competitor titles and subtitles
6. Calculate estimated monthly search volume tiers (High > 500, Medium 100-500, Low < 100)
7. Flag keyword gaps — high-demand phrases NOT used by top competitors

**Input:** Primary niche keyword phrase
**Output:** Keyword map with volume estimates, competition tier, gap opportunities, recommended 7 backend keywords

---

## Agent-3: Competition Analyzer

**Role:** Evaluates competitive landscape — how hard it is to enter and rank in this niche.

**Skill: Competitive Intelligence**

**Process:**
1. Analyze top 20 books in the niche
2. For each competitor, assess:
   - Cover quality (professional vs amateur — score 1-10)
   - Review count and distribution (total #, recent 30-day rate, rating breakdown)
   - Review sentiment (look for recurring complaints — "bad editing," "poor formatting," "too short" — these are entry points)
   - Publication velocity (how many new books enter the niche per month)
   - Author catalog depth (is it a one-off or part of a series?)
   - Pricing strategy
   - Whether they use KDP Select / Kindle Unlimited
3. Identify **review gaps** — niches where top books have under 100 reviews (easier to compete)
4. Identify **quality gaps** — niches where top books have consistent negative feedback
5. Assess **category saturation**: how many categories are the top books spread across?
6. Determine **entry difficulty** tier:
   - **Easy:** < 5,000 search results, top books < 50 reviews, low-quality covers common
   - **Moderate:** 5,000-20,000 results, top books 50-200 reviews, mixed quality
   - **Hard:** 20,000-100,000 results, top books 200-1,000 reviews, professional quality
   - **Saturated:** 100,000+ results, top books 1,000+ reviews, publisher-dominated

**Input:** Niche keyword, top 20 BSR data (from Agent-1)
**Output:** Competitive landscape report, review gaps, quality gaps, entry difficulty tier

---

## Agent-4: Profitability Assessor

**Role:** Calculates financial viability — what you can realistically earn in this niche.

**Skill: Royalty & Pricing Math**

**Process:**
1. Take pricing data from Agent-1's market scan
2. Calculate standard royalties for each price point (use 2026 rates):
   - eBook 70% tier ($2.99-$9.99): (Price × 0.70) − ($0.15 × MB file size)
   - eBook 35% tier (outside range): Price × 0.35
   - Paperback (≥ $9.99): (Price × 0.60) − ($1.00 + $0.012 × pages)
   - Paperback (< $9.99): (Price × 0.50) − ($1.00 + $0.012 × pages)
3. Estimate realistic sales volume based on competitor BSR:
   - BSR 1-5,000: ~500+ copies/month
   - BSR 5,001-20,000: ~100-500 copies/month
   - BSR 20,001-50,000: ~30-100 copies/month
   - BSR 50,001-100,000: ~10-30 copies/month
   - BSR 100,000+: ~1-10 copies/month
4. Calculate monthly revenue scenarios at 3 levels:
   - **Conservative** (BSR similar to #20 in niche)
   - **Moderate** (BSR similar to #10)
   - **Optimistic** (BSR similar to #3)
5. Factor in Amazon Ad costs:
   - Estimate CPC ($0.50-$1.50 depending on niche competitiveness)
   - Estimate conversion rate (5-10% for well-optimized listings)
   - Calculate break-even ACoS
6. Estimate KU page-read earnings if using KDP Select:
   - KENP royalties: pages read × ~$0.0047 per page
   - Typical KU read-through rate: 60-85% of book completed

**Input:** Pricing data, page count estimates, competitor BSR data
**Output:** Profitability model — 3-scenario projections, ad cost estimates, KU earnings estimate, minimum viable price

---

## Agent-5: Trend & Seasonality Analyst

**Role:** Assesses whether the niche is growing, stable, or declining — and identifies seasonal patterns.

**Skill: Trend Analysis**

**Process:**
1. Use Google Trends for the primary niche keyword (filter by Books category if available)
2. Analyze trend direction over:
   - Last 12 months (YoY comparison)
   - Last 5 years (long-term trajectory)
3. Identify seasonality patterns:
   - Q1 (Jan-Mar): Post-holiday slump, New Year resolution niches (self-help, diet, fitness)
   - Q2 (Apr-Jun): Steady, Mother's Day/Father's Day gift niches
   - Q3 (Jul-Sep): Summer reading, back-to-school
   - Q4 (Oct-Dec): Holiday gift niches — peak season
4. Check if related search terms are rising or falling
5. Look for emerging sub-niches within the broader category
6. Check Amazon search trends using tools like Publisher Rocket's trend data or Helium 10's Cerebro
7. Identify pop culture / media correlations:
   - Recent movie/TV adaptations in the genre (e.g., a fantasy series release boosts fantasy book sales)
   - Current events driving interest (e.g., economic topics during recession)
8. Assess the ratio of new vs established books in the top 20 — more new books = active/growing niche

**Input:** Primary niche keyword, competitor publication dates
**Output:** Trend report — direction (growing/stable/declining), seasonality calendar, emerging sub-niches, media correlations

---

## Agent-6: Opportunity Scorer

**Role:** Synthesizes all agent outputs into a single Opportunity Score and ranking.

**Skill: Multi-Factor Scoring & Recommendation**

**Process:**
Receive inputs from Agents 1-5 and calculate weighted scores:

**Scoring Rubric (total 100 points):**

| Factor | Weight | Source |
|--------|--------|--------|
| Market Demand (keyword volume) | 20 pts | Agent-2 |
| Competition Difficulty (inverse) | 20 pts | Agent-3 |
| Profitability Potential | 15 pts | Agent-4 |
| Review Gap Opportunity | 15 pts | Agent-3 |
| Trend Direction | 10 pts | Agent-5 |
| Quality Gap Opportunity | 10 pts | Agent-3 |
| Seasonality Bonus | 5 pts | Agent-5 |
| Author Fit (experience match) | 5 pts | Orchestrator |

**Scoring Tiers:**
- **80-100: Green Light** — Strong opportunity. Proceed to book creation.
- **60-79: Yellow Light** — Moderate opportunity. Proceed with caution; differentiation required.
- **40-59: Orange Light** — Weak opportunity. Only proceed if you have a specific advantage.
- **0-39: Red Light** — Poor opportunity. Recommend different niche.

**Output:**
- Overall Opportunity Score
- Breakdown by factor (strengths / weaknesses)
- Key risks and mitigations
- "Go / No-Go" recommendation
- If Go: recommended format (eBook + paperback), price point, KDP Select recommendation, suggested differentiation angle

---

## Agent-0: Final Synthesis & Report Compilation

**Role:** Takes all agent outputs and compiles them into a structured, actionable final report.

**Output Structure:**

```markdown
# Niche Research Report: [Niche Name]

## Executive Summary
- Opportunity Score: [X]/100 → [Green/Yellow/Orange/Red]
- Verdict: [Go / No-Go / Conditional]
- One-paragraph summary of findings

## Market Overview (Agent-1)
- Total search results: [X]
- Top 20 BSR range: [min] - [max]
- Category paths identified
- Market table (top 10-20 books with title, BSR, price, reviews, rating)

## Keyword Landscape (Agent-2)
- Primary keyword demand estimate
- High-value long-tail keywords
- Keyword gap opportunities
- Recommended 7 backend keywords

## Competition Analysis (Agent-3)
- Entry difficulty: [Easy/Moderate/Hard/Saturated]
- Review gaps identified: [yes/no] — details
- Quality gaps identified: [yes/no] — details
- Cover quality benchmark

## Financial Projection (Agent-4)
- Recommended price: eBook $[X.XX], Paperback $[X.XX]
- Royalty per unit: eBook $[X.XX], Paperback $[X.XX]
- Monthly revenue scenarios: Conservative $[X] / Moderate $[X] / Optimistic $[X]
- KU estimate (if applicable): $[X]/month per [X] complete reads
- Ad cost estimate: $[X] per sale at estimated ACoS

## Trend & Seasonality (Agent-5)
- Trend: [Growing/Stable/Declining]
- Seasonality notes
- Best launch window: [Month(s)]

## Differentiation Strategy
- Recommended angle to stand out
- Cover style suggestion (based on competitor analysis)
- Content gap to fill (based on negative reviews of competitors)

## Action Plan
1. [First step]
2. [Second step]
3. [Third step]
...
n. Target publication date: [Date based on seasonality + prep time]

## Next Agent Handoff
- Ready for: [Content Creation / Book Formatting / Cover Design]
```

## Execution Rules

### Agent Communication
- Agents pass structured JSON-like data between each other (not prose)
- Each agent outputs: `{ agent_id, status, findings, confidence_score, raw_data, errors }`
- Orchestrator validates each output before routing to next agent
- If confidence_score < 0.6 on any critical finding, Orchestrator requests re-run or flags to user

### Error Handling
- If an agent times out or fails to retrieve data, Orchestrator logs the failure and proceeds with partial data, flagging to user
- If Agent-1 finds < 3 books with BSR < 50,000, Orchestrator short-circuits: recommends abandoning the niche before running Agents 2-6

### User Interaction Points
1. **Start:** User provides niche idea / genre / parameters
2. **Mid-point (optional):** If Orchestrator finds conflicting signals, it pauses and asks user for clarification
3. **End:** Final report delivered with "Go / No-Go" verdict
4. **Post-report:** User can request deeper analysis on any specific finding, or proceed to next pipeline stage

### Tool Access by Agent

| Agent | Required Tools |
|-------|---------------|
| Agent-0 | None (coordination only) |
| Agent-1 | Amazon search access, BSR lookup capability |
| Agent-2 | Amazon autocomplete, keyword tool access |
| Agent-3 | Amazon product page access, review analysis |
| Agent-4 | KDP royalty calculator, pricing math engine |
| Agent-5 | Google Trends, trend data sources |
| Agent-6 | Scoring engine (no external tools needed) |

---

## Quick Start Command

```
kdpfy pipeline niche --genre "sci-fi" --subgenre "space opera" --format "eBook + paperback"
```

Or for a full analysis with no prior idea:

```
kdpfy pipeline niche --explore --budget "under $500"
```
