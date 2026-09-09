# Test strategy

## Levels

Unit tests cover passive rules, normalization, exact synthetic fixtures, uncertainty, masking and QR limitations. API tests cover consent, capabilities, role separation, withdrawal, expiry, graph semantics, aggregate suppression, exports and request limits. Static smoke tests check JavaScript parsing and Python compilation.

Browser tests must exercise the real HTTP origin, CSP, service worker, downloads and actual devices. In-process DOM adapters are useful but must be labelled honestly. Offline studio tests check only preview navigation/sample transitions and layout.

## Pilot additions

Add tenant-crossing denial tests, named identity/MFA session handling, signed evidence access, worker deadlines, provider outage states, retention/backup restore, rate/cost ceilings and publication disclosure tests. Test malformed images under an isolated worker rather than relying on input size alone.

Detection evaluation is separate: permissioned labelled cases, benign and ambiguous examples, template/campaign-separated split, human review, disagreement logs, precision/recall where labels allow, false-warning and unknown rates, coverage, latency and confidence intervals. No benchmark score is currently established.

## Acceptance

A visible page is insufficient. A task is done only when its behavior and failure modes are implemented, tested, documented and reviewed. CI status must be checked at the actual commit. Public rollout also requires operational and data-governance gates.
