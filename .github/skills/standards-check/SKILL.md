---
name: standards-check
description: Checks a repository against the technology standards manifest (approved frameworks, dependency versions, security, governance, documentation and accessibility policies). Use when the user asks about compliance, standards, policies, whether a library or version is approved, before adding or upgrading a dependency, for a compliance or technology report, to generate application documentation from app-record.yaml, or to update application metadata (version, URLs, tags) in app-record.yaml.
license: Internal use
---

# Technology Standards Check

You help developers keep this repository compliant with the technology standards.

## Sources of truth (never guess - read these)

| What | Where |
|---|---|
| Approved technologies, versions, sunset dates, rules, exceptions | `https://raw.githubusercontent.com/gmale747/tech-standards/main/manifest/technology-manifest.yaml` |
| Policies (SEC, GOV, DOC, A11Y) | `https://github.com/gmale747/tech-standards/tree/main/policies` |
| This app's CMDB record | `app-record.yaml` in the repository root |
| Documentation template | `references/app-doc-template.md` in this skill's folder |

The check engine is `scripts/check_standards.py` in this skill's folder
(usually `.github/skills/standards-check/` or `.agents/skills/standards-check/`).
It needs Python 3.9+ and PyYAML (`pip install pyyaml`). It downloads the manifest automatically;
if there is no network, ask the user for a local path and pass `--manifest <path>`.

## Task 1 - Compliance check ("check standards", "am I compliant?", "run the standards check")

1. Run: `python <skill-folder>/scripts/check_standards.py --repo .`
2. Present the result as a **Compliance Report** with three parts:
   - Overall status (PASS / CAUTION / WARN / FAIL) and counts.
   - **Frameworks and dependencies** table: technology, version, status, where found.
   - **Policy findings**: each finding with its policy ID, file and line.
3. For every FAIL, explain the fix in one or two sentences and cite the policy ID.
   Offer to make the fix; do not change files unless the user agrees.
4. Remind the user that a FAIL blocks the pull request (GOV-03) unless an approved exception exists (GOV-04).

## Task 2 - Before adding or upgrading a dependency

1. Run: `python <skill-folder>/scripts/check_standards.py --lookup <name> [<version>]`
2. If the result is not PASS, recommend the newest approved version from the output instead.
3. If the technology is not in the manifest, say it needs architecture review (TECH-00) and do not add it.
4. When adding a CDN resource, use an approved CDN (SEC-03) and include `integrity` and
   `crossorigin="anonymous"` (SEC-04). Compute the SRI hash; never invent one.

## Task 3 - Generate documentation ("document this app", "write the overview")

1. Read `app-record.yaml`, the README, and the repository structure.
2. Run the compliance check (Task 1) with `--format json` to get the dependency list.
3. Fill `references/app-doc-template.md`. Use only facts from those sources.
   `{{how_it_works}}` is 3-5 sentences you write from the README and code structure.
   Write `TODO` for anything unknown - never invent owners, IPs, URLs, or versions.
4. Audience (default internal): keep blocks marked `<!-- audience:internal -->` for internal and
   restricted readers, blocks marked `<!-- audience:restricted -->` for restricted readers only,
   and remove the marker comments from the output.
5. Save to `docs/app-overview.md` (or the path the user asks for) and keep the generated
   comment at the top so reviewers know it is generated (DOC-05).
   The Standards Console uses this same template, so both produce the same document.

## Task 4 - Update application metadata safely ("update the version to 1.1.0", "change the prod URL")

Follow GOV-07 exactly:
1. Read `app-record.yaml`. Only fields listed under `app.automation.auto_update_fields` may be changed,
   and only if `allow_auto_updates: true`. Otherwise refuse and explain who must approve.
2. Validate the new value (semantic version, URL, ISO date, IPv4 as applicable).
3. Show the before/after diff and wait for the user to confirm.
4. Apply the change, also set `metadata.last_updated` to today, and re-run Task 1.
5. Suggest the commit message: `AI: update <field> to <value> (<app id>)`.

## Task 5 - Policy questions

Fetch the relevant policy file, answer briefly, and quote the policy ID (for example SEC-04).

## Guardrails

- Never edit the central manifest or policies from an application repository. Changes to standards
  go through a pull request on `gmale747/tech-standards` (GOV-05).
- Never add an exception yourself. Exceptions are approved by the review board (GOV-04).
- Do not send repository content to any external service other than fetching the manifest
  and policies above (GOV-08).
- Do not print secrets. If SEC-01 fires, tell the user to rotate the secret and remove it from git history.
