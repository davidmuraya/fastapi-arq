"""utils/date_parser.py"""

import logging
from datetime import datetime
from typing import Optional


def parse_datetime_str(dt_str: Optional[str]) -> Optional[datetime]:
    if dt_str:
        try:
            # ARQ typically uses ISO format with timezone
            return datetime.fromisoformat(dt_str)
        except ValueError:
            logging.warning(f"Could not parse datetime string: {dt_str}")
            return None
    return None
