import re

from fastapi import HTTPException, status

_SYMBOL_RE = re.compile(r"^[A-Z0-9._-]{1,12}$")


def validate_symbol(symbol: str) -> str:
    """Validate and normalize a stock symbol."""
    normalized = symbol.strip().upper()
    if not _SYMBOL_RE.match(normalized):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid symbol '{symbol}'. Must be 1-12 uppercase alphanumeric "
                "characters, dots, dashes, or underscores."
            ),
        )
    return normalized
