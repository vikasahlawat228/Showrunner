"""ID generation utilities."""

from ulid import ULID


def generate_id() -> str:
    """Generate a unique, sortable ID using ULID."""
    return str(ULID())
