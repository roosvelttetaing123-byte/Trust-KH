## Citizen UX / PDF — 9 September 2026 (this branch)

- Fresh baseline from GitHub: 83 backend tests passed before changes. After this slice: **96 backend tests passed** in Python 3.13.5.
- Python compilation and JavaScript syntax checks pass.
- Offline Chromium DOM + real TestClient handlers passed adaptive fields; compact link input; actual QR image decode; confirmation; invalid-image feedback; loading/duplicate protection; cancellation after clear/tab switch; localized persistent error and retry; Khmer PDF download; three languages at 320/390/768/1280 px; reduced motion. Zero JavaScript errors.
- Generated English, Khmer and Chinese PDFs parsed as PDF, with no link annotations or attachments. English/Khmer/Chinese synthetic samples fit one page. Khmer sample rendered and visually inspected with the repository's existing fonts. Source strings remain draft translations; visual rendering is not a native-language review.
- PDF regressions cover capability/expiry denial, no private fields, language validation, HTML escaping, resource allowlisting, bounded concurrency, and an explicit 503 when the renderer is unavailable. No submitted URL is fetched.
- Ordinary localhost Chromium navigation remains blocked by this authoring environment. The adapter does not establish HTTP/CSP/service-worker behavior. `scripts/citizen_smoke.py` without `--adapter` and the new Citizen UX checks workflow exercise those separately. Remote results must be read on the actual commit; not inferred here.
- Docker image/native Windows PDF prerequisites, physical phones and production capacity were not tested here. No live Render changes, real reports, external-provider calls, or risk-engine changes.

---

# Foundation 0.2 — validation record

Observed 9 September 2026. This records development checks, not production readiness or a security certification.

## Hosted demo mode — executed on the owner's Windows machine (9 September 2026)

- **82 pytest tests passed** (74 previous plus 8 for demo mode).
- The report-intake block was verified **against the API directly from the browser console**, not only through the interface: a fully valid report request with a live scan token returned 403. A tester who opens developer tools cannot submit evidence either.
- Demo build served locally through `scripts/demo.py` on the same code path as the deployment: capability manifest reported `mode=public_demo` and `report_intake=false`, the header showed the demonstration notice, the withdrawal panel was hidden, and the checker still produced a full `high_risk` result with reasons and coverage.
- `production` remains refused by `Settings.from_env`; demo mode refuses to start without an `https` `TRUST_ORIGIN`.

### Defect found and fixed
Loopback origins were pinned to port 8000, so the demo build on another port was rejected by its own origin check and every API call returned 403. That meant the demo could not be tested locally before going public — the first real browser run would have been in production. Loopback is now allowed on any port.

### Not established
No hosting provider has been used, so TLS termination, cold starts, provider request limits, real-device and slow-network behaviour are untested. Demo mode does not reduce any Gate B or C requirement; it only guarantees that report intake is off.

## B01 identity slice — executed on the owner's Windows machine (9 September 2026)

- **74 pytest tests passed** (53 previous plus 21 covering identity, authorization, tenant isolation, audit and recovery).
- TOTP verified against the **RFC 6238 appendix B vectors**, plus drift tolerance, stale-code rejection and malformed input.
- Password-only sessions were confirmed to receive **403, not 200**, on analyst routes: authentication and authorization are separate boundaries.
- Cross-organization review returned **404 and left the foreign report `pending`** — verified by re-reading it from the store, not just by the status code.
- Lockout confirmed to hold against the *correct* password once triggered; unknown-email and wrong-password responses are byte-identical.
- Session tokens and passwords confirmed absent from a full `iterdump()` of the database.
- Backup/restore drill run against the live database: integrity check passed, row counts matched, and reports, graph and pulse queries were served from the restored copy.
- Signed in end to end in a real browser as the seeded admin: password → second factor → Trust Desk, with the audit panel showing `auth.password_ok`, `auth.mfa_ok` and `staff.created` attributed to `admin@trust.local`.
- Schema migration exercised on the pre-existing local database (columns added in place, no data loss).

### Defects found and fixed during this slice
- `with sqlite3.connect(...)` ends the transaction but does not close the handle. Every query leaked a file descriptor and held a Windows file lock; the backup drill failed on temp-directory cleanup, which is what exposed it. `Store.connect()` is now a context manager that commits and closes.
- Schema initialisation created an index on `reports(org_id)` before the migration added that column to an existing database.
- Inline `style` attributes in the JavaScript-rendered sign-in panel were blocked by `style-src 'self'` — moved into the stylesheet. The policy caught this, which is itself evidence the CSP is enforced.

### Not established by the B01 checks
No independent security review of the identity code. No PostgreSQL, password reset, account recovery, external identity provider, managed secret storage, or concurrency/load testing. Lockout is per account and in-process rate limiting is per IP; neither is distributed. The audit trail is append-only by convention, not by storage guarantee — a database administrator can still alter it.

## Interface redesign — executed on the owner's Windows machine (9 September 2026)

First run outside the authoring environment, so this supersedes the "Windows
execution remains outstanding" limitation recorded below.

- Windows 11, Python 3.11.5, fresh `.venv` from `requirements-dev.txt`: **53 pytest tests passed** (51 previous plus 2 new interface regressions).
- `uvicorn` served the application on `127.0.0.1:8000`; the site was opened over ordinary HTTP navigation in a real browser — the localhost block described below did not apply here.
- Exercised end to end in the browser: paste a suspicious message → `credential_request` rule fired → verdict, defanged domain indicator, coverage list and next steps rendered. No console errors.
- Khmer / English / Chinese switching verified in the browser: `<html lang>`, headings, navigation, input placeholders and the rendered result panel all change language, including re-rendering an existing result.
- Kantumruy Pro loaded from `/fonts/` under the unchanged `font-src 'self'` policy; `document.fonts.check` confirmed the Khmer and Latin subsets resolved rather than falling back.
- Content-Security-Policy enforcement observed directly: an injected inline `<style>` element was blocked by `style-src 'self'`.
- Layout checked at 1280 px and at the 375 px mobile preset in Khmer; one real defect was found and fixed (the section-intro paragraph was centred by inherited auto margins instead of aligning to its heading).

### Not established by the Windows run
Service-worker update behaviour needs care: during development an already-installed
worker kept serving a superseded stylesheet until its caches were cleared. The worker
is network-first and self-heals on a later load, but cache-busting on release has not
been designed or tested.

## Executed in the authoring environment
- Python 3.13: **51 pytest tests passed** (43 imported baseline tests plus 8 foundation regressions).
- Python compilation completed for app, scripts and tests.
- Node 22 syntax checks completed for application, language dictionary, service worker and project-studio JavaScript.
- Chromium DOM rendering with the real FastAPI handlers through an in-process TestClient adapter passed: unknown check, warning check, separately consented report, analyst relevance review, associations, analyst lock, separate aggregate role, draft Khmer toggle and 390-pixel mobile overflow check. No JavaScript errors were observed in these flows.
- Project studio: all five sections opened correctly at desktop and 390-pixel widths; no horizontal overflow or script errors in the DOM test.
- Actual application screenshots and proposal pages were rendered for visual inspection; demonstration records are synthetic.

## Not established by those checks
A normal Chromium navigation to the running localhost server returned `net::ERR_BLOCKED_BY_ADMINISTRATOR` in this delivery environment. The DOM/handler adapter does not exercise HTTP navigation, browser CSP enforcement, cookies, service-worker installation/offline behavior, or real-device behavior. `scripts/browser_smoke.py` is provided for a separate local network/browser test; Playwright and a Chromium binary are optional development tools, not application runtime dependencies.

The Docker recipe was not built here. Physical Android/iOS devices, accessibility conformance, load/soak tests, an independent security audit, live-provider contracts/integration and production identity/tenant isolation remain outstanding. No public deployment or real pilot occurred.

The Khmer, English and Chinese interface copy is a working draft. It has not been
reviewed by native speakers or comprehension-tested with users, and translation
quality is not evidence of usability.

GitHub Actions results must be checked on the actual commit in Actions; local results are not a claim that remote CI passed. The workflow runs backend, compilation and JavaScript syntax checks, not browser/device or Docker validation.

## New regressions
The capability manifest reports absent integrations honestly. Its output excludes local keys. The same indicator cannot merge synthetic and non-synthetic graph nodes. Expired reports cannot be accepted for review. The project studio is served; local home assets remain free of vendor scripts; the updated app/OpenAPI version is exposed.
