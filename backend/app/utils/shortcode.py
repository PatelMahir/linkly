"""Short-code generation.

Uses a URL-safe alphabet (no ambiguous characters like 0/O, 1/l) and a
cryptographically secure RNG. Collisions are handled by the service layer,
which retries on a unique-constraint violation.
"""

import secrets

# Base58-style alphabet: digits + letters, minus 0 O I l for readability.
ALPHABET = "23456789abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ"
DEFAULT_LENGTH = 7


def generate_code(length: int = DEFAULT_LENGTH) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
