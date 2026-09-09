"""Versioned implementation manifest. This describes coverage, never safety."""
BUILD_VERSION = "0.2.0"

def manifest(demo: bool = False) -> dict:
    return {
        "version": BUILD_VERSION,
        "mode": "public_demo" if demo else "local_prototype",
        # A hosted demo refuses report intake in the server, so no real citizen
        # evidence can reach it. That is Gate A on a public URL, not Gate C.
        "report_intake": not demo,
        "production_ready": False, "external_requests": False,
        "working": ["passive_message_url_rules", "qr_image_decode",
                    "on_device_image_redaction", "consented_minimized_reports",
                    "manual_relevance_review", "separated_demo_relationships",
                    "aggregate_small_cell_suppression", "private_summary_export", "localized_pdf_summary",
                    "named_staff_accounts", "totp_second_factor",
                    "role_capability_authorization", "per_organization_isolation",
                    "actor_attributed_audit_trail", "verified_backup_restore"],
        "not_implemented": ["live_reputation", "screenshot_text_extraction",
                            "full_khqr_validation", "bank_account_verification",
                            "telegram_bot", "official_police_submission",
                            "postgresql_migration", "external_identity_provider",
                            "password_reset_flow", "billing",
                            "approved_publication_snapshots"],
        "guardrails": ["unknown_is_not_safe", "reports_do_not_change_verdicts",
                       "no_submitted_url_fetching", "no_raw_messages_in_database",
                       "no_automatic_public_accusations"],
    }
