import json
import shutil
import subprocess
from datetime import UTC, date, datetime, timedelta

from app.core.config import get_settings
from app.domain.enums import OrderStatus, ProviderName
from app.schemas.market import (
    AccountSnapshot,
    FilingItem,
    FilingsResponse,
    FundamentalsResponse,
    KlineBar,
    KlineResponse,
    MacroIndicator,
    MacroResponse,
    NewsItem,
    NewsResponse,
    QuoteResponse,
    SentimentResponse,
)
from app.schemas.order import OrderRequest, OrderResponse
from app.services.connectors.base import (
    AccountConnector,
    ConnectorHealth,
    ExecutionConnector,
    MarketDataConnector,
)


class _LongbridgeCliMixin:
    provider_name = ProviderName.LONGBRIDGE

    def __init__(self) -> None:
        self.settings = get_settings()
        self.cli_path = self.settings.longbridge_cli_path
        self.transport = self.settings.longbridge_transport

    def healthcheck(self, capability: str) -> ConnectorHealth:
        if self.transport != "cli":
            return ConnectorHealth(
                provider=self.provider_name,
                capability=capability,
                transport=self.transport,
                available=False,
                message=(
                    "Only CLI transport is implemented in this AlphaMesh version. "
                    "Switch LONGbridge transport to 'cli' or finish MCP support."
                ),
            )
        cli = shutil.which(self.cli_path)
        if cli is None:
            return ConnectorHealth(
                provider=self.provider_name,
                capability=capability,
                transport="cli",
                available=False,
                message=f"Longbridge CLI '{self.cli_path}' was not found on PATH.",
            )
        return ConnectorHealth(
            provider=self.provider_name,
            capability=capability,
            transport="cli",
            available=True,
            message=f"Longbridge CLI found at {cli}.",
        )

    def _run_json_command(
        self,
        *args: str,
        capability: str = "market",
        input_text: str | None = None,
    ) -> object:
        health = _LongbridgeCliMixin.healthcheck(self, capability)
        if not health.available:
            raise ValueError(health.message or "Longbridge CLI is unavailable.")
        try:
            completed = subprocess.run(
                [self.cli_path, *args, "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
                input=input_text,
            )
        except FileNotFoundError as exc:
            raise ValueError(f"Longbridge CLI '{self.cli_path}' is not installed.") from exc
        except subprocess.TimeoutExpired as exc:
            raise ValueError("Longbridge CLI request timed out.") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or "").strip()
            raise ValueError(
                f"Longbridge CLI failed for command '{' '.join(args)}': {stderr or exc}"
            ) from exc

        stdout = completed.stdout.strip()
        if not stdout:
            raise ValueError(f"Longbridge CLI returned empty output for '{' '.join(args)}'.")
        try:
            return json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Longbridge CLI returned non-JSON output for '{' '.join(args)}'."
            ) from exc

    def _parse_decimal(self, value: object, default: float = 0.0) -> float:
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _parse_int(self, value: object, default: int = 0) -> int:
        if value is None or value == "":
            return default
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def _normalize_period(self, interval: str) -> str:
        mapping = {
            "1d": "day",
            "1w": "week",
            "1m": "month",
            "1y": "year",
            "1h": "1h",
            "30m": "30m",
            "15m": "15m",
            "5m": "5m",
            "1m_intraday": "1m",
        }
        return mapping.get(interval, interval)

    def _market_from_symbol(self, symbol: str) -> str:
        if "." not in symbol:
            return "US"
        return symbol.rsplit(".", 1)[1].upper()

    def _extract_first(self, payload: object) -> dict[str, object]:
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            return payload[0]
        if isinstance(payload, dict):
            return payload
        raise ValueError("Longbridge CLI JSON payload shape is unsupported.")


class LongbridgeMarketConnector(_LongbridgeCliMixin, MarketDataConnector):
    def get_quote(self, symbol: str) -> QuoteResponse:
        payload = self._extract_first(self._run_json_command("quote", symbol.upper()))
        return QuoteResponse(
            symbol=symbol.upper(),
            market=str(payload.get("market") or self._market_from_symbol(symbol)),
            currency=str(payload.get("currency") or "USD"),
            provider_symbol=str(payload.get("symbol") or symbol.upper()),
            price=self._parse_decimal(payload.get("last") or payload.get("last_done")),
            open=self._parse_decimal(payload.get("open")),
            high=self._parse_decimal(payload.get("high")),
            low=self._parse_decimal(payload.get("low")),
            previous_close=self._parse_decimal(
                payload.get("prev_close") or payload.get("previous_close")
            ),
            volume=self._parse_int(payload.get("volume")),
            timestamp=datetime.now(UTC),
            provider=self.provider_name,
        )

    def get_kline(
        self,
        symbol: str,
        start: date | None = None,
        end: date | None = None,
        interval: str = "1d",
    ) -> KlineResponse:
        end_date = end or date.today()
        start_date = start or (end_date - timedelta(days=59))
        payload = self._run_json_command(
            "kline",
            symbol.upper(),
            "--period",
            self._normalize_period(interval),
            "--start",
            start_date.isoformat(),
            "--end",
            end_date.isoformat(),
        )
        bars_payload = payload if isinstance(payload, list) else []
        bars = [
            KlineBar(
                symbol=symbol.upper(),
                timestamp=date.fromisoformat(str(item.get("time") or item.get("timestamp"))[:10]),
                open=self._parse_decimal(item.get("open")),
                high=self._parse_decimal(item.get("high")),
                low=self._parse_decimal(item.get("low")),
                close=self._parse_decimal(item.get("close")),
                volume=self._parse_int(item.get("volume")),
            )
            for item in bars_payload
            if isinstance(item, dict) and (item.get("time") or item.get("timestamp"))
        ]
        return KlineResponse(
            symbol=symbol.upper(),
            interval=interval,
            bars=bars,
            provider=self.provider_name,
            market=self._market_from_symbol(symbol),
            currency="USD" if symbol.upper().endswith(".US") else None,
            provider_symbol=symbol.upper(),
        )

    def get_fundamentals(self, symbol: str) -> FundamentalsResponse:
        static_payload = self._extract_first(
            self._run_json_command("static", symbol.upper())
        )
        calc_payload = self._run_json_command(
            "calc-index",
            symbol.upper(),
            "--index",
            "pe,pb,eps",
        )
        calc_map: dict[str, object] = {}
        if isinstance(calc_payload, list):
            for item in calc_payload:
                if isinstance(item, dict):
                    key = str(item.get("index") or item.get("key") or "").lower()
                    calc_map[key] = item.get("value")
        elif isinstance(calc_payload, dict):
            calc_map = {str(k).lower(): v for k, v in calc_payload.items()}
        return FundamentalsResponse(
            symbol=symbol.upper(),
            pe_ratio=self._parse_decimal(calc_map.get("pe") or calc_map.get("pe_ttm")),
            pb_ratio=self._parse_decimal(calc_map.get("pb")),
            revenue_growth=0.0,
            net_margin=0.0,
            debt_to_equity=0.0,
            provider=self.provider_name,
            market=str(static_payload.get("exchange") or self._market_from_symbol(symbol)),
            currency=str(static_payload.get("currency") or "USD"),
            provider_symbol=str(static_payload.get("symbol") or symbol.upper()),
        )

    def get_filings(self, symbol: str, limit: int = 5) -> FilingsResponse:
        payload = self._run_json_command("filing", symbol.upper())
        items = payload if isinstance(payload, list) else []
        filings = [
            FilingItem(
                filing_type=str(item.get("file_name") or item.get("filing_type") or "unknown"),
                title=str(item.get("title") or "Untitled filing"),
                date=date.fromisoformat(
                    str(item.get("publish_at") or item.get("date"))[:10]
                ),
                url=(
                    item.get("url")
                    or (item.get("file_urls") or [None])[0]
                    if isinstance(item.get("file_urls"), list)
                    else None
                ),
                summary=str(item.get("file_name") or item.get("summary") or ""),
            )
            for item in items
            if isinstance(item, dict) and (item.get("publish_at") or item.get("date"))
        ]
        return FilingsResponse(
            symbol=symbol.upper(),
            filings=filings[:limit],
            provider=self.provider_name,
        )

    def get_news(self, symbol: str, limit: int = 10) -> NewsResponse:
        payload = self._run_json_command("news", symbol.upper())
        items = payload if isinstance(payload, list) else []
        news_items = [
            NewsItem(
                headline=str(item.get("headline") or item.get("title") or "Untitled"),
                source=str(item.get("source") or "longbridge"),
                date=datetime.fromisoformat(
                    str(item.get("published_at") or item.get("date")).replace("Z", "+00:00")
                ),
                url=item.get("url"),
                sentiment=float(item["sentiment"]) if item.get("sentiment") is not None else None,
            )
            for item in items
            if isinstance(item, dict) and (item.get("published_at") or item.get("date"))
        ]
        return NewsResponse(
            symbol=symbol.upper(),
            items=news_items[:limit],
            provider=self.provider_name,
        )

    def get_macro(self, region: str = "US") -> MacroResponse:
        payload = self._extract_first(
            self._run_json_command("market-temp", region.upper())
        )
        value = self._parse_decimal(
            payload.get("temperature") or payload.get("value") or payload.get("score")
        )
        indicators = [
            MacroIndicator(
                name="market_temp",
                value=value,
                unit="index",
                date=date.today(),
            )
        ]
        return MacroResponse(
            region=region.upper(),
            indicators=indicators,
            provider=self.provider_name,
        )

    def get_sentiment(self, symbol: str) -> SentimentResponse:
        market = self._market_from_symbol(symbol)
        payload = self._extract_first(
            self._run_json_command("market-temp", market)
        )
        temperature = self._parse_decimal(
            payload.get("temperature") or payload.get("value") or payload.get("score"),
            default=50.0,
        )
        return SentimentResponse(
            symbol=symbol.upper(),
            score=max(-1.0, min(1.0, (temperature - 50.0) / 50.0)),
            sources=["longbridge_market_temp"],
            provider=self.provider_name,
        )

    def healthcheck(self) -> ConnectorHealth:
        return super().healthcheck("market")


class LongbridgeExecutionConnector(_LongbridgeCliMixin, ExecutionConnector):
    def submit_order(self, order_request: OrderRequest) -> OrderResponse:
        side_command = "buy" if order_request.side.value.upper() == "BUY" else "sell"
        payload = self._run_json_command(
            "order",
            side_command,
            order_request.symbol.upper(),
            str(order_request.quantity),
            *(
                ["--price", str(order_request.limit_price)]
                if order_request.limit_price is not None
                else []
            ),
            capability="execution",
            input_text="y\n",
        )
        order_payload = self._extract_first(payload) if isinstance(payload, list) else (
            payload if isinstance(payload, dict) else {}
        )
        order_id = str(
            order_payload.get("order_id")
            or order_payload.get("id")
            or f"longbridge-{datetime.now(UTC).timestamp()}"
        )
        return OrderResponse(
            order_id=order_id,
            symbol=order_request.symbol.upper(),
            side=order_request.side,
            quantity=order_request.quantity,
            limit_price=order_request.limit_price,
            estimated_amount=order_request.estimated_amount,
            status=OrderStatus.SUBMITTED,
            message=str(order_payload.get("message") or "Longbridge order submitted."),
            created_at=datetime.now(UTC),
            paper=False,
            broker=self.provider_name,
            account_id=order_request.account_id,
            environment=order_request.environment or "live",
            external_order_id=str(order_payload.get("external_order_id") or order_id),
            requires_confirmation=False,
        )

    def cancel_order(self, order_id: str) -> OrderResponse:
        payload = self._run_json_command(
            "order",
            "cancel",
            order_id,
            capability="execution",
            input_text="y\n",
        )
        order_payload = payload if isinstance(payload, dict) else {}
        return OrderResponse(
            order_id=order_id,
            symbol=str(order_payload.get("symbol") or "UNKNOWN"),
            side=order_payload.get("side") or "BUY",
            quantity=self._parse_decimal(order_payload.get("quantity")),
            limit_price=(
                self._parse_decimal(order_payload.get("price"))
                if order_payload.get("price") is not None
                else None
            ),
            estimated_amount=self._parse_decimal(order_payload.get("estimated_amount")),
            status=OrderStatus.CANCELLED,
            message=str(order_payload.get("message") or "Longbridge order cancelled."),
            created_at=datetime.now(UTC),
            paper=False,
            broker=self.provider_name,
            account_id=(
                str(order_payload.get("account_id"))
                if order_payload.get("account_id")
                else None
            ),
            environment=str(order_payload.get("environment") or "live"),
            external_order_id=str(order_payload.get("external_order_id") or order_id),
        )

    def healthcheck(self) -> ConnectorHealth:
        return super().healthcheck("execution")


class LongbridgeAccountConnector(_LongbridgeCliMixin, AccountConnector):
    def get_positions(self) -> dict[str, float]:
        snapshot = self.get_account_snapshot()
        return snapshot.positions

    def get_cash(self) -> float:
        snapshot = self.get_account_snapshot()
        return snapshot.cash

    def get_account_snapshot(self) -> AccountSnapshot:
        portfolio_payload = self._run_json_command("portfolio", capability="account")
        portfolio = portfolio_payload if isinstance(portfolio_payload, dict) else {}
        positions_payload = self._run_json_command("positions", capability="account")
        positions_items = positions_payload if isinstance(positions_payload, list) else []
        positions = {
            str(item.get("symbol") or ""): self._parse_decimal(
                item.get("quantity") or item.get("qty")
            )
            for item in positions_items
            if isinstance(item, dict) and item.get("symbol")
        }
        return AccountSnapshot(
            cash=self._parse_decimal(
                portfolio.get("total_cash")
                or portfolio.get("cash")
                or portfolio.get("cash_balance")
            ),
            portfolio_value=self._parse_decimal(
                portfolio.get("total_asset")
                or portfolio.get("portfolio_value")
                or portfolio.get("total_assets")
            ),
            positions=positions,
            provider=self.provider_name,
            account_id=(
                str(portfolio.get("account_id")) if portfolio.get("account_id") else None
            ),
            broker=self.provider_name,
        )

    def healthcheck(self) -> ConnectorHealth:
        return super().healthcheck("account")
