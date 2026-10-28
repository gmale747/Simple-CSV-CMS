# Runbook: Road Construction Help Center

## Run locally
```bash
python3 -m http.server 8080
# open http://localhost:8080
```
The site must be served over HTTP; opening `index.html` directly blocks the CSV fetch.

## Deploy
Pushing to `main` publishes through GitHub Pages (Settings > Pages > Deploy from branch > `main` / root).

## Add or edit an article
1. Edit `data/posts.csv` (columns: post-name, post-category, post-header, post-body, post-main-image, post-url).
2. Put the image in `images/` and reference it as `images/<file>.svg|png|jpg|webp`.
3. `post-url` must be unique; it becomes `post.html?slug=<post-url>`.
4. Separate body paragraphs with a blank line (keep the cell in double quotes).

## Health check
- Home page shows article count and category bars.
- Every card opens its article without an error banner.

## Rollback
Revert the last commit on `main`; Pages redeploys automatically.

## Contacts
See `ownership` in `app-record.yaml`.
