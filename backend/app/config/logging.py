"""
Application Logging Configuration for Train Traffic Control System.
Provides structured logging, log-level configuration, and security sanitization.
"""

import logging
import sys
import re
from typing import Optional
from .settings import settings

# Patterns for sensitive keys to sanitize
SENSITIVE_PATTERNS = [
    re.compile(r"(password|secret|token|api_key|authorization)\s*[:=]\s*['\"]?([^'\"\s]+)", re.IGNORECASE)
]


class SanitizingFormatter(logging.Formatter):
    """Custom formatter that redacts sensitive credentials from log records."""

    def format(self, record: logging.LogRecord) -> str:
        original = super().format(record)
        sanitized = original
        for pattern in SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r"\1=***REDACTED***", sanitized)
        return sanitized


def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """Configures root and application loggers with structured console output."""
    log_level_str = (level or settings.LOG_LEVEL or "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Format string: 2026-09-07 18:30:00 [INFO] train_control: Application started
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    formatter = SanitizingFormatter(fmt=fmt, datefmt=datefmt)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(log_level)

    app_logger = logging.getLogger("train_control")
    app_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates on reloads
    if not app_logger.handlers:
        app_logger.addHandler(handler)
    app_logger.propagate = False

    return app_logger


logger = setup_logging()

