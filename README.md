# Road Construction Help Center (Simple-CSV-CMS)

A deliberately simple blog CMS used for testing of (central YAML manifest + GitHub Copilot skill + PR enforcement + audits).

- HTML5 + Bootstrap 5.3.3 + a little JavaScript (PapaParse 5.4.1 for CSV parsing)
- `data/posts.csv` is the database: `post-name, post-category, post-header, post-body, post-main-image, post-url`
- `index.html` is a visual summary of all articles (stats, category bars, search, filters, cards)
- `post.html?slug=<post-url>` shows one article

## Run locally
```bash
python3 -m http.server 8080   # then open http://localhost:8080
```

## Compliance files
| File | Purpose |
|---|---|
| `app-record.yaml` | This app's CMDB record (owner, department, access level, environments) |
| `.github/skills/standards-check/` | GitHub Copilot skill that checks this repo against the central manifest |
| `.github/copilot-instructions.md` | Always-on Copilot guidance for this repo |
| `.github/workflows/standards-check.yml` | PR gate: calls the central reusable workflow |
| `SECURITY.md`, `docs/runbook.md` | Required documentation |

Standards source of truth: https://github.com/gmale747/tech-standards
