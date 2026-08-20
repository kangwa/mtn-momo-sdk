"""Small internal helpers shared across product clients."""

import uuid


def new_reference_id() -> str:
    """Generate a fresh MoMo X-Reference-Id / externalId value."""
    return str(uuid.uuid4())
