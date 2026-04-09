#和mcp留一个即可
"""API Gateway - Unified interface for third-party APIs.

Provides standardized access to:
- Flight search (Amadeus, Skyscanner, etc.)
- Hotel booking (Booking.com, Expedia, etc.)
- Weather (OpenWeatherMap, etc.)
- Currency exchange
"""

import asyncio
from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional, Protocol

import httpx

from travel_planner.tools.base_tool import BaseTool, ToolResult, ToolConfig
from travel_planner.helpers.logs import get_logger


@dataclass
class APIConfig:
    """Configuration for API client."""

    base_url: str
    api_key: str
    timeout_seconds: float = 30.0
    rate_limit_per_second: float = 10.0


class APIClient(Protocol):
    """Protocol for API clients."""

    async def request(self, method: str, path: str, **kwargs) -> ToolResult:
        """Make an API request."""
        ...


class BaseAPIClient(httpx.AsyncClient):
    """Base HTTP client with common functionality."""

    def __init__(self, config: APIConfig):
        super().__init__(
            base_url=config.base_url,
            timeout=httpx.Timeout(config.timeout_seconds),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
        )
        self._rate_limiter = asyncio.Semaphore(int(config.rate_limit_per_second))

    async def request(self, method: str, path: str, **kwargs) -> ToolResult:
        """Make a rate-limited API request."""
        async with self._rate_limiter:
            try:
                response = await super().request(method, path, **kwargs)
                response.raise_for_status()
                return ToolResult.ok(response.json())
            except httpx.HTTPStatusError as e:
                return ToolResult.fail(f"HTTP error {e.response.status_code}: {e}")
            except httpx.RequestError as e:
                return ToolResult.fail(f"Request failed: {e}")


# -----------------------------------------------------------------------------
# Flight Search APIs
# -----------------------------------------------------------------------------


class FlightSearchParams:
    """Parameters for flight search."""

    def __init__(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        adults: int = 1,
        currency: str = "EUR",
    ):
        self.origin = origin
        self.destination = destination
        self.departure_date = departure_date
        self.return_date = return_date
        self.adults = adults
        self.currency = currency


class AmadeusClient(BaseAPIClient):
    """Amadeus API client for flight search."""

    def __init__(self, api_key: str, api_secret: str):
        # Amadeus uses OAuth2 token exchange
        super().__init__(
            APIConfig(
                base_url="https://test.api.amadeus.com/v1",
                api_key=api_key,  # Actually the access token
                timeout_seconds=30.0,
            )
        )
        self._api_secret = api_secret
        self._token: str | None = None

    async def _get_access_token(self) -> str:
        """Get OAuth2 access token."""
        if self._token:
            return self._token

        # Token acquisition logic here
        # For now, assume api_key is already the token
        self._token = self._api_key
        return self._token

    async def search_flights(self, params: FlightSearchParams) -> ToolResult:
        """Search for flights."""
        flight_offers = {
            "originLocationCode": params.origin,
            "destinationLocationCode": params.destination,
            "departureDate": params.departure_date.isoformat(),
            "adults": params.adults,
            "currencyCode": params.currency,
        }

        if params.return_date:
            flight_offers["returnDate"] = params.return_date.isoformat()

        return await self.request(
            "GET",
            "/shopping/flight-offers",
            params=flight_offers,
        )


# -----------------------------------------------------------------------------
# Weather APIs
# -----------------------------------------------------------------------------


class OpenWeatherClient(BaseAPIClient):
    """OpenWeatherMap API client."""

    def __init__(self, api_key: str):
        super().__init__(
            APIConfig(
                base_url="https://api.openweathermap.org/data/2.5",
                api_key=api_key,
                timeout_seconds=10.0,
            )
        )

    async def get_weather(self, city: str, country_code: str | None = None) -> ToolResult:
        """Get current weather for a city."""
        q = city
        if country_code:
            q = f"{city},{country_code}"

        return await self.request(
            "GET",
            "/weather",
            params={"q": q, "units": "metric"},
        )

    async def get_forecast(self, city: str, days: int = 5) -> ToolResult:
        """Get weather forecast."""
        return await self.request(
            "GET",
            "/forecast",
            params={"q": city, "cnt": days * 8},  # 3-hour intervals
        )


# -----------------------------------------------------------------------------
# API Gateway Facade
# -----------------------------------------------------------------------------


@dataclass
class GatewayConfig:
    """Configuration for the API Gateway."""

    amadeus_api_key: str | None = None
    amadeus_api_secret: str | None = None
    openweather_api_key: str | None = None

    @classmethod
    def from_env(cls) -> "GatewayConfig":
        """Load from environment variables."""
        import os
        return cls(
            amadeus_api_key=os.getenv("AMADEUS_API_KEY"),
            amadeus_api_secret=os.getenv("AMADEUS_API_SECRET"),
            openweather_api_key=os.getenv("OPENWEATHER_API_KEY"),
        )


class APIGateway:
    """Unified gateway to all external APIs.

    Provides a single interface for:
    - Flight search
    - Hotel search
    - Weather
    - Currency exchange
    """

    def __init__(self, config: GatewayConfig | None = None):
        self.config = config or GatewayConfig.from_env()
        self._logger = get_logger()
        self._clients: dict[str, Any] = {}

    def register_client(self, name: str, client: Any) -> None:
        """Register an API client."""
        self._clients[name] = client

    def get_client(self, name: str) -> Any | None:
        """Get a registered client by name."""
        return self._clients.get(name)

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: date | None = None,
        adults: int = 1,
    ) -> ToolResult:
        """Search for flights across configured providers."""
        if self.config.amadeus_api_key:
            client = AmadeusClient(self.config.amadeus_api_key, self.config.amadeus_api_secret)
            params = FlightSearchParams(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                adults=adults,
            )
            return await client.search_flights(params)

        return ToolResult.fail("No flight search provider configured")

    async def get_weather(self, city: str, country_code: str | None = None) -> ToolResult:
        """Get current weather."""
        if self.config.openweather_api_key:
            client = OpenWeatherClient(self.config.openweather_api_key)
            return await client.get_weather(city, country_code)

        return ToolResult.fail("No weather provider configured")

    async def close(self) -> None:
        """Close all client connections."""
        for client in self._clients.values():
            if hasattr(client, "aclose"):
                await client.aclose()
