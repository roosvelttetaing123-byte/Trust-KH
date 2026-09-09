# Project state — foundation 0.2 + B01 identity slice

**Status:** local prototype; not approved for public operation or real citizen evidence.
**Product:** citizen warning-sign explanation → consented minimized report → analyst relevance review → qualified aggregate insight.
**Owner:** repository owner. AI-assisted development; not a two-human team.

## Delivered code
Imported the prior starter; added a coverage manifest, separated synthetic/non-synthetic relationship nodes, purged expired reports before review, and created a project studio and reproducible local launcher.

Rebuilt the interface in the design language of Cambodian government digital services
(Kantumruy Pro, institutional blue, self-hosted fonts under an unchanged strict CSP),
with Khmer as the base language and English and Chinese selectable.

Replaced shared static access keys with named staff accounts: password + TOTP second
factor, server-side sessions, per-account lockout, role capabilities, per-organization
isolation, an actor-attributed audit trail, session retention, and a verified
backup/restore drill.

## Important facts
SQLite remains the only adapter; the target PostgreSQL schema is still documentation, not an applied migration. No live threat feed, screenshot text extractor, bank connection or billing exists. Pulse performs live coarse aggregation scoped to one organization, not a production publication-approval pipeline; cross-organization publication has no disclosure-review step and must not be claimed.

The identity layer is standard-library only. It makes authorization testable against named accounts; it is not a reviewed production identity provider. There is no password reset, no account recovery, no external IdP, and secrets are held in a local `.env` rather than a managed secret store.

Interface copy in all three languages is an unreviewed draft.

## Next implementation slice
**B01b: durable pilot persistence.** Settle the approved pilot's data scope and deployment target first, then port the portable schema in `app/storage.py` to PostgreSQL with migrations, and re-run the tenant-denial and backup/restore checks against it. Choose an identity provider at the same time, so password reset and recovery are solved once rather than twice.

**B02: provider adapter, only after approval.** Choose a licensed provider, define consent/data minimization, set hard cost/time caps, and preserve unknown/partial/unavailable states. Do not silently send full URLs or screenshots externally.

**Also outstanding from B00:** the five staff and ten citizen interviews. The identity work does not substitute for evidence that the workflow is useful.

## Competition
Working primary route: Digital Research & Innovation, subject to organizer confirmation. Minister's Startup remains conditional on applicable eligibility and ownership. Target submission buffer: 28 October–1 November 2026. No application has been submitted. No pilot results or partners are claimed.

## Validation
Read `TEST_REPORT.md` for the latest observed result and remaining limitations. Remote CI status must be checked on the actual commit. Backend tests and browser checks are not a production security audit; the identity layer has had no independent review.

## Needs owner decisions
Pilot partner and approved data scope; deployment target and identity provider; Khmer/English/Chinese wording review; maximum spend and external-provider approval. None of those should block local synthetic development.
