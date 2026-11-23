# Hosting the static package

Deploy root: **`texddssitefull/`**, or extract `texdds-static-<commit>.zip`
directly into a host's document root. No build command is needed. Preserve
`.well-known/` and `okf/`, MIME types, directory `index.html` routing, favicon,
`robots.txt`, `sitemap.xml`, `404.html`, `_headers` and `_redirects`.

## Existing Cloudflare Pages hosting

- Project: `texdds`; production branch: `main`.
- Canonical website: `https://www.texdds.com`; Pages alias: `texdds.pages.dev`.
- `_headers` and `_redirects` are Pages configuration, not ordinary documents.
- Apex `texdds.com` redirects to `www.texdds.com` with path and query preserved.
- Old domains `texasdefensivedrivingschool.com` and
  `www.texasdefensivedrivingschool.com` retain their legacy mappings, then
  redirect unmatched paths to the canonical host with path/query preserved.
- Existing Cloudflare bulk redirects can take precedence over static rules.
  The sanitized October inventory is in `hosting/legacy-bulk-redirects.json`;
  its obsolete review destination is corrected to `/resources/` as documented
  by that release. Verify against the account before changing infrastructure.
- `hosting/zone-rules.json` records the portable rule expressions and actions
  from the October release, without account/zone/rule identifiers. These are
  reference configuration, not an automatic importer or a fresh account audit.

Keep custom-domain DNS/TLS, apex redirects and legacy-domain rules in place.
The repository alone does not provision DNS, certificates, zone-level rules or
the separate student portal. Preserve existing email DNS records.

## Other static hosts

Translate `_redirects` to equivalent HTTP 301 rules and `_headers` to response
headers. Honor file/directory routes and serve the branded `404.html` with an
actual 404 status. Configure canonical HTTPS host redirects at the host/CDN,
preserving query strings. Test old URLs before switching traffic. Do not use
the repository root as a document root: it includes maintenance documentation.

## External services

- `stg.texdds.com`: existing login, checkout and course-delivery application.
  The course page intentionally links to it. Its homepage redirect applies
  only to `/` on GET/HEAD; login and checkout paths must remain intact. A
  zone-level `X-Robots-Tag: noindex, follow` excludes its responses from search.
- Google Tag Manager and public profile links remain external dependencies.
  IDs embedded in public HTML are public configuration, not account credentials.
- Preview Pages hosts must remain noindex, and production canonical pages must
  remain indexable. Preview analytics suppression is already in the HTML.

No portal source, student/customer database, payment secrets, GTM/GA4/Ads account
exports, DNS credentials or Cloudflare credentials are part of this package.
