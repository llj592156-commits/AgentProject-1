from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class HotelInfo(BaseModel):
    name: str
    address: str
    price_per_nfght: float
    currency: str = "EUR"
    rating: Optional[float] = None
    provider_id: str

class HotelAPIParams(BaseModel):
    cityCode: str = Field(..., description="IATA city code (e.g. PAR)")
    checkInDate: date
    checkOutDate: date
    adults: int
    roomQuantity: int = 1
    currency: str = "EUR"
    priceRange: str = Field(..., description="Format 'min-max', e.g. '0-150'")
    sort: str = "PRICE"

class TravelPlannerState(BaseModel):
    """State object produced by CollectTripParamsNode."""

    origin: str = Field(description="City / airport of departure")
    destination: str = Field(description="City / airport of arrival")
    date_from: str = Field(description="Outbound date (YYYY-MM-DD)")
    date_to: str = Field(description="Return date (YYYY-MM-DD)")
    budget: float = Field(ge=0, description="Total budget in EUR")
    interests: list[str] = Field(default_factory=list, description="Interest tags (culture, food, nature, …)")
    pax: int = Field(default=1, gt=0, description="Number of travellers")

    # ──────────────────────────────────────────────────────────────
    # Hotels
    # ──────────────────────────────────────────────────────────────
    hotels: list[HotelInfo] = Field(
        default_factory=list,
        description="List of hotels matching the search criteria",
    )
    hotel_search_api_params: Optional[HotelAPIParams] = Field(
        None,
        description="Parameters for the Amadeus Hotel Offers Search API",
    )

    # ──────────────────────────────────────────────────────────────
    # Validators
    # ──────────────────────────────────────────────────────────────

    @field_validator("origin", "destination", mode="before")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def check_date_range(self) -> "TravelPlannerState":
        if self.date_to < self.date_from:
            raise ValueError("date_to must be on or after date_from")
        return self




