"""Public, non-secret capability inventory. Do not label planned work as operational."""
VERSION = "0.2.0-foundation"

def manifest() -> dict:
    return {
        "version": VERSION,
        "stage": "local_prototype",
        "external_requests": False,
        "production_ready": False,
        "features": {
            "passive_message_link_rules": "implemented_local",
            "qr_image_decoding": "implemented_local",
            "browser_redaction": "implemented_local",
            "consented_reports_and_withdrawal": "implemented_local",
            "reviewer_workspace": "implemented_local",
            "suppressed_aggregates": "implemented_local",
            "screenshot_text_extraction": "planned",
            "live_reputation": "not_configured",
            "full_khqr_conformance": "not_established",
            "named_identity_and_tenant_isolation": "planned",
            "approved_publication_snapshots": "planned",
            "bank_or_government_api": "not_integrated",
        },
        "notice": "Unknown is not safe. Synthetic examples are not evidence of traction or detection performance.",
    }
