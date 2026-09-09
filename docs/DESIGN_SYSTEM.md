# Product design system

## Direction

Calm, credible and easy to understand. Dark navy headings, teal primary actions, soft mint surfaces and restrained warning colors. Do not use a hacker terminal aesthetic or government seals. The product is an aid to judgment, not an authority badge.

## Three surfaces

**Trust Check:** one input, large action, clear reasons, visible analysis gaps and independent next steps. The synthetic product studio illustrates message, unknown-link and safety-advice states. Reporting is a separate decision, never the default consequence of checking.

**Trust Desk:** bounded queue, case detail, evidence completeness and reviewer decisions. The studio illustrates future workflow states; the root application has a working local reviewer adapter. A relevance decision is not a verdict of fraud.

**Trust Pulse:** scoped aggregate cohort and disclosure notes. No raw-message, full-account, full-phone or precise-location drill-down. Clearly distinguish demo numbers from actual report counts. Fixed, reviewed snapshots are planned, not implemented by the dynamic local endpoint.

## Tokens and interactions

Studio tokens live in `app/static/studio.css`: ink #102d38; action #087f73; background #f4f7f5; line #dce7e3; muted #60737a. Use system fonts; the working application requests a locally available Khmer font, with fallbacks. Do not redistribute font binaries.

Primary buttons target at least 44px height. Labels remain visible. Keyboard focus and skip links are provided. Warning meaning must also be conveyed in text, not color alone. Mobile layouts stack at 760px in the studio; test actual narrow devices and long Khmer text. Prefer reduced motion. No external analytics or font requests are necessary for the preview.

## States and copy

Strong warning signs, Caution, and Unknown—not safe/unsafe as absolute labels. No uncalibrated numerical risk probability. Show missing evidence, source, freshness and a next action. User control is explained before upload and again before reporting. Avoid alarmist claims and language implying a criminal identity.

Khmer text in the working prototype is draft copy, not a completed linguistic/accessibility validation. The new design studio is English-first for design review; complete Khmer localization is a pilot requirement.

## Preview integrity

`/studio.html` is an interactive design artifact with fictional examples and fixed sample counts. Its buttons change local sample state only. It does not send information, use a model, verify a bank account, save cases or publish statistics. Do not display it as a live production service.
