# Citizen usability + PDF review

## Implemented
Message text area, compact URL and telephone fields, and a QR tab with visible PNG/JPEG upload, preview, existing on-device redaction, decode and explicit confirmation. Users can replace/remove an image or paste decoded text. Selecting a file does not transmit it; Read QR does. No camera, screenshot-text extraction or external provider is added.

The citizen page is a single centered task. Staff/Pulse links are in the footer but all server permissions remain unchanged. Result reasons and next actions precede expandable technical details. Khmer copy and font sizing were revised; it remains a draft requiring native review. Chinese selection is retained.

Checks show an animated ring around the existing stationary mark and localized status. Duplicate clicks are blocked, errors persist with retry, input is retained, and clear/edit/tab changes invalidate old responses. There is no fake percentage or artificial production delay. Reduced-motion users get static feedback.

## PDF API change
`GET /api/scans/{id}/export?lang=km|en|zh` now returns `application/pdf` rather than ZIP. Default language is Khmer. The expiring bearer capability, no-store response, demo labels and minimization rules remain. Update API consumers that previously expected a ZIP.

The fixed server template contains generated time (UTC+07), reference, warning reasons, next steps, minimized details, limitations, and a non-official-complaint notice. No original message, screenshot, raw payment account, tokens or attachments are exported. Displayed links are plain text, not clickable annotations. The PDF is generated in memory and not persisted. Two rendering slots per process bound concurrent rendering; saturation returns 503. Larger scaling remains separate work.

The renderer uses WeasyPrint 68.0 with Pango shaping and the already tracked Kantumruy font assets. Resources are limited to an exact allowlist of those fonts and the existing logo. All user-derived text is escaped and length-bounded. No arbitrary URL/file/data resource resolution is enabled. Upgrade the renderer only with the regression and visual checks; 68 emits a known fetcher-deprecation warning, and 69+ changes that API.

## Deployment prerequisites — review before merge/deploy
The Dockerfile now installs `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0` and `fonts-noto-cjk` for Chinese output. No service, Render setting, secret or production branch was changed by this document.

For a native Render Python service, confirm the native libraries in its image; installing requirements alone is not proof. Run `python -m weasyprint --info` and generate all three language samples in staging. Use the supplied Docker build when the native runtime cannot provide the dependencies. A missing renderer returns 503 rather than a fake successful download; message checking stays available.

Windows library installation has extra Pango/MSYS2 steps. Follow the version-appropriate official installation guide rather than copying DLLs into the repository. Do not publish .env, databases, real cases or font bundles as review artifacts.

## Reproduce
```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m pip install playwright==1.57.0
python -m playwright install chromium
python scripts/citizen_smoke.py
```
The default smoke starts its own temporary HTTP server and synthetic database. It generates synthetic screenshots/PDFs only. `--adapter` is reserved for restricted environments and does not test HTTP/CSP/service workers. `CHROMIUM_PATH` optionally selects an existing browser executable.

## Review checklist
Try Khmer on a real phone; increase text size to 200%; select a URL and phone; upload/replace/remove QR images; try an unreadable image; decode and confirm; check with slow/disconnected networking; clear/switch tabs during a pending check; download and open a Khmer PDF; confirm the installed service worker loads this release; verify demo report intake remains disabled where configured.

Source: https://doc.courtbouillon.org/weasyprint/v68.0/first_steps.html and https://doc.courtbouillon.org/weasyprint/v68.0/api_reference.html .
