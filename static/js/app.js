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
};

// ── Initialize ─────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  setDefaultDates();
  setupInterestTags();
  loadBookings();
  loadDestinations();

  // Backdrop clicks to close modals
  document.getElementById('bookings-modal')?.addEventListener('click', e => {
    if (e.target.id === 'bookings-modal') closeBookingsModal();
  });
  document.getElementById('itinerary-modal')?.addEventListener('click', e => {
    if (e.target.id === 'itinerary-modal') closeItineraryModal();
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
function switchTab(tab) {
  state.currentTab = tab;
  ['flights', 'hotels', 'planner'].forEach(t => {
    document.getElementById(`panel-${t}`)?.classList.toggle('hidden', t !== tab);
    document.getElementById(`tab-${t}`)?.classList.toggle('active', t === tab);
  });
  document.querySelector('.search-card')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
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

  let html = `
    <div class="bg-blue-50 rounded-xl p-5 mb-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
        <div><div class="text-2xl mb-1">📍</div><div class="font-bold text-gray-800">${itin.destination}</div><div class="text-xs text-gray-500">목적지</div></div>
        <div><div class="text-2xl mb-1">🗓️</div><div class="font-bold text-gray-800">${itin.duration}일</div><div class="text-xs text-gray-500">여행 기간</div></div>
        <div><div class="text-2xl mb-1">💰</div><div class="font-bold text-gray-800">${itin.budget_level || '중간'}</div><div class="text-xs text-gray-500">예산 수준</div></div>
        <div><div class="text-2xl mb-1">💳</div><div class="font-bold text-blue-600 text-sm">${itin.total_estimated_cost || '-'}</div><div class="text-xs text-gray-500">총 예상 비용</div></div>
      </div>
    </div>
  `;

  if (itin.highlights?.length) {
    html += `<div class="mb-6"><h3 class="font-bold text-gray-700 mb-3">✨ 하이라이트</h3><div class="flex flex-wrap gap-2">
      ${itin.highlights.map(h => `<span class="bg-orange-50 text-orange-600 border border-orange-200 px-3 py-1 rounded-full text-sm font-medium">${h}</span>`).join('')}
    </div></div>`;
  }

  (itin.days || []).forEach(day => {
    html += `
      <div class="day-card">
        <div class="day-header">
          <div class="flex items-center justify-between">
            <div>
              <span class="text-sm opacity-80 block">Day ${day.day}</span>
              <h3 class="font-bold text-lg">${day.title || day.day + '일차'}</h3>
            </div>
            <div class="text-right text-sm opacity-80">
              <div>${day.theme || ''}</div>
              <div class="font-semibold">${day.estimated_cost || ''}</div>
            </div>
          </div>
        </div>
        ${(day.activities || []).map(act => `
          <div class="activity-item">
            <span class="activity-time">${act.time || ''}</span>
            <div class="flex-1">
              <div class="flex items-center gap-2 flex-wrap mb-1">
                <span class="font-semibold text-gray-800 text-sm">${act.title}</span>
                <span class="activity-type-badge type-${act.type || '관광'}">${act.type || '관광'}</span>
              </div>
              <p class="text-gray-600 text-xs mb-1">${act.description || ''}</p>
              <div class="flex gap-3 text-xs text-gray-400 flex-wrap">
                ${act.duration ? `<span>⏱ ${act.duration}</span>` : ''}
                ${act.cost ? `<span>💰 ${act.cost}</span>` : ''}
                ${act.tips ? `<span class="text-blue-500">💡 ${act.tips}</span>` : ''}
              </div>
            </div>
          </div>
        `).join('')}
        ${day.meals ? `
          <div class="px-5 py-3 bg-orange-50 border-t border-orange-100">
            <span class="text-xs font-bold text-orange-600 uppercase tracking-wide">추천 식사</span>
            <div class="flex gap-4 mt-1 text-xs text-gray-600 flex-wrap">
              ${day.meals.breakfast ? `<span>🌅 조식: ${day.meals.breakfast}</span>` : ''}
              ${day.meals.lunch     ? `<span>☀️ 중식: ${day.meals.lunch}</span>`     : ''}
              ${day.meals.dinner    ? `<span>🌙 석식: ${day.meals.dinner}</span>`    : ''}
            </div>
          </div>
        ` : ''}
      </div>
    `;
  });

  if (itin.travel_tips?.length) {
    html += `
      <div class="mt-6 bg-blue-50 rounded-xl p-5">
        <h3 class="font-bold text-blue-800 mb-3">💡 여행 꿀팁</h3>
        <ul class="space-y-2">
          ${itin.travel_tips.map(t => `<li class="flex items-start gap-2 text-sm text-blue-700"><span>•</span><span>${t}</span></li>`).join('')}
        </ul>
      </div>
    `;
  }

  if (itin.best_time_to_visit || itin.weather_info) {
    html += `<div class="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
      ${itin.best_time_to_visit ? `<div class="bg-green-50 rounded-xl p-4"><h4 class="font-bold text-green-700 mb-1">📅 최적 여행 시기</h4><p class="text-sm text-green-600">${itin.best_time_to_visit}</p></div>` : ''}
      ${itin.weather_info       ? `<div class="bg-sky-50 rounded-xl p-4"><h4 class="font-bold text-sky-700 mb-1">🌤 날씨 정보</h4><p class="text-sm text-sky-600">${itin.weather_info}</p></div>` : ''}
    </div>`;
  }

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
function fmtNum(n) { return Number(n || 0).toLocaleString('ko-KR'); }

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
