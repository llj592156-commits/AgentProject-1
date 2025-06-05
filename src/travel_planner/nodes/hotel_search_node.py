from __future__ import annotations

import os
from dateutil import parser

import httpx

from travel_planner.models.state import HotelInfo, TravelPlannerState
from travel_planner.nodes.base_node import BaseNode

# ──────────────────────────────────────────────────────────────
# Node implementation
# ──────────────────────────────────────────────────────────────
class HotelSearchNode(BaseNode):
    """
    Queries Amadeus Hotel Offers Search API and returns the best-priced hotels
    that fit (roughly) within the user’s budget.
    """

    _AMADEUS_AUTH_URL = "https://test.api.amadeus.com/v1/security/oauth2/token"
    _AMADEUS_HOTEL_URL = "https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city"

    def __init__(self):
        super().__init__()

    # ── public async entrypoint (LangGraph will await this) ────
    async def async_run(self, state: TravelPlannerState) -> TravelPlannerState:  # type: ignore[override]
        async with httpx.AsyncClient(timeout=15) as client:
            self._client = client
            try:
                token = await self._get_access_token(client=client)
                hotels = await self._search_hotels(client=client, state=state, token=token)
                state.hotels = hotels[: 5]  # keep only top_k
                self.logger.info("HotelSearchNode returned %d options", len(state.hotels))
            except Exception as exc:  # noqa: BLE001
                self.logger.error("Hotel search failed: %s", exc, exc_info=True)
        return state

    # ──────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────

    async def _get_access_token(self, client: httpx.AsyncClient) -> str:
        client_id = os.getenv("AMADEUS_CLIENT_ID")
        client_secret = os.getenv("AMADEUS_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise RuntimeError("AMADEUS_CLIENT_ID / CLIENT_SECRET not set")

        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        resp = await client.post(self._AMADEUS_AUTH_URL, data=data)  # type: ignore[arg-type]
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def _search_hotels(self, client: httpx.AsyncClient, state: TravelPlannerState, token: str) -> list[HotelInfo]:
        """Return a list of HotelInfo sorted by ascending price."""
        parsed_date_from = parser.parse(state.date_from).date()
        parsed_date_to = parser.parse(state.date_to).date()
        nights = (parsed_date_to - parsed_date_from).days or 1

        headers = {"Authorization": f"Bearer {token}"}
        if state.hotel_search_api_params is None:
            raise RuntimeError("Hotel search API parameters not set in state")
        params = state.hotel_search_api_params.model_dump(by_alias=True)
        resp = await client.get(self._AMADEUS_HOTEL_URL, params={"cityCode": "PAR"}, headers=headers)
        resp.raise_for_status()
        data = resp.json()

        hotels: list[HotelInfo] = []
        for offer in data.get("data", []):
            hotel = offer["hotel"]
            first_offer = offer["offers"][0]
            price_info = first_offer["price"]
            nightly = float(price_info["total"]) / nights
            hotels.append(
                HotelInfo(
                    name=hotel["name"],
                    address=hotel["address"].get("lines", [""])[0],
                    price_per_nfght=nightly,
                    currency=price_info["currency"],
                    rating=hotel.get("rating"),
                    provider_id=hotel["hotelId"],
                )
            )

        # Sort cheapest → expensive
        hotels.sort(key=lambda h: h.price_per_nfght)
        return hotels