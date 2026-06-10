import os
import json
import uuid
import tempfile
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File
from openai import OpenAI
from app.models import ReceiptItineraryRequest

router = APIRouter()

RECEIPTS_FILE = Path("receipts.json")

PARSE_SYSTEM_PROMPT = """당신은 여행 예약 전자 영수증 파싱 전문가입니다.
PDF에서 추출된 텍스트를 분석하여 항공편과 호텔 정보를 정확하게 추출합니다.

반드시 다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이 순수 JSON):
{
  "booking_source": "Trip.com | 네이버 | 기타",
  "booking_number": "예약번호",
  "booking_date": "예약일 (YYYY-MM-DD)",
  "contact_name": "연락처 이름",
  "passengers": [
    {"name": "이름", "type": "성인|어린이|유아", "ticket_number": "e티켓번호 (없으면 null)"}
  ],
  "flights": [
    {
      "route": "출발지 - 도착지",
      "departure_airport": "출발 공항명",
      "arrival_airport": "도착 공항명",
      "departure_datetime": "YYYY-MM-DD HH:MM",
      "arrival_datetime": "YYYY-MM-DD HH:MM",
      "airline": "항공사명",
      "flight_number": "항공편 번호",
      "cabin_class": "일반석|비즈니스석|퍼스트클래스",
      "pnr": "항공사 예약번호"
    }
  ],
  "hotels": [
    {
      "name": "호텔명",
      "location": "위치/도시",
      "check_in": "YYYY-MM-DD",
      "check_out": "YYYY-MM-DD",
      "nights": 숫자,
      "room_type": "객실 타입"
    }
  ],
  "price_breakdown": [
    {"item": "항목명", "amount": 숫자, "currency": "KRW|USD|JPY 등"}
  ],
  "total_amount": 숫자,
  "total_currency": "KRW",
  "destination_city": "주요 여행 목적지 도시",
  "destination_country": "주요 여행 목적지 국가"
}

정보가 없는 필드는 null로 채우세요."""

ITINERARY_FROM_BOOKING_PROMPT = """당신은 세계 최고의 여행 일정 전문가입니다.
확정된 항공권과 호텔 예약 정보를 바탕으로 구체적이고 실용적인 여행 일정을 JSON 형식으로 작성합니다.

도착 후 체크인 전 시간, 체크아웃 후 귀국 전 여유 시간도 최대한 활용한 일정을 짜주세요.
탑승객 구성(성인/어린이)을 고려해 가족 친화적 활동을 포함하세요.

반드시 다음 JSON 구조로만 응답하세요 (다른 텍스트 없이 순수 JSON만):
{
  "title": "여행 제목",
  "destination": "목적지",
  "duration": 숫자(일),
  "travel_style": "여행 스타일",
  "highlights": ["하이라이트1", "하이라이트2"],
  "confirmed_info": {
    "hotel": "호텔명",
    "outbound_flight": "출발 항공편 요약",
    "return_flight": "귀국 항공편 요약"
  },
  "days": [
    {
      "day": 1,
      "date": "YYYY-MM-DD",
      "title": "Day 1 제목",
      "theme": "테마",
      "activities": [
        {
          "time": "HH:MM",
          "title": "활동명",
          "description": "상세 설명",
          "duration": "소요시간",
          "cost": "비용 (KRW 기준, 없으면 무료)",
          "tips": "꿀팁",
          "type": "관광|식사|교통|숙박|쇼핑|액티비티|공항"
        }
      ],
      "accommodation": "숙박 장소",
      "meals": {
        "breakfast": "조식 추천",
        "lunch": "중식 추천",
        "dinner": "석식 추천"
      },
      "estimated_cost": "하루 예상 추가 비용 (KRW, 이미 결제된 항공+호텔 제외)"
    }
  ],
  "total_additional_cost": "항공+호텔 외 추가 예상 비용 (KRW)",
  "travel_tips": ["팁1", "팁2", "팁3"],
  "weather_info": "여행 시기 날씨 정보",
  "baggage_reminders": ["수하물 관련 주의사항"],
  "emergency_contacts": [{"name": "기관명", "number": "전화번호"}]
}"""


def load_receipts() -> list:
    if RECEIPTS_FILE.exists():
        with open(RECEIPTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_receipts(receipts: list):
    with open(RECEIPTS_FILE, "w", encoding="utf-8") as f:
        json.dump(receipts, f, ensure_ascii=False, indent=2)


def extract_pdf_text(file_bytes: bytes) -> str:
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 텍스트 추출 실패: {str(e)}")


def parse_receipt_with_ai(text: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=2048,
        messages=[
            {"role": "system", "content": PARSE_SYSTEM_PROMPT},
            {"role": "user", "content": f"다음 영수증 텍스트를 파싱해주세요:\n\n{text}"},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    return json.loads(raw)


@router.get("/")
async def get_receipts():
    receipts = load_receipts()
    return {"receipts": receipts, "count": len(receipts)}


@router.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드 가능합니다.")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다.")

    text = extract_pdf_text(file_bytes)
    if not text:
        raise HTTPException(status_code=400, detail="PDF에서 텍스트를 추출할 수 없습니다.")

    parsed = parse_receipt_with_ai(text)

    receipts = load_receipts()
    new_receipt = {
        "id": str(uuid.uuid4())[:8].upper(),
        "filename": file.filename,
        "uploaded_at": datetime.now().isoformat(),
        "raw_text_length": len(text),
        **parsed,
    }
    receipts.append(new_receipt)
    save_receipts(receipts)

    return {"receipt": new_receipt, "message": "영수증이 성공적으로 파싱되었습니다!"}


@router.get("/{receipt_id}")
async def get_receipt(receipt_id: str):
    receipts = load_receipts()
    receipt = next((r for r in receipts if r["id"] == receipt_id), None)
    if not receipt:
        raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")
    return {"receipt": receipt}


@router.delete("/{receipt_id}")
async def delete_receipt(receipt_id: str):
    receipts = load_receipts()
    updated = [r for r in receipts if r["id"] != receipt_id]
    if len(updated) == len(receipts):
        raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")
    save_receipts(updated)
    return {"message": "영수증이 삭제되었습니다.", "id": receipt_id}


@router.post("/{receipt_id}/itinerary")
async def generate_itinerary_from_receipt(receipt_id: str, req: ReceiptItineraryRequest):
    receipts = load_receipts()
    receipt = next((r for r in receipts if r["id"] == receipt_id), None)
    if not receipt:
        raise HTTPException(status_code=404, detail="영수증을 찾을 수 없습니다.")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY가 설정되지 않았습니다.")

    flights = receipt.get("flights", [])
    hotels = receipt.get("hotels", [])
    passengers = receipt.get("passengers", [])

    style_map = {
        "family": "가족 여행 (어린이 포함)",
        "couple": "커플 여행",
        "solo": "혼자 여행",
        "friends": "친구들과 여행",
    }
    style_str = style_map.get(req.travel_style, req.travel_style)
    interests_str = ", ".join(req.interests) if req.interests else "관광, 맛집, 쇼핑"

    context = f"""확정된 예약 정보:

여행 목적지: {receipt.get('destination_city')}, {receipt.get('destination_country')}
여행 스타일: {style_str}
관심사: {interests_str}
탑승객: {len(passengers)}명 ({', '.join(p['name'] + '(' + p['type'] + ')' for p in passengers)})

항공편:
{json.dumps(flights, ensure_ascii=False, indent=2)}

호텔:
{json.dumps(hotels, ensure_ascii=False, indent=2)}

이미 결제된 금액: {receipt.get('total_amount') or 0:,} {receipt.get('total_currency') or 'KRW'}

위 확정된 일정을 기반으로 상세 여행 일정을 작성해주세요.
호텔 위치(도쿄 디즈니씨 인근인 쉐라톤 도쿄 베이)를 고려하고,
도착 당일(체크인 전)과 귀국 당일(체크아웃 후 공항 이동 전) 시간도 최대한 활용하세요."""

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=4096,
        messages=[
            {"role": "system", "content": ITINERARY_FROM_BOOKING_PROMPT},
            {"role": "user", "content": context},
        ],
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

    itinerary = json.loads(raw)

    receipts = load_receipts()
    for r in receipts:
        if r["id"] == receipt_id:
            r["itinerary"] = itinerary
            r["itinerary_generated_at"] = datetime.now().isoformat()
            break
    save_receipts(receipts)

    return {"itinerary": itinerary, "success": True}
