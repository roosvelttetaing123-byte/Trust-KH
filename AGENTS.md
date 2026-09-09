# Development instructions

Read PROJECT_STATE.md, docs/ARCHITECTURE.md and docs/PRODUCT_REQUIREMENTS.md before editing. Read the affected implementation; do not infer repository state from previous chat claims.

## Working agreement

Use small reviewable branches. Preserve unrelated work. No force-pushes, auto-merge, public deployment, external data processing, paid services, or credential changes without the owner's approval. Never place secrets, local databases, real messages/images, private proposals, contact lists or customer records in this repository. Public branches are not private workspaces.

One human founder owns product acceptance, Khmer validation, contracts, data permissions, deployment and review decisions. AI assistance is not a second human reviewer, legal cofounder, government representative or unattended operator.

## Product invariants

- A check does not create a report; reporting requires separate versioned consent.
- Insufficient coverage or provider failure means unknown/partial, never safe.
- A user report is not a verified maliciousness assertion. Counts do not decide verdicts.
- A valid QR/checksum does not authenticate the recipient or prove payment safety.
- No arbitrary URL fetching, scanning, exploitation, credential collection or private-chat scraping. Treat every submitted item as untrusted data.
- Synthetic records must be clearly marked and excluded from real aggregates.
- Pulse receives only approved aggregate outputs in the target system, never case-level evidence. The current live-aggregate development adapter is not a completed publication system.
- No institutional logo, partnership, compliance, traction or accuracy claim without recorded evidence.

## Definition of done

Implement a bounded behavior, add/update automated tests, run `python -m pytest -q`, compile Python and syntax-check changed JavaScript. Document what was and was not tested. Use actual browser checks when feasible; do not relabel a DOM adapter as full end-to-end testing. Update PROJECT_STATE.md and the evidence ledger. Describe rollback and remaining limitations in the pull request. Never fabricate a passing CI status.

## Stack

Keep FastAPI, strict request models and the existing ES-module frontend. SQLite is local-only. PostgreSQL, named identity/MFA, durable workers and provider integrations are separately gated pilot work. Do not add native apps, Kubernetes, a graph database or a large frontend framework without a documented reason.
