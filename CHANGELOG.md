# Changelog

## Unreleased — Trust.kh brand mark
- Replaced the placeholder `T✓` tile with the commissioned shield mark: Angkor towers, verification check, orbit and accent dots, hand-built as SVG so it stays sharp at favicon and retina sizes.
- Wordmark is now uppercase `TRUST.KH` with the `.KH` in the brand orange `#F58220`, in the header and the footer.
- The accent is a token (`--brand-accent`) used only for the wordmark. It is deliberately **not** a call-to-action colour: orange buttons would pull the interface out of the institutional register the rest of the palette holds, which is what makes the product read as credible.
- The mark's darkest blue is now `#014F99`, the same token the interface uses, so the logo and the UI share a colour rather than merely coordinating.
- Bumped the service-worker cache to `v4`. Without it, returning visitors keep the previous icon, stylesheet and manifest — the same stale-shell trap hit earlier in development.
- Corrected `manifest.webmanifest`, whose `theme_color`/`background_color` were still the pre-redesign `#0b172a`/`#f4f7f7` and disagreed with the page's own `theme-color` meta tag.

### Resolved: removed the Angkor towers and moved off the verify.gov.kh palette
Research into Cambodian law and the competition context changed this decision.

- **Removed the Angkor towers from the mark.** Cambodia's Law on Marks (Art. 4) bars marks that imitate or contain a State emblem as an element, and Angkor Wat appears on the national flag. A monument inside a security shield, under a verification check, is a materially different claim from ordinary commercial use of Angkor imagery.
- **Replaced the interface blue.** The palette was previously copied from `verify.gov.kh`, which is **MPTC's own flagship verification platform** (ASEAN Digital Awards 2024; UN Public Service Award June 2026) — and MPTC runs the CDA 2026 competition this project is entered in. Resembling a ministry's award-winning service while submitting to that ministry's competition reads as borrowing its credibility. The blue now comes from the Trust.kh mark: `#1B63C4`, 5.79:1 on white (AA).
- Kantumruy Pro is kept. It is the standard Khmer typeface, not a government-exclusive asset.
- The disclaimer strip stays. Cambodia's Penal Code (Arts. 635/636/639, aggravated by 642) addresses conduct that misleads the public into believing it carries public authority, and the Consumer Protection Law 2019 reaches misleading conduct "whether intentional or not" — a confusion-based test that a disclaimer mitigates but does not neutralise.

The orange accent is used **only** in the wordmark, where WCAG's logotype exemption applies;
it measures 2.59:1 on white and must not be reused for body text, links or controls.

Not legal advice: the sources are English translations, the scope of MoC Announcement
No. 1064 could not be verified, and a Cambodian lawyer should confirm before submission.

## Unreleased — Project studio on GitHub Pages
- Added `.github/workflows/pages.yml`, publishing the static project studio from `app/static/project/` so there is no duplicated copy to drift out of date.
- The workflow refuses to publish if the studio ever starts calling a backend, since GitHub Pages hosts no application and a silent dependency would ship a broken page.
- The studio's "open the application" link now resolves per context: the running application when served at `/project/`, and the repository when served as static documentation. Previously it was an absolute `/`, which points at nothing on Pages.

## Unreleased — Hosted demonstration mode
- Added `TRUST_ENV=demo`, a documented mode for putting the prototype on a public URL for recruited testers. `/api/reports` is refused by the **server** with 403, so a hosted demo is incapable of collecting citizen evidence; the interface reads `/api/capabilities` and reflects that rather than hiding a button.
- Demo builds require `TRUST_ORIGIN` (an https origin) and send HSTS. `production` is still refused, and demo mode reduces no Gate B or C requirement — recorded as Gate A+ in `docs/RELEASE_GATES.md`.
- Loopback origins are now allowed on any port, so the exact demo build can be exercised locally (`scripts/demo.py`) before it is published, instead of first running in production. Exact-port matching on loopback prevented running the demo alongside the dev server and provided no protection, since anything on the machine can choose its port.
- `Dockerfile` now honours `$PORT` for managed hosts.

## Unreleased — B01: named staff identity, tenant isolation and audit
- Replaced the two shared static access keys with **named staff accounts**: scrypt password hashing, a TOTP second factor verified against the RFC 6238 vectors, server-side sessions stored as digests, per-account lockout, and sign-out revocation.
- A password alone now grants no capability. The session exists but is unauthorized until the second factor succeeds, so `/api/analyst/*` answers 403 rather than 200.
- Added an **organization model**. Reports, associations, aggregates, audit history and staff management are all scoped to the caller's organization; a cross-organization review returns 404 rather than acting, and cannot be used to probe for report identifiers.
- Added **role capabilities** — `analyst`, `pulse`, `admin` — enforced per route, so authentication and authorization are separate boundaries.
- Added an **actor-attributed audit trail** (`/api/analyst/audit`) recording sign-ins, failed sign-ins, MFA outcomes, reviews and account changes against a named account, visible in Trust Desk.
- Added a **backup and restore rehearsal** (`scripts/backup_restore_drill.py`): consistent online backup, integrity check, row-count comparison, and live queries served from the restored copy.
- Retention now also expires stale sessions, and audit history is kept for a year independently of report expiry.
- Provisioning moved to `scripts/init_local.py` (first admin) and `scripts/create_staff.py` (further accounts and organizations). There is no public registration route.
- Fixed a resource leak: `with sqlite3.connect(...)` ends the transaction but never closes the handle, which leaked file descriptors on every query and locked the database file on Windows. `Store.connect()` is now a context manager that commits *and* closes.
- Fixed schema initialisation ordering so an index can no longer be created against a column that `CREATE TABLE IF NOT EXISTS` skipped adding to an existing database.

**Not done in this slice:** the PostgreSQL migration (B01b). There is no deployment
target or pilot partner yet, and no PostgreSQL or container runtime was available to
test a migration honestly, so the SQL is kept portable and the swap is recorded as
outstanding rather than claimed. Password reset, an external identity provider and
production key management also remain outstanding.

## Unreleased — Institutional interface and trilingual copy
- Rebuilt the citizen, analyst and aggregate interfaces in the design language used by Cambodian government digital services (Kantumruy Pro, `#014F99` institutional blue, restrained cards and a formal footer), taking the palette and typeface from the NDGCVP platform at verify.gov.kh.
- Khmer is now the base language of the served HTML, so the primary audience gets Khmer with no JavaScript and no repaint.
- Added a three-language selector — Khmer, English, Chinese — covering interface copy, input placeholders, accessible labels, result panels and runtime messages. All three drafts still need native-speaker review.
- Self-hosted the Kantumruy Pro subsets under `app/static/fonts/` with its OFL licence, so the strict `font-src 'self'` policy is unchanged and no request goes to a third-party CDN.
- Fixed a layout defect where section-intro paragraphs were centred by inherited auto margins instead of aligning to their heading.
- Updated the interface tests and Playwright smoke scripts for the Khmer base language and the `<select>` language control; added regressions asserting all three languages are offered and that the webfont is served locally.

The redesign changes presentation and language only. No API contract, rule, storage
or security-boundary change is included, and the disclaimers stating that Trust.kh is
not a government, bank or authority service are now shown in the site header.

## 0.2.0 — Foundation
- Imported the tested local starter into a dedicated repository.
- Added an honest capability manifest at `/api/capabilities`.
- Prevented demo and non-demo observations from merging in the analyst relationship view.
- Expired reports are purged before relevance-review updates.
- Refreshed the responsive interface without changing the API contract.
- Added a public-safe project studio, architecture, backlog and release documentation.
- Added regression coverage and local developer commands.

No live reputation, screenshot text extraction, bank integration, production identity, or public deployment is introduced by this release.
