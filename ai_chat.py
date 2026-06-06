"""
Amadeus Self-Service API 연동 (실시간 항공/호텔 가격).

환경변수가 설정되어 있으면 실제 Amadeus API를 호출하고,
설정이 없거나 호출 실패 시 None을 반환하여 호출부(search 라우터)가
기존 mock 데이터로 자동 폴백하도록 설계되어 있습니다.

필요한 환경변수:
  AMADEUS_API_KEY      (Self-Service 앱의 API Key / client_id)
  AMADEUS_API_SECRET   (API Secret / client_secret)
  AMADEUS_ENV          "test"(기본) 또는 "production"

⚠️ 참고: Amadeus Self-Service 포털은 2026-07-17 종료 예정입니다.
   장기적으로는 Travelpayouts(Aviasales) 등 대체 무료 API로의 교체를 권장합니다.
   (provider 레이어로 분리되어 있어 이 파일만 교체하면 됩니다.)
"""
import os
import time
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

try:
    import requests
    _REQUESTS_OK = True
except ImportError:  # 배포 환경에 requests 가 없을 경우에도 앱은 동작
    _REQUESTS_OK = False

from app.mock_data import AIRPORTS, CITY_NAMES, AIRLINES

# IATA 공항코드 → 호텔 검색용 도시코드(IATA city code)
CITY_CODE_BY_AIRPORT = {
    "ICN": "SEL", "GMP": "SEL", "NRT": "TYO", "HND": "TYO", "KIX": "OSA",
    "BKK": "BKK", "SIN": "SIN", "HKG": "HKG", "CDG": "PAR", "JFK": "NYC",
    "LAX": "LAX", "LHR": "LON", "DPS": "DPS", "HNL": "HNL", "FCO": "ROM",
    "BCN": "BCN", "DXB": "DXB", "CJU": "CJU",
}

CABIN_MAP = {
    "economy": "ECONOMY", "premium_economy": "PREMIUM_ECONOMY",
    "business": "BUSINESS", "first": "FIRST",
}
CABIN_KR = {
    "ECONOMY": "이코노미", "PREMIUM_ECONOMY": "프리미엄",
    "BUSINESS": "비즈니스", "FIRST": "퍼스트",
}

# 호텔 이미지가 응답에 없을 때 사용할 대체 이미지(도시 무관 일반 호텔 사진)
_HOTEL_FALLBACK_IMAGES = [
    "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&q=80",
    "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=600&q=80",
    "https://images.unsplash.com/photo-1611892440504-42a792e24d32?w=600&q=80",
    "https://images.unsplash.com/photo-1564501049412-61c2a3083791?w=600&q=80",
]

_token_cache = {"token": None, "exp": 0}


def is_configured() -> bool:
    return bool(_REQUESTS_OK and os.getenv("AMADEUS_API_KEY") and os.getenv("AMADEUS_API_SECRET"))


def _base() -> str:
    env = (os.getenv("AMADEUS_ENV") or "test").lower()
    return "https://api.amadeus.com" if env == "production" else "https://test.api.amadeus.com"


def _get_token() -> Optional[str]:
    if not is_configured():
        return None
    now = time.time()
    if _token_cache["token"] and now < _token_cache["exp"] - 30:
        return _token_cache["token"]
    try:
        resp = requests.post(
            f"{_base()}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": os.getenv("AMADEUS_API_KEY"),
                "client_secret": os.getenv("AMADEUS_API_SECRET"),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        _token_cache["token"] = data["access_token"]
        _token_cache["exp"] = now + int(data.get("expires_in", 1799))
        return _token_cache["token"]
    except Exception as e:  # noqa
        print(f"[amadeus] 토큰 발급 실패: {e}")
        return None


def _headers() -> Optional[Dict[str, str]]:
    tok = _get_token()
    return {"Authorization": f"Bearer {tok}"} if tok else None


def _iata(name: str) -> str:
    return AIRPORTS.get((name or "").strip(), (name or "").upper()[:3])


def _iso_duration_to_kr(iso: str) -> str:
    """PT7H30M -> '7h 30m'"""
    if not iso:
        return ""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", iso)
    if not m:
        return iso
    h, mn = m.group(1) or "0", m.group(2) or "0"
    return f"{int(h)}h {int(mn):02d}m"


def _fmt_time(iso_dt: str) -> str:
    try:
        return datetime.fromisoformat(iso_dt).strftime("%H:%M")
    except Exception:
        return iso_dt[-5:] if iso_dt else ""


def _fmt_date(iso_dt: str) -> str:
    try:
        return datetime.fromisoformat(iso_dt).strftime("%Y-%m-%d")
    except Exception:
        return (iso_dt or "")[:10]


# ──────────────────────────────────────────────
# 항공편
# ──────────────────────────────────────────────
def search_flights(
    origin: str, destination: str, departure_date: str,
    return_date: Optional[str] = None, passengers: int = 1,
    cabin_class: str = "economy",
) -> Optional[List[Dict[str, Any]]]:
    headers = _headers()
    if headers is None:
        return None

    orig, dest = _iata(origin), _iata(destination)
    travel_class = CABIN_MAP.get(cabin_class, "ECONOMY")
    params = {
        "originLocationCode": orig,
        "destinationLocationCode": dest,
        "departureDate": departure_date,
        "adults": max(1, passengers),
        "currencyCode": "KRW",
        "travelClass": travel_class,
        "max": 12,
    }
    if return_date:
        params["returnDate"] = return_date

    try:
        resp = requests.get(
            f"{_base()}/v2/shopping/flight-offers",
            params=params, headers=headers, timeout=15,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:  # noqa
        print(f"[amadeus] 항공 검색 실패: {e}")
        return None

    offers = payload.get("data", [])
    carriers = payload.get("dictionaries", {}).get("carriers", {})
    if not offers:
        return []

    results: List[Dict[str, Any]] = []
    for i, offer in enumerate(offers):
        try:
            itin = offer["itineraries"][0]
            segs = itin["segments"]
            dep = segs[0]["departure"]
            arr = segs[-1]["arrival"]
            carrier_code = segs[0].get("carrierCode", "")
            airline_name = (
                carriers.get(carrier_code)
                or AIRLINES.get(carrier_code, {}).get("name")
                or carrier_code
            )
            price_total = float(offer["price"].get("grandTotal") or offer["price"]["total"])
            per_person = int(round(price_total / max(1, passengers)))
            cabin = "ECONOMY"
            try:
                cabin = offer["travelerPricings"][0]["fareDetailsBySegment"][0].get("cabin", "ECONOMY")
            except Exception:
                pass
            results.append({
                "id": offer.get("id", f"AM{i+1:03d}"),
                "airline": airline_name,
                "airline_code": carrier_code,
                "airline_rating": AIRLINES.get(carrier_code, {}).get("rating", 4.3),
                "departure": {
                    "airport": dep.get("iataCode", orig),
                    "city": CITY_NAMES.get(dep.get("iataCode"), dep.get("iataCode", orig)),
                    "time": _fmt_time(dep.get("at", "")),
                    "date": _fmt_date(dep.get("at", "")),
                },
                "arrival": {
                    "airport": arr.get("iataCode", dest),
                    "city": CITY_NAMES.get(arr.get("iataCode"), arr.get("iataCode", dest)),
                    "time": _fmt_time(arr.get("at", "")),
                    "date": _fmt_date(arr.get("at", "")),
                },
                "duration": _iso_duration_to_kr(itin.get("duration", "")),
                "stops": max(0, len(segs) - 1),
                "cabin_class": CABIN_KR.get(cabin, "이코노미"),
                "price_per_person": per_person,
                "total_price": int(round(price_total)),
                "currency": offer["price"].get("currency", "KRW"),
                "seats_left": int(offer.get("numberOfBookableSeats", 9)),
                "baggage": "수하물 정책 항공사 확인",
                "meal": cabin in ("BUSINESS", "FIRST"),
                "refundable": False,
                "source": "amadeus",
            })
        except Exception as e:  # noqa
            print(f"[amadeus] 항공 파싱 건너뜀: {e}")
            continue

    results.sort(key=lambda x: x["total_price"])
    return results


# ──────────────────────────────────────────────
# 호텔
# ──────────────────────────────────────────────
def search_hotels(
    city: str, check_in: str, check_out: str,
    guests: int = 2, rooms: int = 1,
) -> Optional[List[Dict[str, Any]]]:
    headers = _headers()
    if headers is None:
        return None

    airport = _iata(city)
    city_code = CITY_CODE_BY_AIRPORT.get(airport, airport)

    # 1) 도시 내 호텔 ID 목록
    try:
        r1 = requests.get(
            f"{_base()}/v1/reference-data/locations/hotels/by-city",
            params={"cityCode": city_code}, headers=headers, timeout=15,
        )
        r1.raise_for_status()
        hotel_list = r1.json().get("data", [])
    except Exception as e:  # noqa
        print(f"[amadeus] 호텔 목록 조회 실패: {e}")
        return None

    if not hotel_list:
        return []

    hotel_ids = [h["hotelId"] for h in hotel_list[:20] if h.get("hotelId")]
    if not hotel_ids:
        return []

    # 2) 호텔 오퍼(가격) 조회
    try:
        r2 = requests.get(
            f"{_base()}/v3/shopping/hotel-offers",
            params={
                "hotelIds": ",".join(hotel_ids),
                "adults": max(1, guests),
                "checkInDate": check_in,
                "checkOutDate": check_out,
                "roomQuantity": max(1, rooms),
                "currency": "KRW",
                "bestRateOnly": "true",
            },
            headers=headers, timeout=20,
        )
        r2.raise_for_status()
        offers = r2.json().get("data", [])
    except Exception as e:  # noqa
        print(f"[amadeus] 호텔 오퍼 조회 실패: {e}")
        return None

    try:
        ci = datetime.strptime(check_in, "%Y-%m-%d")
        co = datetime.strptime(check_out, "%Y-%m-%d")
        nights = max(1, (co - ci).days)
    except Exception:
        nights = 1

    results: List[Dict[str, Any]] = []
    for idx, item in enumerate(offers):
        try:
            hotel = item.get("hotel", {})
            offer = (item.get("offers") or [{}])[0]
            price = offer.get("price", {})
            total = float(price.get("total") or 0)
            if total <= 0:
                continue
            per_night = int(round(total / nights))
            rating_raw = hotel.get("rating")
            stars = int(rating_raw) if str(rating_raw or "").isdigit() else 4
            results.append({
                "id": hotel.get("hotelId", f"AMH{idx+1:03d}"),
                "name": hotel.get("name", "호텔"),
                "stars": stars,
                "rating": round(min(5.0, 3.8 + stars * 0.2), 1),
                "reviews": 0,
                "location": city,
                "image": _HOTEL_FALLBACK_IMAGES[idx % len(_HOTEL_FALLBACK_IMAGES)],
                "amenities": [],
                "highlight": offer.get("room", {}).get("typeEstimated", {}).get("category", "") or "실시간 요금",
                "price_per_night": per_night,
                "total_price": int(round(total)),
                "currency": price.get("currency", "KRW"),
                "nights": nights,
                "rooms": rooms,
                "guests": guests,
                "check_in": check_in,
                "check_out": check_out,
                "free_cancellation": "CANCELLATION" in str(offer.get("policies", {})).upper(),
                "breakfast_included": str(offer.get("boardType", "")).upper() == "BREAKFAST",
                "source": "amadeus",
            })
        except Exception as e:  # noqa
            print(f"[amadeus] 호텔 파싱 건너뜀: {e}")
            continue

    results.sort(key=lambda x: x["price_per_night"])
    return results
