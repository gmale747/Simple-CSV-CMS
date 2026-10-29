<!-- generated from app-record.yaml with the standards-check template (internal audience) -->
# Road Construction Help Center

> Public-facing help articles about road construction, work zones, detours, and permits. Content is stored in a CSV file.

| | |
|---|---|
| App ID | simple-csv-cms |
| Version | 1.0.0 |
| Lifecycle | development |
| Last updated | 2026-10-22 |
| Visibility / classification | public / public |
| Repository | https://github.com/gmale747/Simple-CSV-CMS |
| Website | https://gmale747.github.io/Simple-CSV-CMS/ |

## How it works
This site is a lightweight static CMS that stores article content in a CSV file and renders it as HTML pages. The main catalog page summarizes all posts with search, filters, and category views, while the detail page loads a single article by slug from the URL query string. The content model uses fields like post-name, category, header, body, image, and URL to drive the site without a database. The app is designed as a small, portable, public-facing content hub for road construction information.

## Ownership
- Department: Transportation Systems
- Team: Public Information Web
- Owner: Jane Doe
- Escalation contact: jane.doe@example.gov

## Environments
| Environment | URL | Hosting |
|---|---|---|
| dev | http://localhost:8080 | local |
| prod | https://gmale747.github.io/Simple-CSV-CMS/ | github-pages |

## Operations
- Runbook: docs/runbook.md
- Security policy: SECURITY.md

## Roles with access
- developer
- content-editor

## Technology stack and compliance
| Technology | Version | Status |
|---|---|---|
| bootstrap | 5.3.3 | approved |
| papaparse | 5.4.1 | approved |

Overall compliance: **PASS** (manifest v1.0.0, checked 2026-10-29T22:39:44+00:00)
