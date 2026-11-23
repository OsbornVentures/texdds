---
type: "AgentInstructions"
title: "TexDDS OKF Agent Instructions"
description: "Rules for consuming and maintaining the TexDDS OKF bundle."
resource: "https://www.texdds.com/okf/AGENTS.md"
tags: ["texdds", "instructions", "maintenance"]
timestamp: "2026-08-14T00:00:00-05:00"
---

# TexDDS OKF Agent Instructions

Use this bundle as a persistent, source-backed knowledge layer. Read [index.md](/okf/index.md) first, then open the specific concept files needed for the task.

## Rules

- Treat [sources/index.md](/okf/sources/index.md) and [sources/ledger.json](/okf/sources/ledger.json) as the claim ledger.
- Do not invent course prices, review text, court deadlines, provider status, or locality statistics.
- For ticket dismissal, always state that the court named on the citation decides eligibility and acceptance.
- Read [terms.md](/okf/terms.md) before using locality data. Research due diligence does not guarantee that a court rule, fee, form, deadline, address, or contact remains current.
- Use public course anchors from [offers/courses.md](/okf/offers/courses.md) for product references; do not cite checkout endpoints as canonical URLs.
- Treat checkout endpoints as gated implementation links available only from the customer Courses page.
- Keep Google and Yelp review text on their live provider profiles unless an official embeddable review feed is added later.
- Trustpilot review cards may cite exact public review URLs listed in [reviews/index.md](/okf/reviews/index.md).
- Preserve the customer site language: $25 flat course, no $3 fee, no electronic delivery fee.
- If a source conflicts with a newer official source, add the conflict to [log.md](/okf/log.md) and update the affected concept file.
- Prefer official government, court, TDLR, DPS, TxDOT, or provider-controlled pages over news sources.
- Exclude paywall-prone sources from production pages unless a non-paywalled official replacement is unavailable and the user approves the tradeoff.

## Maintenance Flow

1. Add or verify a source in the ledger.
2. Update the affected concept file.
3. Update the relevant index.
4. Append a dated entry to [log.md](/okf/log.md).
5. Regenerate the static site and run the validator.
