from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import search, ai_chat, bookings
import uvicorn

app = FastAPI(
    title="AI Travel Agent",
    description="Trip.com 수준의 AI 여행 플랫폼",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(search.router,   prefix="/api/search",   tags=["search"])
app.include_router(ai_chat.router,  prefix="/api/ai",       tags=["ai"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])


@app.get("/")
async def home():
    """메인 페이지 (순수 HTML 서빙 — destinations는 JS에서 API 호출)"""
    return FileResponse("templates/index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "version": "3.0.0", "service": "AI Travel"}


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
