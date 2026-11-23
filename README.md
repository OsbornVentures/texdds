# TexDDS static handoff

Public source of truth for [www.texdds.com](https://www.texdds.com):
[OsbornVentures/texdds](https://github.com/OsbornVentures/texdds).

**Publish the contents of `texddssitefull/` as the website root.** It includes
HTML, images, inline CSS/JavaScript, favicon, sitemap, robots rules, public OKF
knowledge files and `.well-known` discovery files. There is no npm install,
framework build, database or application runtime for this marketing website.

The initial import is the October 30, 2026 production revision, checked against
Cloudflare on November 23: all 111 deployed assets matched. The two additional
files are Pages configuration (`_headers` and `_redirects`). There are 36 HTML
files, 26 city guides and 33 sitemap URLs. See the
[import verification](docs/history/production-import-verification.json).

## Preview and validate

Python 3.12+ is used only for local tooling and release packaging.

```sh
python -m http.server 8080 --directory texddssitefull
python scripts/static_release.py validate
python -m unittest discover -s scripts -p 'test_*.py'
```

Open `http://localhost:8080`. Python's preview server does not apply Cloudflare
redirects, headers or custom 404 routing. See [hosting notes](docs/HOSTING.md).
The checkout, payment flow, student accounts and course delivery remain on the
separate `stg.texdds.com` application; they are not a static-site backend in this
repository. Public analytics integrations also remain external services.

## Release and handoff

```sh
python scripts/static_release.py package
```

Run from a clean commit. The ignored `dist/` directory receives:

- `texdds-static-<commit>.zip`: only deployable website-root files, including
  dotfiles and both Cloudflare configuration files.
- `texdds-handoff-<commit>.zip`: all tracked source, history, changelog,
  maintenance/deployment tools, the exact Git log and release metadata.
- `RELEASE.json`, `CHANGELOG.md`, `GIT-LOG.txt` and `SHA256SUMS.txt`.

ZIP timestamps and permissions are fixed and files are stored without
compression, so the same commit produces identical bytes across platforms.
GitHub's **Static handoff** workflow validates every push/PR, generates signed
provenance for `main` and `v*` tags, and attaches tagged packages to GitHub
Releases. Package digests and changelog content are bound to the source commit.
See [release procedure and attestation verification](docs/RELEASING.md).

## Repo first, production second

Edit static source and changelog, refresh the manifest, validate, commit, push,
and wait for the attested workflow before deploying. The upload tool enforces
these checks and sets Cloudflare's source commit metadata. A repository push
does not deploy production automatically. The hosting setup remains in place.

[CHANGELOG.md](CHANGELOG.md) imports documented prior changes without inventing
old Git commits. The original local `.git` directory was empty. Historical
evidence and its hashes are in [docs/history](docs/history/README.md).

The workspace's `.gitignore` allows only reviewed public handoff paths. Private
records, credentials, caches, research working directories and old release ZIPs
remain local. The publication of these files does not grant an additional
license to TexDDS branding, photographs, copy or third-party material.
