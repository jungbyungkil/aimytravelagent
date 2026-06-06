import os
from fastapi import APIRouter
from openai import OpenAI
from app.models import ChatRequest, ItineraryRequest, DestinationRecommendRequest
import json

router = APIRouter()

TRAVEL_SYSTEM_PROMPT = """당신은 'AI Travel'의 전문 여행 어시스턴트입니다.
세계 각지의 여행 정보에 정통하며, 여행자들에게 맞춤형 조언을 제공합니다.

역할:
- 목적지 추천 및 상세 여행 정보 제공
- 항공편, 호텔, 관광지, 음식, 교통 조언
- 여행 예산 계획 도움
- 현지 팁과 주의사항 안내
- 날씨, 최적 여행 시기 정보

응답 스타일:
- 항상 한국어로 답변 (사용자가 영어로 물으면 영어로 답변)
- 친근하고 열정적인 톤
- 구체적이고 실용적인 정보 제공
- 이모지를 적절히 사용하여 읽기 쉽게
- 필요시 목록 형태로 정리

주의: 여행 관련 질문에만 답변하세요. 무관한 질문은 부드럽게 여행 주제로 전환하세요."""

ITINERARY_SYSTEM_PROMPT = """당신은 여행사 수준의 일정 문서를 만드는 세계 최고의 여행 일정 전문가입니다.
여행자의 취향, 기간, 예산과 함께 제공된 항공편/호텔 정보를 반영하여,
실제 여행사가 고객에게 전달하는 PDF처럼 "타임라인" 형태의 상세 일정을 JSON으로 작성합니다.

작성 원칙:
- 제공된 항공편 정보가 있으면, Day 1 첫 일정은 반드시 "출국 항공편"(공항 도착·탑승·이륙 시각 포함),
  마지막 Day의 마지막 일정은 "귀국 항공편"으로 구성하세요.
- 제공된 호텔 정보가 있으면, 체크인(보통 15:00)·체크아웃(보통 11:00) 시각을 일정에 명시하세요.
- 각 날짜의 activities는 시간 순서대로 정렬하고, 모든 항목에 구체적 "time"(HH:MM)을 넣어 타임라인이 되게 하세요.
- 비용(cost)은 KRW 기준 숫자 또는 "₩30,000" 형태로 구체적으로 적으세요.
- type 은 다음 중 하나: 항공|숙박|관광|식사|교통|쇼핑|액티비티|체크인|체크아웃

반드시 다음 JSON 구조로만 응답하세요 (다른 텍스트 없이 순수 JSON만):
{
  "title": "여행 제목",
  "destination": "목적지",
  "duration": 숫자(일),
  "budget_level": "예산 수준",
  "highlights": ["하이라이트1", "하이라이트2"],
  "flight_summary": {
    "airline": "항공사",
    "outbound": {"route": "ICN → DPS", "depart": "출발일 09:20", "arrive": "현지 14:50", "duration": "7시간 30분"},
    "inbound":  {"route": "DPS → ICN", "depart": "현지 00:35", "arrive": "도착일 08:40", "duration": "6시간 50분"}
  },
  "hotel_summary": {
    "name": "호텔명",
    "grade": "성급",
    "area": "위치",
    "check_in": "Day 1 15:00",
    "check_out": "마지막날 11:00",
    "nights": 숫자
  },
  "days": [
    {
      "day": 1,
      "date": "YYYY-MM-DD",
      "title": "Day 1 제목",
      "theme": "테마",
      "activities": [
        {
          "time": "09:20",
          "title": "활동명",
          "description": "상세 설명",
          "duration": "소요시간",
          "cost": "비용(KRW)",
          "tips": "꿀팁",
          "type": "항공|숙박|관광|식사|교통|쇼핑|액티비티|체크인|체크아웃"
        }
      ],
      "accommodation": "숙박 장소",
      "meals": {"breakfast": "조식", "lunch": "중식", "dinner": "석식"},
      "estimated_cost": "하루 예상 비용 (KRW)"
    }
  ],
  "total_estimated_cost": "총 예상 비용 (KRW)",
  "travel_tips": ["팁1", "팁2", "팁3"],
  "best_time_to_visit": "최적 여행 시기",
  "weather_info": "날씨 정보"
}"""


def get_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


@router.post("/chat")
async def chat(req: ChatRequest):
    """OpenAI 여행 채팅"""
    try:
        client = get_client()

        messages = [{"role": "system", "content": TRAVEL_SYSTEM_PROMPT}]
        for msg in req.history:
            if msg.get("role") in ("user", "assistant"):
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": req.message})

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=messages,
        )

        return {
            "response": response.choices[0].message.content,
            "model": response.model,
        }

    except ValueError as e:
        return {"error": str(e), "response": None}
    except Exception as e:
        return {
            "error": f"AI 서비스 오류: {str(e)}",
            "response": "죄송합니다, 일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
        }


@router.post("/itinerary")
async def generate_itinerary(req: ItineraryRequest):
    """OpenAI 맞춤 여행 일정 생성"""
    try:
        client = get_client()

        interests_str = ", ".join(req.interests) if req.interests else "일반 관광"
        budget_map = {"budget": "저예산", "medium": "중간 예산", "luxury": "럭셔리"}
        budget_str = budget_map.get(req.budget, "중간 예산")

        # 추천 카드에서 넘어온 항공/호텔 컨텍스트
        context_lines = []
        if req.flight:
            f = req.flight
            context_lines.append(
                f"- 항공편: {f.get('airline','')} / {f.get('route','')} / "
                f"{f.get('type','')} / 소요 {f.get('duration','')} / "
                f"1인 왕복 약 {f.get('price_per_person','')}원"
            )
        if req.hotel:
            h = req.hotel
            feats = ", ".join(h.get("features", []) or [])
            context_lines.append(
                f"- 숙소: {h.get('name','')} ({h.get('grade','')}) / "
                f"{h.get('area','')} / 1박 약 {h.get('price_per_night','')}원"
                + (f" / {feats}" if feats else "")
            )
        if req.traveler:
            context_lines.append(f"- 여행 구성원: {req.traveler}")
        context_block = ("\n참조할 예약 정보:\n" + "\n".join(context_lines)) if context_lines else ""

        prompt = f"""다음 조건으로 여행사 PDF 수준의 상세 타임라인 일정을 만들어주세요:

- 목적지: {req.destination}
- 여행 기간: {req.duration_days - 1}박 {req.duration_days}일
- 출발일: {req.start_date}
- 관심사: {interests_str}
- 예산 수준: {budget_str}{context_block}

위에 제공된 항공편/호텔 정보가 있으면 반드시 일정에 반영하세요.
- Day 1 시작은 출국 항공편(공항 도착·이륙 시각), 호텔 체크인 시각을 포함하세요.
- 마지막 날은 호텔 체크아웃과 귀국 항공편으로 마무리하세요.
- 모든 관광지·식당·교통 수단을 시간 순서대로, 예상 비용(KRW)과 꿀팁을 포함해 한국 여행자 기준으로 작성해주세요."""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": ITINERARY_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        raw = response.choices[0].message.content.strip()

        # JSON 파싱 - 마크다운 코드블록 제거
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        itinerary = json.loads(raw)
        return {"itinerary": itinerary, "success": True}

    except json.JSONDecodeError:
        return {
            "itinerary": None,
            "raw_text": response.choices[0].message.content if "response" in dir() else "",
            "success": False,
            "error": "일정 생성 중 형식 오류가 발생했습니다.",
        }
    except ValueError as e:
        return {"success": False, "error": str(e), "itinerary": None}
    except Exception as e:
        return {
            "success": False,
            "error": f"일정 생성 실패: {str(e)}",
            "itinerary": None,
        }


@router.post("/recommend")
async def recommend_destination(req: ChatRequest):
    """목적지 추천"""
    prompt = f"""사용자 요청: {req.message}

위 요청을 바탕으로 최적의 여행지 3곳을 추천해주세요.
각 여행지에 대해 다음을 포함하세요:
1. 여행지명과 국가
2. 추천 이유 (2-3문장)
3. 최적 여행 시기
4. 예상 항공권 가격 (한국 출발, KRW)
5. 한 줄 매력 포인트

읽기 쉽게 이모지와 함께 정리해주세요."""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1024,
            messages=[
                {"role": "system", "content": TRAVEL_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return {"response": response.choices[0].message.content, "success": True}
    except Exception as e:
        return {"success": False, "error": str(e), "response": None}


DESTINATION_RECOMMEND_SYSTEM_PROMPT = """당신은 세계 최고의 가족 여행 전문가입니다.
여행자의 구성원, 여행 시기, 예산을 분석하여 최적의 여행지 3곳을 JSON으로 추천합니다.

중요 지침:
- 모든 가격은 한국(인천/김해) 출발 기준, 실제 시세에 가까운 현실적인 금액으로 추정하세요.
- 가격 필드는 반드시 "숫자만"(쉼표/원화기호/단위 없이) 문자열로 작성하세요. 예: "350000"
- 항공편/호텔은 해당 노선·도시에서 실제로 운항/존재하는 대표적인 항공사·호텔을 기준으로 작성하세요.
- attractions(인기 장소)는 그 도시의 대표 명소 3~4곳을 고르고, 가격은 "여행 구성원 전체 기준" 1회/1일 비용으로 산정하세요.
  (예: 4인 가족이면 도쿄 디즈니랜드 4인 1일권 합계 금액)

반드시 아래 JSON 구조로만 응답하세요 (다른 텍스트 없이 순수 JSON만):
{
  "summary": "여행자 분석 요약 (1-2문장)",
  "destinations": [
    {
      "rank": 1,
      "city": "도시명",
      "country": "나라명",
      "emoji": "대표 이모지",
      "tagline": "한 줄 매력 포인트",
      "reasons": ["추천 이유1", "추천 이유2", "추천 이유3"],
      "family_highlights": ["가족 특화 포인트1", "가족 특화 포인트2"],
      "best_dates": [
        {"period": "12월 말 (예: 12/26~1/2)", "pros": "이 시기 장점", "cons": "단점 또는 주의사항"},
        {"period": "1월 초 (예: 1/10~1/17)", "pros": "이 시기 장점", "cons": "단점 또는 주의사항"}
      ],
      "flight": {
        "airline": "대표 항공사 (예: 대한항공, 아시아나, 제주항공 등)",
        "route": "출발-도착 공항코드 (예: ICN → NRT)",
        "duration": "비행 소요시간 (예: 2시간 30분)",
        "type": "직항|경유",
        "price_per_person": "1인 왕복 항공권 예상가 (KRW, 숫자만)"
      },
      "hotel": {
        "name": "추천 호텔명 (실제 존재하는 대표 호텔)",
        "grade": "성급 (예: 4성급)",
        "area": "위치/지역 (예: 신주쿠 중심가)",
        "price_per_night": "1박 가격 예상 (KRW, 숫자만, 가족룸 기준)",
        "features": ["조식 포함", "수영장", "역세권"]
      },
      "attractions": [
        {
          "emoji": "🎢",
          "name": "대표 명소명 (예: 도쿄 디즈니랜드)",
          "category": "테마파크|관광|체험|쇼핑 등",
          "price": "구성원 전체 기준 비용 (KRW, 숫자만)",
          "price_note": "산정 기준 (예: 4인 가족 1일권)"
        }
      ],
      "budget": {
        "flight_per_person": "항공권 1인 예상 (KRW, 숫자만)",
        "hotel_per_night": "호텔 1박 예상 (KRW, 숫자만, 방 기준)",
        "daily_expense": "1일 현지 경비 예상 (KRW, 전체 가족)",
        "total_estimate": "총 여행 예상 비용 (KRW, 전체 가족)",
        "budget_grade": "알뜰|보통|럭셔리"
      },
      "weather": "해당 시기 날씨 정보",
      "kids_friendly_score": 85,
      "tips": ["꿀팁1", "꿀팁2"]
    }
  ]
}"""


@router.post("/recommend-destinations")
async def recommend_destinations(req: DestinationRecommendRequest):
    """가족/그룹 맞춤 여행지 3곳 추천 (구조화 JSON)"""
    try:
        client = get_client()

        prompt = f"""여행자 정보:
- 구성원: {req.travel_party}
- 여행 희망 시기: {req.travel_period}
- 선호/기타: {req.preferences or '특별한 선호 없음'}
- 예산 수준: {req.budget_level}

위 조건에 맞는 최적의 여행지 3곳을 추천해주세요.
아이들 나이와 가족 구성을 특히 고려하여, 아이들이 즐길 수 있는 액티비티와 안전성도 반영해주세요.
각 여행지별로 사용자가 언급한 시기(12월 말 / 1월 / 11월 등)에 맞는 구체적인 날짜 옵션 2개를 제안하세요."""

        response = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=4096,
            messages=[
                {"role": "system", "content": DESTINATION_RECOMMEND_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        result = json.loads(raw)
        return {"success": True, "data": result}

    except json.JSONDecodeError:
        return {"success": False, "error": "AI 응답 파싱 오류", "data": None}
    except ValueError as e:
        return {"success": False, "error": str(e), "data": None}
    except Exception as e:
        return {"success": False, "error": f"추천 생성 실패: {str(e)}", "data": None}
