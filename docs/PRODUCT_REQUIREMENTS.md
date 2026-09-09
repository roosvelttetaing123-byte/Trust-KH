# Product requirements / phase 1

Version 0.2. Decision owner: human founder. Purpose: make a suspicious interaction understandable and prepare reviewable evidence with deliberate consent.

## Users and jobs

Citizen: understand what is concerning, what is unknown, and the next independent verification step. Reviewer: assemble a useful case without repeatedly requesting irrelevant personal information. Institutional reader: understand a qualified aggregate pattern without viewing private conversations.

## Prioritized requirements

| ID | Priority | Requirement and acceptance |
|---|---|---|
| FR01 | P0 | Anonymous basic check. No account, bank connection, contacts or ID required. |
| FR02 | P0 | Explain reasons and unchecked coverage. Unknown must never be displayed as safe. |
| FR03 | P0 | Separate report consent. Checking alone leaves no persistent report. |
| FR04 | P0 | User correction before screenshot-derived identifiers enter a report. Extraction currently planned. |
| FR05 | P0 | Reviewer authorization. An aggregate reader cannot obtain case details; named tenant identity is a pilot gate. |
| FR06 | P0 | Synthetic/real separation. A demo indicator cannot increase a real-publication count. |
| FR07 | P0 | Withdrawal and expiry. Remove associated observations, retain only justified audit metadata. |
| FR08 | P0 | Khmer usability. Native-language review and a comprehension test, not merely translated labels. |
| FR09 | P0 | Evidence provenance. Sources, freshness and coverage are visible; no invented probability. |
| FR10 | P1 | Licensed reputation with timeouts and explicit failure states. No unapproved external calls. |
| FR11 | P1 | Fixed approved Pulse snapshots. Never a live surveillance or national-prevalence claim. |
| FR12 | P1 | Organizational export and measured reduction in case-preparation work. |
| FR13 | P2 | Opt-in Telegram forwarding, only after the main workflow is useful. |

## Scope boundary

Local prototype now; controlled pilot after security/data gates; public service later. Phone input can normalize and match permitted observations in a future contracted system; it is not a public reverse-identity search. QR decoding is not bank verification. The MVP must remain usable with all external providers disabled.

## Error and empty states

Empty input: explain what is needed. No network/provider: show unavailable/unknown and static independent-verification advice. Insufficient evidence: do not manufacture a warning. Expired capability: ask the user to start a fresh check; do not expose existence to other users. Invalid image: explain supported format/size. Failed report submission: show it was not saved. Duplicate submission: preserve clarity without creating another report. No aggregate cohort: show no publishable data, not a zero-scam claim.

## Success measures to validate

Correct comprehension of unknown; complete reviewable case rate; paired case-preparation time; false warning and abstention rates on a labelled set; source coverage; correction/withdrawal success; support hours per organization. The current rule tests are software tests, not a fraud-performance benchmark. Do not use raw check volume or alarming verdicts as the primary product goal.

## Acceptance demonstration

One synthetic message produces explainable signals; an unfamiliar benign link returns unknown. A separate consent creates a pending case. Reviewer accepts relevance. Related synthetic observations remain labelled. Pulse cannot show the private message. Withdrawal removes the report. A missing external provider remains visibly unavailable.
