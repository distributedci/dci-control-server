from datetime import datetime
from sqlalchemy import Integer, DateTime, Boolean, BigInteger
from sqlalchemy.dialects.postgresql import UUID
import uuid


def convert_value_to_column_type(value, column_type):
    if value is None:
        return None

    if isinstance(column_type, (Integer, BigInteger)):
        return int(value)
    elif isinstance(column_type, Boolean):
        return str(value).lower() in ("true", "1", "yes")
    elif isinstance(column_type, DateTime):
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError, AttributeError):
            return value
    elif isinstance(column_type, UUID):
        return uuid.UUID(value)
    else:
        return value
