from types import SimpleNamespace

from app.domain.enums import OrderSide
from app.schemas.order import OrderRequest
from app.services.connectors.longbridge import (
    LongbridgeAccountConnector,
    LongbridgeExecutionConnector,
    LongbridgeMarketConnector,
)


def test_longbridge_quote_uses_cli_quote_with_format_json(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.connectors.longbridge.shutil.which",
        lambda _: "C:/longbridge.exe",
    )

    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(
            stdout='[{"symbol":"AAPL.US","last":"123.45","open":"120","high":"125","low":"119","prev_close":"121","volume":"1000"}]',
            stderr="",
        )

    monkeypatch.setattr("app.services.connectors.longbridge.subprocess.run", fake_run)

    quote = LongbridgeMarketConnector().get_quote("AAPL.US")

    assert quote.symbol == "AAPL.US"
    assert quote.price == 123.45
    assert calls[0] == ["longbridge", "quote", "AAPL.US", "--format", "json"]


def test_longbridge_kline_uses_cli_kline_period_and_range(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.connectors.longbridge.shutil.which",
        lambda _: "C:/longbridge.exe",
    )

    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return SimpleNamespace(
            stdout='[{"time":"2026-04-01T00:00:00Z","open":"10","high":"12","low":"9","close":"11","volume":"100"}]',
            stderr="",
        )

    monkeypatch.setattr("app.services.connectors.longbridge.subprocess.run", fake_run)

    result = LongbridgeMarketConnector().get_kline("AAPL.US")

    assert len(result.bars) == 1
    assert calls[0][0:4] == ["longbridge", "kline", "AAPL.US", "--period"]
    assert "--format" in calls[0]
    assert "json" in calls[0]


def test_longbridge_submit_order_uses_cli_order_buy_and_confirms(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.connectors.longbridge.shutil.which",
        lambda _: "C:/longbridge.exe",
    )

    captured: dict[str, object] = {}

    def fake_run(args, **kwargs):
        captured["args"] = args
        captured["input"] = kwargs.get("input")
        return SimpleNamespace(
            stdout='{"order_id":"701","message":"submitted"}',
            stderr="",
        )

    monkeypatch.setattr("app.services.connectors.longbridge.subprocess.run", fake_run)

    order = LongbridgeExecutionConnector().submit_order(
        OrderRequest(
            symbol="AAPL.US",
            side=OrderSide.BUY,
            quantity=10,
            limit_price=123.45,
            estimated_amount=1234.5,
        )
    )

    assert order.order_id == "701"
    assert captured["args"] == [
        "longbridge",
        "order",
        "buy",
        "AAPL.US",
        "10.0",
        "--price",
        "123.45",
        "--format",
        "json",
    ]
    assert captured["input"] == "y\n"


def test_longbridge_account_snapshot_uses_portfolio_and_positions(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.connectors.longbridge.shutil.which",
        lambda _: "C:/longbridge.exe",
    )

    def fake_run(args, **kwargs):
        if args[1] == "portfolio":
            return SimpleNamespace(
                stdout='{"total_asset":"10000","total_cash":"2500","account_id":"acct-1"}',
                stderr="",
            )
        if args[1] == "positions":
            return SimpleNamespace(
                stdout='[{"symbol":"AAPL.US","quantity":"12"}]',
                stderr="",
            )
        raise AssertionError(args)

    monkeypatch.setattr("app.services.connectors.longbridge.subprocess.run", fake_run)

    snapshot = LongbridgeAccountConnector().get_account_snapshot()

    assert snapshot.cash == 2500
    assert snapshot.portfolio_value == 10000
    assert snapshot.positions == {"AAPL.US": 12.0}
