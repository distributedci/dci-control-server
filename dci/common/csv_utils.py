import csv
import threading
from contextlib import contextmanager

_CSV_FIELD_SIZE_LOCK = threading.Lock()


@contextmanager
def csv_field_size_limit(minimum=None):
    """Protect CSV reads while temporarily raising the process-wide field limit."""
    with _CSV_FIELD_SIZE_LOCK:
        previous_limit = csv.field_size_limit()
        limit_changed = minimum is not None and minimum > previous_limit
        try:
            if limit_changed:
                csv.field_size_limit(minimum)
            yield
        finally:
            if limit_changed:
                csv.field_size_limit(previous_limit)
