import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models import BookingCreate

router = APIRouter()

BOOKINGS_FILE = Path("bookings.json")


def load_bookings() -> list:
    if BOOKINGS_FILE.exists():
        with open(BOOKINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_bookings(bookings: list):
    with open(BOOKINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(bookings, f, ensure_ascii=False, indent=2)


@router.get("/")
async def get_bookings():
    bookings = load_bookings()
    return {"bookings": bookings, "count": len(bookings)}


@router.post("/")
async def create_booking(booking: BookingCreate):
    bookings = load_bookings()
    new_booking = {
        "id": str(uuid.uuid4())[:8].upper(),
        "type": booking.type,
        "item_id": booking.item_id,
        "details": booking.details,
        "price": booking.price,
        "currency": booking.currency,
        "status": "confirmed",
        "created_at": datetime.now().isoformat(),
    }
    bookings.append(new_booking)
    save_bookings(bookings)
    return {"booking": new_booking, "message": "예약이 완료되었습니다! ✈️"}


@router.delete("/{booking_id}")
async def delete_booking(booking_id: str):
    bookings = load_bookings()
    updated = [b for b in bookings if b["id"] != booking_id]
    if len(updated) == len(bookings):
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다.")
    save_bookings(updated)
    return {"message": "예약이 취소되었습니다.", "id": booking_id}
