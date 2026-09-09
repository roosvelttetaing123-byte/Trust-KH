# Self-hosted fonts

**Kantumruy Pro** — the typeface used by Cambodian government digital services
(for example the NDGCVP certificate verification platform at verify.gov.kh).

| | |
|---|---|
| Source | Google Fonts (`fonts.gstatic.com`), family `Kantumruy Pro` v12 |
| Licence | SIL Open Font License 1.1 — see [OFL.txt](OFL.txt) |
| Files | `kantumruy-pro-khmer.woff2`, `kantumruy-pro-latin.woff2`, `kantumruy-pro-latin-ext.woff2` |
| Total | ~92 KB across three unicode-range subsets |

Each file is a variable font covering weights 400–700, so one file per subset
serves every weight the interface uses.

## Why these are committed rather than loaded from a CDN

The application sends `font-src 'self'` and `style-src 'self'` (see the security
middleware in `app/main.py`). Loading the family from `fonts.googleapis.com`
would require weakening that policy and would leak a request to a third party on
every page view. Self-hosting keeps the policy strict, removes the third-party
dependency, and lets the offline app shell render Khmer correctly.

Chinese text falls back to the reader's system CJK font — bundling a Simplified
Chinese webfont would add several megabytes for a secondary audience.
