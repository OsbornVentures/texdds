# Repository-first releases

1. Change the tracked static source and `CHANGELOG.md`. Keep visible dates,
   sitemap dates and the public knowledge representations consistent.
2. Run `python scripts/static_release.py manifest`, then
   `python scripts/static_release.py validate` and
   `python -m unittest discover -s scripts -p 'test_*.py'`.
3. Review the diff and commit. Push to `main` (through a PR when appropriate).
4. Wait for **Static handoff** to succeed for that exact commit. It validates
   files and the changelog, builds deterministic packages, and signs provenance
   using GitHub's `actions/attest`. No Cloudflare credentials are stored in CI.
5. Optionally create and push a `v*` tag for a numbered handoff. The tag workflow
   must refer to a commit already on `main`; it creates a GitHub Release with
   both ZIPs, checksums, changelog, Git log and release metadata.
6. Preview/test the package, then run the maintained production upload command
   from a clean `main` checkout after fetching the latest repository state:

   ```sh
   node tools/deploy-pages-direct-upload.mjs texddssitefull texdds main
   ```

   Requires Node.js 22+, Git, Python 3.12+, authenticated `gh`, and local
   `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` in the environment or ignored
   `.env`. The tool refuses other roots/branches, dirty or unpushed changes,
   missing successful attested CI, and mismatched manifests. It uploads an
   in-memory snapshot checked against committed hashes and includes the full
   source commit with `commit_dirty=false`. It does not regenerate the website.

7. The upload result and manifest comparison are saved to
   `docs/deployments/<commit>-<deployment>.json`. Verify canonical HTTP behavior,
   headers, redirects and representative desktop/mobile pages. Commit and push
   that receipt and add the outcome to the changelog. This evidence-only commit
   does not require redeploying unchanged site bytes.

## Verify a downloaded handoff

```sh
gh attestation verify texdds-static-<commit>.zip --repo OsbornVentures/texdds
gh attestation verify texdds-handoff-<commit>.zip --repo OsbornVentures/texdds
gh attestation verify CHANGELOG.md --repo OsbornVentures/texdds
```

Inspect `RELEASE.json` for the full source SHA, tree SHA and changelog SHA-256.
Compare ZIP digests with `SHA256SUMS.txt`; per-file site hashes are in
`docs/site-manifest.json` and `docs/SITE-SHA256SUMS.txt`. GitHub provenance binds
the artifact digest to the workflow/source revision; it is not a claim that
historical notes were signed or that a build was deployed.

The package command can be run locally on a clean commit; only CI produces the
signed GitHub attestation. `python scripts/static_release.py gate` is a
read-only preflight for the production requirements.

## Rollback

Revert the relevant site change on `main`, update the changelog and manifest,
push, wait for CI, then deploy the new revert commit through the same gate.
Do not force-push or overwrite release tags. Infrastructure rollback plans must
also be committed before applying the change in a dashboard.

## Enforcement scope

The maintained upload command and CI enforce this workflow. They cannot prevent
someone with separate hosting credentials from using a dashboard or another
script. No automatic production deploy, hosting credential migration or
administrator-access change is configured by this handoff.
