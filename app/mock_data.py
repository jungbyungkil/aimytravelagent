"""
실감나는 Mock 여행 데이터
항공편, 호텔 검색 결과를 실제처럼 생성합니다.
"""
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# ──────────────────────────────────────────────
# 공항 / 도시 매핑
# ──────────────────────────────────────────────
AIRPORTS = {
    "서울": "ICN", "인천": "ICN", "ICN": "ICN",
    "김포": "GMP", "GMP": "GMP",
    "도쿄": "NRT", "NRT": "NRT", "HND": "HND",
    "오사카": "KIX", "KIX": "KIX",
    "방콕": "BKK", "BKK": "BKK",
    "싱가포르": "SIN", "SIN": "SIN",
    "홍콩": "HKG", "HKG": "HKG",
    "파리": "CDG", "CDG": "CDG",
    "뉴욕": "JFK", "JFK": "JFK",
    "로스앤젤레스": "LAX", "LA": "LAX", "LAX": "LAX",
    "런던": "LHR", "LHR": "LHR",
    "발리": "DPS", "DPS": "DPS",
    "하와이": "HNL", "HNL": "HNL",
    "로마": "FCO", "FCO": "FCO",
    "바르셀로나": "BCN", "BCN": "BCN",
    "두바이": "DXB", "DXB": "DXB",
    "제주": "CJU", "CJU": "CJU",
}

CITY_NAMES = {
    "ICN": "서울 (인천)", "GMP": "서울 (김포)",
    "NRT": "도쿄 (나리타)", "HND": "도쿄 (하네다)",
    "KIX": "오사카 (간사이)", "BKK": "방콕 (수완나품)",
    "SIN": "싱가포르", "HKG": "홍콩",
    "CDG": "파리 (샤를드골)", "JFK": "뉴욕 (JFK)",
    "LAX": "로스앤젤레스", "LHR": "런던 (히드로)",
    "DPS": "발리 (응우라라이)", "HNL": "하와이 (호놀룰루)",
    "FCO": "로마 (피우미치노)", "BCN": "바르셀로나",
    "DXB": "두바이", "CJU": "제주",
}

# ──────────────────────────────────────────────
# 항공사 데이터
# ──────────────────────────────────────────────
AIRLINES = {
    "KE": {"name": "대한항공", "logo": "🛫", "rating": 4.5},
    "OZ": {"name": "아시아나항공", "logo": "🛫", "rating": 4.4},
    "7C": {"name": "제주항공", "logo": "✈️", "rating": 4.1},
    "LJ": {"name": "진에어", "logo": "✈️", "rating": 4.0},
    "TW": {"name": "티웨이항공", "logo": "✈️", "rating": 3.9},
    "AF": {"name": "에어프랑스", "logo": "🛫", "rating": 4.3},
    "SQ": {"name": "싱가포르항공", "logo": "🛫", "rating": 4.7},
    "CX": {"name": "캐세이퍼시픽", "logo": "🛫", "rating": 4.4},
    "TG": {"name": "타이항공", "logo": "🛫", "rating": 4.2},
    "EK": {"name": "에미레이트항공", "logo": "🛫", "rating": 4.6},
    "UA": {"name": "유나이티드항공", "logo": "🛫", "rating": 4.0},
    "NH": {"name": "전일본공수(ANA)", "logo": "🛫", "rating": 4.6},
    "JL": {"name": "일본항공(JAL)", "logo": "🛫", "rating": 4.5},
}

# 노선별 기본 가격 (KRW, 편도, 이코노미)
ROUTE_BASE_PRICES = {
    ("ICN", "NRT"): (180000, ["KE", "OZ", "7C", "NH", "JL"]),
    ("ICN", "HND"): (175000, ["KE", "OZ", "LJ"]),
    ("ICN", "KIX"): (165000, ["KE", "OZ", "7C", "TW"]),
    ("ICN", "BKK"): (350000, ["KE", "OZ", "TG"]),
    ("ICN", "SIN"): (420000, ["KE", "OZ", "SQ"]),
    ("ICN", "HKG"): (310000, ["KE", "OZ", "CX"]),
    ("ICN", "CDG"): (950000, ["KE", "OZ", "AF"]),
    ("ICN", "JFK"): (1100000, ["KE", "OZ", "UA"]),
    ("ICN", "LAX"): (1050000, ["KE", "OZ", "UA"]),
    ("ICN", "LHR"): (980000, ["KE", "OZ"]),
    ("ICN", "DPS"): (480000, ["KE", "OZ"]),
    ("ICN", "HNL"): (780000, ["KE", "OZ", "UA"]),
    ("ICN", "FCO"): (920000, ["KE", "OZ", "AF"]),
    ("ICN", "DXB"): (750000, ["KE", "EK"]),
    ("ICN", "CJU"): (85000, ["KE", "OZ", "7C", "LJ", "TW"]),
    ("GMP", "CJU"): (78000, ["KE", "OZ", "7C", "LJ"]),
}

FLIGHT_TIMES = [
    "06:00", "07:30", "08:15", "09:00", "10:30",
    "11:45", "13:00", "14:20", "15:45", "17:00",
    "18:30", "19:45", "21:00", "22:30", "23:55",
]

FLIGHT_DURATIONS = {
    ("ICN", "NRT"): "2h 30m",
    ("ICN", "HND"): "2h 25m",
    ("ICN", "KIX"): "2h 10m",
    ("ICN", "BKK"): "5h 45m",
    ("ICN", "SIN"): "6h 30m",
    ("ICN", "HKG"): "3h 45m",
    ("ICN", "CDG"): "12h 15m",
    ("ICN", "JFK"): "14h 00m",
    ("ICN", "LAX"): "11h 30m",
    ("ICN", "LHR"): "11h 45m",
    ("ICN", "DPS"): "7h 20m",
    ("ICN", "HNL"): "9h 45m",
    ("ICN", "FCO"): "12h 30m",
    ("ICN", "DXB"): "9h 30m",
    ("ICN", "CJU"): "1h 05m",
    ("GMP", "CJU"): "1h 00m",
}

CABIN_MULTIPLIERS = {
    "economy": 1.0,
    "premium_economy": 2.2,
    "business": 4.5,
    "first": 8.0,
}

CABIN_NAMES = {
    "economy": "이코노미",
    "premium_economy": "프리미엄 이코노미",
    "business": "비즈니스",
    "first": "퍼스트",
}


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    passengers: int = 1,
    cabin_class: str = "economy",
) -> List[Dict[str, Any]]:
    """항공편 검색 (Mock 데이터)"""

    # IATA 코드 정규화
    orig_code = AIRPORTS.get(origin.strip(), origin.upper()[:3])
    dest_code = AIRPORTS.get(destination.strip(), destination.upper()[:3])

    # 노선 찾기 (정방향 / 역방향)
    route_key = (orig_code, dest_code)
    rev_key = (dest_code, orig_code)

    if route_key in ROUTE_BASE_PRICES:
        base_price, airline_codes = ROUTE_BASE_PRICES[route_key]
        duration = FLIGHT_DURATIONS.get(route_key, "미정")
    elif rev_key in ROUTE_BASE_PRICES:
        base_price, airline_codes = ROUTE_BASE_PRICES[rev_key]
        duration = FLIGHT_DURATIONS.get(rev_key, "미정")
        orig_code, dest_code = dest_code, orig_code  # swap
    else:
        # 알 수 없는 노선 → 랜덤 생성
        base_price = random.randint(200000, 1500000)
        airline_codes = random.sample(list(AIRLINES.keys()), min(3, len(AIRLINES)))
        duration = f"{random.randint(2, 14)}h {random.randint(0, 59):02d}m"

    cabin_mult = CABIN_MULTIPLIERS.get(cabin_class, 1.0)
    cabin_name = CABIN_NAMES.get(cabin_class, "이코노미")

    results = []
    random.seed(departure_date + orig_code + dest_code)  # 같은 날짜면 동일 결과

    for i, code in enumerate(airline_codes):
        airline = AIRLINES[code]
        dep_time = FLIGHT_TIMES[i % len(FLIGHT_TIMES)]

        # 도착 시간 계산 (간단히)
        dur_hours = int(duration.split("h")[0]) if "h" in duration else 2
        dep_dt = datetime.strptime(dep_time, "%H:%M")
        arr_dt = dep_dt + timedelta(hours=dur_hours)
        arr_time = arr_dt.strftime("%H:%M")

        # 가격 변동 (±20%)
        variation = random.uniform(0.85, 1.20)
        price = int(base_price * cabin_mult * variation)
        # 100원 단위 반올림
        price = round(price / 100) * 100
        total_price = price * passengers

        # 잔여 좌석
        seats_left = random.randint(1, 9)

        flight = {
            "id": f"{code}{departure_date.replace('-','')}{i+1:03d}",
            "airline": airline["name"],
            "airline_code": code,
            "airline_rating": airline["rating"],
            "departure": {
                "airport": orig_code,
                "city": CITY_NAMES.get(orig_code, orig_code),
                "time": dep_time,
                "date": departure_date,
            },
            "arrival": {
                "airport": dest_code,
                "city": CITY_NAMES.get(dest_code, dest_code),
                "time": arr_time,
                "date": departure_date,
            },
            "duration": duration,
            "stops": 0 if "직항" not in duration else 1,
            "cabin_class": cabin_name,
            "price_per_person": price,
            "total_price": total_price,
            "currency": "KRW",
            "seats_left": seats_left,
            "baggage": "15kg 위탁 포함" if cabin_class == "economy" else "23kg 위탁 포함",
            "meal": cabin_class != "economy",
            "refundable": cabin_class in ("business", "first"),
        }
        results.append(flight)

    # 가격순 정렬
    results.sort(key=lambda x: x["total_price"])
    return results


# ──────────────────────────────────────────────
# 호텔 데이터
# ──────────────────────────────────────────────
HOTELS_DB = {
    "도쿄": [
        {
            "name": "파크 하얏트 도쿄",
            "stars": 5,
            "rating": 9.2,
            "reviews": 3842,
            "price_per_night": 520000,
            "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=250&fit=crop",
            "location": "신주쿠, 도쿄",
            "amenities": ["무료 Wi-Fi", "수영장", "스파", "피트니스", "레스토랑", "컨시어지"],
            "highlight": "영화 '사랑도 통역이 되나요?' 촬영지",
        },
        {
            "name": "더 페닌슐라 도쿄",
            "stars": 5,
            "rating": 9.4,
            "reviews": 2916,
            "price_per_night": 680000,
            "image": "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400&h=250&fit=crop",
            "location": "마루노우치, 도쿄",
            "amenities": ["무료 Wi-Fi", "수영장", "스파", "피트니스", "루프탑 바"],
            "highlight": "도쿄역 5분 거리 럭셔리 호텔",
        },
        {
            "name": "시타딘스 신주쿠 도쿄",
            "stars": 4,
            "rating": 8.5,
            "reviews": 5621,
            "price_per_night": 185000,
            "image": "https://images.unsplash.com/photo-1631049307264-da0ec9d70304?w=400&h=250&fit=crop",
            "location": "신주쿠, 도쿄",
            "amenities": ["무료 Wi-Fi", "주방", "세탁기", "편의점 근처"],
            "highlight": "신주쿠 중심가 가성비 호텔",
        },
        {
            "name": "도쿄 스테이션 호텔",
            "stars": 5,
            "rating": 9.0,
            "reviews": 4103,
            "price_per_night": 430000,
            "image": "https://images.unsplash.com/photo-1590073242678-70ee3fc28e8e?w=400&h=250&fit=crop",
            "location": "마루노우치, 도쿄",
            "amenities": ["무료 Wi-Fi", "피트니스", "레스토랑", "컨시어지"],
            "highlight": "도쿄역 바로 연결, 역사적 건물",
        },
    ],
    "방콕": [
        {
            "name": "만다린 오리엔탈 방콕",
            "stars": 5,
            "rating": 9.5,
            "reviews": 6234,
            "price_per_night": 620000,
            "image": "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=400&h=250&fit=crop",
            "location": "차오프라야 강변, 방콕",
            "amenities": ["무료 Wi-Fi", "수영장", "스파", "강변 전망", "버틀러 서비스"],
            "highlight": "150년 전통, 아시아 최고의 호텔",
        },
        {
            "name": "아난타라 시암 방콕",
            "stars": 5,
            "rating": 9.1,
            "reviews": 3812,
            "price_per_night": 380000,
            "image": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=400&h=250&fit=crop",
            "location": "라차담리, 방콕",
            "amenities": ["무료 Wi-Fi", "수영장", "스파", "피트니스", "태국 요리 클래스"],
            "highlight": "BTS 라차담리역 인접",
        },
        {
            "name": "센타라 그랜드 방콕",
            "stars": 5,
            "rating": 8.8,
            "reviews": 7521,
            "price_per_night": 280000,
            "image": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=250&fit=crop",
            "location": "랏차프라송, 방콕",
            "amenities": ["무료 Wi-Fi", "옥상 수영장", "피트니스", "쇼핑몰 연결"],
            "highlight": "센트럴월드 직접 연결",
        },
    ],
    "파리": [
        {
            "name": "르 뫼리스",
            "stars": 5,
            "rating": 9.4,
            "reviews": 2103,
            "price_per_night": 1200000,
            "image": "https://images.unsplash.com/photo-1551918120-9739cb430c6d?w=400&h=250&fit=crop",
            "location": "튀일리 정원 인근, 파리 1구",
            "amenities": ["무료 Wi-Fi", "스파", "미슐랭 레스토랑", "컨시어지", "버틀러"],
            "highlight": "에펠탑 뷰, 200년 역사의 궁전 호텔",
        },
        {
            "name": "노부 파리",
            "stars": 5,
            "rating": 9.0,
            "reviews": 1842,
            "price_per_night": 750000,
            "image": "https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=400&h=250&fit=crop",
            "location": "샹젤리제, 파리 8구",
            "amenities": ["무료 Wi-Fi", "스파", "노부 레스토랑", "루프탑 풀"],
            "highlight": "샹젤리제 정면, 모던 럭셔리",
        },
        {
            "name": "이비스 파리 에펠탑",
            "stars": 3,
            "rating": 8.2,
            "reviews": 9341,
            "price_per_night": 220000,
            "image": "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=400&h=250&fit=crop",
            "location": "에펠탑 인근, 파리 15구",
            "amenities": ["무료 Wi-Fi", "조식 뷔페", "바", "에펠탑 뷰"],
            "highlight": "에펠탑 도보 10분, 가성비 최고",
        },
    ],
    "싱가포르": [
        {
            "name": "마리나 베이 샌즈",
            "stars": 5,
            "rating": 9.2,
            "reviews": 15820,
            "price_per_night": 750000,
            "image": "https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=400&h=250&fit=crop",
            "location": "마리나 베이, 싱가포르",
            "amenities": ["무료 Wi-Fi", "인피니티 풀", "카지노", "쇼핑몰", "세레나데"],
            "highlight": "세계 최고 인피니티 풀, 아이코닉 랜드마크",
        },
        {
            "name": "래플스 싱가포르",
            "stars": 5,
            "rating": 9.3,
            "reviews": 4231,
            "price_per_night": 920000,
            "image": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=400&h=250&fit=crop",
            "location": "시티홀, 싱가포르",
            "amenities": ["무료 Wi-Fi", "수영장", "스파", "버틀러 서비스", "롱바"],
            "highlight": "싱가포르 슬링 발원지, 1887년 개관",
        },
    ],
    "발리": [
        {
            "name": "포시즌스 리조트 사얀",
            "stars": 5,
            "rating": 9.5,
            "reviews": 3241,
            "price_per_night": 880000,
            "image": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=400&h=250&fit=crop",
            "location": "우붓, 발리",
            "amenities": ["무료 Wi-Fi", "풀빌라", "스파", "요가", "정글 뷰"],
            "highlight": "아유강 위 서스펜션 브리지, 최고의 정글 리조트",
        },
        {
            "name": "알릴라 빌라스 울루와투",
            "stars": 5,
            "rating": 9.3,
            "reviews": 2890,
            "price_per_night": 720000,
            "image": "https://images.unsplash.com/photo-1573790387438-4da905039392?w=400&h=250&fit=crop",
            "location": "울루와투, 발리",
            "amenities": ["무료 Wi-Fi", "절벽 수영장", "인도양 뷰", "스파", "요가"],
            "highlight": "인도양 절벽 위 무한 풀, 최고의 선셋 뷰",
        },
        {
            "name": "더블유 발리 스미냑 비치",
            "stars": 5,
            "rating": 8.9,
            "reviews": 5614,
            "price_per_night": 420000,
            "image": "https://images.unsplash.com/photo-1559827291-72ee739d0d9a?w=400&h=250&fit=crop",
            "location": "스미냑 비치, 발리",
            "amenities": ["무료 Wi-Fi", "비치 풀", "서핑", "나이트라이프", "스파"],
            "highlight": "스미냑 비치 직결, 트렌디한 리조트",
        },
    ],
    "제주": [
        {
            "name": "신라 호텔 제주",
            "stars": 5,
            "rating": 9.1,
            "reviews": 8421,
            "price_per_night": 320000,
            "image": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400&h=250&fit=crop",
            "location": "중문, 제주시",
            "amenities": ["무료 Wi-Fi", "야외 풀", "스파", "골프장", "해변 바"],
            "highlight": "제주 중문 해수욕장 인접, 한국 최고급 리조트",
        },
        {
            "name": "롯데 호텔 제주",
            "stars": 5,
            "rating": 8.8,
            "reviews": 11203,
            "price_per_night": 260000,
            "image": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=400&h=250&fit=crop",
            "location": "중문, 제주시",
            "amenities": ["무료 Wi-Fi", "워터파크", "수영장", "스파", "면세점"],
            "highlight": "워터파크 무료 이용, 패밀리 최적",
        },
        {
            "name": "해비치 호텔 제주",
            "stars": 4,
            "rating": 8.5,
            "reviews": 6302,
            "price_per_night": 180000,
            "image": "https://images.unsplash.com/photo-1551882547-ff40c63fe5fa?w=400&h=250&fit=crop",
            "location": "표선, 제주시",
            "amenities": ["무료 Wi-Fi", "수영장", "해변", "스파", "레스토랑"],
            "highlight": "표선 해수욕장 인접, 가성비 리조트",
        },
    ],
    "하와이": [
        {
            "name": "포시즌스 리조트 오아후",
            "stars": 5,
            "rating": 9.4,
            "reviews": 4521,
            "price_per_night": 980000,
            "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=400&h=250&fit=crop",
            "location": "코 올리나, 오아후",
            "amenities": ["무료 Wi-Fi", "비치 풀", "스파", "다이빙", "요트"],
            "highlight": "와이키키 외곽 프라이빗 라군",
        },
        {
            "name": "힐튼 하와이안 빌리지",
            "stars": 4,
            "rating": 8.7,
            "reviews": 21034,
            "price_per_night": 420000,
            "image": "https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?w=400&h=250&fit=crop",
            "location": "와이키키, 호놀룰루",
            "amenities": ["무료 Wi-Fi", "대형 풀", "비치", "쇼핑", "레스토랑 多"],
            "highlight": "와이키키 최대 리조트, 금요 불꽃놀이",
        },
    ],
    "홍콩": [
        {
            "name": "더 페닌슐라 홍콩",
            "stars": 5,
            "rating": 9.5,
            "reviews": 5830,
            "price_per_night": 780000,
            "image": "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?w=400&h=250&fit=crop",
            "location": "침사추이, 구룡",
            "amenities": ["무료 Wi-Fi", "옥상 풀", "스파", "헬리패드", "롤스로이스 셔틀"],
            "highlight": "홍콩섬 야경 최고 뷰, 1928년 개관",
        },
        {
            "name": "W 홍콩",
            "stars": 5,
            "rating": 8.9,
            "reviews": 7240,
            "price_per_night": 480000,
            "image": "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=400&h=250&fit=crop",
            "location": "서구룡, 홍콩",
            "amenities": ["무료 Wi-Fi", "인피니티 풀", "클럽", "스파", "ICC 전망"],
            "highlight": "국제상업센터 인접, 최고 도심 뷰",
        },
    ],
}

# 도시 이름 정규화
CITY_ALIASES = {
    "tokyo": "도쿄", "tokyp": "도쿄",
    "bangkok": "방콕", "bkk": "방콕",
    "paris": "파리",
    "singapore": "싱가포르", "sin": "싱가포르",
    "bali": "발리",
    "jeju": "제주", "jejudo": "제주",
    "hawaii": "하와이", "honolulu": "하와이",
    "hong kong": "홍콩", "hongkong": "홍콩", "hkg": "홍콩",
}


def normalize_city(city: str) -> str:
    city_lower = city.lower().strip()
    return CITY_ALIASES.get(city_lower, city.strip())


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    rooms: int = 1,
) -> List[Dict[str, Any]]:
    """호텔 검색 (Mock 데이터)"""
    city_normalized = normalize_city(city)

    # DB에서 찾기
    hotels_raw = HOTELS_DB.get(city_normalized, [])

    # 못 찾으면 유사 검색
    if not hotels_raw:
        for key in HOTELS_DB:
            if key in city or city in key:
                hotels_raw = HOTELS_DB[key]
                city_normalized = key
                break

    # 그래도 없으면 도쿄 기본 반환
    if not hotels_raw:
        hotels_raw = HOTELS_DB["도쿄"]
        city_normalized = "도쿄"

    # 체크인/아웃 날짜 파싱
    try:
        ci = datetime.strptime(check_in, "%Y-%m-%d")
        co = datetime.strptime(check_out, "%Y-%m-%d")
        nights = max(1, (co - ci).days)
    except Exception:
        nights = 1

    random.seed(check_in + city_normalized)
    results = []
    for idx, hotel in enumerate(hotels_raw):
        # 가격 변동 (±15%)
        variation = random.uniform(0.88, 1.15)
        price_per_night = int(hotel["price_per_night"] * variation / 1000) * 1000
        total_price = price_per_night * nights * rooms

        results.append({
            "id": f"HTL{city_normalized[:2].upper()}{idx+1:03d}",
            "name": hotel["name"],
            "stars": hotel["stars"],
            "rating": hotel["rating"],
            "reviews": hotel["reviews"],
            "location": hotel["location"],
            "image": hotel["image"],
            "amenities": hotel["amenities"],
            "highlight": hotel["highlight"],
            "price_per_night": price_per_night,
            "total_price": total_price,
            "currency": "KRW",
            "nights": nights,
            "rooms": rooms,
            "guests": guests,
            "check_in": check_in,
            "check_out": check_out,
            "free_cancellation": random.choice([True, True, False]),
            "breakfast_included": hotel["stars"] >= 5 and random.choice([True, False]),
        })

    results.sort(key=lambda x: x["price_per_night"])
    return results


# ──────────────────────────────────────────────
# 인기 목적지 (홈화면용)
# ──────────────────────────────────────────────
POPULAR_DESTINATIONS = [
    {
        "city": "도쿄",
        "country": "일본",
        "image": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=600&h=400&fit=crop",
        "min_price": 175000,
        "tag": "인기 1위",
        "tag_color": "#FF6B35",
        "description": "전통과 첨단이 공존하는 매력적인 도시",
    },
    {
        "city": "방콕",
        "country": "태국",
        "image": "https://images.unsplash.com/photo-1508009603885-50cf7c579365?w=600&h=400&fit=crop",
        "min_price": 340000,
        "tag": "인기 급상승",
        "tag_color": "#00B96B",
        "description": "황금사원과 이색 시장의 나라",
    },
    {
        "city": "파리",
        "country": "프랑스",
        "image": "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=600&h=400&fit=crop",
        "min_price": 920000,
        "tag": "로맨틱 여행",
        "tag_color": "#9B59B6",
        "description": "에펠탑, 루브르, 와인… 낭만의 도시",
    },
    {
        "city": "발리",
        "country": "인도네시아",
        "image": "https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&h=400&fit=crop",
        "min_price": 450000,
        "tag": "힐링 여행",
        "tag_color": "#27AE60",
        "description": "신들의 섬, 자연 속 완벽한 휴식",
    },
    {
        "city": "싱가포르",
        "country": "싱가포르",
        "image": "https://images.unsplash.com/photo-1565967511849-76a60a516170?w=600&h=400&fit=crop",
        "min_price": 400000,
        "tag": "도심 여행",
        "tag_color": "#2980B9",
        "description": "마리나베이샌즈와 가든스 바이 더 베이",
    },
    {
        "city": "하와이",
        "country": "미국",
        "image": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&h=400&fit=crop",
        "min_price": 780000,
        "tag": "허니문 추천",
        "tag_color": "#E91E63",
        "description": "태평양의 낙원, 와이키키 비치",
    },
    {
        "city": "제주",
        "country": "한국",
        "image": "https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=600&h=400&fit=crop",
        "min_price": 78000,
        "tag": "국내 여행",
        "tag_color": "#16A085",
        "description": "한라산과 에메랄드 바다가 있는 섬",
    },
    {
        "city": "홍콩",
        "country": "홍콩",
        "image": "https://images.unsplash.com/photo-1474531210469-f91a11c06991?w=600&h=400&fit=crop",
        "min_price": 300000,
        "tag": "미식 여행",
        "tag_color": "#F39C12",
        "description": "야경과 딤섬, 쇼핑의 천국",
    },
]
