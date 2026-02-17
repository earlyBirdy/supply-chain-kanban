from __future__ import annotations

import logging
from typing import Optional

from .request_context import get_request_id

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # Expose request_id to formatter even outside request context.
        try:
            record.request_id = get_request_id()
        except Exception:
            record.request_id = "-"
        return True

def setup_logging(level: int = logging.INFO) -> None:
    # Configure root logger once. If already configured, do minimal augmentation.
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(request_id)s %(name)s %(message)s",
        )
    # Ensure our filter is present on root handlers.
    f = RequestIdFilter()
    for h in root.handlers:
        try:
            h.addFilter(f)
        except Exception:
            pass
