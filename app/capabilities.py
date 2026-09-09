"""Versioned implementation manifest. This describes coverage, never safety."""
BUILD_VERSION = "0.2.0"

def manifest() -> dict:
    return {
        "version": BUILD_VERSION, "mode": "local_prototype",
        "production_ready": False, "external_requests": False,
        "working": ["passive_message_url_rules", "qr_image_decode",
                    "on_device_image_redaction", "consented_minimized_reports",
                    "manual_relevance_review", "separated_demo_relationships",
                    "aggregate_small_cell_suppression", "private_summary_export"],
        "not_implemented": ["live_reputation", "screenshot_text_extraction",
                            "full_khqr_validation", "bank_account_verification",
                            "telegram_bot", "official_police_submission",
                            "named_staff_mfa", "multi_tenant_authorization",
                            "billing", "approved_publication_snapshots"],
        "guardrails": ["unknown_is_not_safe", "reports_do_not_change_verdicts",
                       "no_submitted_url_fetching", "no_raw_messages_in_database",
                       "no_automatic_public_accusations"],
    }
