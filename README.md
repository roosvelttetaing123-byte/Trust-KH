# Trust.kh

**Check before you trust.**

Consent-first scam triage and evidence intake for Cambodia. One human founder, assisted by AI development tools. This is a **local prototype**, not a public safety certification service, bank integration, or official government application.

## Two experiences, clearly separated

- `/` is the working local application: passive checks, deliberate reporting consent, reviewer workspace, withdrawal and aggregate view.
- `/studio.html` is an interactive **design preview** of Trust Check, Trust Desk and Trust Pulse. All examples and metrics there are synthetic; it makes no API requests.

The capability inventory is available at `/api/capabilities`. Unknown never means safe. Rule tests are not fraud-detection accuracy results.

## Run on Windows (Python 3.13)

From the repository folder in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts\init_local.py
.\.venv\Scripts\python.exe -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

Open `http://127.0.0.1:8000`. For the design preview open `http://127.0.0.1:8000/studio.html`.

Use `TRUST_ADMIN_KEY` from the generated local `.env` for Analyst and `TRUST_PULSE_KEY` for Pulse. These are distinct development keys, not named-account authentication. Never commit them or share a screenshot containing them.

## Run on Linux/macOS

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/init_local.py
.venv/bin/python -m uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

Optional labelled data: run `python scripts/seed_demo.py` only against a clean local database, then select the synthetic dataset in Pulse. The script refuses a nonempty database. Demo reports are not real users, victims or traction.

Docker recipe: after initialization, `docker compose up --build`. The host port is loopback-only. The recipe has not been verified by a Docker build in the authoring environment.

## Test

```bash
python -m pytest -q
python -m compileall -q app scripts
node --check app/static/app.js
node --check app/static/i18n.js
node --check app/static/sw.js
node --check app/static/studio.js
```

The foundation suite contains 52 tests. See `TEST_REPORT.md` for actual validation boundaries. GitHub Actions defines dependency installation, tests, compilation and JavaScript syntax checks; do not infer a green run merely from this definition.

## Implemented locally

Passive message/link/phone rules; real PNG/JPEG QR decoding; browser redaction; expiring minimized checks; consented reports; withdrawal receipts; reviewer controls; reviewed co-occurrence associations; small-cell-suppressed aggregates. Submitted websites are **never visited**.

## Not implemented

Screenshot text extraction, live reputation feeds, full KHQR conformance, bank/official complaint APIs, Telegram bot, named staff identity/MFA, tenant isolation, billing, fixed reviewed publication snapshots or public hosting. These require separate development and release gates.

## Engineering map

`AGENTS.md` gives development rules. `PROJECT_STATE.md` records current reality. Read `docs/ARCHITECTURE.md`, `docs/PRODUCT_REQUIREMENTS.md`, `docs/DELIVERY_PLAN.md`, `docs/DESIGN_SYSTEM.md`, `docs/DECISIONS.md`, `docs/TEST_STRATEGY.md` and `docs/RELEASE_GATES.md` before expanding scope. Public source references are in `docs/SOURCE_REGISTER.md`.

## Repository and data boundary

Visibility was public at initialization. **Public branches are public too.** Keep private competition proposals, financial assumptions, partner details, original screenshots/messages, case datasets, credentials, local databases and font binaries out of this repository. Detailed business documents are delivered separately to the founder.

No deployment or external provider account has been created. No application has been submitted to CDA. Review project ownership, branding and eligibility before commercialization. No institutional endorsement is claimed.
