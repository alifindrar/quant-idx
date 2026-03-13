# SKILL: `/memo` — Lynch Pitch + Munger Invert Investment Memo

> **Command:** `/memo [TICKER]`
> **Type:** USER-FACING COMMAND SKILL
> **Version:** 1.0.0
> **Output:** Permanent markdown file saved to `memory/deep-dives/memos/[TICKER]-memo.md`
> **Sourcing Rule:** QUOTE-FIRST DISCIPLINE enforced throughout (see CLAUDE.md Guardrail #6)
> **Mental Models:** Peter Lynch (common-sense bull case) + Charlie Munger Inversion (skeptical bear case)

---

## Objective

Generate a two-part investment memo that forces rigorous thinking from both sides of a position. The memo is intentionally short, plain-English, and quote-anchored — no DCF models, no macro speculation, no jargon. It is designed to be re-read in 90 seconds to instantly reset investment conviction.

This is not a buy/sell recommendation. It is a structured thinking tool.

---

## Inputs Required

```
TICKER:  string — e.g., "AAPL", "NVDA", "META"
```

---

## Pre-Flight: Context Loading

Before writing a single word, load all available context:

```
STEP 0A: Run data-fetcher SKILL (Blocks A, B, C, D) via yfinance
  → Extract: current price, key fundamentals, analyst consensus, recent news headlines

STEP 0B: Check memory/deep-dives/industries/ for a primer matching this company's sector
  → IF FOUND: Read the primer fully. It provides the structural context for all claims.
  → IF NOT FOUND: Flag in memo header: "⚠️ No industry primer found for [SECTOR].
    Run /industry [SECTOR NAME] to create one before the next memo refresh."

STEP 0C: Check memory/deep-dives/memos/ for a prior memo on this ticker
  → IF FOUND: Note the prior memo date and its key thesis in the new memo header.
    Track whether the thesis has changed since the last memo.
  → IF NOT FOUND: Proceed. This is the first memo.

STEP 0D: Check memory/decisions/current-positions.md
  → IF already held: Add "⚠️ EXISTING POSITION" flag at top of memo.

STEP 0E: Check memory/decisions/analysis-log.md for last composite score
  → Include in memo header if available.
```

**Output a context block at the top of the memo:**
```
📂 MEMO CONTEXT
  ├─ Ticker: [TICKER] | Company: [NAME] | Sector: [SECTOR] | Industry: [INDUSTRY]
  ├─ Current Price: $[X.XX] as of [TIMESTAMP]
  ├─ Industry Primer: [✅ Loaded from memory / ⚠️ Not found]
  ├─ Prior Memo: [Date of last memo / "None — first memo"]
  ├─ Last Composite Score: [X.X / 10 or "N/A"]
  └─ Position Status: [Not held / ⚠️ EXISTING POSITION]
```

---

## Part A — The Lynch Pitch (Bull Case)

_"I want to be able to explain in two minutes why I own a stock." — Peter Lynch_

Write a short investment pitch explaining why this company COULD be a good long-term stock to own. Use simple, common-sense reasoning. Write it like you are explaining it to a thoughtful friend who knows nothing about the company.

**QUOTE-FIRST RULE:** For every financial metric or business claim, provide the exact quote from the source document FIRST, then your interpretation. Never state a metric without citing where it came from.

### Answer these 8 questions in order:

**Q1. What does the company actually do? (1 sentence)**
- State the core business in plain language. No jargon.
- Cite source: company 10-K business description or yfinance `tk.info["longBusinessSummary"]`
- Format: `[Source]: "exact quote" → plain-English interpretation`

**Q2. What is the ONE simple reason this stock could work?**
- State ONE main idea. No stories. No compound thesis.
- This is the single most important sentence in the entire memo.
- It must be falsifiable (i.e., you can state what would prove it wrong).

**Q3. How does the company actually make money?**
- Describe the revenue model with evidence from filings.
- What is the gross margin, and what does it tell you about pricing power?
- Format all metrics as: `[Source, Period]: "exact quote" → interpretation`

**Q4. What does the balance sheet look like today?**
- Debt, cash, free cash flow — state exact figures with source and period.
- Survivability question: Could this company survive a 2-year revenue decline of 20%?
- Format: `[yfinance Block B / 10-K, Year]: "key metric quote" → interpretation`

**Q5. What kind of company is this?**
Classify using Lynch's taxonomy (cite the evidence that supports the classification):
- `SLOW GROWER` — large, mature, low single-digit revenue growth
- `STALWART` — large, durable, 10–12% growth in good years
- `FAST GROWER` — small-to-mid, 20%+ growth, high risk/reward
- `CYCLICAL` — revenues track economic cycles tightly
- `TURNAROUND` — recovering from distress; thesis is mean reversion
- `ASSET PLAY` — market undervalues tangible or hidden assets

**Q6. What could go wrong? (Be honest — this is the most important question in the bull case)**
- List the 2–3 most credible risks, sourced from the company's own risk factors (10-K) or recent news.
- Format: `[10-K Risk Factors / News Source]: "exact quote" → what this actually means`

**Q7. Why might the market be missing this?**
- What does the current price imply the market believes?
- What evidence suggests the market might be wrong?
- Mark as `(inferred)` if not directly supported by a source.

**Q8. Bottom line (3–4 sentences)**
- Why it's interesting.
- What must go right for the thesis to work.
- What single fact or event would make you wrong.

---

## Part B — The Munger Invert (Bear Case)

_"Invert, always invert." — Charlie Munger_

Now assume the opposite: **this is a bad long-term investment.** Your job is to invalidate the bull case. Write with direct, skeptical tone. No jargon, no hedging language.

**QUOTE-FIRST RULE applies identically here.** Every structural weakness you cite must be grounded in a source quote or explicitly marked `(inferred)`.

### Answer these 8 questions in order:

**Q1. What is the most likely way an investor could lose money here?**
- Not a black swan. The most probable, boring, base-case path to a bad outcome.
- Cite the mechanism: price compression, margin erosion, competition, leverage, etc.

**Q2. Where is the business structurally weak?**
- Where does the company have low pricing power, high substitutability, or weak moat?
- Format: `[Source]: "exact quote" → structural implication`

**Q3. What assumptions must go right — and what is the probability they don't?**
- Identify the 2–3 critical assumptions embedded in the bull case.
- For each, find evidence of prior execution failure or structural headwinds.
- Format: `Assumption: [X] | Evidence it may be wrong: [Source]: "quote"`

**Q4. What could permanently impair earnings or cash flow?**
- Not cyclical softness. Permanent capital impairment — regulatory change, technology displacement, loss of a key customer, pricing collapse.
- Cite specific risk factors from the most recent 10-K or earnings transcript.

**Q5. Is the balance sheet a hidden risk?**
- Debt maturity schedule, pension obligations, off-balance sheet liabilities, goodwill as % of equity.
- Format all figures with source and period.

**Q6. Where could management hurt shareholders?**
- Dilution history: has share count grown? At what rate?
- Capital allocation track record: acquisitions, buybacks at cycle peaks, capex discipline.
- Executive compensation vs. returns to shareholders.
- Format: `[Source, Period]: "exact quote" → interpretation`

**Q7. Why might investors be fooling themselves?**
- What is the consensus narrative that could be wrong?
- What does the data say that contradicts the popular story?
- Mark reasoning as `(inferred)` if not directly sourced.

**Q8. What evidence would prove this bear case right?**
- Name 2–3 specific, observable signals that would confirm the bear thesis is playing out.
- These should be monitorable — e.g., "gross margin declining below X% for 2 consecutive quarters."

---

## Memo Footer

```markdown
---

## 📊 Key Data Points at Time of Writing

| Metric | Value | Source | Period |
|--------|-------|--------|--------|
| Current Price | $X.XX | yfinance Block A | [DATE] |
| Market Cap | $X.XXB | yfinance Block A | [DATE] |
| Trailing P/E | Xx | yfinance Block B | TTM |
| Forward P/E | Xx | yfinance Block B | NTM |
| Revenue (TTM) | $X.XXB | yfinance Block B | TTM |
| Revenue Growth (YoY) | X% | yfinance Block B | TTM |
| Gross Margin | X% | yfinance Block B | TTM |
| Net Margin | X% | yfinance Block B | TTM |
| Free Cash Flow | $X.XXB | yfinance Block B | TTM |
| Debt / Equity | Xx | yfinance Block B | Latest |
| Analyst Consensus | [Buy/Hold/Sell] | yfinance Block C | [DATE] |
| Mean Price Target | $X.XX | yfinance Block C | [DATE] |

## 📎 Sources Used
[numbered list of all sources cited in the memo]

## 🕐 Memo Metadata
- **Ticker:** [TICKER]
- **Created:** [DATE]
- **Next Review Trigger:** Before next earnings ([DATE if known]) or if price moves ±15%
- **Thesis Stability:** [STABLE / WATCH / REVISIT — based on how much has changed since last memo]

> ⚠️ This memo is a structured thinking tool, not a trade recommendation.
> All analysis is for informational purposes only.
```

---

## File Save Instructions

1. Save to: `memory/deep-dives/memos/[TICKER]-memo.md`
2. If a previous memo exists at that path → save new file as `[TICKER]-memo-[YYYYMMDD].md` to preserve history. Do NOT overwrite.
3. Confirm: `"✅ Memo saved: memory/deep-dives/memos/[TICKER]-memo.md"`
4. Suggest next steps:
   ```
   💡 Next steps:
   - Run /analyze [TICKER] for the full quantitative scoring pipeline.
     The memo will load automatically as qualitative context.
   - Re-run /memo [TICKER] after next earnings to track thesis drift.
   ```

---

## Quality Gates

Before saving, verify:

- [ ] Every financial metric cited has a source label and period.
- [ ] Every inference is explicitly marked `(inferred)`.
- [ ] No claim relies on AI training knowledge without a sourced document.
- [ ] Bull case and bear case are written from genuinely opposite perspectives — not the same view with different framing.
- [ ] Q8 in both sections names specific, observable, falsifiable signals.
- [ ] No valuation models (DCF, multiples-based price targets) are included unless drawn directly from an analyst source with citation.

---

## Error Handling

| Condition | Response |
|-----------|---------|
| yfinance Block B returns all nulls | Continue. Note: "Fundamental data unavailable from yfinance — qualitative sections based on SEC filings and news only." Attempt to fetch 10-K from SEC EDGAR via web search. |
| No industry primer and no SEC filings found | Write memo with LOW confidence rating. Flag every inference clearly. |
| Company is non-US / ADR | Note that SEC filings may be 20-F not 10-K. Adjust source references accordingly. |
| Ticker not recognized by yfinance | Abort: "⛔ [TICKER] not recognized. Verify ticker symbol and exchange suffix (e.g., BABA, BABA.HK)." |
