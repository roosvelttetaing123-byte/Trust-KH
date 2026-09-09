"""Contract-only extension points. These adapters DO NOT contact any provider.
Do not switch to a commercial provider without licensing, privacy review,
secret management, timeouts, caching policy and explicit coverage reporting.
"""
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class ProviderResult:
    checked: bool
    findings: tuple[str, ...] = ()
    source: str = 'not_configured'
    unavailable_reason: str | None = None

class ReputationProvider(Protocol):
    def lookup(self, approved_indicator: str) -> ProviderResult: ...

class ScreenshotTextProvider(Protocol):
    def extract(self, user_approved_redacted_image: bytes) -> ProviderResult: ...

class DisabledReputation:
    def lookup(self, approved_indicator: str) -> ProviderResult:
        return ProviderResult(False,unavailable_reason='No licensed threat feed is configured.')

class DisabledScreenshotText:
    def extract(self, user_approved_redacted_image: bytes) -> ProviderResult:
        return ProviderResult(False,unavailable_reason='Screenshot text extraction is not implemented. Ask the user to transcribe relevant content.')
