import logging
import json
import re
import sys
from datetime import datetime, timezone
from typing import Dict, Any

SENSITIVE_KEYS = {"api_key", "password", "authorization", "token", "secret", "bearer", "cookie"}

def mask_sensitive_data(data: Any) -> Any:
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if any(s_key in str(k).lower() for s_key in SENSITIVE_KEYS):
                masked[k] = "***REDACTED***"
            else:
                masked[k] = mask_sensitive_data(v)
        return masked
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        # Redact JWT tokens & bearer patterns in raw strings
        if "bearer " in data.lower() or "eyjhbg" in data.lower():
            return re.sub(r'(bearer\s+)[^\s]+', r'\1***REDACTED***', data, flags=re.IGNORECASE)
    return data

class StructuredJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }

        # Add Correlation IDs & Tenant Context if available
        if hasattr(record, "request_id"):
            log_obj["request_id"] = getattr(record, "request_id")
        if hasattr(record, "correlation_id"):
            log_obj["correlation_id"] = getattr(record, "correlation_id")
        if hasattr(record, "organization_id"):
            log_obj["organization_id"] = getattr(record, "organization_id")

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        masked_log = mask_sensitive_data(log_obj)
        return json.dumps(masked_log)

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredJSONFormatter())
    root_logger.addHandler(handler)

    # Reduce noisiness from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
