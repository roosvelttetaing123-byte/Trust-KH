# Project state

Updated: 9 September 2026. Branch: `build/foundation-and-cda-2026`.

## Product

Trust.kh is a consent-first scam-triage and evidence-intake prototype. Trust Check helps the citizen; Trust Desk supports a reviewer; Trust Pulse is an aggregate-only view. The intended first commercial product is organizational evidence intake, not a guarantee that a payment is safe.

## Current implementation

The imported local starter supports passive text/link/phone rules, PNG/JPEG QR decoding, browser redaction, expiring checks, opt-in minimized reports, withdrawal receipts, reviewer controls, co-occurrence associations and bounded aggregates. It does not visit submitted websites. A standalone design preview illustrates the target experience using synthetic data.

Not implemented: screenshot text extraction, licensed live reputation, full KHQR conformance, bank APIs, Telegram bot, named identity/MFA, tenant isolation, billing, reviewed publication snapshots or public hosting.

## Workspace

Main contained a README at inspection. Changes are proposed on a review branch. Repository visibility was public when inspected; private business documents stay out of GitHub. No `.env`, database, evidence, font binaries or customer documents belong in source control. Review TEST_REPORT.md for measured checks; a local test pass does not establish GitHub CI or production readiness.

## Next work, in order

1. Confirm project ownership, repository visibility and CDA category eligibility.
2. Validate the evidence-intake job with support staff and Khmer-speaking users.
3. Establish a consented evaluation corpus and measured baseline.
4. Add named identity/tenant controls before accepting pilot case data.
5. Add one licensed reputation adapter and user-confirmed extraction, each with fail-to-unknown behavior.
6. Run a controlled pilot, measure outcomes, and freeze features before submission.

## Decision gates

Provisional award track: Digital Research & Innovation. Reconsider Minister's Startup only with confirmed eligibility. No published numerical judging weights have been verified. Planned outcomes are not achievements. Never use the government affiliation of a team member as implied endorsement.

See docs/DELIVERY_PLAN.md, docs/EVIDENCE_LEDGER.md and docs/COMPETITION_CHECKLIST.md. The detailed proposal and business assumptions are supplied separately, not committed to this public repository.
