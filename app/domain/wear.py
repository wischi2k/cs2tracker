from __future__ import annotations

import re


WEAR_CONDITIONS = (
    "Factory New",
    "Minimal Wear",
    "Field-Tested",
    "Well-Worn",
    "Battle-Scarred",
)

_WEAR_RE = re.compile(
    r"\((" + "|".join(re.escape(condition) for condition in WEAR_CONDITIONS) + r")\)\s*$"
)


def extract_wear_condition(market_hash: str | None) -> str | None:
    """Return the CS2 wear condition from a market hash, if it has one."""
    match = _WEAR_RE.search(market_hash or "")
    return match.group(1) if match else None


def append_wear_condition(display_name: str | None, market_hash: str | None) -> str:
    """Append the wear condition when Steam's localized display name omits it."""
    name = (display_name or market_hash or "").strip()
    wear = extract_wear_condition(market_hash)
    if not wear or wear in name:
        return name
    return f"{name} ({wear})"
