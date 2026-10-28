# Copilot instructions for this repository

This repository is governed by the technology standards
(source of truth: https://github.com/gmale747/tech-standards).

- Before adding or upgrading any library, framework, or CDN resource, use the
  `standards-check` skill to confirm the version is approved in the central manifest.
- Load third-party scripts and styles only from approved CDNs, with `integrity` and `crossorigin` attributes.
- Never write CSV or user content to the page with `innerHTML`; use `textContent`.
- Keep `app-record.yaml`, `README.md`, `SECURITY.md`, and `docs/runbook.md` current when behavior changes.
- When asked for documentation, a compliance report, or an update to app metadata, use the
  `standards-check` skill.
