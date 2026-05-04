def apply_slippage(price: float, side: str, slippage_bps: float) -> float:
    """Adjust price for slippage. BUY pays more, SELL receives less."""
    if slippage_bps <= 0:
        return price
    factor = slippage_bps / 10_000
    if side.upper() == "BUY":
        return price * (1 + factor)
    return price * (1 - factor)


def deduct_commission(cash: float, commission: float) -> float:
    """Deduct per-trade commission from cash."""
    if commission <= 0:
        return cash
    return cash - commission
