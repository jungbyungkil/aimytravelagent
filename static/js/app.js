/* ═══════════════════════════════════════
   AI Travel — Frontend Logic
   Trip.com급 사용자 경험
═══════════════════════════════════════ */

// ── State ──────────────────────────────
const state = {
  currentTab: 'flights',
  flightResults: [],
  hotelResults: [],
  chatHistory: [],
  chatOpen: false,
  bookings: [],
  resultType: null,  // 'flight' | 'hotel'
  recommendations: [],
};

// ── Initialize ─────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setDefaultDates();
  setupInterestTags();
  loadBookings();

  // Backdrop clicks to close modals
  document.getElementById('bookings-modal')?.addEventListener('click', e => {
    if (e.target.id === 'bookings-modal') closeBookingsModal();
  });
  document.getElementById('itinerary-modal')?.addEventListener('click', e => {
    if (e.target.id === 'itinerary-modal') closeItineraryModal();
  });
  document.getElementById('search-modal')?.addEventListener('click', e => {
    if (e.target.id === 'search-modal') closeSearchModal();
  });
});

function setDefaultDates() {
  const addDays = (n) => {
    const d = new Date(); d.setDate(d.getDate() + n);
    return d.toISOString().split('T')[0];
  };
  const fDate = document.getElementById('f-date');
  const hCi   = document.getElementById('h-checkin');
  const hCo   = document.getElementById('h-checkout');
  if (fDate) fDate.value = addDays(7);
  if (hCi)   hCi.value   = addDays(7);
  if (hCo)   hCo.value   = addDays(10);
}

function setupInterestTags() {
  document.querySelectorAll('.interest-tag').forEach(btn => {
    btn.addEventListener('click', () => btn.classList.toggle('active'));
  });
}

// ── Tab Switching ──────────────────────
const TAB_TITLES = { flights: '✈️ 항공편 검색', hotels: '🏨 호텔 검색', planner: '🤖 AI 일정 플래너' };

function switchTab(tab) {
  state.currentTab = tab;
  ['flights', 'hotels', 'planner'].forEach(t => {
    document.getElementById(`panel-${t}`)?.classList.toggle('hidden', t !== tab);
    document.getElementById(`tab-${t}`)?.classList.toggle('active', t === tab);
  });
  const titleEl = document.getElementById('search-modal-title');
  if (titleEl) titleEl.textContent = TAB_TITLES[tab] || '🔎 검색';
}

// ── Search Modal (팝업) ─────────────────
function openSearchModal(tab = 'flights', opts = {}) {
  switchTab(tab);
  // 추천 카드에서 넘어온 목적지/도시 프리필
  if (opts.destination) {
    const fd = document.getElementById('f-dest');   if (fd) fd.value = opts.destination;
    const hc = document.getElementById('h-city');   if (hc) hc.value = opts.destination;
    const pd = document.getElementById('p-dest');   if (pd) pd.value = opts.destination;
  }
  // 이전 검색 결과 감추기
  document.getElementById('results-section')?.classList.add('hidden');
  const modal = document.getElementById('search-modal');
  modal?.classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeSearchModal() {
  document.getElementById('search-modal')?.classList.add('hidden');
  document.body.style.overflow = '';
}

// ── Load Destinations ──────────────────
async function loadDestinations() {
  try {
    const res  = await fetch('/api/search/destinations');
    const data = await res.json();
    renderDestinations(data.destinations || []);
  } catch (_) {
    document.getElementById('destinations-grid').innerHTML =
      '<p class="col-span-4 text-center text-gray-300 py-4">목적지 정보를 불러올 수 없습니다.</p>';
  }
}

function renderDestinations(destinations) {
  const grid = document.getElementById('destinations-grid');
  if (!grid) return;
  grid.innerHTML = destinations.map(dest => `
    <div class="destination-card group cursor-pointer rounded-2xl overflow-hidden shadow-md hover:shadow-xl transition-all duration-300"
      onclick="quickSearch('${dest.city}')">
      <div class="relative h-52 overflow-hidden">
        <img src="${dest.image}" alt="${dest.city}"
          class="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          loading="lazy" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent"></div>
        <span class="absolute top-3 left-3 text-xs px-2 py-1 rounded-full text-white font-semibold"
          style="background-color:${dest.tag_color};">${dest.tag}</span>
        <div class="absolute bottom-0 left-0 right-0 p-4 text-white">
          <h3 class="font-bold text-lg leading-tight">${dest.city}</h3>
          <p class="text-xs text-gray-300">${dest.country}</p>
          <p class="mt-1 text-sm font-semibold text-orange-300">
            항공 ₩${fmtNum(dest.min_price)}~
          </p>
        </div>
      </div>
    </div>
  `).join('');
}

// ── Quick Search (from destination cards) ─
function quickSearch(city) {
  switchTab('hotels');
  const hCity = document.getElementById('h-city');
  if (hCity) hCity.value = city;
  searchHotels();
}

// ─────────────────────────────────────────
// FLIGHT SEARCH
// ─────────────────────────────────────────
async function searchFlights() {
  const origin = document.getElementById('f-origin')?.value?.trim();
  const dest   = document.getElementById('f-dest')?.value?.trim();
  const date   = document.getElementById('f-date')?.value;
  const pax    = document.getElementById('f-pax')?.value   || '1';
  const cabin  = document.getElementById('f-cabin')?.value || 'economy';

  if (!origin || !dest) { showToast('⚠️ 출발지와 도착지를 입력해주세요.'); return; }
  if (!date)             { showToast('⚠️ 출발 날짜를 선택해주세요.'); return; }

  setFlightBtnState(true);
  try {
    const res  = await fetch('/api/search/flights', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ origin, destination: dest, departure_date: date,
        passengers: +pax, cabin_class: cabin }),
    });
    const data = await res.json();
    state.flightResults = data.results || [];
    state.resultType = 'flight';
    renderFlightResults(data);
  } catch (e) {
    showToast('❌ 검색 중 오류가 발생했습니다.');
  } finally {
    setFlightBtnState(false);
  }
}

function setFlightBtnState(loading) {
  const icon = document.getElementById('flight-btn-icon');
  const txt  = document.getElementById('flight-btn-text');
  if (icon) icon.textContent = loading ? '⏳' : '🔍';
  if (txt)  txt.textContent  = loading ? '검색 중…' : '항공편 검색';
}

function renderFlightResults(data) {
  const results = data.results || [];
  const params  = data.search_params || {};
  showResultsSection(
    `✈️ ${params.origin || ''} → ${params.destination || ''} 항공편`,
    `${results.length}개의 항공편 · ${params.departure_date || ''} · ${params.passengers || 1}명`
  );

  if (!results.length) {
    document.getElementById('results-grid').innerHTML = '';
    document.getElementById('results-empty').classList.remove('hidden');
    return;
  }
  document.getElementById('results-empty').classList.add('hidden');

  document.getElementById('results-grid').innerHTML = results.map((f, i) => `
    <div class="result-card" style="animation-delay:${i * 0.06}s">
      <div class="p-5">
        <div class="flex items-center justify-between mb-4">
          <div>
            <span class="font-bold text-gray-800 text-sm">${f.airline}</span>
            <span class="ml-2 text-xs text-gray-400">${f.id}</span>
          </div>
          <div class="flex gap-1 flex-wrap">
            <span class="flight-badge badge-direct">직항</span>
            <span class="flight-badge ${cabinBadgeClass(f.cabin_class)}">${f.cabin_class}</span>
          </div>
        </div>
        <div class="flex items-center justify-between mb-4">
          <div class="text-center">
            <div class="text-2xl font-black text-gray-800">${f.departure.time}</div>
            <div class="text-xs text-gray-400 mt-1">${f.departure.airport}</div>
            <div class="text-xs text-gray-500 leading-tight">${f.departure.city}</div>
          </div>
          <div class="flex-1 mx-3 text-center">
            <div class="text-xs text-gray-400 mb-1">${f.duration}</div>
            <div class="flex items-center gap-1">
              <div class="h-px flex-1 bg-gray-200"></div>
              <span class="text-blue-500">✈</span>
              <div class="h-px flex-1 bg-gray-200"></div>
            </div>
            <div class="text-xs text-green-600 font-medium mt-1">직항</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-black text-gray-800">${f.arrival.time}</div>
            <div class="text-xs text-gray-400 mt-1">${f.arrival.airport}</div>
            <div class="text-xs text-gray-500 leading-tight">${f.arrival.city}</div>
          </div>
        </div>
        <div class="flex flex-wrap gap-1 mb-4">
          <span class="amenity-tag">🧳 ${f.baggage}</span>
          ${f.meal ? '<span class="amenity-tag">🍽 기내식</span>' : ''}
          ${f.refundable ? '<span class="amenity-tag">💰 환불가능</span>' : '<span class="amenity-tag text-red-400">⚠️ 환불불가</span>'}
          <span class="amenity-tag">💺 잔여 ${f.seats_left}석</span>
        </div>
        <div class="flex items-end justify-between pt-3 border-t border-gray-100">
          <div>
            <div class="price-main">₩${fmtNum(f.total_price)}</div>
            <div class="price-sub">${params.passengers > 1 ? `1인 ₩${fmtNum(f.price_per_person)} · ${params.passengers}명` : '총 금액'}</div>
          </div>
          <button onclick="saveBooking('flight', ${i})"
            class="btn-orange px-5 py-2.5 rounded-xl text-sm font-bold">
            예약하기
          </button>
        </div>
      </div>
    </div>
  `).join('');

  document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

function cabinBadgeClass(cabin) {
  if (!cabin) return 'badge-economy';
  if (cabin.includes('비즈')) return 'badge-business';
  if (cabin.includes('퍼스')) return 'badge-first';
  return 'badge-economy';
}

// ─────────────────────────────────────────
// HOTEL SEARCH
// ─────────────────────────────────────────
async function searchHotels() {
  const city = document.getElementById('h-city')?.value?.trim();
  const ci   = document.getElementById('h-checkin')?.value;
  const co   = document.getElementById('h-checkout')?.value;

  if (!city)       { showToast('⚠️ 도시를 입력해주세요.'); return; }
  if (!ci || !co)  { showToast('⚠️ 체크인/체크아웃 날짜를 선택해주세요.'); return; }

  showLoading('호텔 검색 중…');
  try {
    const res  = await fetch('/api/search/hotels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ city, check_in: ci, check_out: co, guests: 2, rooms: 1 }),
    });
    const data = await res.json();
    state.hotelResults = data.results || [];
    state.resultType = 'hotel';
    renderHotelResults(data);
  } catch (e) {
    showToast('❌ 검색 중 오류가 발생했습니다.');
  } finally {
    hideLoading();
  }
}

function renderHotelResults(data) {
  const results = data.results || [];
  const params  = data.search_params || {};
  const nights  = results[0]?.nights || 1;

  showResultsSection(
    `🏨 ${params.city || ''} 호텔`,
    `${results.length}개의 호텔 · ${params.check_in || ''} ~ ${params.check_out || ''} (${nights}박)`
  );

  if (!results.length) {
    document.getElementById('results-grid').innerHTML = '';
    document.getElementById('results-empty').classList.remove('hidden');
    return;
  }
  document.getElementById('results-empty').classList.add('hidden');

  document.getElementById('results-grid').innerHTML = results.map((h, i) => `
    <div class="result-card" style="animation-delay:${i * 0.06}s">
      <div class="relative h-44 overflow-hidden">
        <img src="${h.image}" alt="${h.name}" class="w-full h-full object-cover" loading="lazy" />
        <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
        ${h.free_cancellation ? '<span class="absolute top-3 left-3 bg-green-500 text-white text-xs px-2 py-1 rounded-full font-semibold">무료 취소</span>' : ''}
        ${h.breakfast_included ? '<span class="absolute top-3 right-3 bg-orange-500 text-white text-xs px-2 py-1 rounded-full font-semibold">조식 포함</span>' : ''}
      </div>
      <div class="p-5">
        <div class="flex items-start justify-between mb-2">
          <div class="flex-1 mr-2">
            <h3 class="font-bold text-gray-800 text-sm leading-tight">${h.name}</h3>
            <p class="text-xs text-gray-500 mt-0.5">📍 ${h.location}</p>
          </div>
          <span class="rating-chip flex-shrink-0">${h.rating}</span>
        </div>
        <div class="flex items-center gap-1 mb-1">
          <span class="stars">${'★'.repeat(h.stars)}${'☆'.repeat(5 - h.stars)}</span>
          <span class="text-xs text-gray-400">(${fmtNum(h.reviews)}개 리뷰)</span>
        </div>
        <p class="text-xs text-blue-600 font-medium mb-3 italic">"${h.highlight}"</p>
        <div class="flex flex-wrap gap-1 mb-4">
          ${h.amenities.slice(0, 4).map(a => `<span class="amenity-tag">${a}</span>`).join('')}
          ${h.amenities.length > 4 ? `<span class="amenity-tag">+${h.amenities.length - 4}개</span>` : ''}
        </div>
        <div class="flex items-end justify-between pt-3 border-t border-gray-100">
          <div>
            <div class="price-main">₩${fmtNum(h.price_per_night)}<span class="text-sm font-normal text-gray-400">/박</span></div>
            <div class="price-sub">총 ${h.nights}박 ₩${fmtNum(h.total_price)}</div>
          </div>
          <button onclick="saveBooking('hotel', ${i})"
            class="btn-orange px-5 py-2.5 rounded-xl text-sm font-bold">
            예약하기
          </button>
        </div>
      </div>
    </div>
  `).join('');

  document.getElementById('results-section').scrollIntoView({ behavior: 'smooth' });
}

function showResultsSection(title, subtitle) {
  document.getElementById('results-section').classList.remove('hidden');
  document.getElementById('results-title').textContent  = title;
  document.getElementById('results-subtitle').textContent = subtitle;
}

// ── Sort Results ───────────────────────
function sortResults() {
  const sort = document.getElementById('sort-select')?.value || 'price';
  const sorter = (a, b, key, desc = false) => desc ? b[key] - a[key] : a[key] - b[key];

  if (state.resultType === 'flight') {
    if (sort === 'price')       state.flightResults.sort((a, b) => a.total_price - b.total_price);
    if (sort === 'price_desc')  state.flightResults.sort((a, b) => b.total_price - a.total_price);
    if (sort === 'rating')      state.flightResults.sort((a, b) => b.airline_rating - a.airline_rating);
    renderFlightResults({ results: state.flightResults, search_params: {} });
  } else if (state.resultType === 'hotel') {
    if (sort === 'price')       state.hotelResults.sort((a, b) => a.price_per_night - b.price_per_night);
    if (sort === 'price_desc')  state.hotelResults.sort((a, b) => b.price_per_night - a.price_per_night);
    if (sort === 'rating')      state.hotelResults.sort((a, b) => b.rating - a.rating);
    renderHotelResults({ results: state.hotelResults, search_params: {} });
  }
}

// ─────────────────────────────────────────
// AI CHAT
// ─────────────────────────────────────────
function toggleChat() {
  state.chatOpen = !state.chatOpen;
  document.getElementById('chat-panel')?.classList.toggle('hidden', !state.chatOpen);
  if (state.chatOpen) document.getElementById('chat-input')?.focus();
}

function sendQuickMsg(msg) {
  const input = document.getElementById('chat-input');
  if (input) input.value = msg;
  sendChat();
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const msg   = input?.value?.trim();
  if (!msg) return;

  appendChatMessage('user', msg);
  state.chatHistory.push({ role: 'user', content: msg });
  input.value = '';

  const typingId = showTyping();

  try {
    const res  = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, history: state.chatHistory.slice(-10) }),
    });
    const data = await res.json();
    removeTyping(typingId);

    const reply = data.response || (data.error ? `❌ ${data.error}\n\n💡 .env 파일에 ANTHROPIC_API_KEY를 설정해주세요.` : '오류가 발생했습니다.');
    appendChatMessage('assistant', reply);
    if (data.response) state.chatHistory.push({ role: 'assistant', content: data.response });

  } catch (e) {
    removeTyping(typingId);
    appendChatMessage('assistant', '❌ 연결 오류가 발생했습니다. 서버를 확인해주세요.');
  }
}

function appendChatMessage(role, content) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}`;
  const html = content
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n/g, '<br/>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  div.innerHTML = `<div class="chat-bubble ${role === 'assistant' ? 'assistant-bubble' : 'user-bubble'}">${html}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function showTyping() {
  const container = document.getElementById('chat-messages');
  const id = 'typing-' + Date.now();
  const div = document.createElement('div');
  div.id = id;
  div.className = 'chat-msg assistant';
  div.innerHTML = `<div class="chat-bubble assistant-bubble typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTyping(id) { document.getElementById(id)?.remove(); }

// ─────────────────────────────────────────
// AI ITINERARY
// ─────────────────────────────────────────
async function generateItinerary() {
  const dest     = document.getElementById('p-dest')?.value?.trim();
  const duration = document.getElementById('p-duration')?.value || '7';
  const budget   = document.getElementById('p-budget')?.value   || 'medium';

  if (!dest) { showToast('⚠️ 여행지를 입력해주세요.'); return; }

  const interests = [...document.querySelectorAll('.interest-tag.active')].map(t => t.dataset.value);
  const today = new Date().toISOString().split('T')[0];

  showLoading(`🤖 Claude AI가 ${dest} ${duration}일 일정을 생성 중…`);

  try {
    const res  = await fetch('/api/ai/itinerary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ destination: dest, duration_days: +duration,
        start_date: today, interests, budget }),
    });
    const data = await res.json();
    hideLoading();

    if (data.success && data.itinerary) {
      renderItinerary(data.itinerary);
    } else {
      showToast(`❌ ${data.error || '일정 생성에 실패했습니다.'}`);
    }
  } catch (e) {
    hideLoading();
    showToast('❌ 서버 연결 오류가 발생했습니다.');
  }
}

function renderItinerary(itin) {
  document.getElementById('itinerary-title').textContent =
    `🗺️ ${itin.title || itin.destination + ' 여행 일정'}`;

  const fs = itin.flight_summary || null;
  const hs = itin.hotel_summary || null;

  // ── 상단 요약 바 ─
  let html = `
    <div class="itin-doc">
    <div class="itin-summary">
      <div class="itin-summary-item"><span class="itin-summary-ico">📍</span><div><div class="itin-summary-val">${itin.destination || '-'}</div><div class="itin-summary-key">목적지</div></div></div>
      <div class="itin-summary-item"><span class="itin-summary-ico">🗓️</span><div><div class="itin-summary-val">${(itin.duration || (itin.days||[]).length)}일</div><div class="itin-summary-key">여행 기간</div></div></div>
      <div class="itin-summary-item"><span class="itin-summary-ico">💰</span><div><div class="itin-summary-val">${itin.budget_level || '중간'}</div><div class="itin-summary-key">예산 수준</div></div></div>
      <div class="itin-summary-item"><span class="itin-summary-ico">💳</span><div><div class="itin-summary-val itin-cost">${itin.total_estimated_cost || '-'}</div><div class="itin-summary-key">총 예상 비용</div></div></div>
    </div>
  `;

  // ── 항공 / 호텔 요약 카드 ─
  if (fs || hs) {
    html += `<div class="itin-cards">`;
    if (fs) {
      const ob = fs.outbound || {}, ib = fs.inbound || {};
      html += `
        <div class="itin-card itin-card-flight">
          <div class="itin-card-head">✈️ 항공편 <span>${fs.airline || ''}</span></div>
          ${ob.route ? `
          <div class="itin-leg">
            <span class="itin-leg-tag">가는 편</span>
            <div class="itin-leg-route">${ob.route}</div>
            <div class="itin-leg-time"><strong>${ob.depart || ''}</strong> → <strong>${ob.arrive || ''}</strong></div>
            ${ob.duration ? `<div class="itin-leg-dur">⏱ ${ob.duration}</div>` : ''}
          </div>` : ''}
          ${ib.route ? `
          <div class="itin-leg">
            <span class="itin-leg-tag">오는 편</span>
            <div class="itin-leg-route">${ib.route}</div>
            <div class="itin-leg-time"><strong>${ib.depart || ''}</strong> → <strong>${ib.arrive || ''}</strong></div>
            ${ib.duration ? `<div class="itin-leg-dur">⏱ ${ib.duration}</div>` : ''}
          </div>` : ''}
        </div>`;
    }
    if (hs) {
      html += `
        <div class="itin-card itin-card-hotel">
          <div class="itin-card-head">🏨 숙소 <span>${hs.grade || ''}</span></div>
          <div class="itin-hotel-name">${hs.name || '추천 호텔'}</div>
          ${hs.area ? `<div class="itin-hotel-area">📍 ${hs.area}</div>` : ''}
          <div class="itin-hotel-times">
            <div><span>체크인</span><strong>${hs.check_in || '15:00'}</strong></div>
            <div><span>체크아웃</span><strong>${hs.check_out || '11:00'}</strong></div>
            ${hs.nights ? `<div><span>숙박</span><strong>${hs.nights}박</strong></div>` : ''}
          </div>
        </div>`;
    }
    html += `</div>`;
  }

  // ── 하이라이트 ─
  if (itin.highlights?.length) {
    html += `<div class="itin-highlights"><h3>✨ 하이라이트</h3><div class="itin-chips">
      ${itin.highlights.map(h => `<span class="itin-chip">${h}</span>`).join('')}
    </div></div>`;
  }

  // ── 일자별 타임라인 ─
  const typeIcon = {
    '항공': '✈️', '숙박': '🏨', '체크인': '🔑', '체크아웃': '🧳',
    '관광': '📷', '식사': '🍽', '교통': '🚌', '쇼핑': '🛍', '액티비티': '🏄', '예술': '🎨', '야경': '🌃',
  };

  (itin.days || []).forEach(day => {
    html += `
      <div class="itin-day">
        <div class="itin-day-head">
          <div class="itin-day-no">Day ${day.day}</div>
          <div class="itin-day-meta">
            <div class="itin-day-title">${day.title || day.day + '일차'}</div>
            <div class="itin-day-sub">${day.date ? day.date + ' · ' : ''}${day.theme || ''}</div>
          </div>
          ${day.estimated_cost ? `<div class="itin-day-cost">${day.estimated_cost}</div>` : ''}
        </div>
        <div class="itin-timeline">
          ${(day.activities || []).map(act => {
            const t = act.type || '관광';
            return `
            <div class="itin-tl-item type-${t}">
              <div class="itin-tl-time">${act.time || ''}</div>
              <div class="itin-tl-dot"><span>${typeIcon[t] || '📍'}</span></div>
              <div class="itin-tl-body">
                <div class="itin-tl-title">${act.title || ''} <span class="itin-tl-badge">${t}</span></div>
                ${act.description ? `<div class="itin-tl-desc">${act.description}</div>` : ''}
                <div class="itin-tl-meta">
                  ${act.duration ? `<span>⏱ ${act.duration}</span>` : ''}
                  ${act.cost ? `<span>💰 ${act.cost}</span>` : ''}
                  ${act.tips ? `<span class="itin-tl-tip">💡 ${act.tips}</span>` : ''}
                </div>
              </div>
            </div>`;
          }).join('')}
        </div>
        ${day.meals ? `
          <div class="itin-meals">
            <span class="itin-meals-label">🍴 추천 식사</span>
            ${day.meals.breakfast ? `<span>🌅 ${day.meals.breakfast}</span>` : ''}
            ${day.meals.lunch     ? `<span>☀️ ${day.meals.lunch}</span>`     : ''}
            ${day.meals.dinner    ? `<span>🌙 ${day.meals.dinner}</span>`    : ''}
          </div>` : ''}
      </div>
    `;
  });

  // ── 꿀팁 / 시기 / 날씨 ─
  if (itin.travel_tips?.length) {
    html += `<div class="itin-tips"><h3>💡 여행 꿀팁</h3><ul>
      ${itin.travel_tips.map(t => `<li>${t}</li>`).join('')}
    </ul></div>`;
  }
  if (itin.best_time_to_visit || itin.weather_info) {
    html += `<div class="itin-foot-grid">
      ${itin.best_time_to_visit ? `<div class="itin-foot-box best"><h4>📅 최적 여행 시기</h4><p>${itin.best_time_to_visit}</p></div>` : ''}
      ${itin.weather_info       ? `<div class="itin-foot-box weather"><h4>🌤 날씨 정보</h4><p>${itin.weather_info}</p></div>` : ''}
    </div>`;
  }

  html += `</div>`;  // /itin-doc

  document.getElementById('itinerary-content').innerHTML = html;
  document.getElementById('itinerary-modal').classList.remove('hidden');
}

function closeItineraryModal() { document.getElementById('itinerary-modal').classList.add('hidden'); }

// ─────────────────────────────────────────
// BOOKING MANAGEMENT
// ─────────────────────────────────────────
async function saveBooking(type, index) {
  // index-based lookup from state (avoids HTML escaping issues)
  const item = type === 'flight' ? state.flightResults[index] : state.hotelResults[index];
  if (!item) { showToast('❌ 예약 정보를 찾을 수 없습니다.'); return; }
  const payload = {
    type,
    item_id: item.id || 'ITEM' + Date.now(),
    details: item,
    price:   item.total_price || 0,
    currency: 'KRW',
  };

  try {
    const res  = await fetch('/api/bookings/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    showToast(`✅ 예약 완료! 예약번호: ${data.booking?.id || 'OK'}`);
    await loadBookings();
  } catch (e) {
    showToast('❌ 예약 저장 중 오류가 발생했습니다.');
  }
}

async function loadBookings() {
  try {
    const res  = await fetch('/api/bookings/');
    const data = await res.json();
    state.bookings = data.bookings || [];
    updateBookingBadge();
  } catch (_) { /* silent */ }
}

function updateBookingBadge() {
  const badge = document.getElementById('booking-badge');
  if (!badge) return;
  const count = state.bookings.length;
  badge.textContent = count;
  badge.classList.toggle('hidden',  count === 0);
  badge.classList.toggle('flex',    count > 0);
}

async function cancelBooking(id) {
  if (!confirm('예약을 취소하시겠습니까?')) return;
  try {
    await fetch(`/api/bookings/${id}`, { method: 'DELETE' });
    showToast('예약이 취소되었습니다.');
    await loadBookings();
    openBookingsModal();
  } catch (e) {
    showToast('❌ 취소 중 오류가 발생했습니다.');
  }
}

async function openBookingsModal() {
  document.getElementById('bookings-modal').classList.remove('hidden');
  await loadBookings();

  const list = document.getElementById('bookings-list');
  if (!state.bookings.length) {
    list.innerHTML = `
      <div class="text-center py-16">
        <div class="text-6xl mb-4">✈️</div>
        <p class="text-gray-400 font-medium">예약 내역이 없습니다.</p>
        <p class="text-gray-300 text-sm mt-1">항공편이나 호텔을 검색하고 예약해보세요!</p>
      </div>`;
    return;
  }

  list.innerHTML = state.bookings.map(b => {
    const d = b.details || {};
    const isFlight = b.type === 'flight';
    return `
      <div class="booking-card">
        <div class="flex items-start justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full flex items-center justify-center text-xl ${isFlight ? 'bg-blue-50' : 'bg-orange-50'}">
              ${isFlight ? '✈️' : '🏨'}
            </div>
            <div>
              <div class="font-semibold text-gray-800 text-sm">
                ${isFlight ? `${d.departure?.city || '출발지'} → ${d.arrival?.city || '도착지'}` : d.name || '호텔'}
              </div>
              <div class="text-xs text-gray-500 mt-0.5">
                ${isFlight
                  ? `${d.airline || ''} · ${d.departure?.date || ''} · ${d.cabin_class || ''}`
                  : `${d.location || ''} · ${d.check_in || ''} ~ ${d.check_out || ''}`}
              </div>
              <div class="flex items-center gap-2 mt-1.5">
                <span class="text-xs bg-green-50 text-green-600 border border-green-200 px-2 py-0.5 rounded-full font-medium">✓ 예약확정</span>
                <span class="text-xs text-gray-400">예약번호: ${b.id}</span>
              </div>
            </div>
          </div>
          <div class="text-right flex-shrink-0 ml-3">
            <div class="font-bold text-blue-600">₩${fmtNum(b.price)}</div>
            <button onclick="cancelBooking('${b.id}')"
              class="text-xs text-red-400 hover:text-red-600 transition mt-1 block">취소</button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function closeBookingsModal() { document.getElementById('bookings-modal').classList.add('hidden'); }

// ── Utilities ──────────────────────────
function fmtNum(n) {
  if (n === null || n === undefined || n === '') return '0';
  const num = typeof n === 'number' ? n : Number(String(n).replace(/[^0-9.-]/g, ''));
  return Number.isFinite(num) ? num.toLocaleString('ko-KR') : '0';
}

function showLoading(text = '처리 중…') {
  document.getElementById('loading-text').textContent = text;
  document.getElementById('loading-overlay').classList.remove('hidden');
}
function hideLoading() { document.getElementById('loading-overlay').classList.add('hidden'); }

function showToast(msg, ms = 3500) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), ms);
}

// (escJSON 제거: 인덱스 기반 예약으로 대체)


// ═════════════════════════════════════════
// AI 여행지 추천
// ═════════════════════════════════════════

// 빠른 예시 채우기
const AI_EXAMPLES = {
  'family-winter': {
    party:  '4인 가족 — 초등 6학년 여아(만13세), 3학년 남아(만9세), 어른 2명',
    period: '12월 말(12/26~) 또는 2027년 1월, 겨울방학 기간',
    pref:   '아이들이 즐길 수 있는 테마파크·자연·문화 체험, 안전한 여행지 선호',
  },
  'couple-fall': {
    party:  '신혼부부 2명',
    period: '10월 중순 ~ 11월 초, 7박 8일',
    pref:   '로맨틱한 분위기, 좋은 호텔, 맛집 투어',
  },
  'friends-summer': {
    party:  '20대 친구 3명',
    period: '7월 말 ~ 8월 초, 5박 6일',
    pref:   '바다·해변, 액티비티, 나이트라이프, 저예산',
  },
  'solo-spring': {
    party:  '혼자 여행 (30대 여성)',
    period: '3월 말 ~ 4월 초, 4박 5일',
    pref:   '안전한 여행지, 카페·문화·예술, 힐링',
  },
};

function fillAIExample(key) {
  const ex = AI_EXAMPLES[key];
  if (!ex) return;
  document.getElementById('ai-party').value  = ex.party;
  document.getElementById('ai-period').value = ex.period;
  document.getElementById('ai-pref').value   = ex.pref;
}

async function recommendDestinations() {
  const party  = document.getElementById('ai-party')?.value?.trim();
  const period = document.getElementById('ai-period')?.value?.trim();
  const pref   = document.getElementById('ai-pref')?.value?.trim();
  const budget = document.getElementById('ai-budget')?.value || 'medium';

  if (!party)  { showToast('⚠️ 여행 인원/구성을 입력해주세요.'); return; }
  if (!period) { showToast('⚠️ 여행 시기를 입력해주세요.'); return; }

  // 버튼 로딩 상태
  const btn  = document.getElementById('ai-recommend-btn');
  const icon = document.getElementById('ai-btn-icon');
  const txt  = document.getElementById('ai-btn-text');
  btn.disabled = true;
  icon.textContent = '⏳';
  txt.textContent  = 'AI 분석 중…';

  showLoading('✨ AI가 최적의 여행지를 찾고 있습니다…');

  try {
    const res  = await fetch('/api/ai/recommend-destinations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ travel_party: party, travel_period: period,
                             preferences: pref, budget_level: budget }),
    });
    const data = await res.json();
    hideLoading();

    if (data.success && data.data) {
      renderAIDestinations(data.data, party, period);
    } else {
      showToast(`❌ ${data.error || '추천 생성에 실패했습니다.'}`);
    }
  } catch (e) {
    hideLoading();
    showToast('❌ 서버 연결 오류가 발생했습니다.');
  } finally {
    btn.disabled = false;
    icon.textContent = '✨';
    txt.textContent  = 'AI 추천 받기';
  }
}

// 도시별 대표 이미지 (Unsplash)
const DEST_IMAGES = {
  '도쿄': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=600&q=80',
  '오사카': 'https://images.unsplash.com/photo-1590559899731-a382839e5549?w=600&q=80',
  '방콕': 'https://images.unsplash.com/photo-1563492065599-3520f775eeed?w=600&q=80',
  '발리': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?w=600&q=80',
  '싱가포르': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=600&q=80',
  '홍콩': 'https://images.unsplash.com/photo-1474531210469-f91a11c06991?w=600&q=80',
  '파리': 'https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=600&q=80',
  '런던': 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=600&q=80',
  '뉴욕': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=600&q=80',
  '하와이': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=600&q=80',
  '제주': 'https://images.unsplash.com/photo-1556075798-4825dfaaf498?w=600&q=80',
  '다낭': 'https://images.unsplash.com/photo-1559592413-7cec4d0cae2b?w=600&q=80',
  '세부': 'https://images.unsplash.com/photo-1518548419970-58e3b4079ab2?w=600&q=80',
  '두바이': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=600&q=80',
  '바르셀로나': 'https://images.unsplash.com/photo-1539037116277-4db20889f2d4?w=600&q=80',
  '로마': 'https://images.unsplash.com/photo-1552832230-c0197dd311b5?w=600&q=80',
  '괌': 'https://images.unsplash.com/photo-1501854140801-50d01698950b?w=600&q=80',
  '사이판': 'https://images.unsplash.com/photo-1505118380757-91f5f5632de0?w=600&q=80',
  '푸켓': 'https://images.unsplash.com/photo-1589394815804-964ed0be2eb5?w=600&q=80',
  '코타키나발루': 'https://images.unsplash.com/photo-1596422846543-75c6fc197f07?w=600&q=80',
};

function getDestImage(city) {
  for (const [key, url] of Object.entries(DEST_IMAGES)) {
    if (city.includes(key) || key.includes(city)) return url;
  }
  return 'https://images.unsplash.com/photo-1488085061387-422e29b40080?w=600&q=80';
}

function renderAIDestinations(data, party, period) {
  const section  = document.getElementById('ai-results-section');
  const grid     = document.getElementById('ai-dest-grid');
  const summary  = document.getElementById('ai-summary-box');
  const subtitle = document.getElementById('ai-results-subtitle');

  // 요약 박스
  if (data.summary) {
    summary.textContent = `🤖 ${data.summary}`;
    summary.classList.remove('hidden');
  }
  subtitle.textContent = `${party} · ${period}`;

  const dests = data.destinations || [];
  state.recommendations = dests;  // "일정 만들기"에서 항공/호텔 참조용

  grid.innerHTML = dests.map((d, i) => {
    const imgUrl   = getDestImage(d.city);
    const isTop    = d.rank === 1;
    const rankLabel = isTop ? '🏆 1위 추천' : `${d.rank}위 추천`;
    const rankClass = isTop ? 'gold' : '';
    const budgetInfo = d.budget || {};
    const cityArg = (d.city || '').replace(/'/g, "\\'");

    // 날짜 옵션
    const datesHtml = (d.best_dates || []).map(dt => `
      <div class="ai-dest-date-item">
        <div class="ai-dest-date-period">📅 ${dt.period}</div>
        <div class="ai-dest-date-pros">✅ ${dt.pros}</div>
        ${dt.cons ? `<div class="ai-dest-date-cons">⚠️ ${dt.cons}</div>` : ''}
      </div>
    `).join('');

    // 예산 (항공권·호텔 항목 클릭 → 검색 팝업)
    const budgetHtml = `
      <div class="ai-dest-budget-grid">
        <div class="ai-dest-budget-item clickable" title="항공편 검색"
          onclick="openSearchModal('flights', { destination: '${cityArg}' })">
          <label>✈️ 항공권 (1인) <span class="ai-dest-search-hint">검색 →</span></label>
          <span>₩${fmtNum(budgetInfo.flight_per_person)}</span>
        </div>
        <div class="ai-dest-budget-item clickable" title="호텔 검색"
          onclick="openSearchModal('hotels', { destination: '${cityArg}' })">
          <label>🏨 호텔 (1박) <span class="ai-dest-search-hint">검색 →</span></label>
          <span>₩${fmtNum(budgetInfo.hotel_per_night)}</span>
        </div>
        <div class="ai-dest-budget-item">
          <label>🍽 현지 경비 (1일)</label>
          <span>₩${fmtNum(budgetInfo.daily_expense)}</span>
        </div>
        <div class="ai-dest-budget-item">
          <label>예산 등급</label>
          <span>${budgetInfo.budget_grade || '-'}</span>
        </div>
      </div>
      <div class="ai-dest-budget-total">
        <span>전체 예상 비용</span>
        <div style="display:flex;align-items:center;gap:8px;">
          <strong>₩${fmtNum(budgetInfo.total_estimate)}</strong>
          <span class="ai-dest-budget-grade">${budgetInfo.budget_grade || ''}</span>
        </div>
      </div>
    `;

    const kidsScore = d.kids_friendly_score || 70;

    // ── 항공편 상세 (클릭 → 항공 검색 팝업) ─
    const flight = d.flight || {};
    const flightHtml = (flight.airline || flight.route) ? `
      <div class="ai-dest-section-title">✈️ 항공편</div>
      <div class="ai-dest-info-card clickable" title="항공편 검색"
        onclick="openSearchModal('flights', { destination: '${cityArg}' })">
        <div class="ai-dest-info-head">
          <span class="ai-dest-info-name">${flight.airline || '항공편'}</span>
          ${flight.type ? `<span class="ai-dest-info-tag">${flight.type}</span>` : ''}
        </div>
        <div class="ai-dest-info-route">
          <span>${flight.route || '-'}</span>
          ${flight.duration ? `<span class="ai-dest-info-sub">⏱ ${flight.duration}</span>` : ''}
        </div>
        <div class="ai-dest-info-price">
          <span>1인 왕복 <span class="ai-dest-search-hint">· 검색 →</span></span><strong>₩${fmtNum(flight.price_per_person)}</strong>
        </div>
      </div>
    ` : '';

    // ── 호텔 상세 (클릭 → 호텔 검색 팝업) ─
    const hotel = d.hotel || {};
    const hotelFeatures = (hotel.features || []).map(f =>
      `<span class="ai-dest-chip">${f}</span>`).join('');
    const hotelHtml = (hotel.name || hotel.price_per_night) ? `
      <div class="ai-dest-section-title">🏨 추천 호텔</div>
      <div class="ai-dest-info-card clickable" title="호텔 검색"
        onclick="openSearchModal('hotels', { destination: '${cityArg}' })">
        <div class="ai-dest-info-head">
          <span class="ai-dest-info-name">${hotel.name || '추천 호텔'}</span>
          ${hotel.grade ? `<span class="ai-dest-info-tag">${hotel.grade}</span>` : ''}
        </div>
        ${hotel.area ? `<div class="ai-dest-info-sub">📍 ${hotel.area}</div>` : ''}
        ${hotelFeatures ? `<div class="ai-dest-chips">${hotelFeatures}</div>` : ''}
        <div class="ai-dest-info-price">
          <span>1박 <span class="ai-dest-search-hint">· 검색 →</span></span><strong>₩${fmtNum(hotel.price_per_night)}</strong>
        </div>
      </div>
    ` : '';

    // ── 인기 장소 & 가격 ─
    const attractions = d.attractions || [];
    const attractionsHtml = attractions.length ? `
      <div class="ai-dest-section-title">🎡 인기 장소 & 가격</div>
      <div class="ai-dest-attractions">
        ${attractions.map(a => `
          <div class="ai-dest-attraction">
            <div class="ai-dest-attraction-info">
              <span class="ai-dest-attraction-name">${a.emoji || '📍'} ${a.name}</span>
              ${a.price_note ? `<span class="ai-dest-attraction-note">${a.price_note}</span>` : ''}
            </div>
            <span class="ai-dest-attraction-price">₩${fmtNum(a.price)}</span>
          </div>
        `).join('')}
      </div>
    ` : '';

    return `
      <div class="ai-dest-card ${isTop ? 'rank-1' : ''}" style="animation-delay:${i * 0.12}s">
        <div class="ai-dest-img-wrap">
          <img src="${imgUrl}" alt="${d.city}" loading="lazy" />
          <div class="ai-dest-img-overlay"></div>
          <span class="ai-dest-rank-badge ${rankClass}">${rankLabel}</span>
          <div class="ai-dest-img-bottom">
            <div class="ai-dest-city">${d.emoji || ''} ${d.city}</div>
            <div class="ai-dest-country">${d.country}</div>
          </div>
        </div>

        <div class="ai-dest-body">
          <div class="ai-dest-tagline">${d.tagline || ''}</div>

          <!-- 추천 이유 -->
          <div class="ai-dest-section-title">추천 이유</div>
          <ul class="ai-dest-reasons">
            ${(d.reasons || []).map(r => `<li>${r}</li>`).join('')}
          </ul>

          <!-- 가족 특화 포인트 -->
          ${(d.family_highlights || []).length ? `
          <div class="ai-dest-section-title">👨‍👩‍👧‍👦 가족 포인트</div>
          <ul class="ai-dest-reasons" style="margin-bottom:14px">
            ${d.family_highlights.map(h => `<li style="color:#0E72CC">${h}</li>`).join('')}
          </ul>` : ''}

          <!-- 항공편 -->
          ${flightHtml}

          <!-- 호텔 -->
          ${hotelHtml}

          <!-- 인기 장소 -->
          ${attractionsHtml}

          <!-- 날짜 옵션 -->
          <div class="ai-dest-section-title">📅 추천 날짜</div>
          <div class="ai-dest-dates">${datesHtml}</div>

          <!-- 예산 -->
          <div class="ai-dest-section-title">💰 예상 예산</div>
          <div class="ai-dest-budget">${budgetHtml}</div>

          <!-- 아이 친화도 -->
          <div class="ai-dest-kids-score">
            <span class="ai-dest-kids-label">👧 아이 친화도</span>
            <div class="ai-dest-kids-bar">
              <div class="ai-dest-kids-fill" style="width:${kidsScore}%"></div>
            </div>
            <span class="ai-dest-kids-num">${kidsScore}</span>
          </div>

          <!-- CTA -->
          <button class="ai-dest-cta-btn"
            onclick="startPlanFromRecommend('${d.city}')">
            🗺️ ${d.city} 일정 만들기
          </button>
        </div>
      </div>
    `;
  }).join('');

  section.classList.remove('hidden');
  setTimeout(() => {
    section.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, 100);
}

// 추천 결과에서 바로 AI 일정 생성 (항공·호텔 정보 참조, 3박4일)
async function startPlanFromRecommend(city) {
  const rec = (state.recommendations || []).find(r => r.city === city) || {};
  const interests = ['관광', '음식'];  // 추천 기반 기본 관심사
  const duration = 4;  // 3박 4일
  const today = new Date().toISOString().split('T')[0];

  showLoading(`🤖 ${city} 3박 4일 일정을 항공·호텔 정보와 함께 만드는 중…`);

  try {
    const res = await fetch('/api/ai/itinerary', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        destination: city,
        duration_days: duration,
        start_date: today,
        interests,
        budget: (rec.budget && rec.budget.budget_grade === '럭셔리') ? 'luxury'
              : (rec.budget && rec.budget.budget_grade === '알뜰') ? 'budget' : 'medium',
        flight: rec.flight || null,
        hotel: rec.hotel || null,
        traveler: document.getElementById('ai-party')?.value?.trim() || '',
      }),
    });
    const data = await res.json();
    hideLoading();
    if (data.success && data.itinerary) {
      renderItinerary(data.itinerary);
    } else {
      showToast(`❌ ${data.error || '일정 생성에 실패했습니다.'}`);
    }
  } catch (e) {
    hideLoading();
    showToast('❌ 서버 연결 오류가 발생했습니다.');
  }
}
