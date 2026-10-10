"""
Core password logic for the advanced tier (no GUI code here, so it is easy to test).
Uses `secrets` (cryptographically secure) instead of `random`.
"""

import math
import secrets
import string

MIN_LENGTH = 8
MAX_LENGTH = 64
AMBIGUOUS = set("0Oo1lI|`'\"")

CHAR_SETS = {
    "upper": string.ascii_uppercase,
    "lower": string.ascii_lowercase,
    "digits": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.<>?/~",
}


def build_pools(selected, exclude_ambiguous=False):
    """Return {type: characters} for the selected types, minus ambiguous chars if asked."""
    pools = {}
    for name in selected:
        chars = CHAR_SETS[name]
        if exclude_ambiguous:
            chars = "".join(c for c in chars if c not in AMBIGUOUS)
        pools[name] = chars
    return pools


def generate_password(length, selected, exclude_ambiguous=False):
    """Generate a password with at least one character from every selected type."""
    if length < MIN_LENGTH or length > MAX_LENGTH:
        raise ValueError(f"Length must be between {MIN_LENGTH} and {MAX_LENGTH}.")
    if len(selected) < 2:
        raise ValueError("Select at least 2 character types.")

    pools = build_pools(selected, exclude_ambiguous)
    chars = [secrets.choice(p) for p in pools.values()]          # one from each type
    combined = "".join(pools.values())
    chars += [secrets.choice(combined) for _ in range(length - len(chars))]

    secrets.SystemRandom().shuffle(chars)                        # secure shuffle
    return "".join(chars)


def strength(length, selected, exclude_ambiguous=False):
    """Return (label, fraction 0-1) based on length and character diversity (entropy)."""
    pool_size = len(set("".join(build_pools(selected, exclude_ambiguous).values())))
    bits = length * math.log2(pool_size) if pool_size > 1 else 0
    if bits < 45 or length < 10:
        label = "Weak"
    elif bits < 70:
        label = "Medium"
    else:
        label = "Strong"
    return label, min(bits / 100, 1.0)
