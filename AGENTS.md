# TexDDS repository and production policy

The public source of truth is https://github.com/OsbornVentures/texdds.
All changes go to this repository before production. This applies to content,
assets, redirects, headers, hosting configuration and deployment tooling.

1. Edit the tracked static files in `texddssitefull/`. This is a static handoff;
   no build step or server runtime is required to serve it. Local legacy
   generators and dated output folders are not authoritative release sources.
2. Preserve the public source ledger and the scoped instructions in
   `texddssitefull/okf/AGENTS.md`. Keep visible content, JSON-LD, OKF exports,
   page dates and sitemap dates synchronized when changing content.
3. Update `CHANGELOG.md` for each change. Run
   `python scripts/static_release.py manifest` after any static asset change.
4. Run `python scripts/static_release.py validate` and
   `python -m unittest discover -s scripts -p 'test_*.py'`.
5. Commit and push to GitHub; wait for the Static handoff workflow to succeed.
   Never deploy an uncommitted, unpushed or failed-check revision.
6. Deploy only the exact bytes from the reviewed commit. The maintained upload
   tool verifies a clean checkout, the current remote main commit, a successful
   attested workflow and the SHA-256 manifest before any Cloudflare write.
7. Record the production deployment ID, source commit, package hashes and
   verification result in `docs/deployments/`, then commit and push that receipt.
   Do not backdate or claim attestations for imported pre-Git releases.

Never publish credentials, contracts, customer/order data, analytics exports,
browser profiles, caches or private working notes. The root allowlist in
`.gitignore` is deliberate. Review additions to it. Do not force-add ignored
files. Do not run the older direct-upload copies in ignored output folders.

External dashboard changes must first have their intended configuration and
changelog committed and pushed; append the applied result afterward. Repository
policy and the maintained deploy command do not prevent a person with separate
Cloudflare access from bypassing this process.
