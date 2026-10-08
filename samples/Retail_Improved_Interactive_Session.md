# Retail Sales Analytics — Improved Interactive Analyst Session

This session demonstrates InsightForge's improved deterministic analytics workflow. The v1.1 engine extends descriptive reporting with a profit-at-risk concentration diagnostic that identifies markets where 30%+ discount losses are disproportionately concentrated relative to the market's sales footprint.

---

## InsightForge > Which markets have disproportionate exposure to high-discount profit losses?

Total Profit is a scale-dependent business metric. The profit-at-risk diagnostic identifies markets where 30%+ discount losses are disproportionately concentrated relative to the market's sales footprint. This supports prioritization of disproportionate exposure without establishing that discounting caused the loss.

### Priority Diagnostic

| Market | Sales Share | 30%+ Loss Share | Concentration |
|---|---:|---:|---:|
| **EMEA** | **6.38%** | **15.12%** | **2.37×** |
| Africa | 6.20% | 10.90% | 1.76× |
| LATAM | 17.12% | 17.87% | 1.04× |

EMEA represents **6.38% of total sales but 15.12% of 30%+ discount losses**, producing a **2.37× concentration**.

This indicates disproportionate exposure relative to the market's sales footprint and provides a stronger prioritization signal than absolute loss alone.

> The diagnostic does **not** establish that discounting caused the losses.

---

## InsightForge > What changed from the original analysis?

The original analysis ranked markets primarily by absolute 30%+ discount loss.

Under that approach, the top three markets were:

1. EU — 0.87× concentration
2. APAC — 0.68× concentration
3. LATAM — 1.04× concentration

The improved diagnostic prioritizes **disproportionate exposure** instead:

1. **EMEA — 2.37×**
2. **Africa — 1.76×**
3. **LATAM — 1.04×**

The improved diagnostic therefore changes the priority list from **EU, APAC, and LATAM** to **EMEA, Africa, and LATAM**.

This ranking intentionally prioritizes **disproportionate exposure** rather than total absolute loss.

---

## Business Interpretation

The improved diagnostic changes the business question from:

> Which market has the largest absolute high-discount loss?

to:

> Which market is carrying a disproportionately large share of high-discount losses relative to its sales footprint?

This makes **EMEA the highest-priority market for investigation**, despite having a relatively small overall sales footprint.

---

## Analytical Validation

The new prioritization was evaluated against the v1.0 baseline before being retained.

### Experiment Result

| Measure | v1.0 Baseline | v1.1 Improved |
|---|---:|---:|
| Priority method | Absolute loss | **Disproportionate exposure** |
| Top priority | EU | **EMEA** |
| Avg. top-3 concentration | 0.86× | **1.72×** |
| Change | — | **+99.6%** |
| Decision | — | **KEEP** |

### What changed?

**Before**

> Which market has the largest absolute high-discount loss?

**After**

> Which market is carrying a disproportionately large share of high-discount losses relative to its sales footprint?

### Validation Outcome

**KEEP — the improved diagnostic produced a materially different priority list and increased the average concentration of the prioritized markets from 0.86× to 1.72×.**

The new ranking intentionally prioritizes **disproportionate exposure**, not total absolute loss. The top-three markets' share of total absolute high-discount loss decreased from **57.34% to 43.87%**, reflecting this deliberate trade-off.

All conclusions remain bounded by deterministic evidence from the SQL/Python analytics engine.