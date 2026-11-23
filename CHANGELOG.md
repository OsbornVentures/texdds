# Changelog

Dates use America/Chicago. Entries before November 23, 2026 are imported from
local release records and the site's existing public OKF log. They are not
historical Git commits or retroactive build attestations.

## 2026-11-23 — Public static handoff (v1.0.0)

- Imported the current production static website: 113 files, including 111
  assets and two Cloudflare configuration files; 36 HTML pages and all media,
  knowledge exports, discovery files, sitemap and redirects.
- Verified every deployed asset against the current Cloudflare production
  manifest, with no differing, missing or extra static assets.
- Imported the public content log, page-date history and selected local
  deployment/verification records with original-file SHA-256 hashes.
- Added a restrictive public-file `.gitignore`, byte-preserving Git attributes,
  static validation, deterministic release ZIPs and per-file checksums.
- Added GitHub Actions build provenance covering the handoff, static ZIP,
  release metadata and changelog; tagged releases publish downloadable assets.
- Established repository-first changes and a deployment guard requiring clean,
  pushed `main`, passing attested CI and matching file hashes. Added hosting and
  handoff instructions, including the separate student portal dependency.
- No production deployment or customer-facing content change in this release.

## 2026-10-30 — Course comparison link visibility (imported)

- Made linked course names inherit the comparison table header color so the
  text remains visible. Preserved comparison content, schema and purchase links.
- Local production verification recorded one changed asset,
  `/courses/index.html`, and no removals. Deployment:
  `0e480199-802e-494e-bb44-7eeb2ab2c4d6`.
- Evidence: [verification](docs/history/imported/2026-10-30-verification.json).

## 2026-10-22 — October website updates (imported)

- Added the About page, updated the homepage and course comparison/FAQs, and
  expanded city-page titles, introductory content and related links.
- Updated separate review-platform snapshots, page dates, breadcrumbs, schema
  logo, court identifiers and relationships while preserving the source graph.
- Added the branded 404 page, revised legacy redirects and preview indexing
  headers, and limited the customer sitemap to 33 canonical pages.
- Retained the delayed analytics loader. Paid-checkout acceptance, analytics
  account changes and warning-free Search Console acceptance were not claimed
  complete by the prior release records. These remain outside this import.
- Deployment: `c65a9dd1-45a2-4620-9f75-8c0985556a10`.
- Evidence: [deployment](docs/history/imported/2026-10-22-deployment.json),
  [QA](docs/history/imported/2026-10-22-qa-results.json),
  [existing public log](texddssitefull/okf/log.md).

## 2026-10-02 — September copy and schema updates (imported)

- Updated page titles, brand copy, FAQs, review labeling and source records.
- Verified and labeled the San Angelo Google rating snapshot; preserved
  separate review platforms and omitted AggregateRating structured data.
- Preserved course and portal destinations and existing locality details.
- Deployment: `96d76ec9-1613-4552-ae26-0c23f7d5c47b`.
- Evidence: [deployment](docs/history/imported/2026-10-02-deployment.json),
  [QA](docs/history/imported/2026-10-02-qa-results.json),
  [existing public log](texddssitefull/okf/log.md).

## 2026-08-14 — Static website and knowledge bundle (imported)

- Generated customer pages, Terms, locality guidance and the OKF v0.2 public
  knowledge bundle with source ledger, offers, FAQs and discovery exports.
- Added canonical host handling and linked public course-anchor targets.
- The dated public log also records August 12 Waco-area research integration.
- Evidence: [existing public log](texddssitefull/okf/log.md).
