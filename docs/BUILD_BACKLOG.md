# Build backlog — decisions and acceptance gates

Planned capacity: approximately 18–22 focused founder hours/week; adjust after the first week. AI-assisted implementation does not replace Khmer review, customer interviews, access approval or independent testing. Dates are a planning baseline, not delivery promises.

| ID / priority | Window | Work | Acceptance / exit |
|---|---|---|---|
| F00 / done locally | 9 Sep | Import starter, capability manifest, interface, documentation | local regression tests; recorded validation limits |
| B00 / P0 | 9–15 Sep | Validate workflow, competitor walkthrough, category/ownership | five staff + ten citizen interviews; unambiguous applicant route |
| B01 / P0 | 16–22 Sep | PostgreSQL migration and named staff identity design | migration/recovery/tenant-denial tests; no real evidence yet |
| B02 / P0 | 16–29 Sep | Licensed lookup with explicit external-processing decision | provenance, timeouts, capped spend, unknown-on-failure tests |
| B03 / P1 | 23–29 Sep | User-confirmed screenshot extraction and Khmer review | extraction errors editable; model has no tools; measured field accuracy |
| B04 / P0 | 30 Sep–6 Oct | Consent, retention, withdrawal, exports and audit hardening | cross-tenant export denied; purge/restore proven; privacy review |
| B05 / P1 | 30 Sep–6 Oct | KHQR compatibility evaluation | official spec test corpus; unsupported vs invalid separated; no owner claim |
| B06 / P0 | 7–13 Oct | One controlled design-partner pilot | baseline and intervention timing; comprehension and error review |
| B07 / P0 | 14–20 Oct | Fix pilot defects; second partner and price test | measured staff workload; no unreviewed impact claims |
| B08 / P0 | 21–27 Oct | Feature freeze, evaluation report, proposal and demo | source-linked claims; synthetic/live/planned visibly distinct |
| B09 / P0 | 28 Oct–1 Nov | Application review and submission buffer | owner approves final factual claims and submits |
| B10 / later | after gates | Telegram / embed / subscriptions / institutional hosting | documented demand and authorized integration |

## B01 status
- (a) data map and organization model — **done**; organizations, staff, sessions and report ownership in `app/storage.py`.
- (b) migrations on isolated test PostgreSQL — **not done**. No deployment target or pilot partner is settled, and no PostgreSQL or container runtime was available to test a migration honestly. The schema is kept portable; the swap is deferred to B01b, not claimed.
- (c) named staff session contract and MFA selection — **done** as a standard-library scrypt + RFC 6238 TOTP implementation, chosen so the pilot does not commit to an identity vendor before (b). Not a production identity provider: no password reset or recovery.
- (d) per-route and per-job authorization tests — **done**; role capability denial, password-only denial, and cross-organization denial for reports, reviews, graph, pulse, audit and staff management.
- (e) backup/restore rehearsal — **done**; `scripts/backup_restore_drill.py` verifies integrity, compares row counts and serves live queries from the restored copy.

## Next work item: B01b + B00
Settle the pilot data scope and deployment target, then port the schema to PostgreSQL with migrations and re-run the tenant-denial and restore checks against it. Pick the identity provider in the same decision so password reset and recovery are solved once. B00's five staff and ten citizen interviews remain outstanding and are not replaced by this engineering work.

## Scope-cut order
Cut Telegram, geographic maps, native apps, fancy graph drawing and autonomous AI agents before consent, honest unknown states, evidence correction, access control, Khmer comprehension tests or evaluation. Below 12 founder hours/week, restrict the competition scope to user-corrected message/link intake and one organization.

## Per-task completion record
Record commit, behavior, acceptance checks, observed test result, limitations, source/dependency decisions and next task. A screenshot is not an integration. A draft policy is not applied access control.
