# Foundation 0.2 — validation record

Observed 9 September 2026. This records development checks, not production readiness or a security certification.

## Executed on the owner's Windows machine (9 September 2026)

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
