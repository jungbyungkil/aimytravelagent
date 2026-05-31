from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class FlightSearchRequest(BaseModel):
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    passengers: int = 1
    cabin_class: str = "economy"


class HotelSearchRequest(BaseModel):
    city: str
    check_in: str
    check_out: str
    guests: int = 1
    rooms: int = 1


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []


class ItineraryRequest(BaseModel):
    destination: str
    duration_days: int
    start_date: str
    interests: List[str]
    budget: str = "medium"


class DestinationRecommendRequest(BaseModel):
    travel_party: str
    travel_period: str
    preferences: str = ""
    budget_level: str = "medium"


class BookingCreate(BaseModel):
    type: str          # "flight" | "hotel"
    item_id: str
    details: Dict[str, Any]
    price: float
    currency: str = "KRW"
