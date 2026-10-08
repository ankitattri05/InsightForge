# Telecom Service Assurance — Improved Interactive Analyst Session

This session demonstrates InsightForge's improved deterministic analytics workflow. The v1.1 engine extends SLA reporting with excess-breach impact analysis, translating breach rates into estimated business impact and prioritization.

---

## InsightForge > Which fault category has the greatest SLA breach impact?

The overall SLA breach rate is **9.99%**.

The excess-breach diagnostic compares observed breaches with the number expected if each fault category performed at the overall breach rate.

### SLA Breach Impact

| Fault Category | Incident Share | Breach Share | Excess Breaches | Concentration |
|---|---:|---:|---:|---:|
| **Optical Network** | **25.67%** | **50.72%** | **625.94** | **1.98×** |
| Access Equipment | 19.47% | 31.96% | 311.79 | 1.64× |
| Power & Environment | 6.57% | 11.89% | 132.86 | 1.81× |

Optical Network represents only **25.67% of incidents but approximately 50.72% of estimated SLA breaches**, producing a **1.98× breach concentration**.

The category recorded **1,267 observed breaches** versus approximately **641 expected breaches**, resulting in approximately **626 excess breaches**.

This provides an impact-based prioritization signal rather than relying only on breach rate.

---

## InsightForge > How did the prioritization change?

A simple breach-rate ranking identifies the highest-rate categories.

The improved diagnostic instead evaluates **excess breach impact** relative to the overall SLA breach rate.

For Optical Network:

- Overall breach rate: **9.99%**
- Optical Network breach rate: **19.74%**
- Observed breaches: **1,267**
- Expected breaches: **641**
- Excess breaches: **625.94**
- Breach concentration: **1.98×**

This translates a rate difference into an estimated operational impact.

---

## Business Interpretation

The improved analysis changes the question from:

> Which category has the highest SLA breach rate?

to:

> Which category is contributing disproportionately to the organization's SLA breach burden?

**Optical Network is the highest-impact fault category**, accounting for approximately half of estimated SLA breaches while representing only about one-quarter of incidents.

The analysis identifies where the breach burden is concentrated; it does not establish the causal reason for the breaches.

---

## Analytical Validation

The impact-based prioritization was evaluated against the original rate-based analysis.

The improved ranking was retained because it translated SLA performance into measurable excess-breach impact and materially changed prioritization at the state level: **Goa** ranked first by raw breach rate, while **Punjab** ranked first by excess-breach impact with **19.39 excess breaches**.

The resulting prioritization was also tested against fault-mix adjustment. The vendor and state top-three rankings remained **3/3 unchanged**, so the impact ranking was retained.

All conclusions remain bounded by deterministic evidence from the SQL/Python analytics engine.