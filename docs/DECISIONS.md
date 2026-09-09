# Architecture decision records

All records are dated 9 September 2026; reconsider when evidence changes.

| ID | Decision | Reason / consequence |
|---|---|---|
| ADR001 | Modular monolith | One human founder can operate one codebase; a worker is a process boundary, not a microservice fleet. |
| ADR002 | Keep lightweight browser frontend | Avoid rewriting a working flow before validating the user problem. |
| ADR003 | SQLite local; PostgreSQL pilot | Local ease does not establish tenant security or production concurrency. |
| ADR004 | Never fetch submitted URLs in MVP | Passive checks avoid arbitrary browsing/probing and reduce data exposure. |
| ADR005 | Unknown is a first-class result | Missing coverage must never become a reassuring safe label. |
| ADR006 | Separate report consent | A private check is not permission to retain, train, publish or file an official complaint. |
| ADR007 | Reports and assertions differ | Mass allegations cannot automatically become a maliciousness blocklist. |
| ADR008 | Pulse is aggregate-only | Target published snapshots require disclosure review; local suppression alone is insufficient. |
| ADR009 | Human-confirmed extraction | A machine's transcription error must not silently attach an allegation to an identifier. |
| ADR010 | Design preview is separate | Stakeholders can review the visual direction without fictitious performance/traction claims. |

No technology decision authorizes provider spending, external processing, public deployment, institutional branding or automatic repository merging.
