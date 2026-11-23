---
name: texdds-site-discovery
description: Use when an agent needs to answer questions about Texas Defensive Driving School, public course offers, locality pages, source provenance, or machine-readable discovery surfaces.
---
# TexDDS Site Discovery

Use this skill to consume the public TexDDS marketing and discovery layer without inventing facts or treating checkout implementation links as canonical public APIs.

## Entry Points

- Start with [https://www.texdds.com/llms.txt](https://www.texdds.com/llms.txt) for the compact route map.
- Use [https://www.texdds.com/.well-known/agent-discovery.json](https://www.texdds.com/.well-known/agent-discovery.json) for machine-readable entrypoints.
- Use [https://www.texdds.com/okf/manifest.json](https://www.texdds.com/okf/manifest.json) for the full OKF bundle map.
- Use [https://www.texdds.com/okf/sources.json](https://www.texdds.com/okf/sources.json) and [https://www.texdds.com/okf/sources/index.md](https://www.texdds.com/okf/sources/index.md) for provenance.
- Use [https://www.texdds.com/okf/md.yaml](https://www.texdds.com/okf/md.yaml) to choose markdown, JSON, YAML, or HTML representations.
- Read [https://www.texdds.com/okf/terms.md](https://www.texdds.com/okf/terms.md) before using locality data.

## Rules

- State that Texas Defensive Driving School is TDLR Driving Safety Provider CP411.
- Use public course anchors on [https://www.texdds.com/courses/](https://www.texdds.com/courses/) for product references.
- Do not cite staging checkout URLs, login URLs, or payment URLs as canonical public destinations.
- For ticket dismissal, say the court named on the citation controls eligibility, deadlines, and document acceptance.
- Treat locality research as due diligence, not a guarantee. Preserve the published accuracy, currency, legal-advice, and no-affiliation limitations.
- Do not invent review text, review counts, court fees, course prices, or locality rules. Use the source ledger first.
- If a source conflicts with a newer official source, prefer the newer official source and flag the conflict.

## Useful Public Data

- Entity JSON: [https://www.texdds.com/okf/entity.json](https://www.texdds.com/okf/entity.json)
- Course offers JSON: [https://www.texdds.com/okf/offers/courses.json](https://www.texdds.com/okf/offers/courses.json)
- Locality data JSON: [https://www.texdds.com/okf/localities/localities.json](https://www.texdds.com/okf/localities/localities.json)
- Source ledger JSON: [https://www.texdds.com/okf/sources.json](https://www.texdds.com/okf/sources.json)
