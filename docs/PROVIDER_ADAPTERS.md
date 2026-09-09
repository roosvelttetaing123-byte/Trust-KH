# Provider adapters — designed, not integrated

`app/providers.py` defines adapter contracts with deliberately disabled implementations.
Nothing in this document is built, contracted or claimed. It records what an integration
would require so the design is reviewable before any data agreement is signed, and so the
capability manifest at `/api/capabilities` never drifts from reality.

Two adapters exist as contracts today: `ReputationProvider` and `ScreenshotTextProvider`.
This document adds the design for a third that has been asked about repeatedly — a
telephone-number check — and explains why the obvious version of it is unsafe.

---

## 1. What the phone check does today

`analyze(kind='phone', ...)` in `app/engine.py`:

- normalises the input to `+855…` and rejects anything that is not a Cambodian number,
- adds one **masked** indicator (`+855 •••• 678`) — the full number is never displayed
  back and only its HMAC fingerprint is stored on a consented report,
- appends the coverage note that no owner, banking or reputation database is connected.

**It contains no rule and emits no signal.** A telephone check therefore always returns
`unknown` with zero reasons. Verified by direct call: four different Cambodian numbers,
all `verdict=unknown, signals=0`.

So the phone tab is **evidence intake, not detection**. Its value is that a citizen who
chooses to report contributes a minimized indicator an analyst can correlate across
reports — which is the product thesis — not that the citizen learns anything.

### The risk this creates

A citizen who types a scammer's number and reads *"Unknown — not verified"* may take it
as reassurance. For an input class that can **never** produce a warning, the interface is
doing something close to the harm the product exists to prevent.

This is an open product decision, deliberately not resolved in code. The options are to
state plainly in the phone tab that no telephone database exists so this can only ever
return unknown; to reframe the tab as *report this number* rather than *check* it; or to
remove it until an adapter exists. It should not be left ambiguous.

---

## 2. Designed adapter: telephone registration status

### The regulatory picture

A February 2023 law requires SIMs to be registered in a national database held by
**MPTC** — not by individual operators. TRC has ordered operators to collect subscriber
ID and deactivate numbers without it, and the ministry set a target of eliminating
improperly registered SIMs by **August 2026**.

The practical consequence: the counterparty for this data is **the regulator, not a
telco**. This is one regulatory conversation, not three commercial ones.

### Why "is this number registered?" is the wrong question

The documented fraud pattern is not unregistered SIMs. It is SIMs **registered with
someone else's identity documents** — TRC publicised a case of one person's ID card being
used to register three numbers. Two things follow:

1. As the deactivation drive succeeds, unregistered numbers stop existing, so the
   signal's coverage falls toward zero.
2. A scam number will typically return **registered** — laundered through a stolen
   identity. A naive integration would return the reassuring answer for the dangerous
   number, which is worse than returning nothing.

The signals that would actually carry information — recently activated, many numbers
against one identity document, registered name inconsistent with the claimed sender — are
materially more sensitive and correspondingly harder to obtain.

**Design conclusion:** do not build a registration lookup that renders as a verdict. If
this adapter is ever built, `registered` must be presented as *provenance*, never as
reassurance, and must not move a verdict toward safe.

### Contract

```python
class PhoneRegistrationProvider(Protocol):
    def status(self, e164_number: str) -> ProviderResult: ...
```

Returning the existing `ProviderResult`, so an unavailable provider is indistinguishable
in type from one that answered — the caller must handle `checked=False` explicitly. The
engine already treats missing intelligence as `unknown`, never as negative.

### Result vocabulary — binding

| Provider state | Interface must say | Must never say |
|---|---|---|
| registered | "This number is in the national register. That does not tell you who is using it." | "Verified", "Genuine", "Safe" |
| not registered | "This number is not in the national register." (a reason to pause, not proof) | "Confirmed fraudulent" |
| unavailable / timeout | "Registration could not be checked." | anything implying a completed negative lookup |

Rule 1 of `AGENTS.md` applies unchanged: missing or unavailable intelligence must stay
distinguishable from a completed check.

### Privacy controls that would be required

A lookup service accumulates a record of **who checked whose number**, which is data this
product has so far deliberately refused to hold. Without these controls the integration
should not be built:

- **Query minimization.** Send only the E.164 number. Never the message, the scan id, or
  any identifier for the person asking.
- **No query log linking checker to subject.** Counts for capacity planning only. A
  citizen must not be able to use Trust.kh to profile a person they know — that is the
  obvious abuse and it is not hypothetical.
- **Consent boundary unchanged.** A registration check is part of a check, not a report.
  It must not create a stored record without the existing separate consent step.
- **Hard timeout and cost cap**, with `unknown` on failure. No retry storm against a
  regulator's service.
- **Provenance on the result** — source and timestamp — carried into the PDF, as with
  every other finding.
- **Rate limiting per caller**, because a bulk-enumeration path against a national
  register is an obvious abuse vector and would be the ministry's first question.

### Preconditions before approaching anyone

Not a technical list. None of these are currently met:

- a registered Cambodian legal entity able to sign a data agreement,
- a written data-protection position and a completed security assessment,
- a tested backup/restore and incident-response process (the drill exists;
  `scripts/backup_restore_drill.py`),
- named accountable staff — the identity layer exists but has had no independent review,
- and a reference customer, because a regulator will ask who already relies on this.

Attempting the conversation before these exist wastes the relationship, and in a market
this small the first impression is the only one.

---

## 3. How to read this document

This is a design record, not a roadmap commitment. Nothing here changes
`/api/capabilities`, which continues to report `live_reputation: false` and lists the
unimplemented integrations. If any adapter is built, this file and the manifest are
updated in the same change as the code — never in advance of it.

**Sources** (verify before use in a customer-facing document; Cambodian regulatory status
moves):
[Developing Telecoms](https://developingtelecoms.com/telecom-business/telecom-regulation/16689-cambodian-regulator-cracks-down-on-unregistered-sim-cards.html) ·
[Cambodianess](https://cambodianess.com/article/trc-targets-illegal-sim-registrations-after-fraud-case-exposes-security-gaps) ·
[Khmer Times](https://www.khmertimeskh.com/501485835/trc-tightens-control-on-sim-card-vendors/) ·
[Digital Watch](https://dig.watch/updates/the-telecommunication-regulator-of-cambodia-is-tightening-sim-card-regulations)
