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

Open `http://127.0.0.1:8000`. Stop the server with Ctrl+C.

### Signing in to Trust Desk and Trust Pulse

On first run the launcher creates `.env` and a **first admin account**, printing its
email, password and MFA secret once. Keep them: they are not stored anywhere readable.

Staff sign-in needs the password **and** a current 6-digit TOTP code. Add the printed
`otpauth://` URI to any authenticator app, or print a code from the terminal:

```bash
python scripts/create_staff.py --totp-code YOUR_MFA_SECRET
```

Manage accounts and organizations with the same script:

```bash
python scripts/create_staff.py --list
python scripts/create_staff.py --email analyst@example.org --role analyst
python scripts/create_staff.py --create-org "Partner organization"
```

Roles are `analyst` (review reports), `pulse` (aggregates only) and `admin` (both, plus
account management). Each account belongs to one organization and sees only that
organization's reports, associations, aggregates and audit history. There is no public
sign-up route, and there should not be one before the release gates are met.

Rehearse recovery at any time with `python scripts/backup_restore_drill.py`.

### Project studio on GitHub Pages

`app/static/project/` is public-safe project documentation — static, with no API calls,
no citizen data and no backend. `.github/workflows/pages.yml` publishes it to GitHub
Pages on pushes to `main` that touch it, and on manual dispatch. It publishes straight
from `app/static/project/`, so there is no second copy to drift, and it fails the build
if the studio ever starts calling a backend.

**One manual step:** in the repository settings, under **Pages**, set *Source* to
**GitHub Actions**. Until that is done the workflow will fail. The site is then served
at `https://<user>.github.io/Trust-KH/`.

The studio is documentation only. The application is not published there — running it
needs a Python host, and a public demonstration needs `TRUST_ENV=demo` below.

### Hosting a public demonstration

`TRUST_ENV=demo` builds a version safe to put on a public URL for recruited testers:
the server **refuses report intake with 403**, so no citizen evidence can be collected.
The interface reads that from `/api/capabilities` and says so; it is not a hidden button.

Check it locally first — this runs the same code path as the deployment:

```bash
python scripts/demo.py
```

To deploy, use the `Dockerfile` on any host that sets `$PORT` (Render, Fly.io, Hugging
Face Spaces). Required environment:

| Variable | Value |
|---|---|
| `TRUST_ENV` | `demo` |
| `TRUST_ORIGIN` | the public `https://` origin, e.g. `https://your-demo.onrender.com` |
| `TRUST_HMAC_KEY` | a fresh 40+ character random secret — **not** the one from your local `.env` |
| `TRUST_DB` | a scratch path; the pilot database must never be deployed |

Read [Gate A+ in the release gates](docs/RELEASE_GATES.md) before publishing the link.
A hosted demo is for recruited testers and partner walkthroughs; inviting the general
public to check real messages is Gate C and needs security testing, abuse controls,
incident response and published privacy/limitations pages.

**Do not expose the prototype through a public tunnel or deploy it with real citizen evidence.** Public-launch requirements are in [release gates](docs/RELEASE_GATES.md). The project does not require paid services to run locally.

## What works / what does not

Working: passive message/link rules; QR-image decoding; browser redaction; optional minimized reports; relevance review; report withdrawal; summary export; reviewed associations; separated synthetic/non-synthetic graph nodes; aggregate small-cell suppression; responsive citizen UI in an institutional design language, with draft Khmer, English and Chinese copy (Khmer is the base language; all three drafts await native-speaker review); named staff accounts with a TOTP second factor, role capabilities, per-organization isolation, an actor-attributed audit trail, and a verified backup/restore drill.

Not implemented: screenshot text extraction; live reputation feeds; bank ownership verification; complete KHQR compatibility; Telegram; official police submission; PostgreSQL migration; an external identity provider; password reset and recovery; billing; scheduled approved publication snapshots. See `/api/capabilities` for the machine-readable implementation manifest.

The identity layer is standard-library only and deliberately minimal. It exists so
authorization can be designed and tested against named accounts instead of a shared
key — it is not a reviewed production identity provider, and it has no password reset,
no session revocation UI beyond sign-out, and no rate limiting beyond per-account
lockout and the per-IP API limiter.

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
