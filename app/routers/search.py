from fastapi import APIRouter
from app.models import FlightSearchRequest, HotelSearchRequest
from app.mock_data import search_flights, search_hotels, POPULAR_DESTINATIONS, AIRPORTS, CITY_NAMES

router = APIRouter()


@router.post("/flights")
async def search_flights_endpoint(req: FlightSearchRequest):
    results = search_flights(
        origin=req.origin,
        destination=req.destination,
        departure_date=req.departure_date,
        return_date=req.return_date,
        passengers=req.passengers,
        cabin_class=req.cabin_class,
    )
    return {
        "results": results,
        "count": len(results),
        "search_params": req.model_dump(),
    }


@router.post("/hotels")
async def search_hotels_endpoint(req: HotelSearchRequest):
    results = search_hotels(
        city=req.city,
        check_in=req.check_in,
        check_out=req.check_out,
        guests=req.guests,
        rooms=req.rooms,
    )
    return {
        "results": results,
        "count": len(results),
        "search_params": req.model_dump(),
    }


@router.get("/destinations")
async def get_destinations():
    """인기 목적지 반환"""
    return {"destinations": POPULAR_DESTINATIONS}


@router.get("/airports")
async def get_airports(q: str = ""):
    """공항 자동완성"""
    q_lower = q.lower()
    matches = []
    for city, code in AIRPORTS.items():
        if q_lower in city.lower() or q_lower in code.lower():
            matches.append({
                "city": city,
                "code": code,
                "display": CITY_NAMES.get(code, f"{city} ({code})"),
            })
    # 중복 제거
    seen = set()
    unique = []
    for m in matches:
        key = m["code"]
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return {"airports": unique[:10]}
