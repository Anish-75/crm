import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict


# Sensitive keys to redact from logs
SENSITIVE_KEYS = {
    "authorization",
    "password",
    "secret",
    "token",
    "service_role_key",
    "consumer_secret",
    "api_key",
    "resend_api_key",
    "access_token",
    "refresh_token",
}


def sanitize_dict(data: Any) -> Any:
    """Recursively redact sensitive keys from dictionary objects."""
    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if str(key).lower() in SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, (dict, list)):
                sanitized[key] = sanitize_dict(value)
            else:
                sanitized[key] = value
        return sanitized
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    return data


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON with ISO timestamps and redaction of secrets."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include request context or extra fields if provided
        for key in ("request_id", "method", "path", "status_code", "duration_ms", "user_id"):
            if hasattr(record, key):
                log_obj[key] = getattr(record, key)

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(sanitize_dict(log_obj))


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with structured JSON output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Remove existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)

    # Configure uvicorn loggers to use structured format
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(logger_name)
        uv_logger.handlers = [handler]
        uv_logger.propagate = False

