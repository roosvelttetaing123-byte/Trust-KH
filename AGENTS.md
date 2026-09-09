# Development contract

Read `PROJECT_STATE.md`, `docs/ARCHITECTURE.md`, `docs/BUILD_BACKLOG.md` and `TEST_REPORT.md` before editing. Read actual code; do not infer a completed feature from a plan.

## Product rules
1. Unknown never means safe. Missing/expired/unavailable intelligence must stay distinguishable from a completed negative lookup.
2. No arbitrary URL fetching, attachment execution or intrusive scanning. This is a defensive intake product.
3. Citizen reporting is separately consented. No raw conversations or payment/identity documents in logs, telemetry, fixtures or Git.
4. Reports are allegations/observations; acceptance is relevance review, not criminal attribution. No automatic blocklisting from vote counts.
5. AI is an optional extraction/explanation component, not the verdict authority. User confirmation and provenance are required.
6. Keep synthetic data separate. No fabricated partners, endorsements, users, incident totals or savings.
7. Capability claims must match `/api/capabilities`. Keep current and planned architecture distinct.

## Working method
Use small branches and explicit acceptance tests. Keep one modular application and one repository. Do not introduce another frontend framework, microservices, Kafka, Kubernetes or a graph database without a recorded decision and measured need. Do not spend money, enable external data processing, or deploy publicly without owner approval.

Run the backend tests and JavaScript syntax checks after meaningful changes. State skipped checks. Add a regression for a fixed defect. Update `PROJECT_STATE.md` and the relevant backlog item at the same time. Do not call the product production-ready based on unit tests or a screenshot.

## Publication and secrets
The repository was public when this foundation was prepared. Never add private business plans, API keys, real reports, phone/account identifiers or sensitive government material. Any secret exposure requires rotation; deletion from the latest commit is not enough.

## Done means
Implemented behavior + passing relevant tests + documented limitation + reproducible local steps + no secrets. A mock, disabled adapter or schema sketch is not a completed integration. CI results and test counts must be observed, not copied from previous sessions.
