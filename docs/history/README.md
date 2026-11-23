# Imported history and provenance

There were no recoverable local commits at import: the workspace `.git`
directory existed but contained no files, refs, objects or configuration.
The new repository starts with a real November 23, 2026 import commit.
No past commits, authorship timestamps or successful CI runs were fabricated.

The existing public [OKF log](../../texddssitefull/okf/log.md) and
`page-history.json` preserve earlier content revision records. `imported/`
contains selected deployment and QA JSON files copied byte-for-byte from local
release folders. [import-manifest.json](import-manifest.json) records their
original workspace-relative paths and SHA-256 digests. Other records were
summarized in the root changelog to exclude private correspondence, accounts,
business agreements and unrelated operational data.

[production-import-verification.json](production-import-verification.json)
records the read-only comparison with the current Cloudflare deployment.
All 111 served assets matched; the separately processed `_headers` and
`_redirects` are included and checksummed in the static file manifest.

Imported records establish what was recorded locally. Signed GitHub build
provenance begins with this repository's successful workflows; it does not
attest to the truth or execution of historical records.
