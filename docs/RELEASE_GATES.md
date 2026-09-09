# Release gates — local demo is not public operation

The source intentionally refuses `TRUST_ENV` values other than local/test. Do not remove that guard to bypass this checklist. Static role keys and SQLite are development conveniences, not a secure public SaaS configuration.

## Gate A — local synthetic demo
Backend regressions pass; main UI flow works; fixtures are labelled; no external requests; source and output contain no secrets; unsupported features are visible. Browser HTTP/CSP/service-worker testing must be reported separately from DOM-adapter tests.

### Gate A+ — hosted synthetic demonstration (`TRUST_ENV=demo`)
Gate A on a public URL, for recruited testers and partner walkthroughs. Permitted because
**no citizen evidence can be collected**: `/api/reports` is refused by the server with 403,
not hidden in the interface, and the interface reads the server's capability manifest rather
than assuming. Withdrawal is hidden because there is nothing to withdraw. Requires
`TRUST_ORIGIN` set to the public https origin, and sends HSTS.

This is **not** Gate C. It does not authorise inviting the general public to check real
scam messages, and it does not reduce any Gate B or C requirement. Anyone hosting it must
still expect real people to paste real messages into the checker, so the "unknown is not
safe" wording and the not-a-government-service disclaimer carry the safety load and must
stay visible. If report intake is ever wanted on a public URL, that is Gate C.

## Gate B — approved controlled pilot
Named staff identity and MFA; organization-level authorization at every route/job/export; persistent migrated database; backups and observed restore; retention job; deletion/withdrawal semantics; documented data scope and privacy notice; correction process; qualified local legal review as needed; Khmer review; approved provider contracts and quotas; isolated and bounded image processing; redaction and error-recovery tests. Real evidence must not be placed in Git, issue attachments or model prompts without a specifically approved data path.

## Gate C — public citizen intake
Threat-model review, independent security testing, abuse/report brigading controls, provider cost controls, monitored failure handling, verified official escalation information, incident response process, public privacy/limitations pages, support capacity, accessibility/device/network testing, recovery drills and owner approval. No blocking payments, contacting subjects, takedowns or official filings without separate authority.

## Gate D — institutional reporting
Purpose-bound access, approved fixed-window snapshots, complementary suppression/differencing review, audit, retention and documented interpretation. Do not expose a live investigative database under a ministerial dashboard label. Synthetic and consented datasets remain separate.

## Gate E — claims and commercial readiness
Evidence-based feature claims; actual pilot outcomes; no invented customers/partners; licensing and IP reviewed; prices explicitly agreed; no unlimited manual investigation in low-price plans; business-hours support scope. Public launch, cloud spending, registration and competition submission require owner actions/approval.
