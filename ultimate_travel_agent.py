import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import json
import glob

# PDF 처리 라이브러리
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False
    print("⚠️ PyPDF2 라이브러리가 없습니다. PDF 처리를 위해 설치하세요: pip install PyPDF2")

# 캘린더 관련 라이브러리
try:
    from icalendar import Calendar, Event, vText, Alarm
    ICALENDAR_AVAILABLE = True
except ImportError:
    ICALENDAR_AVAILABLE = False

# Google Calendar API
try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    import pickle
    GOOGLE_CALENDAR_AVAILABLE = True
except ImportError:
    GOOGLE_CALENDAR_AVAILABLE = False

load_dotenv()


class TravelExpense(BaseModel):
    """여행 경비 데이터 모델"""
    category: str  # 항공, 숙박, 교통, 식사, 투어 등
    amount: float
    currency: str
    description: str
    date: Optional[str] = None


class TravelGuide(BaseModel):
    """여행 가이드 데이터 모델"""
    destination: str
    weather_info: str
    exchange_rate: str
    essential_phrases: List[Dict[str, str]]
    local_tips: List[str]
    emergency_contacts: List[Dict[str, str]]


class CalendarEvent:
    """캘린더 이벤트 데이터 모델"""
    def __init__(
        self,
        title: str,
        start_datetime: datetime,
        end_datetime: datetime,
        location: str = "",
        description: str = "",
        reminder_minutes: int = 60,
        event_type: str = "booking"  # booking, reminder, checklist
    ):
        self.title = title
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.location = location
        self.description = description
        self.reminder_minutes = reminder_minutes
        self.event_type = event_type


class UltimateTravelAgent:
    """궁극의 여행 AI Agent"""
    
    def __init__(self, model: str = "gpt-4o"):
        self.client = OpenAI()
        self.model = model
        self.all_bookings = []  # 모든 예약 정보 저장
        self.all_events = []  # 모든 캘린더 이벤트
        self.all_expenses = []  # 모든 경비
        self.travel_guides = {}  # 목적지별 가이드
        
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """
        파일 내용을 읽기 (txt 또는 pdf)
        """
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.txt':
                # 텍스트 파일 읽기
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif file_ext == '.pdf':
                # PDF 파일 읽기
                if not PDF_AVAILABLE:
                    print(f"   ⚠️ PyPDF2가 설치되지 않아 PDF를 읽을 수 없습니다: {Path(file_path).name}")
                    return None
                
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text += page.extract_text() + "\n"
                
                if not text.strip():
                    print(f"   ⚠️ PDF에서 텍스트를 추출할 수 없습니다: {Path(file_path).name}")
                    return None
                
                return text
            
            else:
                print(f"   ⚠️ 지원하지 않는 파일 형식: {file_ext}")
                return None
                
        except Exception as e:
            print(f"   ❌ 파일 읽기 오류 ({Path(file_path).name}): {e}")
            return None
    
    def process_booking_folder(self, folder_path: str = "bookings") -> Dict[str, Any]:
        """
        📁 기능 1: 여러 예약 파일을 한 번에 처리
        폴더 안의 모든 txt, pdf 파일을 읽어서 처리
        """
        print("\n" + "=" * 70)
        print("📁 예약 파일 일괄 처리 시작")
        print("=" * 70)
        
        # txt와 pdf 파일 모두 찾기
        txt_files = glob.glob(f"{folder_path}/*.txt")
        pdf_files = glob.glob(f"{folder_path}/*.pdf")
        booking_files = txt_files + pdf_files
        
        if not booking_files:
            print(f"⚠️ {folder_path} 폴더에 txt 또는 pdf 파일이 없습니다.")
            return {"success": False, "message": "No files found"}
        
        print(f"✅ {len(booking_files)}개의 파일 발견")
        print(f"   • TXT: {len(txt_files)}개")
        print(f"   • PDF: {len(pdf_files)}개\n")
        
        results = {
            "summaries": [],
            "events": [],
            "expenses": [],
            "destinations": set()
        }
        
        for idx, file_path in enumerate(booking_files, 1):
            file_name = Path(file_path).name
            file_type = Path(file_path).suffix.upper()[1:]  # .txt -> TXT
            
            print(f"[{idx}/{len(booking_files)}] 처리 중: {file_name} ({file_type})")
            
            try:
                # 파일 내용 읽기 (txt 또는 pdf)
                raw_text = self._read_file_content(file_path)
                
                if not raw_text:
                    print(f"   ⚠️ 건너뜀: 내용을 읽을 수 없음\n")
                    continue
                
                # 요약 생성
                summary = self._summarize_booking(raw_text)
                results["summaries"].append({
                    "file": file_name,
                    "type": file_type,
                    "summary": summary
                })
                
                # 이벤트 추출
                events = self._extract_calendar_events(raw_text)
                results["events"].extend(events)
                
                # 경비 추출
                expenses = self._extract_expenses(raw_text)
                results["expenses"].extend(expenses)
                
                # 목적지 추출
                destination = self._extract_destination(raw_text)
                if destination:
                    results["destinations"].add(destination)
                
                print(f"   ✅ 완료: 이벤트 {len(events)}개, 경비 {len(expenses)}개\n")
                
            except Exception as e:
                print(f"   ❌ 오류: {e}\n")
                continue
        
        self.all_bookings = results["summaries"]
        self.all_events = results["events"]
        self.all_expenses = results["expenses"]
        
        return results
    
    def create_smart_reminders(self, travel_start_date: datetime) -> List[CalendarEvent]:
        """
        🔔 기능 2: 자동 알림 설정
        여행 전후로 스마트 알림 생성
        """
        print("\n" + "=" * 70)
        print("🔔 스마트 알림 생성 중...")
        print("=" * 70)
        
        reminders = []
        
        # D-7: 여행 준비 시작
        reminder_7days = CalendarEvent(
            title="🎒 여행 준비 시작",
            start_datetime=travel_start_date - timedelta(days=7),
            end_datetime=travel_start_date - timedelta(days=7) + timedelta(hours=1),
            description="여행 준비를 시작하세요!\n• 환전 준비\n• 여행자 보험 가입\n• 필요한 물품 리스트 작성",
            event_type="reminder",
            reminder_minutes=1440  # 1일 전
        )
        reminders.append(reminder_7days)
        
        # D-3: 여권 및 서류 확인
        reminder_3days = CalendarEvent(
            title="📋 여권 및 예약 확인",
            start_datetime=travel_start_date - timedelta(days=3),
            end_datetime=travel_start_date - timedelta(days=3) + timedelta(hours=1),
            description="출발 전 필수 체크!\n• 여권 유효기간 확인 (6개월 이상)\n• 항공권 출력 또는 모바일 티켓 준비\n• 호텔 예약 확인서 준비\n• ESTA/비자 확인",
            event_type="reminder",
            reminder_minutes=1440
        )
        reminders.append(reminder_3days)
        
        # D-1: 짐싸기
        reminder_1day = CalendarEvent(
            title="🧳 짐싸기 체크리스트",
            start_datetime=travel_start_date - timedelta(days=1),
            end_datetime=travel_start_date - timedelta(days=1) + timedelta(hours=2),
            description="짐싸기 체크리스트:\n• 여권, 항공권, 예약 확인서\n• 환전한 현금, 신용카드\n• 충전기, 어댑터\n• 상비약\n• 의류 (날씨 확인)\n• 세면도구",
            event_type="reminder",
            reminder_minutes=180
        )
        reminders.append(reminder_1day)
        
        # D-Day: 공항 출발
        reminder_departure = CalendarEvent(
            title="✈️ 공항 출발 시간",
            start_datetime=travel_start_date - timedelta(hours=3),
            end_datetime=travel_start_date - timedelta(hours=2),
            description="공항으로 출발하세요!\n• 국제선: 3시간 전 도착 권장\n• 여권, 항공권 최종 확인\n• 공항 교통편 확인",
            event_type="reminder",
            reminder_minutes=60
        )
        reminders.append(reminder_departure)
        
        print(f"✅ {len(reminders)}개의 스마트 알림 생성 완료\n")
        
        for reminder in reminders:
            print(f"   📌 {reminder.title}")
            print(f"      {reminder.start_datetime.strftime('%Y-%m-%d %H:%M')}\n")
        
        self.all_events.extend(reminders)
        return reminders
    
    def generate_travel_guide(self, destination: str) -> TravelGuide:
        """
        📖 기능 3: 여행 가이드 생성
        목적지별 날씨, 환율, 필수 회화, 팁 생성
        """
        print("\n" + "=" * 70)
        print(f"📖 여행 가이드 생성 중: {destination}")
        print("=" * 70)
        
        # 여행 시작 날짜 추출 (이벤트에서)
        travel_month = None
        if self.all_events:
            travel_month = self.all_events[0].start_datetime.strftime('%m월')
        
        guide_prompt = f"""
다음 여행 목적지에 대한 실용적인 여행 가이드를 생성해주세요: {destination}

다음 정보를 JSON 형식으로 제공하세요:
{{
  "destination": "{destination}",
  "weather_info": "{travel_month if travel_month else '여행 시기'}의 {destination} 날씨를 구체적으로 설명 (평균 기온 범위, 강수 확률, 추천 복장 포함)",
  "exchange_rate": "1 KRW = ? JPY 형식으로 작성. 예: 1,000 KRW = 약 110 JPY (2024년 기준)",
  "essential_phrases": [
    {{"korean": "안녕하세요", "local": "일본어", "pronunciation": "발음"}},
    {{"korean": "감사합니다", "local": "일본어", "pronunciation": "발음"}},
    {{"korean": "얼마예요?", "local": "일본어", "pronunciation": "발음"}},
    {{"korean": "도와주세요", "local": "일본어", "pronunciation": "발음"}},
    {{"korean": "화장실이 어디예요?", "local": "일본어", "pronunciation": "발음"}},
    {{"korean": "영어 할 수 있어요?", "local": "일본어", "pronunciation": "발음"}},
    {{"korean": "이거 주세요", "local": "일본어", "pronunciation": "발음"}}
  ],
  "local_tips": [
    "실용적인 현지 여행 팁 7개 이상"
  ],
  "emergency_contacts": [
    {{"service": "주일본 한국대사관", "number": "+81-3-3452-7611", "note": "긴급상황 시 24시간 연락 가능"}},
    {{"service": "주일본 한국대사관 영사콜센터", "number": "+81-3-3455-2601~3"}},
    {{"service": "일본 경찰 (긴급)", "number": "110"}},
    {{"service": "일본 구급차/소방서", "number": "119"}},
    {{"service": "도쿄 관광안내 (영어)", "number": "050-3816-2787"}},
    {{"service": "분실물 센터", "number": "03-3814-4151"}}
  ]
}}

중요:
- 환율은 반드시 KRW(한국 원) 기준으로 JPY(일본 엔)과 비교
- 날씨는 {travel_month if travel_month else '여행 시기'} 기준으로 구체적으로
- 긴급 연락처는 반드시 일본의 한국대사관 포함
- 실용적이고 최신 정보로 작성
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": guide_prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            guide_data = json.loads(response.choices[0].message.content)
            guide = TravelGuide(**guide_data)
            
            self.travel_guides[destination] = guide
            
            print(f"\n✅ {destination} 여행 가이드 생성 완료")
            print(f"\n🌤️  날씨: {guide.weather_info}")
            print(f"💱 환율: {guide.exchange_rate}")
            print(f"🗣️  필수 회화: {len(guide.essential_phrases)}개")
            print(f"💡 여행 팁: {len(guide.local_tips)}개")
            print(f"🆘 긴급 연락처: {len(guide.emergency_contacts)}개")
            
            return guide
            
        except Exception as e:
            print(f"❌ 가이드 생성 실패: {e}")
            return None
    
    def calculate_total_expenses(self) -> Dict[str, Any]:
        """
        💰 기능 4: 여행 경비 자동 집계
        모든 예약에서 추출한 금액을 카테고리별로 정리
        """
        print("\n" + "=" * 70)
        print("💰 여행 경비 집계")
        print("=" * 70)
        
        if not self.all_expenses:
            print("⚠️ 집계할 경비 정보가 없습니다.\n")
            return {"total": 0, "by_category": {}}
        
        # 카테고리별 집계
        by_category = {}
        total = 0
        
        for expense in self.all_expenses:
            category = expense.category
            amount = expense.amount
            
            if category not in by_category:
                by_category[category] = {
                    "total": 0,
                    "currency": expense.currency,
                    "items": []
                }
            
            by_category[category]["total"] += amount
            by_category[category]["items"].append({
                "description": expense.description,
                "amount": amount
            })
            total += amount
        
        # 결과 출력
        print(f"\n💵 총 여행 경비: {total:,.0f} 원\n")
        print("📊 카테고리별 상세:")
        
        for category, data in sorted(by_category.items(), key=lambda x: x[1]["total"], reverse=True):
            print(f"\n  {category}: {data['total']:,.0f} {data['currency']}")
            for item in data['items']:
                print(f"    • {item['description']}: {item['amount']:,.0f}")
        
        return {
            "total": total,
            "by_category": by_category
        }
    
    def _create_event_html(self, event) -> str:
        """개별 이벤트 HTML 생성"""
        # 이벤트 타입에 따른 아이콘
        icon = "✈️" if "항공" in event.title or "Flight" in event.title else \
               "🏨" if "호텔" in event.title or "Hotel" in event.title or "체크" in event.title else \
               "🚗" if "교통" in event.title or "Transfer" in event.title or "픽업" in event.title else \
               "🎢" if "디즈니" in event.title or "파크" in event.title else \
               "🍴" if "식사" in event.title or "레스토랑" in event.title else \
               "🔔" if event.event_type == "reminder" else \
               "📋"
        
        # 종료 시간이 있으면 표시
        time_display = event.start_datetime.strftime('%H:%M')
        if event.end_datetime and event.end_datetime != event.start_datetime:
            duration_hours = (event.end_datetime - event.start_datetime).total_seconds() / 3600
            if duration_hours < 24:  # 24시간 미만인 경우만 종료 시간 표시
                time_display = f"{event.start_datetime.strftime('%H:%M')} - {event.end_datetime.strftime('%H:%M')}"
        
        return f"""
        <div class="timeline-item">
            <div class="timeline-time">{time_display}</div>
            <div class="timeline-content">
                <h3>{icon} {event.title}</h3>
                {f'<p class="location">📍 {event.location}</p>' if event.location else ''}
                {f'<p class="description">{event.description[:200]}</p>' if event.description else ''}
            </div>
        </div>
        """
    
    def generate_web_interface_html(self, output_path: str = "output/travel_dashboard.html"):
        """
        🌐 기능 5: 웹 인터페이스 생성
        모든 정보를 한눈에 볼 수 있는 대시보드
        """
        print("\n" + "=" * 70)
        print("🌐 웹 대시보드 생성 중...")
        print("=" * 70)
        
        # 타임라인 생성 (모든 이벤트를 시간순 정렬)
        timeline_events = sorted(
            self.all_events,
            key=lambda x: x.start_datetime
        )
        
        # Day별로 이벤트 그룹핑
        events_by_day = {}
        if timeline_events:
            trip_start = timeline_events[0].start_datetime.date()
            
            for event in timeline_events:
                event_date = event.start_datetime.date()
                day_number = (event_date - trip_start).days + 1
                
                if event_date not in events_by_day:
                    events_by_day[event_date] = {
                        'day_number': day_number,
                        'date': event_date,
                        'morning': [],    # 06:00 ~ 11:59
                        'afternoon': [],  # 12:00 ~ 17:59
                        'evening': [],    # 18:00 ~ 23:59
                        'night': []       # 00:00 ~ 05:59
                    }
                
                # 시간대별 분류
                hour = event.start_datetime.hour
                if 6 <= hour < 12:
                    events_by_day[event_date]['morning'].append(event)
                elif 12 <= hour < 18:
                    events_by_day[event_date]['afternoon'].append(event)
                elif 18 <= hour < 24:
                    events_by_day[event_date]['evening'].append(event)
                else:
                    events_by_day[event_date]['night'].append(event)
        
        # HTML 생성
        timeline_html = ""
        
        for date in sorted(events_by_day.keys()):
            day_data = events_by_day[date]
            day_num = day_data['day_number']
            
            # 요일 한글 변환
            weekdays = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일']
            weekday = weekdays[date.weekday()]
            
            timeline_html += f"""
            <div class="day-container">
                <div class="day-header">
                    <h2>✈️ Day {day_num} — {date.strftime('%Y년 %m월 %d일')} ({weekday})</h2>
                </div>
            """
            
            # 새벽 (00:00 ~ 05:59)
            if day_data['night']:
                timeline_html += '<div class="time-period"><h3>🌙 새벽</h3>'
                for event in day_data['night']:
                    timeline_html += self._create_event_html(event)
                timeline_html += '</div>'
            
            # 오전 (06:00 ~ 11:59)
            if day_data['morning']:
                timeline_html += '<div class="time-period"><h3>🌅 오전</h3>'
                for event in day_data['morning']:
                    timeline_html += self._create_event_html(event)
                timeline_html += '</div>'
            
            # 오후 (12:00 ~ 17:59)
            if day_data['afternoon']:
                timeline_html += '<div class="time-period"><h3>☀️ 오후</h3>'
                for event in day_data['afternoon']:
                    timeline_html += self._create_event_html(event)
                timeline_html += '</div>'
            
            # 저녁 (18:00 ~ 23:59)
            if day_data['evening']:
                timeline_html += '<div class="time-period"><h3>🌆 저녁</h3>'
                for event in day_data['evening']:
                    timeline_html += self._create_event_html(event)
                timeline_html += '</div>'
            
            timeline_html += '</div>'  # day-container 종료
        
        # 경비 차트 데이터
        expense_data = self.calculate_total_expenses()
        expense_chart_data = []
        for category, data in expense_data.get("by_category", {}).items():
            expense_chart_data.append({
                "category": category,
                "amount": data["total"]
            })
        
        # 여행 가이드 HTML
        guides_html = ""
        for dest, guide in self.travel_guides.items():
            phrases_html = "".join([
                f'<li><strong>{p["korean"]}</strong> → {p["local"]} <em>({p["pronunciation"]})</em></li>'
                for p in guide.essential_phrases
            ])
            
            tips_html = "".join([f'<li>{tip}</li>' for tip in guide.local_tips])
            
            emergency_html = "".join([
                f'<div class="emergency-item">'
                f'<strong>{contact["service"]}</strong><br>'
                f'📞 <a href="tel:{contact["number"]}">{contact["number"]}</a>'
                f'{f"<br><em>{contact.get("note", "")}</em>" if contact.get("note") else ""}'
                f'</div>'
                for contact in guide.emergency_contacts
            ])
            
            guides_html += f"""
            <div class="guide-card">
                <h2>📍 {guide.destination}</h2>
                <div class="guide-section">
                    <h3>🌤️ 날씨 정보</h3>
                    <p>{guide.weather_info}</p>
                </div>
                <div class="guide-section">
                    <h3>💱 환율</h3>
                    <p>{guide.exchange_rate}</p>
                </div>
                <div class="guide-section">
                    <h3>🗣️ 필수 회화</h3>
                    <ul>{phrases_html}</ul>
                </div>
                <div class="guide-section">
                    <h3>💡 여행 팁</h3>
                    <ul>{tips_html}</ul>
                </div>
                <div class="guide-section emergency-section">
                    <h3>🆘 긴급 연락처</h3>
                    {emergency_html}
                </div>
            </div>
            """
        
        html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>✈️ 나의 여행 대시보드</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #667eea;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        
        .day-container {{
            background: #ffffff;
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            border-left: 5px solid #667eea;
        }}
        
        .day-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }}
        
        .day-header h2 {{
            margin: 0;
            font-size: 1.6em;
            color: white;
        }}
        
        .time-period {{
            margin: 20px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
        }}
        
        .time-period h3 {{
            color: #764ba2;
            font-size: 1.3em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e0e0e0;
        }}
        
        .timeline-item {{
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
            padding: 15px;
            background: white;
            border-radius: 10px;
            border-left: 4px solid #667eea;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .timeline-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }}
        
        .timeline-time {{
            flex-shrink: 0;
            width: 120px;
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
            padding-top: 2px;
        }}
        
        .timeline-content {{
            flex: 1;
        }}
        
        .timeline-content h3 {{
            margin: 0 0 8px 0;
            color: #333;
            font-size: 1.1em;
        }}
        
        .timeline-content .location {{
            color: #666;
            margin: 5px 0;
            font-size: 0.95em;
        }}
        
        .timeline-content .description {{
            color: #888;
            margin: 8px 0 0 0;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        
        .timeline-content h3 {{
            margin-bottom: 10px;
            color: #333;
        }}
        
        .timeline-content p {{
            color: #666;
            line-height: 1.6;
        }}
        
        .description {{
            font-size: 0.9em;
        }}
        
        .guide-card {{
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            margin-bottom: 20px;
        }}
        
        .guide-card h2 {{
            color: #667eea;
            margin-bottom: 20px;
        }}
        
        .guide-section {{
            margin-bottom: 20px;
        }}
        
        .guide-section h3 {{
            color: #764ba2;
            margin-bottom: 10px;
            font-size: 1.2em;
        }}
        
        .guide-section ul {{
            list-style-position: inside;
            line-height: 1.8;
        }}
        
        .guide-section li {{
            margin-bottom: 5px;
        }}
        
        .emergency-section {{
            background: #fff3cd;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #ff6b6b;
        }}
        
        .emergency-section h3 {{
            color: #dc3545;
        }}
        
        .emergency-item {{
            background: white;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 3px solid #dc3545;
        }}
        
        .emergency-item strong {{
            color: #dc3545;
            font-size: 1.05em;
        }}
        
        .emergency-item a {{
            color: #0066cc;
            text-decoration: none;
            font-weight: bold;
        }}
        
        .emergency-item a:hover {{
            text-decoration: underline;
        }}
        
        .emergency-item em {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .expense-item {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            background: #f8f9fa;
            margin-bottom: 10px;
            border-radius: 8px;
        }}
        
        .expense-category {{
            font-weight: bold;
            color: #667eea;
        }}
        
        .expense-amount {{
            color: #764ba2;
            font-weight: bold;
        }}
        
        @media (max-width: 768px) {{
            .stats {{
                grid-template-columns: 1fr;
            }}
            
            .timeline-item {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✈️ 나의 여행 대시보드</h1>
            <p>모든 여행 정보를 한눈에!</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>📋 예약 건수</h3>
                <div class="value">{len(self.all_bookings)}</div>
            </div>
            <div class="stat-card">
                <h3>📅 일정 개수</h3>
                <div class="value">{len(timeline_events)}</div>
            </div>
            <div class="stat-card">
                <h3>💰 총 경비</h3>
                <div class="value">{expense_data.get('total', 0):,.0f}원</div>
            </div>
            <div class="stat-card">
                <h3>🌍 목적지</h3>
                <div class="value">{len(self.travel_guides)}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📅 여행 타임라인</h2>
            {timeline_html if timeline_html else '<p>등록된 일정이 없습니다.</p>'}
        </div>
        
        <div class="section">
            <h2>💰 여행 경비 분석</h2>
            {"".join([f'<div class="expense-item"><span class="expense-category">{cat}</span><span class="expense-amount">{data["total"]:,.0f} {data["currency"]}</span></div>' for cat, data in expense_data.get("by_category", {}).items()]) if expense_data.get("by_category") else '<p>경비 정보가 없습니다.</p>'}
        </div>
        
        <div class="section">
            <h2>📖 여행 가이드</h2>
            {guides_html if guides_html else '<p>여행 가이드가 없습니다.</p>'}
        </div>
    </div>
</body>
</html>
        """
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"✅ 웹 대시보드 생성 완료: {output_path}")
        print(f"   브라우저에서 열어보세요!\n")
        
        return output_path
    
    # 내부 헬퍼 메서드들
    def _summarize_booking(self, raw_text: str) -> str:
        """예약 정보 요약"""
        system_prompt = """
You are a Travel Booking Summarization AI Agent.
Extract key information and create a clean, organized summary in Korean.
Include: booking type, dates, locations, costs, and important details.
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_text}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    
    def _extract_calendar_events(self, raw_text: str) -> List[CalendarEvent]:
        """캘린더 이벤트 추출"""
        extraction_prompt = f"""
Extract calendar events from this booking confirmation:

{raw_text}

Return JSON with this structure:
{{
  "events": [
    {{
      "title": "Flight ICN→NRT",
      "start_datetime": "2026-04-02T10:30:00",
      "end_datetime": "2026-04-02T14:30:00",
      "location": "Tokyo",
      "description": "Booking ref: ABC123",
      "reminder_minutes": 180
    }}
  ]
}}

CRITICAL RULES:
- Use the EXACT year, month, and date from the booking text
- If the booking mentions "2026년 4월 2일" use "2026-04-02"
- DO NOT assume or change the year
- Only include events with explicit date/time
- Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS)
- Flight: 180min reminder, Hotel: 1440min, Transport: 60min
- Sort events chronologically

Example dates to look for:
- "2026년 4월 2일", "4월 2일", "April 2, 2026"
- "2026-04-02", "2026/04/02"
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": extraction_prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            events = []
            
            for e in result.get("events", []):
                try:
                    start_dt = datetime.fromisoformat(e["start_datetime"].replace('Z', ''))
                    end_dt = datetime.fromisoformat(e["end_datetime"].replace('Z', ''))
                    
                    events.append(CalendarEvent(
                        title=e["title"],
                        start_datetime=start_dt,
                        end_datetime=end_dt,
                        location=e.get("location", ""),
                        description=e.get("description", ""),
                        reminder_minutes=e.get("reminder_minutes", 60)
                    ))
                except Exception as parse_error:
                    print(f"   ⚠️ 이벤트 파싱 실패: {parse_error}")
                    continue
            
            # 시간순 정렬
            events.sort(key=lambda x: x.start_datetime)
            return events
        except Exception as e:
            print(f"   ⚠️ 이벤트 추출 오류: {e}")
            return []
    
    def _extract_expenses(self, raw_text: str) -> List[TravelExpense]:
        """경비 정보 추출"""
        expense_prompt = f"""
Extract all costs from this booking:

{raw_text}

Return JSON:
{{
  "expenses": [
    {{
      "category": "항공",
      "amount": 500000,
      "currency": "KRW",
      "description": "ICN-NRT round trip"
    }}
  ]
}}

Categories: 항공, 숙박, 교통, 식사, 투어, 기타
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": expense_prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return [TravelExpense(**e) for e in result.get("expenses", [])]
        except:
            return []
    
    def _extract_destination(self, raw_text: str) -> Optional[str]:
        """목적지 추출 (중복 제거 및 정규화)"""
        dest_prompt = f"""
Extract the main travel destination from this booking:

{raw_text}

Return JSON with the MAIN destination only (city or region level, not both).
Example: {{"destination": "도쿄, 일본"}} or {{"destination": "오사카, 일본"}}

Important: Return only ONE main destination, not multiple similar ones.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": dest_prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("destination")
        except:
            return None
    
    def create_ics_file(self, output_path: str = "output/complete_travel.ics") -> str:
        """모든 이벤트를 ICS 파일로 생성"""
        if not ICALENDAR_AVAILABLE or not self.all_events:
            return ""
        
        cal = Calendar()
        cal.add('prodid', '-//Ultimate Travel Agent//Complete Schedule//KR')
        cal.add('version', '2.0')
        
        for event_data in self.all_events:
            event = Event()
            event.add('summary', event_data.title)
            event.add('dtstart', event_data.start_datetime)
            event.add('dtend', event_data.end_datetime)
            
            if event_data.location:
                event.add('location', vText(event_data.location))
            
            if event_data.description:
                event.add('description', vText(event_data.description))
            
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('trigger', timedelta(minutes=-event_data.reminder_minutes))
            event.add_component(alarm)
            
            cal.add_component(event)
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(cal.to_ical())
        
        return output_path
    
    def add_all_to_google_calendar(self, credentials_path: str = 'credentials.json') -> bool:
        """모든 이벤트를 Google Calendar에 추가"""
        if not GOOGLE_CALENDAR_AVAILABLE or not self.all_events:
            return False
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(credentials_path):
                    print(f"❌ {credentials_path} 파일이 없습니다.")
                    return False
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0, open_browser=True)
                except Exception as e:
                    print(f"⚠️ 인증 실패: {e}")
                    return False
            
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            
            print(f"\n📅 Google Calendar에 {len(self.all_events)}개 이벤트 추가 중...\n")
            
            for event_data in self.all_events:
                event = {
                    'summary': event_data.title,
                    'location': event_data.location,
                    'description': event_data.description,
                    'start': {
                        'dateTime': event_data.start_datetime.isoformat(),
                        'timeZone': 'Asia/Seoul',
                    },
                    'end': {
                        'dateTime': event_data.end_datetime.isoformat(),
                        'timeZone': 'Asia/Seoul',
                    },
                    'reminders': {
                        'useDefault': False,
                        'overrides': [
                            {'method': 'popup', 'minutes': event_data.reminder_minutes},
                            {'method': 'email', 'minutes': event_data.reminder_minutes},
                        ],
                    },
                    'colorId': '9' if event_data.event_type == 'booking' else '11'
                }
                
                service.events().insert(calendarId='primary', body=event).execute()
                print(f"  ✅ {event_data.title}")
            
            print("\n✅ Google Calendar 연동 완료!")
            return True
            
        except Exception as e:
            print(f"❌ Google Calendar 추가 실패: {e}")
            return False


def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("✈️  ULTIMATE TRAVEL AI AGENT")
    print("=" * 70)
    print("\n🚀 5가지 강력한 기능:")
    print("   1️⃣  여러 예약 파일 일괄 처리 (TXT, PDF)")
    print("   2️⃣  스마트 알림 자동 생성")
    print("   3️⃣  AI 여행 가이드")
    print("   4️⃣  여행 경비 자동 집계")
    print("   5️⃣  웹 대시보드 생성\n")
    
    print("📄 지원 파일 형식:")
    print("   • TXT 파일: 예약 확인서 텍스트")
    print("   • PDF 파일: 전자 영수증, 예약 확인서")
    if not PDF_AVAILABLE:
        print("   ⚠️ PDF 지원을 위해 설치: pip install PyPDF2")
    print()
    
    # Agent 초기화
    agent = UltimateTravelAgent()
    
    # 1단계: 예약 파일 일괄 처리
    print("📁 예약 파일이 있는 폴더를 지정하세요")
    folder_path = input("   폴더 경로 (기본값: bookings): ").strip() or "bookings"
    
    # bookings 폴더가 없으면 생성하고 안내
    if not os.path.exists(folder_path):
        Path(folder_path).mkdir(parents=True, exist_ok=True)
        print(f"\n⚠️  {folder_path} 폴더가 생성되었습니다.")
        print(f"   여행 예약 확인서 파일들을 이 폴더에 넣어주세요.")
        print(f"   지원 형식: .txt, .pdf")
        
        # 단일 파일 모드로 전환
        single_file = input("\n단일 파일로 테스트하시겠습니까? (y/n): ").lower().strip()
        if single_file == 'y':
            file_path = input("파일 경로 입력 (.txt 또는 .pdf): ").strip()
            if os.path.exists(file_path):
                # 파일을 bookings 폴더로 복사
                import shutil
                dest_path = os.path.join(folder_path, Path(file_path).name)
                shutil.copy(file_path, dest_path)
                print(f"✅ 파일을 {dest_path}로 복사했습니다.")
            else:
                print("❌ 파일을 찾을 수 없습니다.")
                return
        else:
            print("프로그램을 종료합니다.")
            return
    
    # 예약 파일 처리
    results = agent.process_booking_folder(folder_path)
    
    if not results.get("events"):
        print("\n⚠️ 처리할 이벤트가 없습니다. 프로그램을 종료합니다.")
        return
    
    # 2단계: 스마트 알림 생성
    if results["events"]:
        first_event_date = min([e.start_datetime for e in results["events"]])
        print(f"\n여행 시작일: {first_event_date.strftime('%Y-%m-%d')}")
        
        create_reminders = input("스마트 알림을 생성하시겠습니까? (y/n): ").lower().strip()
        if create_reminders == 'y':
            agent.create_smart_reminders(first_event_date)
    
    # 3단계: 여행 가이드 생성
    if results["destinations"]:
        # 중복 제거 및 정규화
        unique_destinations = set()
        for dest in results["destinations"]:
            # "우라야스 시, 일본"과 "도쿄, 일본"을 "도쿄, 일본"으로 통합
            if dest:
                # 메인 도시로 정규화
                if "우라야스" in dest or "디즈니" in dest:
                    unique_destinations.add("도쿄, 일본")
                else:
                    unique_destinations.add(dest)
        
        if unique_destinations:
            print(f"\n발견된 목적지: {', '.join(unique_destinations)}")
            create_guide = input("여행 가이드를 생성하시겠습니까? (y/n): ").lower().strip()
            
            if create_guide == 'y':
                for destination in unique_destinations:
                    agent.generate_travel_guide(destination)
    
    # 4단계: 경비 집계
    if results["expenses"]:
        expense_summary = agent.calculate_total_expenses()
    
    # 5단계: 웹 대시보드 생성
    print("\n" + "=" * 70)
    create_web = input("웹 대시보드를 생성하시겠습니까? (y/n): ").lower().strip()
    
    if create_web == 'y':
        dashboard_path = agent.generate_web_interface_html()
        
        # 브라우저로 열기
        open_browser = input("브라우저에서 바로 열어보시겠습니까? (y/n): ").lower().strip()
        if open_browser == 'y':
            import webbrowser
            webbrowser.open(f'file://{os.path.abspath(dashboard_path)}')
    
    # 6단계: ICS 파일 생성
    if ICALENDAR_AVAILABLE:
        print("\n" + "=" * 70)
        create_ics = input("ICS 캘린더 파일을 생성하시겠습니까? (y/n): ").lower().strip()
        
        if create_ics == 'y':
            ics_path = agent.create_ics_file()
            print(f"✅ ICS 파일: {ics_path}")
    
    # 7단계: Google Calendar 연동
    if GOOGLE_CALENDAR_AVAILABLE:
        print("\n" + "=" * 70)
        sync_google = input("Google Calendar에 동기화하시겠습니까? (y/n): ").lower().strip()
        
        if sync_google == 'y':
            agent.add_all_to_google_calendar()
    
    # 완료 메시지
    print("\n" + "=" * 70)
    print("🎉 모든 작업이 완료되었습니다!")
    print("=" * 70)
    print(f"\n📊 처리 결과:")
    print(f"   • 예약 파일: {len(results['summaries'])}개")
    print(f"   • 캘린더 이벤트: {len(agent.all_events)}개")
    print(f"   • 여행 경비: {len(agent.all_expenses)}건")
    print(f"   • 여행 가이드: {len(agent.travel_guides)}개 목적지")
    
    print(f"\n📁 생성된 파일:")
    print(f"   • output/complete_travel.ics")
    print(f"   • output/travel_dashboard.html")
    print(f"\n✨ 즐거운 여행 되세요! ✨\n")


if __name__ == "__main__":
    main()