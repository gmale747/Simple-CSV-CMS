# Security Policy

## Reporting a vulnerability
Report suspected vulnerabilities to the application owner listed in `app-record.yaml`
(`ownership.escalation_contact`). Do not open a public issue for security problems.

## Security controls in this app
- Static site; no server-side code, no user accounts, no data collection.
- All third-party libraries load from an approved CDN with Subresource Integrity (SRI) hashes.
- A Content-Security-Policy meta tag restricts scripts and styles to this site and the approved CDN.
- CSV content is rendered with `textContent` only; image paths are restricted to the local `images/` folder.

## Standards
This repository follows the Standards Lab Security Standard (SEC) in
https://github.com/gmale747/tech-standards/blob/main/policies/security-standard.md
