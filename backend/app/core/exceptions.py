class AlphaMeshError(Exception):
    """Base exception for domain-level AlphaMesh errors."""


class LiveTradingDisabledError(AlphaMeshError):
    """Raised when live automation is requested while disabled."""
