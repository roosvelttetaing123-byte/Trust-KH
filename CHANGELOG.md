# Changelog

## Unreleased — Institutional interface and trilingual copy
- Rebuilt the citizen, analyst and aggregate interfaces in the design language used by Cambodian government digital services (Kantumruy Pro, `#014F99` institutional blue, restrained cards and a formal footer), taking the palette and typeface from the NDGCVP platform at verify.gov.kh.
- Khmer is now the base language of the served HTML, so the primary audience gets Khmer with no JavaScript and no repaint.
- Added a three-language selector — Khmer, English, Chinese — covering interface copy, input placeholders, accessible labels, result panels and runtime messages. All three drafts still need native-speaker review.
- Self-hosted the Kantumruy Pro subsets under `app/static/fonts/` with its OFL licence, so the strict `font-src 'self'` policy is unchanged and no request goes to a third-party CDN.
- Fixed a layout defect where section-intro paragraphs were centred by inherited auto margins instead of aligning to their heading.
- Updated the interface tests and Playwright smoke scripts for the Khmer base language and the `<select>` language control; added regressions asserting all three languages are offered and that the webfont is served locally.

The redesign changes presentation and language only. No API contract, rule, storage
or security-boundary change is included, and the disclaimers stating that Trust.kh is
not a government, bank or authority service are now shown in the site header.

## 0.2.0 — Foundation
- Imported the tested local starter into a dedicated repository.
- Added an honest capability manifest at `/api/capabilities`.
- Prevented demo and non-demo observations from merging in the analyst relationship view.
- Expired reports are purged before relevance-review updates.
- Refreshed the responsive interface without changing the API contract.
- Added a public-safe project studio, architecture, backlog and release documentation.
- Added regression coverage and local developer commands.

No live reputation, screenshot text extraction, bank integration, production identity, or public deployment is introduced by this release.
