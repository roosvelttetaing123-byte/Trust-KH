# Evaluation and proof of impact

## Primary question
Does user-confirmed, structured intake reduce the time required to prepare a reviewable case without increasing incorrect accusations, misunderstanding or unnecessary sensitive-data collection?

## Pilot design
Recruit five or more support/review staff and 30–50 consenting citizen testers only after release and privacy gates. Start with an agreed, redacted or synthetic task set. Compare the team's existing workflow against Trust Desk using matched tasks with randomized order to reduce learning bias. Record task boundaries and whether staff were helped. Separate training examples from held-out evaluation examples. Never recycle near-duplicates of the same campaign across the two splits.

## Measures and denominators
| Measure | Definition | Initial target, not an achieved claim |
|---|---|---|
| Case preparation time | elapsed active time from receipt to complete review packet | 30% lower median vs baseline |
| Next-action comprehension | correct answer to a scenario question / completed tasks | at least 80% in the controlled test |
| Field correction burden | edited extracted fields / all proposed fields | report by field and Khmer/English |
| High-warning precision | adjudicated relevant warnings / adjudicated high warnings | measure; no unsupported 99% claim |
| Missed warnings | adjudicated missed relevant warning / relevant cases | report with sample limitations |
| Unknown/abstention rate | unknown outputs / all evaluable checks | publish, do not hide it |
| Review workload | human minutes per report and per paying account | measure affordability and staffing |
| Retention completion | expired items deleted within policy / due items | verify with automated fixtures |

Precision, recall and binary labels only make sense where an adjudicated ground truth exists. Use two independent reviewers where feasible, document disagreements and avoid calling a user's allegation ground truth. Reviewers need appropriate authorization and confidentiality. Report sample sizes, uncertainty and applicability; a small convenience sample does not establish national performance.

## Research comparison
Compare manual intake, structured intake without automated extraction, and user-confirmed assisted extraction. This isolates the contribution of the product rather than attributing every improvement to AI. Track malformed inputs, non-ASCII QR payloads, Khmer Unicode variants, unsupported image formats, extraction substitutions, negated security advice, expired intelligence and provider timeouts.

## Claims policy
Do not convert check counts into prevented fraud, unique victims or money saved. User-reported avoided interactions are self-reports. Deduplicate cautiously, and show the denominator. No national prevalence estimate from an opt-in app. Synthetic demos must never enter real usage analytics or a competition traction slide.

## Evidence pack
Versioned test set manifest; provenance/permission register; timing protocol; anonymized results; adjudication notes; model/rule versions; limitations; actual letters; screenshots with dataset labels; reproducible commands. Keep real evidence outside this public repository.
