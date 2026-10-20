"""Victory Crest One - Structured Logging
Enterprise-grade logging with consistent formatting, ISO timestamps, and sensitive credential protection.
"""

import logging
import sys
from typing import Any, Dict


class SafeFormatter(logging.Formatter):
    """Custom formatter ensuring clear output without exposing secrets."""
    
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Redact typical credential strings if accidentally logged
        for sensitive_keyword in ["password=", "secret_key=", "api_key=", "token="]:
            if sensitive_keyword in msg.lower():
                import re
                msg = re.sub(rf"({sensitive_keyword})[^\s,;&]+", r"\1[REDACTED]", msg, flags=re.IGNORECASE)
        return msg


def setup_logger(name: str = "victory_crest", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a structured logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = SafeFormatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False
    return logger


logger = setup_logger()
