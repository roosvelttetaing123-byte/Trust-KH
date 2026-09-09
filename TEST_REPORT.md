# Foundation 0.2 — validation record

Observed 9 September 2026. This records development checks, not production readiness or a security certification.

## Executed in the development environment
- Python 3.13: **51 pytest tests passed** (43 imported baseline tests plus 8 foundation regressions).
- Python compilation completed for app, scripts and tests.
- Node 22 syntax checks completed for application, language dictionary, service worker and project-studio JavaScript.
- Chromium DOM rendering with the real FastAPI handlers through an in-process TestClient adapter passed: unknown check, warning check, separately consented report, analyst relevance review, associations, analyst lock, separate aggregate role, draft Khmer toggle and 390-pixel mobile overflow check. No JavaScript errors were observed in these flows.
- Project studio: all five sections opened correctly at desktop and 390-pixel widths; no horizontal overflow or script errors in the DOM test.
- Actual application screenshots and proposal pages were rendered for visual inspection; demonstration records are synthetic.

## Not established by those checks
A normal Chromium navigation to the running localhost server returned `net::ERR_BLOCKED_BY_ADMINISTRATOR` in this delivery environment. The DOM/handler adapter does not exercise HTTP navigation, browser CSP enforcement, cookies, service-worker installation/offline behavior, or real-device behavior. `scripts/browser_smoke.py` is provided for a separate local network/browser test; Playwright and a Chromium binary are optional development tools, not application runtime dependencies.

The Docker recipe was not built here. Windows execution, physical Android/iOS devices, accessibility conformance, load/soak tests, an independent security audit, live-provider contracts/integration and production identity/tenant isolation remain outstanding. No public deployment or real pilot occurred.

GitHub Actions results must be checked on the actual commit in Actions; local results are not a claim that remote CI passed. The workflow runs backend, compilation and JavaScript syntax checks, not browser/device or Docker validation.

## New regressions
The capability manifest reports absent integrations honestly. Its output excludes local keys. The same indicator cannot merge synthetic and non-synthetic graph nodes. Expired reports cannot be accepted for review. The project studio is served; local home assets remain free of vendor scripts; the updated app/OpenAPI version is exposed.
