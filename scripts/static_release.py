"""Dependency-free validation, deterministic packages and repo-first release gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'texddssitefull'
REPOSITORY = 'OsbornVentures/texdds'
MANIFEST = ROOT / 'docs/site-manifest.json'
SECRETS = [
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),
    re.compile(rb'github_pat_[A-Za-z0-9_]{40,}'),
    re.compile(rb'AKIA[0-9A-Z]{16}'),
]
BANNED_PARTS = {'.git', '.env', '.wrangler', 'node_modules', '__pycache__',
                '.venv', '__qa__', '.edge-profile'}


def run(*args: str) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True,
                            encoding='utf-8', errors='replace')
    if result.returncode:
        raise ValueError(f'{args[0]} failed: {result.stderr.strip() or result.stdout.strip()}')
    return result.stdout


def git(*args: str) -> str:
    return run('git', *args).strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')


def safe_path(name: str) -> bool:
    p = Path(name)
    lowered = [part.lower() for part in p.parts]
    if p.is_absolute() or '..' in p.parts or any(part in BANNED_PARTS for part in lowered):
        return False
    if p.name == '.env.example' and name == '.env.example':
        return True
    return not (p.name.lower().startswith('.env.') or
                p.suffix.lower() in {'.pem', '.key', '.p12', '.pfx', '.pyc', '.log', '.bak'} or
                any(word in p.name.lower() for word in ('credentials', 'secrets.json', '.env.')))


def inventory() -> dict:
    files = []
    for p in sorted(SITE.rglob('*'), key=lambda item: item.relative_to(SITE).as_posix()):
        if p.is_symlink():
            raise ValueError(f'Symlinks are not allowed: {p.relative_to(ROOT)}')
        if not p.is_file():
            continue
        name = p.relative_to(SITE).as_posix()
        if not safe_path(name):
            raise ValueError(f'Forbidden static path: {name}')
        data = p.read_bytes()
        if any(pattern.search(data) for pattern in SECRETS):
            raise ValueError(f'Possible credential in {name}')
        files.append({'path': name, 'bytes': len(data), 'sha256': digest(data)})
    if not files:
        raise ValueError('Static site is empty')
    return {'schemaVersion': 1, 'deployRoot': 'texddssitefull',
            'canonicalOrigin': 'https://www.texdds.com', 'fileCount': len(files),
            'byteCount': sum(item['bytes'] for item in files), 'files': files}


def refresh_manifest() -> dict:
    value = inventory()
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_bytes(json_bytes(value))
    (MANIFEST.parent / 'SITE-SHA256SUMS.txt').write_bytes(
        ''.join(f"{f['sha256']}  texddssitefull/{f['path']}\n" for f in value['files']).encode())
    return {'status': 'PASS', 'fileCount': value['fileCount'], 'byteCount': value['byteCount']}


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ('href', 'src'):
            if attrs.get(key):
                self.refs.append(attrs[key])
        if attrs.get('srcset'):
            self.refs.extend(item.strip().split()[0] for item in attrs['srcset'].split(',') if item.strip())


def validate() -> dict:
    actual = inventory()
    if json.loads(MANIFEST.read_text(encoding='utf-8')) != actual:
        raise ValueError('Static manifest is stale; run: python scripts/static_release.py manifest')
    expected_sums = ''.join(f"{f['sha256']}  texddssitefull/{f['path']}\n" for f in actual['files'])
    if (ROOT / 'docs/SITE-SHA256SUMS.txt').read_text(encoding='utf-8') != expected_sums:
        raise ValueError('SITE-SHA256SUMS.txt is stale')
    for p in SITE.rglob('*.html'):
        parser = Links()
        parser.feed(p.read_text(encoding='utf-8'))
        for ref in parser.refs:
            url = urlsplit(ref)
            if url.scheme not in ('', 'http', 'https') or (url.netloc and url.netloc != 'www.texdds.com'):
                continue
            if not url.path:
                continue
            path = unquote(url.path)
            target = (SITE / path.lstrip('/')) if path.startswith('/') else (p.parent / path)
            target = target.resolve()
            if not target.is_relative_to(SITE.resolve()):
                raise ValueError(f'Link escapes static root: {p.relative_to(SITE)}')
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_file():
                # Pages clean URLs also map /name (and its slash variant) to name.html.
                clean_target = (SITE / path.strip('/')) if path.startswith('/') else (p.parent / path.rstrip('/'))
                if not clean_target.suffix and clean_target.with_suffix('.html').is_file():
                    target = clean_target.with_suffix('.html')
            if not target.is_file():
                raise ValueError(f'Missing local asset: {p.relative_to(SITE)} -> {ref}')
    # Preserve the established content/schema/purchase-link contract validator.
    contract = json.loads(run(sys.executable, 'site-tools/validate_site.py'))
    for name in git('ls-files', '-z').split('\0'):
        if not name:
            continue
        if not safe_path(name):
            raise ValueError(f'Forbidden tracked path: {name}')
        p = ROOT / name
        if p.is_symlink() or not p.is_file():
            raise ValueError(f'Tracked file missing or symlink: {name}')
        if any(pattern.search(p.read_bytes()) for pattern in SECRETS):
            raise ValueError(f'Possible credential in tracked file: {name}')
    return {'status': 'PASS', 'fileCount': actual['fileCount'], 'byteCount': actual['byteCount'],
            'siteContract': contract}


def require_clean() -> None:
    if git('status', '--porcelain', '--untracked-files=all'):
        raise ValueError('Release requires a clean checkout; commit all public changes first')
    actual = {p.relative_to(ROOT).as_posix() for p in SITE.rglob('*') if p.is_file()}
    tracked = set(git('ls-files', 'texddssitefull').splitlines())
    if tracked != actual:
        raise ValueError('Every static file must be tracked; ignored/untracked site assets cannot ship')


def committed_bytes(name: str) -> bytes:
    return subprocess.check_output(['git', 'show', f'HEAD:{name}'], cwd=ROOT)


def write_zip(target: Path, entries: dict[str, bytes]) -> None:
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip():
            raise ValueError('ZIP integrity check failed')


def package() -> dict:
    require_clean()
    validate()
    sha = git('rev-parse', 'HEAD')
    files = git('ls-files').splitlines()
    entries = {name: committed_bytes(name) for name in files}
    metadata = {'schemaVersion': 1, 'repository': f'https://github.com/{REPOSITORY}',
                'sourceCommit': sha, 'sourceTree': git('rev-parse', 'HEAD^{tree}'),
                'commitDate': git('show', '-s', '--format=%cI', 'HEAD'),
                'deployRoot': 'texddssitefull',
                'siteManifestSha256': digest(entries['docs/site-manifest.json']),
                'changelogSha256': digest(entries['CHANGELOG.md']),
                'siteFileCount': len([p for p in files if p.startswith('texddssitefull/')]),
                'note': 'Packaging does not deploy production. GitHub CI provides signed build provenance.'}
    log = run('git', 'log', '--date=iso-strict', '--format=%H%nAuthor: %an <%ae>%nDate: %aI%n%n%B%n').encode('utf-8')
    entries.update({'RELEASE.json': json_bytes(metadata), 'GIT-LOG.txt': log})
    entries['SHA256SUMS.txt'] = ''.join(f'{digest(data)}  {name}\n' for name, data in sorted(entries.items())).encode()
    out = ROOT / 'dist'
    out.mkdir(exist_ok=True)
    static_name = f'texdds-static-{sha[:12]}.zip'
    handoff_name = f'texdds-handoff-{sha[:12]}.zip'
    write_zip(out / static_name, {name.removeprefix('texddssitefull/'): data for name, data in entries.items() if name.startswith('texddssitefull/')})
    write_zip(out / handoff_name, entries)
    for name in ('RELEASE.json', 'GIT-LOG.txt', 'CHANGELOG.md'):
        (out / name).write_bytes(entries[name])
    assets = [static_name, handoff_name, 'RELEASE.json', 'GIT-LOG.txt', 'CHANGELOG.md']
    sums = ''.join(f'{digest((out / name).read_bytes())}  {name}\n' for name in sorted(assets))
    (out / 'SHA256SUMS.txt').write_bytes(sums.encode())
    return {'status': 'PASS', 'commit': sha, 'files': assets + ['SHA256SUMS.txt']}


def remote_main_matches(head: str, refs: str) -> bool:
    return any(line.split() == [head, 'refs/heads/main'] for line in refs.splitlines())


def gate() -> dict:
    require_clean()
    validate()
    sha = git('rev-parse', 'HEAD')
    if git('branch', '--show-current') != 'main':
        raise ValueError('Production deploy must run from main')
    origin = git('remote', 'get-url', 'origin').removesuffix('.git')
    if origin not in (f'https://github.com/{REPOSITORY}', f'git@github.com:{REPOSITORY}'):
        raise ValueError('Origin must be the public OsbornVentures/texdds repository')
    refs = git('ls-remote', '--exit-code', 'origin', 'refs/heads/main')
    if not remote_main_matches(sha, refs):
        raise ValueError('HEAD must match current remote main; push/fetch before production')
    result = json.loads(run('gh', 'api', f'repos/{REPOSITORY}/actions/workflows/static-handoff.yml/runs?head_sha={sha}&branch=main&event=push&status=success&per_page=100'))
    successful = [r for r in result.get('workflow_runs', []) if r.get('head_sha') == sha and r.get('conclusion') == 'success']
    if not successful:
        raise ValueError('No successful attested Static handoff push workflow for this commit')
    return {'status': 'PASS', 'commit': sha, 'workflowRun': successful[0]['html_url']}


def check_changelog(base: str) -> dict:
    changed = set(git('diff', '--name-only', base, 'HEAD').splitlines())
    if changed and 'CHANGELOG.md' not in changed:
        raise ValueError('Every change must update CHANGELOG.md in the same push/PR')
    return {'status': 'PASS', 'changedFiles': len(changed)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['manifest', 'validate', 'package', 'gate', 'changelog'])
    parser.add_argument('--base')
    args = parser.parse_args()
    try:
        if args.command == 'changelog':
            if not args.base:
                parser.error('--base is required')
            result = check_changelog(args.base)
        else:
            result = {'manifest': refresh_manifest, 'validate': validate, 'package': package, 'gate': gate}[args.command]()
        print(json.dumps(result, indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f'Release blocked: {error}', file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    main()
