import contextvars
import json
import logging
import sys
import time
from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional
from app.core.config import settings

# Context variable to hold request_id across async request execution context
request_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


class StructuredFormatter(logging.Formatter):
    """Custom formatter rendering structured JSON or key-value format."""

    def format(self, record: logging.LogRecord) -> str:
        req_id = request_id_ctx.get()
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "request_id": req_id or "N/A",
            "message": record.getMessage(),
            "module": f"{record.module}:{record.lineno}",
        }

        # Include custom extra parameters passed to logger call
        if hasattr(record, "extra_fields") and isinstance(record.extra_fields, dict):
            log_data.update(record.extra_fields)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if settings.LOG_FORMAT == "json":
            return json.dumps(log_data)
        else:
            extras = " ".join(
                f"{k}={v}"
                for k, v in log_data.items()
                if k not in ("timestamp", "level", "message", "logger")
            )
            return f"[{log_data['timestamp']}] [{log_data['level']}] [{log_data['logger']}] [req_id={log_data['request_id']}]: {log_data['message']} {extras}".strip()


def setup_logger(name: str = "ai_invoice_reader") -> logging.Logger:
    """Configures structured logger instance."""
    logger = logging.getLogger(name)
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter())
        logger.addHandler(handler)

    return logger


logger = setup_logger()


@contextmanager
def log_timing(
    operation: str, extra: Optional[Dict[str, Any]] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager to log the duration of an operation (OCR, LLM, upload).
    Yields dynamic metrics dict that can be updated during execution.
    """
    start_time = time.perf_counter()
    metrics: Dict[str, Any] = extra.copy() if extra else {}
    req_id = request_id_ctx.get()
    
    logger.info(f"Starting {operation}...", extra={"extra_fields": {"request_id": req_id, **metrics}})
    try:
        yield metrics
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metrics["duration_ms"] = duration_ms
        logger.info(
            f"Completed {operation} in {duration_ms}ms",
            extra={"extra_fields": {"request_id": req_id, **metrics}},
        )
    except Exception as e:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        metrics["duration_ms"] = duration_ms
        metrics["error"] = str(e)
        logger.error(
            f"Failed {operation} after {duration_ms}ms: {str(e)}",
            extra={"extra_fields": {"request_id": req_id, **metrics}},
            exc_info=True,
        )
        raise
