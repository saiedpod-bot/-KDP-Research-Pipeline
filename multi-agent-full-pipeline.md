# Multi-Agent Orchestration: Full KDP Book Pipeline

## System Architecture

A hierarchical multi-agent system covering the entire KDP book lifecycle — from niche research to post-launch optimization.

```
┌─────────────────────────────────────────────────────────┐
│                 SUPER-ORCHESTRATOR (Agent-0)             │
│       Manages pipeline flow, stage gates, rollbacks      │
└─────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Stage 1  │  │ Stage 2  │  │ Stage 3  │  │ Stage 4  │
   │  Niche   │→│ Content  │→│ Format   │→│  Cover   │
   │ Research │  │ Creation │  │ & Layout │  │  Design  │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
   │ Stage 5  │  │ Stage 6  │  │ Stage 7  │  │ Stage 8  │
   │ Listing  │→│  Amazon  │→│  Launch  │→│ Post-    │
   │   Opt.   │  │   Ads    │  │ Strategy │  │ Launch   │
   └──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## Super-Orchestrator (Agent-0)

**Role:** End-to-end pipeline manager. Receives the user's idea. Calls pipeline stages in order with stage-gate validation between each. Handles rollbacks, re-runs, and user approval gates.

**Stage Gates:**
- **Gate 1→2:** Niche Opportunity Score ≥ 60 to proceed. If < 60, ask user: proceed anyway or abandon?
- **Gate 2→3:** Manuscript approved by user (content complete, edited)
- **Gate 3→4:** Format passes Kindle Previewer validation (no rendering errors)
- **Gate 4→5:** Cover approved by user (3 concepts minimum)
- **Gate 5→6:** Listing optimized and user-approved
- **Gate 6→7:** Ad budget confirmed, campaigns structured
- **Gate 7→8:** Launch executed, tracking active
- **Gate 8→loop:** Monthly performance review → loop back to optimize

---

## Stage 1: Niche Research

*(Full multi-agent system defined in `multi-agent-niche-research.md` — Agents 1.1 through 1.6)*

**Sub-agents:** Market Scanner, Keyword Analyst, Competition Analyzer, Profitability Assessor, Trend & Seasonality Analyst, Opportunity Scorer

**Deliverable:** Niche Research Report with Go/No-Go verdict

---

## Stage 2: Content Creation

### Agents

| ID | Agent | Role |
|----|-------|------|
| 2.1 | **Outline Architect** | Structures the book based on niche research + proven bestseller templates |
| 2.2 | **Draft Writer** | Generates full manuscript from outline (fiction chapter-by-chapter, nonfiction section-by-section) |
| 2.3 | **Editor** | Developmental edit + line edit + proofread. Checks pacing, structure, grammar, consistency |
| 2.4 | **Beta Reader Synthesizer** | Simulates beta reader feedback based on genre conventions and target audience expectations. Flags plot holes, weak characters, boring sections |
| 2.5 | **Quality Assurance** | Final manuscript check — word count target met? Tone consistent? Genre conventions followed? No AI tell-tale patterns? |

### Workflow

```
Agent 2.1 (Outline) → user approval → Agent 2.2 (Draft) → Agent 2.3 (Edit)
    → Agent 2.4 (Beta Read) → revisions loop → Agent 2.5 (QA) → Gate 2→3
```

### Agent 2.1 — Outline Architect

**Input:** Niche research report (keywords, competitor gaps, reader expectations)
**Process:**
1. Analyze top 5 competitors' table of contents / chapter structure (inferred from "Look Inside" samples)
2. Identify structural patterns — what do successful books in this niche include?
3. Map keywords to chapter topics (SEO-informed content structure)
4. For fiction: outline acts, chapters, major plot points, character arcs
5. For nonfiction: outline introduction, chapters, action steps, appendix
6. Include word count target per chapter
7. Note content gaps — topics competitors miss that readers want (sourced from review analysis)
**Output:** Full chapter-by-chapter outline with word counts, ISBN-style structure

### Agent 2.2 — Draft Writer

**Input:** Approved outline, niche tone/style guide
**Process:**
1. Write to outline precisely — no deviation without approval
2. Match genre-appropriate word count (novel: 60k-90k; nonfiction: 30k-50k; children's: 500-2000)
3. For fiction: maintain consistent POV, tense, voice. Include genre-mandatory beats (romance: meet-cute, dark moment, HEA/HFN)
4. For nonfiction: include examples, case studies, exercises, summaries per chapter
5. Use natural language — no fluff, no padding
6. Deliver chapter by chapter for incremental editing
**Output:** Complete first draft manuscript

### Agent 2.3 — Editor

**Input:** First draft manuscript
**Process:**
1. **Developmental pass:** Structure, pacing, plot holes, character consistency, argument flow, missing sections
2. **Line pass:** Sentence structure, word choice, readability score (target: Flesch-Kincaid 65-80 for general audience)
3. **Proofread pass:** Spelling, grammar, punctuation, consistency (e.g., "e-book" vs "ebook" — pick one and enforce)
4. **Style guide enforcement:** Ensure consistent heading styles, capitalizations, formatting conventions
5. Track changes — explain WHY each change is made
**Output:** Edited manuscript with track changes + editorial notes

### Agent 2.4 — Beta Reader Synthesizer

**Input:** Edited manuscript
**Process:**
1. Simulate reader perspectives for the target audience
2. Identify: boring sections, confusing parts, pacing issues, emotional engagement weak points
3. For fiction: is the hook strong enough? Are stakes clear? Is the ending satisfying?
4. For nonfiction: is the advice actionable? Are examples relatable? Is the expertise credible?
5. Flag sections that may generate negative reviews
6. Recommend specific revisions
**Output:** Beta reader simulation report + revision recommendations

### Agent 2.5 — Quality Assurance

**Input:** Final revised manuscript
**Process:**
1. Word count matches target ±10%
2. Section/chapter structure matches outline
3. No grammar/spelling errors
4. Readability score appropriate for genre
5. No plagiarized content (paraphrase check)
6. No obvious AI-generated patterns (repetitive phrasing, unnatural transitions, hollow descriptions)
7. Front matter complete (title page, copyright, dedication, TOC placeholder)
8. Back matter complete (author bio, also-by list, CTA for reviews)
**Output:** QA Pass/Fail + final approved manuscript

---

## Stage 3: Book Formatting & Layout

### Agents

| ID | Agent | Role |
|----|-------|------|
| 3.1 | **eBook Format Specialist** | Converts manuscript to Kindle-ready EPUB/KPF |
| 3.2 | **Print Layout Engineer** | Creates print-ready PDF for paperback + hardcover |
| 3.3 | **Validation & Preview Tester** | Runs Kindle Previewer + KDP validation checks |

### Workflow

```
Agent 3.1 (eBook) ─┐
                    ├──→ Agent 3.3 (Validation) → Gate 3→4
Agent 3.2 (Print)  ─┘
```

### Agent 3.1 — eBook Format Specialist

**Input:** Final manuscript, front/back matter
**Process:**
1. Strip all hardcoded formatting from source
2. Apply proper heading styles: Heading 1 for chapter titles, Heading 2 for subheadings, Normal for body
3. Set body: serif font for fiction, sans-serif for nonfiction, 11-12pt, line spacing 1.15-1.3
4. Apply first-line indent 0.25-0.3 inches (fiction) or block paragraphs with space after (nonfiction)
5. Create live Table of Contents from heading styles
6. Insert front matter: title page (half-title + full title), copyright page (pre-filled with KDP boilerplate), dedication, TOC
7. Insert back matter: author bio with links, also-by list with links, CTA for reviews with link
8. Ensure images (if any) are 300 DPI, JPG/PNG, under 3MB total file size
9. Export as EPUB (preferred) or DOCX
10. Name file: `Book-Title-KINDLE-EPUB-v1.epub`
**Output:** Format-ready EPUB file

### Agent 3.2 — Print Layout Engineer

**Input:** Final manuscript, front/back matter, trim size selection
**Process:**
1. Select trim size based on genre (fiction: 5×8" or 5.5×8.5"; nonfiction: 6×9"; children's: 8×10")
2. Set margins: inside gutter 0.75", outside/top/bottom 0.5-0.75"
3. Add 0.125" bleed if any elements touch page edge
4. Apply body font: serif 10-12pt for fiction, 10-11pt for nonfiction
5. Chapter headings: centered or drop, 18-24pt, consistent
6. Page numbers: bottom center or outer, starting after TOC
7. Front matter: lowercase Roman numerals for front matter pages
8. Spine width calculation: page count × paper thickness (standard B&W: ~0.0025"/page)
9. Export as PDF/X-1a (print standard)
10. Name file: `Book-Title-PAPERBACK-v1.pdf` and `Book-Title-HARDCOVER-v1.pdf`
**Output:** Print-ready PDF files

### Agent 3.3 — Validation & Preview Tester

**Input:** EPUB + PDF files
**Process:**
1. Run EPUB through Kindle Previewer — check all devices (Paperwhite, Oasis, Scribe, iOS, Android, Fire)
2. Check: TOC links work, chapter breaks render, images display, no missing fonts, no text overflow
3. Run print PDF through KDP's print preview — check margins, trim, bleed, spine text
4. Verify page count against estimated (should be within ±5%)
5. Check file sizes: EPUB < 10MB (ideally < 3MB for 70% royalty), PDF < 50MB
6. Generate preview screenshots for user approval
**Output:** Validation report (Pass/Fail) with screenshots

---

## Stage 4: Cover Design

### Agents

| ID | Agent | Role |
|----|-------|------|
| 4.1 | **Cover Strategist** | Defines cover direction based on genre benchmarks |
| 4.2 | **Cover Designer** | Generates 3 cover concepts |
| 4.3 | **Thumbnail Tester** | Evaluates covers at Amazon thumbnail size (≈ 1" × 1.5") |

### Workflow

```
Agent 4.1 (Strategy) → Agent 4.2 (Concepts) → Agent 4.3 (Thumbnail test)
    → user selects winner → refinements → Gate 4→5
```

### Agent 4.1 — Cover Strategist

**Input:** Niche research report, competitor top 20 covers
**Process:**
1. Analyze top 20 bestselling covers in the niche — what visual language do they share?
2. Identify 3 cover styles common in the niche:
   - **Style A:** Dominant (most common — follow to fit in)
   - **Style B:** Subversive (different enough to stand out but still genre-recognizable)
   - **Style C:** Premium (upscale look that signals higher quality)
3. Define color palette for the niche (dark & moody for thriller, bright & illustrated for cozy mystery, minimalist for business)
4. Identify typography conventions (serif vs sans-serif, all-caps vs title case, gold foil effect vs flat color)
5. Note: what makes a cover look "amateur" vs "professional" in this niche?
6. Provide mockup brief: front cover elements, spine text, back cover elements, barcode placement
**Output:** Cover design brief with genre-conforming specifications

### Agent 4.2 — Cover Designer

**Input:** Cover design brief, book title/subtitle, author name, blurb (for back cover)
**Process:**
1. Create 3 distinct concepts following the brief:
   - **Concept A:** Genre-safe (matches top sellers closely)
   - **Concept B:** Standout (unique angle, higher differentiation)
   - **Concept C:** Premium (designed to look like a traditional publisher release)
2. Each concept includes:
   - Full front cover with title + subtitle + author name
   - Full spine with title + author
   - Full back cover with blurb, barcode area, author photo area
   - Dimensions match chosen trim size + 0.125" bleed
3. Format: 300 DPI CMYK PDF + JPEG preview
4. Ensure title is readable at thumbnail size (Amazon search results: ~1" × 1.5" on desktop)
5. Test: no text too close to trim edge, barcode area clear
**Output:** 3 full cover sets (front + spine + back) in print-ready PDF + JPEG preview

### Agent 4.3 — Thumbnail Tester

**Input:** 3 cover concepts
**Process:**
1. Resize each cover to Amazon thumbnail dimensions (approx 160 × 240 px)
2. Place each thumbnail next to competitor thumbnails in a simulated search results grid
3. Evaluate:
   - Visibility: does it stand out in a grid of 8-12 covers?
   - Readability: can you read the title at thumbnail size?
   - Genre clarity: can you tell what genre it is at a glance?
4. Pick the concept that performs best in thumbnail context
5. Recommend refinements if needed (larger title font, higher contrast, simpler composition)
**Output:** Thumbnail comparison grid + recommended winner + refinement suggestions

---

## Stage 5: Listing Optimization

### Agents

| ID | Agent | Role |
|----|-------|------|
| 5.1 | **Keyword Packager** | Finalizes and optimizes all 7 backend keyword slots |
| 5.2 | **Blurb Writer** | Crafts the Amazon book description |
| 5.3 | **Category Sourcer** | Identifies the 3 best categories for ranking |
| 5.4 | **A+ Content Designer** | Creates Enhanced Brand Content (if brand-registered) |

### Workflow

```
Agent 5.1 (Keywords) ─┐
Agent 5.2 (Blurb)    ─┤──→ user approval → Gate 5→6
Agent 5.3 (Category) ─┘
Agent 5.4 (A+)       ─┘ (optional)
```

### Agent 5.1 — Keyword Packager

**Input:** Niche keywords from Stage 1 (Agent 1.2), title/subtitle
**Process:**
1. Gather all keyword research from Stage 1
2. Remove words already in title + subtitle (Amazon ignores duplicates)
3. Group remaining keywords into 7 groups of 50 characters or less
4. Apply optimization rules:
   - No commas between words (spaces only — commas waste characters)
   - Order by importance within each slot
   - Include: synonyms, misspellings, related terms, long-tail phrases
   - Include audience descriptors ("for beginners", "advanced guide", "thriller fans")
   - Include format terms if relevant ("box set", "series", "trilogy")
5. Each slot max 50 characters, total across 7 slots max 350
6. Validate: no competitor trademarks, no offensive terms, no Amazon policy violations
**Output:** 7 optimized keyword strings (50 chars each)

### Agent 5.2 — Blurb Writer

**Input:** Book manuscript, niche research, competitor blurbs
**Process:**
1. Analyze top 5 competitor blurbs — what hooks work? What patterns repeat?
2. Write blurb following proven Amazon structure:
   - **Hook (first 3 lines):** Problem, question, or compelling statement that grabs attention (this is what shows "above the fold" before "See more")
   - **Stakes:** What's at risk? What transformation awaits?
   - **Bullet points (3-5):** Key features/benefits/themes
   - **Social proof:** "If you like [Comp Author], you'll love..."
   - **Call to action:** "Scroll up and click Buy Now"
3. Keep under 3,000 characters (Amazon limit)
4. Use short paragraphs (1-3 sentences), no walls of text
5. For fiction: set tone, introduce protagonist, establish conflict, tease but don't spoil
6. For nonfiction: state problem → promise solution → preview key chapters → establish authority
7. No formatting HTML needed unless specific styling required (Amazon supports bold, italic, line breaks)
**Output:** Amazon-optimized blurb (under 3,000 chars)

### Agent 5.3 — Category Sourcer

**Input:** Niche category paths from Stage 1 (Agent 1.1)
**Process:**
1. Review all category paths used by top 20 competitors
2. Check BSR thresholds for each category:
   - What BSR is #1 in that category?
   - What BSR is #20 in that category?
3. Select 3 categories where the user can realistically hit top 20
4. Prioritize: 2 niche categories (easier to rank) + 1 broader category (if viable)
5. Verify categories exist in KDP's current dropdown (Amazon sometimes consolidates)
6. Check for category policy changes — some categories require approval (e.g., erotica, religious)
**Output:** 3 recommended KDP categories with BSR thresholds

### Agent 5.4 — A+ Content Designer (Optional)

**Input:** Book manuscript, author brand assets, niche research
**Process:**
1. Determine if user is brand-registered (required for A+ Content)
2. If not registered, recommend registration process (trademark filing, brand registry)
3. Design A+ Content modules:
   - **Hero image:** Book cover + tagline
   - **Comparison chart:** How this book compares to competitors
   - **Feature-benefit blocks:** 3-4 modules highlighting key aspects
   - **Author bio + authority:** Establish credibility
   - **Series banner:** If part of series
4. Keep text concise — A+ is visual, not a second blurb
5. Use lifestyle images (people using/reading the book), not just stock photos
**Output:** A+ Content layout with image briefs + text copy

---

## Stage 6: Amazon Advertising

### Agents

| ID | Agent | Role |
|----|-------|------|
| 6.1 | **Campaign Architect** | Structures the ad account — campaigns, ad groups, budgets |
| 6.2 | **Keyword Bidder** | Sets initial bids by keyword match type |
| 6.3 | **Product Targeting Specialist** | Identifies competitor ASINs for product targeting ads |
| 6.4 | **Budget Optimizer** | Calculates optimal daily budget based on BSR targets |

### Workflow

```
Agent 6.1 (Structure) → Agent 6.2 (Keywords) + Agent 6.3 (ASINs)
    → Agent 6.4 (Budget) → user confirms budget → Gate 6→7
```

### Agent 6.1 — Campaign Architect

**Input:** Niche research, book price, royalty per unit
**Process:**
1. Set up campaign structure:
   - **Campaign A — Auto-target (Discovery):** Let Amazon match keywords. Low bids. Used for data gathering.
   - **Campaign B — Broad/Phrase (Scale):** Manual keywords, broad + phrase match. Main volume driver.
   - **Campaign C — Exact (Precision):** High-converting exact-match keywords. Highest bids.
   - **Campaign D — Product Targeting (Competitors):** Target competitor ASINs. Steal their audience.
2. Each campaign gets 1 ad group initially (expand later)
3. Set default bid: 50% of max allowable ACoS bid
**Output:** Campaign structure with naming convention, default bids, targeting strategy

### Agent 6.2 — Keyword Bidder

**Input:** Keyword list from Stage 5 (Agent 5.1), competition analysis
**Process:**
1. Classify keywords into tiers:
   - **Tier 1 (Exact):** Core, high-intent keywords from niche research — highest bid
   - **Tier 2 (Phrase):** Related phrases — medium bid
   - **Tier 3 (Broad):** Topical terms — lowest bid
   - **Negative keywords:** Irrelevant terms (filter immediately)
2. Set initial bids by competitiveness:
   - Low competition niche: $0.30-0.60 bids
   - Medium competition niche: $0.60-1.00 bids
   - High competition niche: $1.00-2.00+ bids
3. Calculate max bid: (royalty per unit × target ACoS) ÷ conversion rate
   - Example: $3.04 royalty, 30% ACoS target, 8% conversion rate → max bid = ($3.04 × 0.30) / 0.08 = $11.40... but cap at $1.50 initially
4. Set at least 20 keywords per manual campaign
**Output:** Bidding table — keyword, match type, initial bid

### Agent 6.3 — Product Targeting Specialist

**Input:** Competitor top 20 list from Stage 1 (Agent 1.1)
**Process:**
1. Identify 10-20 competitor ASINs to target
2. Prioritize:
   - Books with similar content, price range, and audience
   - Books with BSR 5,000-50,000 (not too big, not too small)
   - Books with 50-500 reviews (engaged audience, but not too expensive to target)
3. Avoid targeting: books by the same author (cannibalization), books in different subgenres, mega-bestsellers (too expensive)
4. Set lower bids for product targeting (usually converts at higher rate but lower volume)
**Output:** Target ASIN list with bid adjustments

### Agent 6.4 — Budget Optimizer

**Input:** Campaign structure, BSR target, book economics
**Process:**
1. Estimate required sales for target BSR:
   - Target BSR 20,000: ~100-150 sales/month → ~3-5 sales/day
   - Target BSR 10,000: ~200-300 sales/month → ~7-10 sales/day
2. Calculate required ad spend:
   - Organic sales ratio (50-70% for established books, 10-30% for new releases)
   - Ad sales needed = Total sales − Organic sales
   - Ad spend = Ad sales × (CPC / Conversion rate)
3. Set daily budget: $5-10/day minimum, $20-50/day for aggressive launch
4. Set monthly budget cap
5. Include ramp-up schedule: start conservative → increase after 7 days of positive ACoS
**Output:** Daily budget recommendation, monthly budget cap, ramp schedule

---

## Stage 7: Launch Strategy

### Agents

| ID | Agent | Role |
|----|-------|------|
| 7.1 | **Timeline Planner** | Builds the full launch calendar |
| 7.2 | **ARC Coordinator** | Manages Advanced Reader Copy distribution and review collection |
| 7.3 | **Promotion Sequencer** | Schedules KDP Select Free Days + Countdown Deals |
| 7.4 | **Launch Day Commander** | Coordinates all launch-day timing and execution |

### Workflow

```
Agent 7.1 (Timeline) → Agent 7.2 (ARCs) + Agent 7.3 (Promos)
    → Agent 7.4 (Launch Day) → Gate 7→8
```

### Agent 7.1 — Timeline Planner

**Input:** All prior stage outputs, seasonality data
**Process:**
1. Work backward from target launch date (ideally 4-6 weeks from pipeline start)
2. Build timeline:
   - **T-6 weeks:** Niche research complete → content creation begins
   - **T-4 weeks:** Manuscript complete → formatting + cover begins
   - **T-3 weeks:** ARC outreach begins → send advance copies
   - **T-2 weeks:** Listing created in KDP (unpublished/coming soon) → set up pre-order if desired
   - **T-10 days:** Amazon Ads campaigns created (paused until launch)
   - **T-7 days:** Email list teaser → "coming soon" announcement
   - **T-3 days:** ARC reviews should start coming in → add to listing
   - **T-1 day:** Final review of all listing components
   - **T-0 (Launch Day):** Publish → unpause ads → email list launch announcement
   - **T+7 days:** First performance review
   - **T+14 days:** First ad optimization pass
   - **T+30 days:** Category ranking check → consider category change requests
   - **T+90 days:** KDP Select renewal decision
3. Account for marketplace-specific timelines (each Amazon marketplace has different review times)
**Output:** Full launch calendar with milestones, dependencies, and deadlines

### Agent 7.2 — ARC Coordinator

**Input:** Book metadata, genre, target audience
**Process:**
1. Determine ARC distribution strategy:
   - **Booksprout:** Best for fiction, integrated with Amazon, cost-effective
   - **BookSirens:** Curated reviewer base, good for nonfiction
   - **NetGalley:** Premium ($350-450), best for big launches, trade reviews
   - **Own street team:** Email list subscribers, most reliable
2. Determine number of ARC copies needed:
   - Target: 20-50 reviews within first month
   - Typical conversion: 30-50% of ARC recipients leave a review
   - Send 60-100 ARC copies minimum
3. Prepare ARC materials:
   - eBook copy (EPUB/MOBI)
   - One-page summary/cheat sheet for reviewers
   - Review guidelines (what to cover, what not to spoil)
   - Deadline for review (1-2 weeks before launch)
4. Set up tracking: spreadsheet or tool to track sent/received/posted
5. Follow-up sequence: Day 1 (thanks + access), Day 7 (reminder), Day 14 (final reminder), Post-launch (thank you + link to live listing)
**Output:** ARC distribution plan, reviewer outreach template, tracking system

### Agent 7.3 — Promotion Sequencer

**Input:** KDP Select enrollment status, pricing strategy
**Process:**
1. If enrolled in KDP Select, plan 90-day promotion calendar:
   - **Free Book Promotion (5 days per 90-day period):**
     - Best timing: When BSR is not yet established (weeks 1-2)
     - Day 1-3: Free promotion → spike downloads → boost BSR → organic visibility
     - Do NOT run free promotion if you have active ARC reviews coming in (waste of reviews)
   - **Kindle Countdown Deal (limited days per 90-day period):**
     - Best timing: After organic rank is established (weeks 3-6)
     - Discount by 20-30% from regular price
     - Creates urgency with countdown clock + strikethrough pricing
   - Schedule: Free promo first → Countdown Deal 2-3 weeks later
2. If wide distribution:
   - Plan BookBub submission (6-8 weeks lead time)
   - Schedule price promotions on other platforms (Kobo, Apple Books, Google Play)
3. Avoid promo fatigue — at least 2 weeks between promotions
**Output:** 90-day promotion schedule with dates, discount levels, expected outcomes

### Agent 7.4 — Launch Day Commander

**Input:** All launch materials, ARC reviews, promotion schedule
**Process:**
1. **T-24 hours (Pre-launch checklist):**
   - Verify listing is live and visible on Amazon
   - Verify all categories are applied
   - Verify price is correct across all marketplaces
   - Verify "Look Inside" feature works
   - Verify buy buttons work (eBook + paperback)
   - Screenshot the listing for records
2. **T-0 (Launch: morning):**
   - Hit "Publish" or confirm pre-order goes live
   - Unpause all ad campaigns
   - Send launch email to email list
   - Post on social media (all platforms)
   - Submit to relevant deal newsletters (if applicable)
3. **T+0 to T+3 (Launch: monitoring):**
   - Monitor BSR every 6 hours — log the data
   - Monitor ad performance — watch for anomalies (spikes in spend, drops in conversion)
   - Monitor reviews — respond within 24 hours (professional tone for negative)
   - Monitor "Also Boughts" — check which books appear (your target competitors?)
4. **T+7 (First review checkpoint):**
   - How many reviews? Target: 10+ minimum
   - What's the average rating? Target: 4.0+ (below 3.8 = problem)
   - BSR trend: improving or flat?
   - ACoS: within 30% target?
5. **Escalation triggers:**
   - If ACoS > 50% after 3 days → pause campaigns, re-evaluate keywords
   - If 0 sales after 48 hours → check listing errors, pricing, categorization
   - If 3+ negative reviews in first week → evaluate if product or placement problem
**Output:** Launch day playbook + monitoring dashboard

---

## Stage 8: Post-Launch Monitoring & Optimization

### Agents

| ID | Agent | Role |
|----|-------|------|
| 8.1 | **BSR & Sales Tracker** | Monitors ranking trends, detects drops/spikes |
| 8.2 | **Ad Performance Optimizer** | Adjusts bids, pauses underperformers, scales winners |
| 8.3 | **Review & Sentiment Monitor** | Tracks new reviews, analyzes sentiment, flags crises |
| 8.4 | **Competitive Intelligence Updater** | Rescans the niche quarterly for new entrants and ranking shifts |
| 8.5 | **Catalog Expansion Advisor** | Recommends next book based on performance data |

### Workflow

```
Phase 1 (Week 1-4): Daily monitoring by Agents 8.1, 8.2, 8.3
Phase 2 (Month 2+): Weekly monitoring, Agent 8.4 quarterly, Agent 8.5 monthly
```

### Agent 8.1 — BSR & Sales Tracker

**Input:** KDP Reports data, Amazon product page BSR
**Process:**
1. Track daily BSR across all categories the book is in
2. Log sales estimates (derived from BSR using conversion tables)
3. Detect anomalies:
   - BSR drop > 20% in 24 hours → investigate (competitor promo? algorithm change?)
   - BSR spike > 50% → investigate (negative review? price change?)
4. Track KU page reads (KENP) — daily total, trend direction
5. Calculate estimated daily revenue: (eBook sales × royalty) + (paperback sales × royalty) + (KENP × rate)
6. Generate weekly dashboard: BSR chart, revenue chart, KU chart
**Output:** Weekly performance dashboard with trend alerts

### Agent 8.2 — Ad Performance Optimizer

**Input:** Amazon Ads reports
**Process:**
1. Weekly ad optimization pass:
   - **Pause:** Keywords with ACoS > 50% and no sales after 100+ clicks
   - **Reduce bids:** Keywords with ACoS 30-50% — drop bid by 10-15%
   - **Maintain:** Keywords with ACoS 15-30% — keep as is
   - **Increase bids:** Keywords with ACoS < 15% — increase bid by 10-15% to capture more volume
   - **Add negatives:** Search terms that cost > $5 without a conversion
2. Add new keywords from search term reports (terms that converted but aren't targeted)
3. Adjust daily budget weekly:
   - If spend exceeds budget 3+ days in a row → increase budget by 20%
   - If spend is < 50% of budget consistently → decrease budget by 20%
4. Monthly: duplicate best-performing ad group into its own campaign for scaling
**Output:** Weekly optimization actions, updated bids, budget adjustments

### Agent 8.3 — Review & Sentiment Monitor

**Input:** Amazon product page reviews
**Process:**
1. Monitor new reviews daily in first month, weekly thereafter
2. Classify each review:
   - **Positive (4-5★):** Log praise patterns (what do readers love? — use in future blurbs)
   - **Neutral (3★):** Log concerns, look for patterns
   - **Negative (1-2★):** Flag immediately — assess validity and severity
3. Sentiment analysis:
   - Track recurring themes (positive and negative)
   - If 3+ reviews mention the same issue → escalate to revision queue
   - If 5+ reviews mention the same praise → use in A+ Content or ad copy
4. Respond to negative reviews professionally:
   - Acknowledge the issue, thank the reader, offer resolution if applicable
   - DO NOT argue, defend, or attack
   - DO NOT review-gamify (offering incentives for review changes is against T&C)
5. Monthly: update book quality based on review patterns
   - If editing complaints > 20% of negative reviews → schedule revision
   - If content gap complaints > 30% → plan sequel or companion book
**Output:** Review log, sentiment trends, escalation flags

### Agent 8.4 — Competitive Intelligence Updater

**Input:** Current top 20 in niche, BSR data
**Process:**
1. Every 90 days, re-run Stage 1 (Agents 1.1-1.3) for the niche
2. Compare against original research:
   - New competitors entered?
   - Prices changed?
   - New categories emerged?
   - Seasonality patterns confirmed?
3. Identify:
   - If competition increased significantly → consider new niches or differentiation
   - If competition decreased → opportunity to increase ad spend
   - If new sub-niches emerged → opportunity for next book
4. Update the Opportunity Score for the niche (has it improved or degraded?)
**Output:** Quarterly competitive landscape update

### Agent 8.5 — Catalog Expansion Advisor

**Input:** All performance data from 8.1-8.4
**Process:**
1. Analyze what's working:
   - Which genre/category performs best?
   - Which keywords drive most sales?
   - Which price point maximizes revenue?
   - Which book length gets best reviews?
2. Recommend next book direction:
   - **Sequels/Series:** If fiction with good KU read-through → prioritize next in series
   - **Companion book:** If nonfiction with good sales → expand on a popular chapter topic
   - **New niche:** If current niche is saturated → recommend new validated niche from Stage 1
   - **Format expansion:** If eBook performs well but no paperback → add paperback
   - **International:** If US sales strong → translate for DE/UK/JP/FR marketplaces
3. Estimate ROI for each option:
   - Sequel: fastest time-to-market, highest probability of success (existing audience)
   - New niche: longer time-to-market, lower probability but potentially higher ceiling
   - Translation: moderate time-to-market, good ROI if US book is proven
4. Prioritize: rank options by expected ROI ÷ time investment
**Output:** Next-book recommendation with rationale, expected ROI, development timeline

---

## Pipeline Orchestration Rules

### Stage Gates

Every stage has a mandatory gate before the next stage can begin:

| Gate | Condition | Action on Fail |
|------|-----------|----------------|
| **G1→2** | Opportunity Score ≥ 60 | Return to Stage 1 with different niche |
| **G2→3** | User approves final manuscript | Return to Agent 2.3 for revision |
| **G3→4** | Validation Test PASS | Fix formatting errors, re-run validation |
| **G4→5** | User approves selected cover | Return to Agent 4.2 for new concepts |
| **G5→6** | User approves listing components | Revise based on feedback |
| **G6→7** | User confirms ad budget | Adjust budget or scale back campaigns |
| **G7→8** | Launch executed successfully | Debug listing issues, retry |

### Error Handling

- **Agent timeout:** 30-second max per sub-agent task. Orchestrator logs timeout, proceeds with partial data.
- **Conflicting agent outputs:** Orchestrator flags both to user with recommendation.
- **Critical failure (any stage):** Pipeline pauses, user notified, rollback to last successful stage.
- **User unresponsive at gate:** Default to "proceed with current data" after 48 hours.

### Resource Budget

Pipeline tracks estimated costs per stage:

| Stage | Estimated Cost | Notes |
|-------|---------------|-------|
| 1. Niche Research | $0 (free tools) | |
| 2. Content Creation | $0-2,000 | $0 if self-written, $500-2,000 if ghostwritten |
| 3. Formatting | $0-300 | $0 if DIY, $50-300 if hired out |
| 4. Cover Design | $0-500 | $0 if DIY (Canva), $100-500 if professional |
| 5. Listing Optimization | $0 | DIY |
| 6. Amazon Ads | $150-450/month | $5-15/day at 30-day launch |
| 7. Launch Strategy | $0-500 | $0 if organic launch, $350-500 if NetGalley |
| 8. Post-Launch | $150-450/month ongoing | Ads + tools subscriptions |

### Quick Start Commands

```
# Full pipeline from scratch
kdpfy pipeline full --genre "sci-fi" --subgenre "space opera"

# Resume from checkpoint
kdpfy pipeline resume --stage 3 --book-id "my-book-v1"

# Run single stage
kdpfy pipeline stage 6 --book-id "my-book-v1" --ad-budget $10

# Quick validation of existing assets
kdpfy pipeline validate --epub "my-book.epub" --cover "cover.jpg"

# Generate report without publishing
kdpfy pipeline report --book-id "my-book-v1" --format "pdf"
```

### Agent Communication Protocol

All agents communicate via structured JSON payloads:

```json
{
  "pipeline_id": "uuid",
  "stage": 3,
  "agent_id": "3.1",
  "status": "complete",
  "confidence": 0.92,
  "output": { ... },
  "artifacts": [ "my-book-KINDLE-EPUB-v1.epub" ],
  "errors": [],
  "warnings": [ "File size 3.2MB — near 70% royalty threshold" ],
  "next_agent": "3.3"
}
```

### Agent Inventory Summary

| Stage | Agent ID | Agent Name | Dependencies |
|-------|----------|------------|-------------|
| **Stage 1** | 1.1 | Market Scanner | None |
| | 1.2 | Keyword Analyst | None |
| | 1.3 | Competition Analyzer | None |
| | 1.4 | Profitability Assessor | 1.1, 1.3 |
| | 1.5 | Trend & Seasonality Analyst | None |
| | 1.6 | Opportunity Scorer | 1.1-1.5 |
| **Stage 2** | 2.1 | Outline Architect | Stage 1 |
| | 2.2 | Draft Writer | 2.1 |
| | 2.3 | Editor | 2.2 |
| | 2.4 | Beta Reader Synthesizer | 2.3 |
| | 2.5 | Quality Assurance | 2.4 |
| **Stage 3** | 3.1 | eBook Format Specialist | Stage 2 |
| | 3.2 | Print Layout Engineer | Stage 2 |
| | 3.3 | Validation & Preview Tester | 3.1, 3.2 |
| **Stage 4** | 4.1 | Cover Strategist | Stage 1 |
| | 4.2 | Cover Designer | 4.1 |
| | 4.3 | Thumbnail Tester | 4.2 |
| **Stage 5** | 5.1 | Keyword Packager | Stage 1 |
| | 5.2 | Blurb Writer | Stage 2 |
| | 5.3 | Category Sourcer | Stage 1 |
| | 5.4 | A+ Content Designer | Stage 2 |
| **Stage 6** | 6.1 | Campaign Architect | Stage 1, 5 |
| | 6.2 | Keyword Bidder | 6.1 |
| | 6.3 | Product Targeting Specialist | Stage 1 |
| | 6.4 | Budget Optimizer | 6.1, 6.2, 6.3 |
| **Stage 7** | 7.1 | Timeline Planner | All prior stages |
| | 7.2 | ARC Coordinator | Stage 2 (manuscript) |
| | 7.3 | Promotion Sequencer | Stage 5 (pricing) |
| | 7.4 | Launch Day Commander | 7.1, 7.2, 7.3 |
| **Stage 8** | 8.1 | BSR & Sales Tracker | Stage 7 |
| | 8.2 | Ad Performance Optimizer | Stage 6, 8.1 |
| | 8.3 | Review & Sentiment Monitor | Stage 7 |
| | 8.4 | Competitive Intelligence Updater | Stage 1, 8.1 |
| | 8.5 | Catalog Expansion Advisor | 8.1, 8.2, 8.3, 8.4 |
