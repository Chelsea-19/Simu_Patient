"""
Structured logging configuration for the application.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the application root logger."""
    settings = get_settings()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger("simupatient")
    root.setLevel(settings.LOG_LEVEL.upper())
    root.handlers.clear()
    root.addHandler(handler)
    root.propagate = False

    return root


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the simupatient namespace."""
    return logging.getLogger(f"simupatient.{name}")
