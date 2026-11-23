from __future__ import annotations

import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlparse


TOOL_PARENT = Path(__file__).resolve().parents[1]
ROOT = TOOL_PARENT if TOOL_PARENT.name == "texddssitefull" else TOOL_PARENT / "texddssitefull"


def internal_target(href: str) -> Path:
    href = href.split("#", 1)[0]
    if href == "/":
        return ROOT / "index.html"
    if href.endswith("/"):
        return ROOT / href.strip("/") / "index.html"
    return ROOT / href.strip("/")


def graph_nodes(schema: dict) -> list[dict]:
    graph = schema.get("@graph", [])
    return graph if isinstance(graph, list) else []


def json_string_values(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for entry in value for item in json_string_values(entry)]
    if isinstance(value, dict):
        return [item for entry in value.values() for item in json_string_values(entry)]
    return []


def is_absolute_http(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> int:
    html_files = sorted(ROOT.rglob("*.html"))
    errors: list[str] = []
    stg_refs: list[str] = []
    locality_regions: dict[str, str] = {}
    paywalled_domains = {
        "houstonchronicle.com",
        "beaumontenterprise.com",
        "chron.com",
        "lmtonline.com",
        "mrt.com",
        "mysanantonio.com",
    }
    required_purchase_links = {
        "https://stg.texdds.com/addpackage/1",
        "https://stg.texdds.com/addreset/1",
        "https://stg.texdds.com/addreset/2",
        "https://stg.texdds.com/addreset/3",
    }
    required_public_offer_targets = {
        "https://www.texdds.com/courses/#defensive-driving",
        "https://www.texdds.com/courses/#bundle",
        "https://www.texdds.com/courses/#driver-record",
        "https://www.texdds.com/courses/#insurance",
    }
    required_discovery_urls = {
        "https://www.texdds.com/llms.txt",
        "https://www.texdds.com/.well-known/llms.txt",
        "https://www.texdds.com/okf/manifest.json",
        "https://www.texdds.com/.well-known/okf-manifest.json",
        "https://www.texdds.com/okf/index.md",
        "https://www.texdds.com/.well-known/okf-index.md",
        "https://www.texdds.com/okf/md.yaml",
        "https://www.texdds.com/.well-known/okf-md.yaml",
        "https://www.texdds.com/.well-known/api-catalog",
        "https://www.texdds.com/.well-known/agent-skills/index.json",
        "https://www.texdds.com/.well-known/site-status.json",
        "https://www.texdds.com/okf/AGENTS.md",
        "https://www.texdds.com/okf/terms.md",
        "https://www.texdds.com/okf/entity.json",
        "https://www.texdds.com/okf/offers/courses.json",
        "https://www.texdds.com/okf/faqs/faqs.json",
        "https://www.texdds.com/okf/faqs/index.md",
        "https://www.texdds.com/okf/sources.json",
        "https://www.texdds.com/.well-known/okf-sources.json",
        "https://www.texdds.com/okf/directories/index.md",
        "https://www.texdds.com/okf/reviews/index.md",
        "https://www.texdds.com/okf/sources/index.md",
        "https://www.texdds.com/.well-known/agent-discovery.json",
        "https://www.texdds.com/.well-known/ai-discovery.json",
        "https://www.texdds.com/.well-known/author.json",
    }
    waco_deep_fragments = {
        "waco",
        "robinson",
        "hewitt",
        "mcgregor",
        "lorena",
        "bellmead",
        "lacy-lakeview",
        "riesel",
        "china-spring",
        "woodway",
        "west",
    }
    found_purchase_links: set[str] = set()
    locality_counts: dict[str, int] = {}
    locality_signal_counts: dict[str, int] = {}
    okf_version = None
    okf_manifest_documents = 0
    okf_source_count = 0
    okf_locality_count = 0
    required_okf_files = {
        "llms.txt",
        "okf/manifest.json",
        "okf/index.md",
        "okf/md.yaml",
        "okf/AGENTS.md",
        "okf/log.md",
        "okf/terms.md",
        "okf/entities/texdds.md",
        "okf/offers/courses.md",
        "okf/offers/courses.json",
        "okf/faqs/index.md",
        "okf/faqs/faqs.json",
        "okf/sources.json",
        "okf/sources/index.md",
        "okf/sources/ledger.json",
        "okf/localities/index.md",
        "okf/localities/localities.json",
        "okf/directories/index.md",
        "okf/reviews/index.md",
        "_headers",
        ".well-known/agent-discovery.json",
        ".well-known/ai-discovery.json",
        ".well-known/api-catalog",
        ".well-known/author.json",
        ".well-known/llms.txt",
        ".well-known/okf-manifest.json",
        ".well-known/okf-index.md",
        ".well-known/okf-md.yaml",
        ".well-known/okf-sources.json",
        ".well-known/site-status.json",
        ".well-known/agent-skills/index.json",
        ".well-known/agent-skills/texdds-site-discovery/SKILL.md",
    }
    duplicate_domain_refs = {
        "approvedtexasdefensivedrivingschool.com",
        "texasdefensivedrivingschool.com",
    }

    for rel in sorted(required_okf_files):
        if not (ROOT / rel).exists():
            errors.append(f"missing OKF/discovery file {rel}")
    if (ROOT / "assets" / "fonts").exists():
        errors.append("assets/fonts: font pack directory should not ship")

    extra_well_known_files = [ROOT / ".well-known/api-catalog"]
    files_to_scan = [
        *ROOT.rglob("*.html"),
        *ROOT.rglob("*.md"),
        *ROOT.rglob("*.json"),
        *ROOT.rglob("*.txt"),
        *ROOT.rglob("*.yaml"),
        *(path for path in extra_well_known_files if path.exists()),
    ]
    for file in sorted(set(files_to_scan)):
        text = file.read_text(encoding="utf-8")
        rel = file.relative_to(ROOT).as_posix()
        if "stg.texdds.com" in text and rel != "courses/index.html":
            errors.append(f"{rel}: staging URL must only appear in courses/index.html")
        if re.search(r"https://texdds\.com(?:/|\b)", text):
            errors.append(f"{rel}: apex TexDDS URL must use https://www.texdds.com/")
        if "woff2" in text or "/assets/fonts/" in text or "@font-face" in text:
            errors.append(f"{rel}: font request/reference still present")
        if "live-texdds-stale-copy" in text:
            errors.append(f"{rel}: internal migration QA source note leaked into public output")
        for domain in paywalled_domains:
            if domain in text:
                errors.append(f"{rel}: paywalled source domain still present: {domain}")

    manifest_path = ROOT / "okf/manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"okf/manifest.json: invalid JSON: {exc}")
            manifest = {}
        if manifest.get("okfVersion") != "0.2":
            errors.append("okf/manifest.json: missing okfVersion 0.2")
        okf_version = manifest.get("okfVersion")
        okf_manifest_documents = len(manifest.get("documents", []))
        offer_targets = set((manifest.get("publicOfferTargets") or {}).values())
        if not required_public_offer_targets.issubset(offer_targets):
            errors.append("okf/manifest.json: missing public course anchor targets")
        checkout_policy = manifest.get("checkoutPolicy") or {}
        if checkout_policy.get("indexed") is not False:
            errors.append("okf/manifest.json: checkoutPolicy.indexed must be false")
        for doc in manifest.get("documents", []):
            path = doc.get("path")
            if not path or not (ROOT / path).exists():
                errors.append(f"okf/manifest.json: missing document path {path}")

    llms_path = ROOT / "llms.txt"
    if llms_path.exists():
        llms = llms_path.read_text(encoding="utf-8")
        if not re.search(r"^#\s+\S", llms, flags=re.M):
            errors.append("llms.txt: missing H1 header")
        if not re.search(r"\[[^\]]+\]\(https://www\.texdds\.com/[^)]+\)", llms):
            errors.append("llms.txt: missing markdown links")
        if "Checkout indexing policy" not in llms:
            errors.append("llms.txt: missing checkout indexing policy")
        for target in sorted(required_public_offer_targets):
            if target not in llms:
                errors.append(f"llms.txt: missing public offer target {target}")

    robots_path = ROOT / "robots.txt"
    if robots_path.exists():
        robots = robots_path.read_text(encoding="utf-8")
        if re.search(r"(?m)^(LLMs|OKF-|Agent-|AI-)", robots):
            errors.append("robots.txt: use Allow/Sitemap directives only for machine discovery")
        if "Content-Signal: ai-train=yes, search=yes, ai-input=yes" not in robots:
            errors.append("robots.txt: missing Content-Signal directive")
        for target in sorted(required_discovery_urls):
            relative = "/" + urlparse(target).path.lstrip("/")
            if f"Allow: {relative}" not in robots:
                errors.append(f"robots.txt: missing Allow directive for {relative}")
        if f"Sitemap: https://www.texdds.com/sitemap.xml" not in robots:
            errors.append("robots.txt: missing final sitemap directive")

    sitemap_path = ROOT / "sitemap.xml"
    if sitemap_path.exists():
        sitemap = sitemap_path.read_text(encoding="utf-8")
        if "https://www.texdds.com/okf/" in sitemap:
            errors.append("sitemap.xml: OKF belongs in discovery links, not the customer sitemap")
        if "https://www.texdds.com/terms/" not in sitemap:
            errors.append("sitemap.xml: missing Terms page https://www.texdds.com/terms/")
        for target in sorted(required_discovery_urls):
            if target not in sitemap:
                continue
            errors.append(f"sitemap.xml: deep discovery target should move to robots.txt, not sitemap.xml: {target}")
        forbidden_sitemap_fragments = (
            "/.well-known/",
            "/llms.txt",
            "/okf/AGENTS.md",
            "/okf/entity.json",
            "/okf/index.md",
            "/okf/md.yaml",
            "/okf/manifest.json",
            "/okf/sources.json",
            "/okf/offers/courses.json",
            "/okf/sources/",
            "/okf/localities/",
            "/okf/directories/",
            "/okf/reviews/",
        )
        for fragment in forbidden_sitemap_fragments:
            if fragment in sitemap:
                errors.append(f"sitemap.xml: machine file should not be listed directly: {fragment}")

    headers_path = ROOT / "_headers"
    if headers_path.exists():
        headers = headers_path.read_text(encoding="utf-8")
        required_header_links = {
            '</llms.txt>; rel="alternate"; type="text/plain"',
            '</okf/manifest.json>; rel="describedby"; type="application/json"',
            '</okf/index.md>; rel="alternate"; type="text/markdown"',
            '</okf/md.yaml>; rel="describedby"; type="application/yaml"',
            '</okf/sources.json>; rel="describedby"; type="application/json"',
            '</.well-known/agent-discovery.json>; rel="describedby"; type="application/json"',
            '</sitemap.xml>; rel="sitemap"; type="application/xml"',
        }
        for link in sorted(required_header_links):
            if link not in headers:
                errors.append(f"_headers: missing Link target {link}")
        if "Content-Signal: ai-train=yes, search=yes, ai-input=yes" not in headers:
            errors.append("_headers: missing Content-Signal directive")
        if "/.well-known/api-catalog" not in headers or "application/linkset+json" not in headers:
            errors.append("_headers: missing api-catalog content type override")
        speculative_discovery = (
            "/.well-known/openid-configuration",
            "/.well-known/oauth-authorization-server",
            "/.well-known/oauth-protected-resource",
            "/auth.md",
            "/.well-known/mcp",
        )
        for target in speculative_discovery:
            if target in headers:
                errors.append(f"_headers: speculative agent platform endpoint should not be advertised: {target}")

    source_ledger_paths = (
        "okf/sources/ledger.json",
        "okf/sources.json",
        ".well-known/okf-sources.json",
    )
    allowed_verification_methods = {"primary-source", "operator-attested"}
    for rel in source_ledger_paths:
        path = ROOT / rel
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON: {exc}")
            continue
        sources = payload if isinstance(payload, list) else payload.get("sources", [])
        if not isinstance(sources, list) or not sources:
            errors.append(f"{rel}: missing source list")
            continue
        if rel == "okf/sources.json":
            okf_source_count = len(sources)
        ids = {source.get("id") for source in sources if isinstance(source, dict)}
        if "live-texdds-stale-copy" in ids:
            errors.append(f"{rel}: internal migration QA source note should not be public")
        for source in sources:
            if not isinstance(source, dict):
                errors.append(f"{rel}: source entries must be objects")
                continue
            method = source.get("verificationMethod")
            if method not in allowed_verification_methods:
                errors.append(f"{rel}: {source.get('id', '<missing id>')} has invalid verificationMethod {method}")
            if source.get("id") == "dps-type-3a-record":
                claim = source.get("claim", "")
                if "$24.95" in claim or "TexDDS" in claim:
                    errors.append(f"{rel}: dps-type-3a-record should not carry TexDDS pricing/product copy")

    source_markdown_path = ROOT / "okf/sources/index.md"
    if source_markdown_path.exists():
        source_markdown = source_markdown_path.read_text(encoding="utf-8")
        if "| ID | Publisher | Claim | URL | Retrieved | Verification | Status |" not in source_markdown:
            errors.append("okf/sources/index.md: missing Verification column")

    for rel in (".well-known/agent-discovery.json", ".well-known/ai-discovery.json", ".well-known/okf-manifest.json", ".well-known/okf-sources.json", ".well-known/author.json", ".well-known/api-catalog", ".well-known/site-status.json", ".well-known/agent-skills/index.json"):
        path = ROOT / rel
        if path.exists():
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: invalid JSON: {exc}")
                continue
            if rel.endswith("api-catalog"):
                linkset = payload.get("linkset")
                if not isinstance(linkset, list) or not linkset:
                    errors.append(".well-known/api-catalog: missing non-empty linkset array")
                else:
                    first = linkset[0]
                    for field in ("anchor", "item", "service-desc", "service-doc", "status"):
                        if field not in first:
                            errors.append(f".well-known/api-catalog: missing {field}")
            if rel.endswith("agent-skills/index.json"):
                if payload.get("$schema") != "https://schemas.agentskills.io/discovery/0.2.0/schema.json":
                    errors.append(".well-known/agent-skills/index.json: missing v0.2.0 schema")
                skills = payload.get("skills")
                if not isinstance(skills, list) or not skills:
                    errors.append(".well-known/agent-skills/index.json: missing skills")
                else:
                    skill = skills[0]
                    if skill.get("name") != "texdds-site-discovery":
                        errors.append(".well-known/agent-skills/index.json: missing texdds-site-discovery skill")
                    if not str(skill.get("digest", "")).startswith("sha256:"):
                        errors.append(".well-known/agent-skills/index.json: missing sha256 digest")
            if rel.endswith("author.json"):
                if payload.get("name") != "Dekker Osborn":
                    errors.append(".well-known/author.json: missing Dekker Osborn author name")
                if "https://orcid.org/0009-0002-3066-7001" not in json_string_values(payload):
                    errors.append(".well-known/author.json: missing ORCID URL")
                if "https://dekkerosborn.im/" not in json_string_values(payload):
                    errors.append(".well-known/author.json: missing author URL")
            if rel.endswith("agent-discovery.json") or rel.endswith("ai-discovery.json"):
                entrypoints = payload.get("entrypoints", {})
                for target in sorted(required_discovery_urls):
                    if target.endswith("/.well-known/ai-discovery.json"):
                        continue
                    if target not in entrypoints.values() and target not in payload.get("publicOfferTargets", {}).values():
                        if target.endswith("/.well-known/agent-discovery.json"):
                            continue
                        errors.append(f"{rel}: missing discovery target {target}")

    for rel in ("okf/offers/courses.json", "okf/entity.json"):
        path = ROOT / rel
        if path.exists():
            data_text = path.read_text(encoding="utf-8")
            try:
                payload = json.loads(data_text)
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: invalid JSON: {exc}")
                continue
            strings = json_string_values(payload)
            if "purchase_url" in data_text:
                errors.append(f"{rel}: purchase_url must not be exported")
            if "stg.texdds.com" in data_text:
                errors.append(f"{rel}: staging checkout URL must not be exported")
            found_targets = {value for value in strings if value in required_public_offer_targets}
            if not required_public_offer_targets.issubset(found_targets):
                errors.append(f"{rel}: missing public course anchor targets")

    faq_json_path = ROOT / "okf/faqs/faqs.json"
    if faq_json_path.exists():
        try:
            faq_json = json.loads(faq_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"okf/faqs/faqs.json: invalid JSON: {exc}")
        else:
            questions = faq_json.get("mainEntity", [])
            if faq_json.get("@type") != "FAQPage" or len(questions) != 10:
                errors.append("okf/faqs/faqs.json: expected FAQPage with 10 questions")
            for question in questions:
                if not str(question.get("@id", "")).startswith("https://www.texdds.com/resources/#faq-"):
                    errors.append("okf/faqs/faqs.json: question missing stable resources fragment")

    locality_json_path = ROOT / "okf/localities/localities.json"
    if locality_json_path.exists():
        try:
            locality_json = json.loads(locality_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"okf/localities/localities.json: invalid JSON: {exc}")
        else:
            okf_locality_count = len(locality_json)
            locality_regions = {
                str(item.get("slug")): str(item.get("region"))
                for item in locality_json
                if item.get("slug") and item.get("region")
            }
            waco_records = [item for item in locality_json if item.get("slug") == "waco"]
            if len(waco_records) != 1:
                errors.append("okf/localities/localities.json: expected one Waco record")
            else:
                deep = waco_records[0].get("deepResearch") or {}
                panels = deep.get("sub_localities") or []
                fragments = {item.get("fragment") for item in panels}
                if len(panels) != 10 or fragments != (waco_deep_fragments - {"waco"}):
                    errors.append("okf/localities/localities.json: incomplete Waco deep-locality panels")
                if not (deep.get("hub") or {}).get("verbatim"):
                    errors.append("okf/localities/localities.json: missing Waco verbatim court instructions")
                if len(waco_records[0].get("deepSources") or []) < 20:
                    errors.append("okf/localities/localities.json: incomplete Waco deep source set")

    for file in sorted((ROOT / "okf").rglob("*.md")) if (ROOT / "okf").exists() else []:
        text = file.read_text(encoding="utf-8")
        rel = file.relative_to(ROOT).as_posix()
        if not text.startswith("---\n"):
            errors.append(f"{rel}: missing OKF YAML frontmatter")
            continue
        try:
            frontmatter = text.split("---\n", 2)[1]
        except IndexError:
            errors.append(f"{rel}: malformed OKF YAML frontmatter")
            continue
        for field in ("type:", "title:", "description:", "resource:", "tags:", "timestamp:"):
            if field not in frontmatter:
                errors.append(f"{rel}: missing OKF frontmatter field {field[:-1]}")
        for value in re.findall(r"\]\((/[^)\s#]+)", text):
            if not internal_target(value).exists():
                errors.append(f"{rel}: broken internal markdown link {value}")

    for file in html_files:
        text = file.read_text(encoding="utf-8")
        visible_markup = re.sub(r"<script\b.*?</script>", "", text, flags=re.IGNORECASE | re.DOTALL)
        plain_text = unescape(re.sub(r"<[^>]+>", "", visible_markup))
        rel = file.relative_to(ROOT).as_posix()
        schema = None

        if "window.location.hostname.toLowerCase()" not in text or "https://www.texdds.com" not in text:
            errors.append(f"{rel}: missing canonical www host redirect")
        canonical_match = re.search(r'<link rel="canonical" href="([^"]+)">', text)
        if not canonical_match or not canonical_match.group(1).startswith("https://www.texdds.com/"):
            errors.append(f"{rel}: canonical URL must start with https://www.texdds.com/")
        if rel not in {"reviews/index.html", "okf/index.html"}:
            if '<footer class="site-footer">' not in text:
                errors.append(f"{rel}: missing customer footer")
            if 'href="/terms/">Terms</a>' not in text:
                errors.append(f"{rel}: missing footer Terms link")
            if 'footer-terms' in text:
                errors.append(f"{rel}: footer Terms link must use the standard plain-text style")
        if rel == "terms/index.html":
            required_terms_copy = (
                "more than 200 Texas localities",
                "Research and due diligence do not guarantee accuracy",
                "The exact court named on the citation controls",
                "Student enrollment contract",
                "Software agreement",
                "General educational information",
            )
            for phrase in required_terms_copy:
                if phrase not in plain_text:
                    errors.append(f"terms/index.html: missing required terms copy: {phrase}")

        if rel.startswith("texas/lott/") or rel == "texas/lott/index.html":
            errors.append(f"{rel}: removed locality still present")

        if 'rel="stylesheet"' in text or "assets/styles.css" in text:
            errors.append(f"{rel}: external stylesheet reference found")

        if "fonts.googleapis.com" in text or "fonts.gstatic.com" in text:
            errors.append(f"{rel}: external font host reference found")

        if "<style>" not in text:
            errors.append(f"{rel}: missing inline CSS style block")

        if (
            'href="/okf/manifest.json"' not in text
            or 'href="/okf/index.md"' not in text
            or 'href="/okf/md.yaml"' not in text
            or 'href="/okf/sources.json"' not in text
            or 'href="/llms.txt"' not in text
        ):
            errors.append(f"{rel}: missing OKF/discovery alternate links")

        schema_pos = text.find('<script type="application/ld+json">')
        style_pos = text.find("<style>")
        if schema_pos == -1 or style_pos == -1 or schema_pos > style_pos:
            errors.append(f"{rel}: JSON-LD should appear before inline CSS")

        match = re.search(
            r'<script type="application/ld\+json">(.*?)</script>',
            text,
            flags=re.S,
        )
        if not match:
            errors.append(f"{rel}: missing JSON-LD")
        else:
            try:
                schema = json.loads(match.group(1))
            except json.JSONDecodeError as exc:
                errors.append(f"{rel}: invalid JSON-LD: {exc}")

        if schema:
            for value in json_string_values(schema):
                if "stg.texdds.com" in value:
                    errors.append(f"{rel}: JSON-LD must not reference staging checkout URL")
            for node in graph_nodes(schema):
                types = node.get("@type", [])
                if isinstance(types, str):
                    types = [types]
                if "DrivingSchool" in types:
                    errors.append(f"{rel}: schema still contains invalid/unwanted DrivingSchool type")
                if "AggregateRating" in types and node.get("itemReviewed", {}).get("@id") == "https://www.texdds.com/#organization":
                    errors.append(f"{rel}: self-serving organization AggregateRating should not be published")
                citations = node.get("citation", [])
                if isinstance(citations, str):
                    citations = [citations]
                for citation in citations:
                    if not is_absolute_http(str(citation)):
                        errors.append(f"{rel}: non-absolute schema citation {citation}")
                    for domain in duplicate_domain_refs:
                        parsed = urlparse(str(citation))
                        if parsed.netloc.endswith(domain):
                            errors.append(f"{rel}: duplicate consolidation domain present in schema citation: {domain}")

            if rel == "resources/index.html":
                faq_nodes = [node for node in graph_nodes(schema) if node.get("@type") == "FAQPage"]
                if len(faq_nodes) != 1:
                    errors.append("resources/index.html: expected one FAQPage node")
                else:
                    questions = faq_nodes[0].get("mainEntity", [])
                    if len(questions) != 10:
                        errors.append("resources/index.html: FAQPage should contain 10 questions")
                    for question in questions:
                        fragment = str(question.get("@id", "")).split("#", 1)[-1]
                        if not fragment.startswith("faq-") or f'id="{fragment}"' not in text:
                            errors.append(f"resources/index.html: schema fragment missing visible answer {fragment}")
                if 'href="/okf/">Open Knowledge Format</a>' not in text or 'href="#texdds-faq"' not in text:
                    errors.append("resources/index.html: missing OKF or FAQ fragment pill")
                if 'id="open-knowledge-format"' in text or 'class="okf-discovery-link"' in text:
                    errors.append("resources/index.html: retired OKF card or small discovery link still present")

            if rel == "texas/waco/index.html":
                for fragment in sorted(waco_deep_fragments):
                    if f'id="{fragment}"' not in text or f'href="#{fragment}"' not in text:
                        errors.append(f"texas/waco/index.html: missing visible fragment and link {fragment}")
                if text.count('class="locality-panel"') != 11:
                    errors.append("texas/waco/index.html: expected eleven conditional locality panels")
                if 'href="#waco">Waco</a>' not in text or "Waco court process</a>" in text:
                    errors.append("texas/waco/index.html: Waco sitepill should use the simple #waco mapping")
                if text.find('id="waco"') > text.find('id="robinson"'):
                    errors.append("texas/waco/index.html: Waco card should precede Robinson")
                if text.count('class="button secondary compact close-panel" href="/texas/waco/"') != 11:
                    errors.append("texas/waco/index.html: every hide link should resolve to /texas/waco/")
                if "#waco-court-process" in text:
                    errors.append("texas/waco/index.html: retired Waco fragment remains")
                if "10 calendar days (not 10 working days)" not in text:
                    errors.append("texas/waco/index.html: missing Waco calendar-day instruction")
                if "$143.90" not in text or "$168.90" not in text:
                    errors.append("texas/waco/index.html: missing McGregor fee distinction")
                if "does not publish a fee amount" not in text:
                    errors.append("texas/waco/index.html: missing Lacy Lakeview fee limitation")
                if "3,048 reportable crashes" not in text or "80 suspected-serious-injury crashes" not in text:
                    errors.append("texas/waco/index.html: missing concise Waco crash context")
                if "Most reviewed McLennan County courts publish $144" not in text:
                    errors.append("texas/waco/index.html: missing accurate Waco-area fee pattern")
                if "published DSC request average" in text:
                    errors.append("texas/waco/index.html: retired DSC fee-average wording remains")
                if "Riesel began as a cotton-gin and railroad community on Highway 6" not in plain_text:
                    errors.append("texas/waco/index.html: missing combined Riesel locality opening")
                if "China Spring Cougar country" not in plain_text:
                    errors.append("texas/waco/index.html: missing China Spring locality anchor")
                if "not China Spring" in text:
                    errors.append("texas/waco/index.html: contains public-facing locality correction language")
                if "Bellmead's Memorial Park" in plain_text:
                    errors.append("texas/waco/index.html: contains forced Bellmead locality color")
                if '<p class="locality-bridge"><strong><a ' in visible_markup:
                    errors.append("texas/waco/index.html: locality inference should not be visibly cited")
                lede_match = re.search(r'<p class="lede">(.*?)</p>', visible_markup, re.DOTALL)
                if not lede_match:
                    errors.append("texas/waco/index.html: missing Waco opening")
                else:
                    lede_links = re.findall(r'<a\b[^>]*href="([^"]+)"', lede_match.group(1))
                    if lede_links != [
                        "https://www.txdot.gov/content/dam/docs/division/trf/crash-records/2024/14.pdf"
                    ]:
                        errors.append("texas/waco/index.html: Waco opening should visibly cite only the TxDOT metrics")
                if any(token in text for token in ('class="fee-pattern"', 'class="locality-citations"', 'class="fragment-permalink"')):
                    errors.append("texas/waco/index.html: contains retired fee or citation blocks")
                if text.count('class="fact-card signal-card"'):
                    errors.append("texas/waco/index.html: Waco signals should be integrated into the opening, not cards")
                nodes = graph_nodes(schema)
                parts = [node for node in nodes if node.get("@type") == "WebPageElement"]
                if len(parts) != 11:
                    errors.append("texas/waco/index.html: expected eleven WebPageElement fragment nodes")
                for part in parts:
                    citations = part.get("citation", [])
                    if len(citations) < 1 or not all(is_absolute_http(url) for url in citations):
                        errors.append(f"texas/waco/index.html: incomplete schema citations for {part.get('@id')}")
                web_pages = [node for node in nodes if node.get("@type") == "WebPage"]
                if len(web_pages) != 1:
                    errors.append("texas/waco/index.html: expected one canonical WebPage entity")
                    local_page = None
                else:
                    local_page = web_pages[0]
                    if local_page.get("@id") != "https://www.texdds.com/texas/waco/#webpage":
                        errors.append("texas/waco/index.html: canonical WebPage @id is not slash-safe #webpage")
                    if local_page.get("url") != "https://www.texdds.com/texas/waco/":
                        errors.append("texas/waco/index.html: canonical WebPage URL is not normalized")
                if any(str(node.get("@id", "")).endswith("#locality-page") for node in nodes):
                    errors.append("texas/waco/index.html: duplicate #locality-page entity remains")
                if local_page:
                    page_citations = set(local_page.get("citation", []))
                    part_citations = {
                        url
                        for part in parts
                        for url in part.get("citation", [])
                    }
                    if not part_citations.issubset(page_citations):
                        errors.append("texas/waco/index.html: canonical WebPage schema omits fragment citations")
                    part_ids = {part["@id"] for part in parts}
                    has_part_ids = {item.get("@id") for item in local_page.get("hasPart", [])}
                    if has_part_ids != part_ids:
                        errors.append("texas/waco/index.html: WebPage hasPart does not exactly match fragment nodes")
                forbidden_schema_values = (
                    "Court named on the citation",
                    "tigerweb.geo.census.gov",
                    "chinaspringisd.net",
                    "baylorbears.com",
                    "magnolia.com",
                    "nps.gov/waco",
                    "risdweb.org",
                    "/774/History",
                    "/city-services/volunteer-fire-department/",
                    "/86/History",
                    "/198/Parks-Recreation",
                    "/community/page/history",
                    "/about-3",
                    "/woodway-history/",
                    "/visit-west-texas/",
                )
                schema_text = json.dumps(schema, ensure_ascii=False)
                for forbidden in forbidden_schema_values:
                    if forbidden in schema_text:
                        errors.append(f"texas/waco/index.html: inference-only schema value remains: {forbidden}")
                jp_offices = [
                    node
                    for node in nodes
                    if node.get("@type") == "GovernmentOffice"
                    and node.get("name") == "McLennan County Justice Courts"
                    and node.get("url") == "https://www.mclennan.gov/267/Justices-of-the-Peace"
                ]
                if len(jp_offices) != 1:
                    errors.append("texas/waco/index.html: missing real McLennan County Justice Courts entity")
                else:
                    china_part = next(
                        (part for part in parts if str(part.get("@id", "")).endswith("#china-spring")),
                        None,
                    )
                    if not china_part or china_part.get("about", {}).get("@id") != jp_offices[0].get("@id"):
                        errors.append("texas/waco/index.html: China Spring fragment is not anchored to McLennan County Justice Courts")
                if not any(node.get("@type") == "ItemList" and str(node.get("@id", "")).endswith("#waco-area-court-processes") for node in nodes):
                    errors.append("texas/waco/index.html: missing Waco-area court-process ItemList")
                else:
                    item_list = next(
                        node
                        for node in nodes
                        if node.get("@type") == "ItemList"
                        and str(node.get("@id", "")).endswith("#waco-area-court-processes")
                    )
                    item_urls = [item.get("item", {}).get("@id") for item in item_list.get("itemListElement", [])]
                    if item_urls != [part.get("@id") for part in parts]:
                        errors.append("texas/waco/index.html: ItemList order does not match Waco-first fragment graph")
                internal_schema_urls = [
                    value
                    for value in json_string_values(schema)
                    if value.startswith("https://www.texdds.com/")
                ]
                bad_internal_urls = [
                    value
                    for value in internal_schema_urls
                    if (
                        urlparse(value.split("#", 1)[0].split("?", 1)[0]).path != "/"
                        and "." not in urlparse(value.split("#", 1)[0].split("?", 1)[0]).path.rsplit("/", 1)[-1]
                        and not urlparse(value.split("#", 1)[0].split("?", 1)[0]).path.endswith("/")
                    )
                ]
                if bad_internal_urls:
                    errors.append(f"texas/waco/index.html: internal schema URLs missing trailing slashes: {bad_internal_urls[:3]}")
                if '<link rel="canonical" href="https://www.texdds.com/texas/waco/">' not in text:
                    errors.append("texas/waco/index.html: canonical link missing trailing slash")
                if '<meta property="og:url" content="https://www.texdds.com/texas/waco/">' not in text:
                    errors.append("texas/waco/index.html: og:url missing trailing slash")

        for match in re.finditer(r'<a\b[^>]*href="[^"]*stg\.texdds\.com[^"]*"[^>]*>', text):
            anchor = match.group(0)
            if 'rel="' not in anchor or "nofollow" not in anchor:
                errors.append(f"{rel}: staging link should use rel=\"nofollow noopener\"")

        for note_block in re.findall(
            r'<ul class="action-notes">(.*?)</ul>', text, flags=re.DOTALL
        ):
            action_notes = [
                re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", item))).strip().casefold()
                for item in re.findall(r"<li>(.*?)</li>", note_block, flags=re.DOTALL)
            ]
            if len(action_notes) != len(set(action_notes)):
                errors.append(f"{rel}: duplicate action note rendered beneath court buttons")

        for attr in ("href", "src"):
            for value in re.findall(rf'{attr}="([^"]+)"', text):
                if value.startswith("/") and not value.startswith("//"):
                    if not internal_target(value).exists():
                        errors.append(f"{rel}: broken internal {attr} {value}")
                if "stg.texdds.com" in value:
                    stg_refs.append(f"{rel}: {value}")
                    if rel != "courses/index.html":
                        errors.append(f"{rel}: staging link must stay gated behind /courses/")
                    if value in required_purchase_links:
                        found_purchase_links.add(value)

        if rel.startswith("texas/") and rel.endswith("/index.html") and rel != "texas/index.html":
            is_deep_locality = 'class="locality-panel"' in text
            locality_counts[rel] = (
                text.count('class="locality-panel"')
                if is_deep_locality
                else text.count("Court reminder")
            )
            locality_signal_counts[rel] = text.count('class="fact-card signal-card"')
            locality_slug = rel.split("/")[1]
            expected_region = locality_regions.get(locality_slug)
            if expected_region and f'<p class="eyebrow">{expected_region}</p>' not in text:
                errors.append(f"{rel}: locality eyebrow does not match the hub region")
            if "court-source research checked" in plain_text:
                errors.append(f"{rel}: internal research-check label must not appear in the visible header")
            if "The separate figure is published in" in plain_text:
                errors.append(f"{rel}: stranded secondary TxDOT citation sentence remains")
            if "For context, TxDOT also publishes a separate 2024 DUI-alcohol city table" in plain_text:
                errors.append(f"{rel}: repetitive DUI context belongs on the Texas hub, not locality pages")
            if "No separate $3 materials fee:" not in plain_text:
                errors.append(f"{rel}: missing HB 3012 locality fee guidance")
            if "/courses/#insurance" in text or "Insurance Discount Course" in plain_text:
                errors.append(f"{rel}: insurance-discount course must not be promoted on locality pages")
            panel_count = text.count('class="locality-panel"')
            course_fit_count = text.count('class="locality-course-fit"')
            court_terms_count = text.count('class="locality-court-terms"')
            if is_deep_locality and course_fit_count != panel_count:
                errors.append(
                    f"{rel}: expected one course/record guidance state per court panel "
                    f"({course_fit_count} != {panel_count})"
                )
            if is_deep_locality and court_terms_count != 1:
                errors.append(
                    f"{rel}: expected one terminology block in the main court panel "
                    f"({court_terms_count} != 1)"
                )
            if locality_slug == "waco" and (
                "https://www.txdot.gov/content/dam/docs/division/trf/crash-records/2024/14.pdf"
                not in text
            ):
                errors.append("texas/waco/index.html: city crash citation must target the TxDOT PDF")
            if not is_deep_locality and locality_signal_counts[rel] < 2:
                errors.append(f"{rel}: fewer than two local signal cards")
            if schema:
                nodes = graph_nodes(schema)
                place_ids = {
                    node.get("@id")
                    for node in nodes
                    if node.get("@type") == "Place" and str(node.get("@id", "")).endswith("#place")
                }
                local_pages = [
                    node
                    for node in nodes
                    if node.get("@type") == "WebPage"
                    and str(node.get("@id", "")).endswith("#webpage")
                ]
                if not place_ids:
                    errors.append(f"{rel}: missing locality Place schema")
                if not local_pages:
                    errors.append(f"{rel}: missing locality WebPage schema")
                if any(
                    node.get("@type") == "WebPage"
                    and str(node.get("@id", "")).endswith("#locality-page")
                    for node in nodes
                ):
                    errors.append(f"{rel}: duplicate #locality-page schema remains")
                for node in local_pages:
                    coverage = node.get("spatialCoverage", {}).get("@id")
                    if coverage not in place_ids:
                        errors.append(f"{rel}: locality WebPage schema missing spatialCoverage Place link")
                    citations = node.get("citation", [])
                    if len(citations) < 2:
                        errors.append(f"{rel}: locality WebPage schema has fewer than two citations")

        if rel == "texas/index.html":
            if plain_text.count("Y'all") != 1:
                errors.append("texas/index.html: statewide identity copy must use Y'all exactly once")
            if "Use the court name printed on your citation, not the city you were driving through." not in plain_text:
                errors.append("texas/index.html: missing court-name disambiguator in the hero")
            if text.find('id="city-guides"') > text.find('id="find-your-court"'):
                errors.append("texas/index.html: locality grid must precede the not-listed fallback")
            if "https://card.txcourts.gov/ajrdata.aspx/1000" not in text:
                errors.append("texas/index.html: missing official statewide court-directory fallback")
            for traffic_pdf in ("/2024/14.pdf", "/2024/42.pdf"):
                if traffic_pdf not in text:
                    errors.append(f"texas/index.html: missing statewide city-table context {traffic_pdf}")

    missing_purchase_links = sorted(required_purchase_links - found_purchase_links)
    for link in missing_purchase_links:
        errors.append(f"missing required purchase link {link}")

    sitemap_urls = (ROOT / "sitemap.xml").read_text(encoding="utf-8").count("<url>")
    result = {
        "html_files": len(html_files),
        "schema_errors_or_broken_links": len(errors),
        "errors": errors[:50],
        "stg_refs": len(stg_refs),
        "required_purchase_links_missing": missing_purchase_links,
        "locality_pages": len(locality_counts),
        "locality_pages_without_facts": [
            route for route, count in locality_counts.items() if count == 0
        ],
        "min_local_fact_cards": min(locality_counts.values()) if locality_counts else 0,
        "min_local_signal_cards": min(locality_signal_counts.values()) if locality_signal_counts else 0,
        "sitemap_urls": sitemap_urls,
        "okf_documents": len(list((ROOT / "okf").rglob("*.md"))) if (ROOT / "okf").exists() else 0,
        "okf_version": okf_version,
        "okf_manifest_documents": okf_manifest_documents,
        "okf_source_count": okf_source_count,
        "okf_locality_count": okf_locality_count,
        "canonical_host": "https://www.texdds.com",
    }
    print(json.dumps(result, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
