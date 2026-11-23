---
type: "Log"
title: "TexDDS OKF Change Log"
description: "Chronological build and source-integration log."
resource: "https://www.texdds.com/okf/log.md"
tags: ["texdds", "log"]
timestamp: "2026-08-14T00:00:00-05:00"
---

# TexDDS OKF Change Log

## [2026-10-22] October batch updates

- Preserved the source-backed court graph, locality data feeds and discovery files.
- Added owner attribution for the lifetime student count and the About page.
- Updated independent review snapshots from current Google, Yelp and Trustpilot profiles.
- Corrected court entity IDs into the TexDDS namespace and child-office relationships to department.
- Removed redundant ListItem URL fields while retaining each full WebPageElement, its URL, citations and ItemList reference.
- Added page dates, stable breadcrumb IDs, visible FAQ markup and a square schema logo.
- Kept source retrieval dates separate from page revision dates.
- Removed OKF from the customer sitemap while preserving its public discovery links and exports.

## [2026-08-12] locality research | Waco-area court process module

- Added a source-backed Waco hub and ten fragment-addressable sublocality court answers.
- Preserved the City of Waco's published DSC instructions at `/texas/waco/#waco-court-process`.
- Added direct official request forms and court contact actions where the publishing court provides them.
- Recorded fee differences instead of inferring a county-wide rule: seven pages publish $144 / $169, McGregor publishes $143.90 / $168.90, West publishes only $144 on its DSC page, and Lacy Lakeview omits an amount.
- Recorded the McGregor court-page / linked-PDF email-domain conflict and routed customers to the current court phone or page.
- Added structured `WebPageElement` fragments, an `ItemList`, source-ledger records, and deep-locality JSON export data.

## [2026-08-14] build | Generated customer site and OKF bundle

- Built customer-facing static pages.
- Added the customer Terms page, the locality-research limitation notice, and a footer Terms link across customer pages.
- Added a canonical-host redirect for apex-domain requests while keeping canonical, schema, sitemap, discovery, and OKF URLs on `https://www.texdds.com/`.
- Added the terms and locality-limitations document to OKF v0.2 discovery.
- Generated the OKF v0.2 corpus with shared FAQ, offer, locality, entity, and source-ledger representations.
- Generated `llms.txt`, `okf/manifest.json`, `okf/md.yaml`, and JSON data exports.
- Linked OKF discovery from every HTML page head.
- Published public course-anchor targets in `llms.txt`, OKF index, manifest, and offer exports.
- Kept checkout endpoints out of OKF, `llms.txt`, sitemap, and JSON-LD as canonical URLs.
- Added stable FAQ fragments aligned across visible HTML, `FAQPage` JSON-LD, Markdown, and JSON.

## [2026-10-02] September on-site copy and schema updates

- Expanded page titles and introductory brand references on Courses, the statewide guide, Resources, and the Texas city hub.
- Replaced four vague online-tenure lines with the established 2008 public domain-footprint fact.
- Added eight visible ticket-dismissal questions and four course questions using the supplied copy, plus four in-body navigation links.
- Added matching visible review dates and WebPage dateModified only to Resources and the statewide guide.
- Preserved all nine requested sameAs profiles and the existing Knowledge Graph link; added the San Angelo hasMap value and Texas areaServed to both Service nodes.
- Confirmed published JSON-LD already omitted AggregateRating; removed the unused rating-schema generator and retained visible review cards.
- Aligned the insurance-course description with its existing not-for-ticket-dismissal restriction and the new FAQ.

## [2026-10-02] Google rating verification | San Angelo profile

- Directly verified Google's displayed San Angelo rating: 4.8 out of 5 from 49 reviews, replacing the June 17 snapshot of 4.7 from 47 reviews.
- Labeled the visible Google cards as San Angelo, with the source link and October 2 verification date on the homepage and Resources.
- Updated the source ledger and review index; corrected the review index's stale statement that no Google rating had been verified.
- Kept review platforms and locations separate and left AggregateRating out of published structured data.

## [2026-08-14] source integration | Public claims and localities

- Preserved TDLR, DPS, TxDOT, court, public profile, and course-pricing claims in the source ledger.
- Kept paywall-prone news domains out of production locality citations.
- Added locality pages with local court reminders and traffic-safety signals.
