<!-- generated from app-record.yaml with the standards-check template ({{audience}} audience) - edit app-record.yaml, then regenerate -->
# {{app.name}}

> {{app.description}}

| | |
|---|---|
| App ID | {{app.id}} |
| Version | {{app.metadata.version}} |
| Lifecycle | {{app.metadata.lifecycle}} |
| Last updated | {{app.metadata.last_updated}} |
| Visibility / classification | {{app.access.visibility}} / {{app.access.data_classification}} |
| Repository | {{app.repositories.primary_repo}} |
| Website | {{app.environments.prod.url}} |

## How it works
{{how_it_works}}

<!-- audience:internal -->
## Ownership
- Department: {{app.ownership.department}}
- Team: {{app.ownership.team}}
- Owner: {{app.ownership.owner}}
- Escalation contact: {{app.ownership.escalation_contact}}

## Environments
| Environment | URL | Hosting |
|---|---|---|
{{#each app.environments}}| {{@key}} | {{url}} | {{hosting}} |
{{/each}}

## Operations
- Runbook: {{app.documentation.runbook}}
- Security policy: {{app.documentation.security}}

## Roles with access
{{#each app.access.roles_allowed}}- {{this}}
{{/each}}
<!-- /audience -->

<!-- audience:restricted -->
## Hosting detail
| Environment | IP address | Region |
|---|---|---|
{{#each app.environments}}| {{@key}} | {{ip}} | {{region}} |
{{/each}}
<!-- /audience -->

## Technology stack and compliance
| Technology | Version | Status |
|---|---|---|
{{#each dependencies}}| {{technology}} | {{version}} | {{status}} |
{{/each}}

Overall compliance: **{{overall}}** (manifest v{{manifest_version}}, checked {{checked_at}})
