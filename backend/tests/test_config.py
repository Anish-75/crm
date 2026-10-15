import json
import logging
from app.config import Settings
from app.logging_config import StructuredJsonFormatter, sanitize_dict


def test_settings_cors_origins_parsing():
    settings = Settings(
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-key",
        FRONTEND_ORIGIN="http://localhost:5173, http://crm.local:3000",
    )
    assert settings.cors_origins == ["http://localhost:5173", "http://crm.local:3000"]


def test_settings_single_cors_origin():
    settings = Settings(
        SUPABASE_URL="https://test.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="service-key",
        FRONTEND_ORIGIN="http://localhost:5173",
    )
    assert settings.cors_origins == ["http://localhost:5173"]


def test_structured_logging_redacts_secrets():
    data = {
        "user": "alice",
        "password": "supersecretpassword",
        "authorization": "Bearer token123",
        "api_key": "resend_12345",
        "nested": {
            "service_role_key": "secret_key_123",
            "normal_field": "visible",
        },
    }
    sanitized = sanitize_dict(data)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["nested"]["service_role_key"] == "[REDACTED]"
    assert sanitized["nested"]["normal_field"] == "visible"


def test_structured_json_formatter():
    formatter = StructuredJsonFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-123"
    formatted = formatter.format(record)
    parsed = json.loads(formatted)

    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Test log message"
    assert parsed["request_id"] == "req-123"
    assert "timestamp" in parsed

