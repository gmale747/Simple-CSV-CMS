#!/usr/bin/env python3
"""
standards check engine.

One deterministic engine, three callers:
  * the standards-check Copilot skill (developer runs it on demand)
  * the reusable GitHub Actions workflow (PR gate)
  * tools/audit.py (scans every repo for monitoring and technology audits)

Usage:
  check_standards.py [--repo PATH] [--manifest PATH_OR_URL]
                     [--format md|json|both] [--out PREFIX] [--fail-on fail|warn|never]
  check_standards.py --lookup NAME [VERSION]      # "is this version approved?"

Requires: Python 3.9+ and PyYAML (pip install pyyaml)
"""
from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is required: pip install pyyaml")

DEFAULT_MANIFEST_URL = os.environ.get(
    "STANDARDS_MANIFEST",
    "https://raw.githubusercontent.com/gmale747/tech-standards/main/manifest/technology-manifest.yaml",
)
STATUS_TO_LEVEL = {"approved": "PASS", "caution": "CAUTION", "deprecated": "WARN", "prohibited": "FAIL"}
LEVEL_RANK = {"PASS": 0, "CAUTION": 1, "WARN": 2, "FAIL": 3}
LEVEL_ICON = {"PASS": "✅", "CAUTION": "🟡", "WARN": "🟠", "FAIL": "❌"}
TEXT_EXT = {".html", ".htm", ".js", ".ts", ".css", ".json", ".yml", ".yaml", ".py", ".java", ".xml",
            ".properties", ".env", ".cs", ".config", ".md", ".txt", ".csv"}


# --------------------------------------------------------------------------- manifest
def load_manifest(source: str) -> dict:
    if re.match(r"^https?://", source):
        with urllib.request.urlopen(source, timeout=20) as r:  # nosec - fixed, trusted source
            return yaml.safe_load(r.read().decode("utf-8"))
    return yaml.safe_load(Path(source).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- versions
def parse_version(v: str) -> tuple | None:
    m = re.search(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?", str(v))
    if not m:
        return None
    return tuple(int(x or 0) for x in m.groups())


def in_range(version: tuple, spec: str) -> bool:
    spec = str(spec).strip()
    if spec in ("*", ""):
        return True
    for part in spec.split():
        m = re.match(r"^(>=|<=|>|<|==)?(.+)$", part)
        op, target = m.group(1) or "==", parse_version(m.group(2))
        if target is None:
            return False
        ok = {">=": version >= target, "<=": version <= target, ">": version > target,
              "<": version < target, "==": version == target}[op]
        if not ok:
            return False
    return True


def find_technology(manifest: dict, name: str) -> dict | None:
    n = name.lower()
    for t in manifest.get("technologies", []):
        names = [t["name"].lower()] + [a.lower() for a in t.get("aliases", [])]
        if n in names:
            return t
    return None


def evaluate_version(manifest: dict, name: str, version: str, app_id: str | None, today: dt.date) -> dict:
    tech = find_technology(manifest, name)
    result = {"technology": name, "version": version, "category": "unlisted", "status": "unlisted",
              "level": "WARN", "note": "Not in the approved manifest - needs architecture review (TECH-00).",
              "policy": "TECH-00"}
    if not tech:
        return result
    result.update(technology=tech["name"], category=tech.get("category", ""), policy="SEC-02")
    pv = parse_version(version)
    if pv is None:
        result.update(status="unknown-version", level="WARN",
                      note=f"Could not read version '{version}'. Pin an exact version.")
        return result
    for rule in tech.get("versions", []):
        if in_range(pv, rule["range"]):
            status = rule["status"]
            level = STATUS_TO_LEVEL[status]
            note = rule.get("note", "")
            sunset = rule.get("sunset")
            if status == "deprecated" and sunset:
                sunset_d = sunset if isinstance(sunset, dt.date) else dt.date.fromisoformat(str(sunset))
                days = (sunset_d - today).days
                if days < 0:
                    level, note = "FAIL", f"Sunset date {sunset_d} has passed. {note}".strip()
                else:
                    note = f"Sunsets {sunset_d} ({days} days). {note}".strip()
            result.update(status=status, level=level, note=note)
            break
    else:
        result.update(status="no-matching-range", level="WARN", note="Version not covered by manifest ranges.")
    if result["level"] == "FAIL":
        exc = find_exception(manifest, app_id, tech["name"], version, today)
        if exc:
            result.update(level="WARN", status=f"{result['status']} (exception)",
                          note=f"Exception {exc.get('ticket')} until {exc.get('expires')}: {exc.get('reason', '')}")
    return result


def find_exception(manifest, app_id, tech_name, version, today):
    for e in manifest.get("exceptions", []) or []:
        expires = e.get("expires")
        expires = expires if isinstance(expires, dt.date) else dt.date.fromisoformat(str(expires))
        if (e.get("app_id") == app_id and e.get("technology", "").lower() == tech_name.lower()
                and str(e.get("version")) == str(version).lstrip("^~=v") and expires >= today):
            return e
    return None


# --------------------------------------------------------------------------- repo walking
def iter_files(repo: Path, exclude_dirs: list[str]):
    excl = {e.strip("/") for e in exclude_dirs}
    for root, dirs, files in os.walk(repo):
        rel_root = Path(root).relative_to(repo).as_posix()
        # skip a folder if its repo-relative path or its bare name is excluded
        dirs[:] = [d for d in dirs if d not in excl and (d if rel_root == "." else f"{rel_root}/{d}") not in excl]
        for f in files:
            yield Path(root) / f


def rel(p: Path, repo: Path) -> str:
    return p.relative_to(repo).as_posix()


def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# --------------------------------------------------------------------------- dependency detection
CDN_PATTERNS = [
    re.compile(r"https?://(?:cdn\.jsdelivr\.net/npm|unpkg\.com)/((?:@[\w.-]+/)?[\w.-]+)@(\d[\w.-]*)"),
    re.compile(r"https?://cdnjs\.cloudflare\.com/ajax/libs/([\w.-]+)/(\d[\w.-]*)/"),
    re.compile(r"https?://code\.jquery\.com/(jquery)-(\d+\.\d+\.\d+)"),
    re.compile(r"https?://ajax\.googleapis\.com/ajax/libs/([\w.-]+)/(\d[\w.-]*)/"),
]


def detect_dependencies(repo: Path, files: list[Path]) -> list[dict]:
    found: dict[tuple, dict] = {}

    def add(name, version, source, ecosystem):
        key = (name.lower(), str(version))
        found.setdefault(key, {"name": name, "version": str(version), "ecosystem": ecosystem, "sources": []})
        if source not in found[key]["sources"]:
            found[key]["sources"].append(source)

    for p in files:
        r = rel(p, repo)
        if p.name == "package.json":
            try:
                data = json.loads(read_text(p))
            except json.JSONDecodeError:
                continue
            for sec in ("dependencies", "devDependencies"):
                for n, v in (data.get(sec) or {}).items():
                    add(n, v.lstrip("^~=v"), r, "npm")
        elif p.name == "requirements.txt":
            for line in read_text(p).splitlines():
                m = re.match(r"^\s*([A-Za-z0-9_.-]+)\s*(?:==|>=|~=)\s*([\w.]+)", line)
                if m:
                    add(m.group(1), m.group(2), r, "pip")
        elif p.name == "pom.xml":
            try:
                root = ET.fromstring(read_text(p))
            except ET.ParseError:
                continue
            ns = {"m": root.tag.split("}")[0].strip("{")} if root.tag.startswith("{") else {}
            q = (lambda t: f"m:{t}") if ns else (lambda t: t)
            for dep in root.iter(f"{{{ns['m']}}}dependency" if ns else "dependency"):
                a, v = dep.find(q("artifactId"), ns), dep.find(q("version"), ns)
                if a is not None and v is not None and not v.text.startswith("${"):
                    add(a.text, v.text, r, "maven")
        elif p.suffix.lower() in (".html", ".htm"):
            text = read_text(p)
            for pat in CDN_PATTERNS:
                for m in pat.finditer(text):
                    add(m.group(1), m.group(2), r, "cdn")
    return list(found.values())


# --------------------------------------------------------------------------- rule checks
TAG_RE = re.compile(r"<(script|link)\b[^>]*>", re.I)
ATTR = lambda name: re.compile(rf'\b{name}\s*=\s*["\']([^"\']*)["\']', re.I)  # noqa: E731


def line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def external_tags(text: str):
    for m in TAG_RE.finditer(text):
        tag = m.group(0)
        if m.group(1).lower() == "link" and not re.search(r'rel\s*=\s*["\']stylesheet', tag, re.I):
            continue
        url = ATTR("src").search(tag) or ATTR("href").search(tag)
        if url and re.match(r"^(https?:)?//", url.group(1)):
            yield m, tag, url.group(1)


def run_rule(rule: dict, manifest: dict, repo: Path, files: list[Path]) -> list[dict]:
    out = []
    level = {"fail": "FAIL", "warn": "WARN", "caution": "CAUTION"}[rule.get("severity", "warn")]
    targets = [p for p in files if any(fnmatch.fnmatch(p.name.lower(), g.lower()) for g in rule.get("files", ["*"]))]
    check = rule["check"]

    def finding(path, line, msg):
        out.append({"policy": rule["id"], "title": rule["title"], "level": level,
                    "file": rel(path, repo), "line": line, "message": msg})

    for p in targets:
        if check == "forbidden_file":
            finding(p, None, f"{p.name} found - convert to Markdown.")
            continue
        text = read_text(p)
        if check == "forbidden_pattern":
            for pat in rule["patterns"]:
                for m in re.finditer(pat, text):
                    snippet = m.group(0)[:60].replace("\n", " ")
                    if rule["id"] == "SEC-01":
                        snippet = snippet[:12] + "…(redacted)"
                    finding(p, line_of(text, m.start()), f"Forbidden pattern: `{snippet}`")
        elif check == "required_pattern":
            if not any(re.search(pat, text) for pat in rule["patterns"]):
                finding(p, None, "Required element missing.")
        elif check == "approved_cdn":
            allowed = [h.lower() for h in manifest.get("approved_cdns", [])]
            for m, _tag, url in external_tags(text):
                host = re.sub(r"^(https?:)?//", "", url).split("/")[0].lower()
                if host not in allowed:
                    finding(p, line_of(text, m.start()), f"Unapproved host `{host}`.")
        elif check == "external_resource_integrity":
            for m, tag, url in external_tags(text):
                if not ATTR("integrity").search(tag) or not ATTR("crossorigin").search(tag):
                    finding(p, line_of(text, m.start()), f"Missing integrity/crossorigin on `{url[:70]}`.")
        elif check == "img_alt":
            for m in re.finditer(r"<img\b[^>]*>", text, re.I):
                if not re.search(r"\balt\s*=", m.group(0), re.I):
                    finding(p, line_of(text, m.start()), "Image without alt attribute.")
    return out


# --------------------------------------------------------------------------- app record
def get_path(data: dict, dotted: str):
    cur = data
    for key in dotted.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def check_app_record(repo: Path, manifest: dict) -> tuple[dict | None, list[dict]]:
    findings = []
    path = repo / "app-record.yaml"
    if not path.exists():
        return None, findings  # reported by required_files
    try:
        record = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        return None, [{"policy": "GOV-02", "title": "App record is valid", "level": "FAIL",
                       "file": "app-record.yaml", "line": None, "message": f"YAML parse error: {e}"}]
    spec = manifest.get("app_record", {})
    for field in spec.get("required_fields", []):
        if get_path(record, field) in (None, "", []):
            findings.append({"policy": "GOV-02", "title": "App record complete", "level": "FAIL",
                             "file": "app-record.yaml", "line": None, "message": f"Missing `{field}`."})
    for field, allowed in (spec.get("allowed_values") or {}).items():
        val = get_path(record, field)
        if val is not None and val not in allowed:
            findings.append({"policy": "GOV-02", "title": "App record values", "level": "FAIL",
                             "file": "app-record.yaml", "line": None,
                             "message": f"`{field}` = `{val}`; allowed: {', '.join(allowed)}."})
    dept = get_path(record, "app.ownership.department")
    if dept and spec.get("departments") and dept not in spec["departments"]:
        findings.append({"policy": "GOV-02", "title": "App record values", "level": "WARN",
                         "file": "app-record.yaml", "line": None, "message": f"Unknown department `{dept}`."})
    return record, findings


# --------------------------------------------------------------------------- main check
def run_check(repo: str | Path, manifest: dict, today: dt.date | None = None) -> dict:
    repo = Path(repo).resolve()
    today = today or dt.date.today()
    files = list(iter_files(repo, manifest.get("scan", {}).get("exclude_dirs", [])))
    findings: list[dict] = []

    for req in manifest.get("required_files", []):
        if not (repo / req["path"]).exists():
            findings.append({"policy": req["policy"], "title": "Required file present", "level": "FAIL",
                             "file": req["path"], "line": None, "message": f"`{req['path']}` is missing."})

    record, rec_findings = check_app_record(repo, manifest)
    findings += rec_findings
    app = (record or {}).get("app", {})
    app_id = app.get("id")

    deps = []
    for d in detect_dependencies(repo, files):
        ev = evaluate_version(manifest, d["name"], d["version"], app_id, today)
        ev.update(ecosystem=d["ecosystem"], sources=d["sources"])
        deps.append(ev)
    deps.sort(key=lambda x: (-LEVEL_RANK[x["level"]], x["technology"]))

    for rule in manifest.get("rules", []):
        findings += run_rule(rule, manifest, repo, files)

    all_levels = [f["level"] for f in findings] + [d["level"] for d in deps]
    overall = max(all_levels, key=lambda lv: LEVEL_RANK[lv]) if all_levels else "PASS"
    counts = {lv: all_levels.count(lv) for lv in ("FAIL", "WARN", "CAUTION")}
    return {
        "checked_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "repo": repo.name,
        "manifest_version": manifest.get("manifest_version"),
        "overall": overall,
        "counts": counts,
        "app": {
            "id": app_id, "name": app.get("name"),
            "department": get_path(app, "ownership.department"),
            "owner": get_path(app, "ownership.owner"),
            "visibility": get_path(app, "access.visibility"),
            "data_classification": get_path(app, "access.data_classification"),
            "version": get_path(app, "metadata.version"),
            "lifecycle": get_path(app, "metadata.lifecycle"),
        },
        "dependencies": deps,
        "findings": sorted(findings, key=lambda f: (-LEVEL_RANK[f["level"]], f["policy"])),
    }


# --------------------------------------------------------------------------- output
def to_markdown(r: dict, policies_url: str = "") -> str:
    a = r["app"]
    L = [f"# Compliance Report: {a.get('name') or r['repo']}", "",
         f"**Overall: {LEVEL_ICON[r['overall']]} {r['overall']}**  ·  "
         f"{r['counts']['FAIL']} fail · {r['counts']['WARN']} warn · {r['counts']['CAUTION']} caution  ·  "
         f"manifest v{r['manifest_version']}  ·  {r['checked_at']}", "",
         "## Application record (CMDB)", "",
         "| App ID | Department | Owner | Visibility | Classification | Version | Lifecycle |",
         "|---|---|---|---|---|---|---|",
         f"| {a.get('id') or '—'} | {a.get('department') or '—'} | {a.get('owner') or '—'} | "
         f"{a.get('visibility') or '—'} | {a.get('data_classification') or '—'} | {a.get('version') or '—'} | "
         f"{a.get('lifecycle') or '—'} |", "",
         "## Frameworks and dependencies (version status)", ""]
    if r["dependencies"]:
        L += ["| Status | Technology | Version | Category | Found in | Note |", "|---|---|---|---|---|---|"]
        for d in r["dependencies"]:
            L.append(f"| {LEVEL_ICON[d['level']]} {d['status']} | {d['technology']} | {d['version']} | "
                     f"{d['category']} | {', '.join(d['sources'])} | {d['note']} |")
    else:
        L.append("_No dependencies detected._")
    L += ["", "## Policy findings", ""]
    if r["findings"]:
        L += ["| Level | Policy | Rule | Location | Detail |", "|---|---|---|---|---|"]
        for f in r["findings"]:
            loc = f["file"] + (f":{f['line']}" if f.get("line") else "")
            L.append(f"| {LEVEL_ICON[f['level']]} {f['level']} | {f['policy']} | {f['title']} | `{loc}` | {f['message']} |")
    else:
        L.append("✅ No policy findings.")
    L += ["", "---", "PASS = approved · CAUTION = allowed, plan upgrade · WARN = review / deprecated · "
          "FAIL = blocks merge unless an approved exception exists (GOV-04)."]
    if policies_url:
        L.append(f"Policies: {policies_url}")
    return "\n".join(L) + "\n"


def emit_github_annotations(r: dict):
    for f in r["findings"]:
        kind = "error" if f["level"] == "FAIL" else "warning"
        line = f",line={f['line']}" if f.get("line") else ""
        print(f"::{kind} file={f['file']}{line},title={f['policy']}::{f['title']}: {f['message']}")
    for d in r["dependencies"]:
        if d["level"] in ("FAIL", "WARN"):
            kind = "error" if d["level"] == "FAIL" else "warning"
            print(f"::{kind} file={d['sources'][0]},title={d['policy']}::{d['technology']} {d['version']} "
                  f"is {d['status']}. {d['note']}")


def lookup(manifest: dict, name: str, version: str | None):
    tech = find_technology(manifest, name)
    if not tech:
        print(f"{name}: NOT IN MANIFEST - requires architecture review before use (TECH-00).")
        return
    print(f"{tech['name']} ({tech.get('category')}) - ecosystems: {', '.join(tech.get('ecosystems', []))}")
    for v in tech["versions"]:
        extra = f" sunset {v['sunset']}" if v.get("sunset") else ""
        print(f"  {v['range']:<20} {v['status']}{extra}  {v.get('note', '')}")
    if version:
        ev = evaluate_version(manifest, name, version, None, dt.date.today())
        print(f"\n{name} {version}: {ev['level']} ({ev['status']}) {ev['note']}")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST_URL)
    ap.add_argument("--format", choices=["md", "json", "both"], default="md")
    ap.add_argument("--out", help="write report(s) to PREFIX.md / PREFIX.json instead of stdout")
    ap.add_argument("--fail-on", choices=["fail", "warn", "never"], default="never")
    ap.add_argument("--lookup", nargs="+", metavar=("NAME", "VERSION"))
    args = ap.parse_args(argv)

    manifest = load_manifest(args.manifest)
    if args.lookup:
        lookup(manifest, args.lookup[0], args.lookup[1] if len(args.lookup) > 1 else None)
        return 0

    report = run_check(args.repo, manifest)
    md = to_markdown(report, manifest.get("policies_base_url", ""))
    if args.out:
        if args.format in ("md", "both"):
            Path(f"{args.out}.md").write_text(md, encoding="utf-8")
        if args.format in ("json", "both"):
            Path(f"{args.out}.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
        print(f"Overall: {report['overall']}  (report written to {args.out}.*)")
    else:
        print(md if args.format != "json" else json.dumps(report, indent=2, default=str))

    if os.environ.get("GITHUB_ACTIONS") == "true":
        emit_github_annotations(report)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
                fh.write(md)

    threshold = {"fail": 3, "warn": 2, "never": 99}[args.fail_on]
    return 1 if LEVEL_RANK[report["overall"]] >= threshold else 0


if __name__ == "__main__":
    sys.exit(main())
