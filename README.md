# Trust.kh
### Check before you trust.

**Version 0.2.0 · local prototype · synthetic examples first**

Trust.kh is a Cambodian scam-triage and evidence-intake project. The citizen interface explains warning signs; the analyst workspace reviews consented, minimized reports; Trust Pulse exposes limited aggregate information. It is not a safety certificate, a bank service, an official complaint portal, or an endorsed government application.

## Start here

Requires Python 3.13 for the tested configuration. From the repository directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\dev.py
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/dev.py
```

Open `http://127.0.0.1:8000`. The launcher generates three unique secrets in `.env` only when it does not exist. Keep that file private. Use `TRUST_ADMIN_KEY` for the Analyst view and `TRUST_PULSE_KEY` for Pulse. These development keys are not production identity. Stop the server with Ctrl+C.

**Do not expose the prototype through a public tunnel or deploy it with real citizen evidence.** Public-launch requirements are in [release gates](docs/RELEASE_GATES.md). The project does not require paid services to run locally.

## What works / what does not

Working: passive message/link rules; QR-image decoding; browser redaction; optional minimized reports; relevance review; report withdrawal; summary export; reviewed associations; separated synthetic/non-synthetic graph nodes; aggregate small-cell suppression; responsive citizen UI and draft Khmer citizen copy.

Not implemented: screenshot text extraction; live reputation feeds; bank ownership verification; complete KHQR compatibility; Telegram; official police submission; named-account MFA; tenant isolation; billing; scheduled approved publication snapshots. See `/api/capabilities` for the machine-readable implementation manifest.

Checks are not stored as raw conversations. Reports require a separate choice. User reports never directly change risk verdicts. Unknown does not mean safe. A graph connection is not criminal attribution.

## Explore

- [Project state](PROJECT_STATE.md) — what is actually done and the next task.
- [Project studio](app/static/project/index.html) — product, architecture, roadmap, demonstration; served at `/project/`.
- [Architecture](docs/ARCHITECTURE.md) — current vs target system and data boundaries.
- [Build backlog](docs/BUILD_BACKLOG.md) — priorities, dependencies, acceptance checks.
- [Competition brief](docs/COMPETITION_BRIEF.md) — public-safe entry strategy.
- [Evaluation plan](docs/EVALUATION.md) — how impact and limitations will be measured.
- [Demo script](docs/DEMO.md) — a reproducible synthetic walkthrough.
- [Development instructions](AGENTS.md) — continuity for AI-assisted work.
- [Test report](TEST_REPORT.md) — performed and outstanding validation.

## Development checks

```bash
python -m pytest -q
python -m compileall -q app scripts
node --check app/static/app.js
node --check app/static/i18n.js
node --check app/static/sw.js
```

Optional UI testing requires Playwright and Chromium; it is not a runtime dependency. `scripts/browser_smoke.py` tests a running local server. `scripts/dom_smoke.py` exercises real API handlers through an in-process browser adapter, but does not establish HTTP/CSP/service-worker behavior.

`python scripts/seed_demo.py` seeds six explicitly synthetic accepted reports into an otherwise empty local database. It refuses a populated database. Select the synthetic dataset in Pulse. Never call these real users, cases, victims, savings or adoption.

## Repository and rights

Do not commit `.env`, evidence, local databases, credentials, private proposals or customer details. No government, bank or partner logos are included. Trust.kh is a working project name; domain availability and trademark rights are not established. This public repository does not itself grant a broad software license; the owner must decide licensing after ownership and dependency review.
