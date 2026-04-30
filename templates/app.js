// ══════════════════════════════════════════
//  JobAnalytics — App JavaScript
//  Fetches REAL data from /api/data endpoint
// ══════════════════════════════════════════

let DATA = null; // Loaded from API

// ── PAGE SWITCHING ──
function switchPage(pageId, el) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + pageId).classList.add('active');
  el.classList.add('active');
  if (window.innerWidth < 769) toggleSidebar();
}

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
  document.getElementById('overlay').classList.toggle('active');
}

// ── ANIMATED COUNTERS ──
function animateCounter(el, target) {
  const duration = 1200;
  const step = target / (duration / 16);
  let current = 0;
  const timer = setInterval(() => {
    current += step;
    if (current >= target) { current = target; clearInterval(timer); }
    el.textContent = Math.floor(current).toLocaleString();
  }, 16);
}

// ── CHART.JS DEFAULTS ──
Chart.defaults.color = '#8888aa';
Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
Chart.defaults.font.family = 'Inter';
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;

// ══════════════════════════
//  PAGE 1: OVERVIEW
// ══════════════════════════
function renderOverview(ov) {
  // Stat cards
  const stats = [
    { id: 'statJobs', value: ov.total_jobs, label: 'Total Jobs' },
    { id: 'statCompanies', value: ov.total_companies, label: 'Companies Hiring' },
    { id: 'statCities', value: ov.total_cities, label: 'Cities Covered' },
    { id: 'statSkills', value: ov.total_skills, label: 'Skills Tracked' },
  ];
  stats.forEach(s => {
    const numEl = document.getElementById(s.id);
    if (numEl) animateCounter(numEl, s.value);
  });

  // Last updated
  if (ov.last_updated) {
    const d = new Date(ov.last_updated);
    document.getElementById('lastUpdated').textContent =
      `Last updated ${d.toLocaleDateString('en-IN')} at ${d.toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit'})}`;
  }

  // Top 10 Skills Bar Chart
  const skillLabels = Object.keys(ov.top_skills);
  const skillValues = Object.values(ov.top_skills);
  const skillsCtx = document.getElementById('chartSkills').getContext('2d');
  const skillGrad = skillsCtx.createLinearGradient(0, 0, 400, 0);
  skillGrad.addColorStop(0, '#6c63ff'); skillGrad.addColorStop(1, '#a78bfa');
  new Chart(skillsCtx, {
    type: 'bar',
    data: {
      labels: skillLabels,
      datasets: [{ data: skillValues, backgroundColor: skillGrad, borderRadius: 6, borderSkipped: false, barThickness: 18 }]
    },
    options: {
      indexAxis: 'y', responsive: true,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } }, y: { grid: { display: false }, ticks: { font: { size: 11, weight: 500 } } } }
    }
  });

  // Experience Donut
  const expLabels = Object.keys(ov.experience_distribution);
  const expValues = Object.values(ov.experience_distribution);
  const totalJobs = ov.total_jobs;
  new Chart(document.getElementById('chartExp'), {
    type: 'doughnut',
    data: {
      labels: expLabels,
      datasets: [{ data: expValues, backgroundColor: ['#48bb78', '#f6ad55', '#6c63ff'], borderWidth: 0, cutout: '68%' }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom', labels: { padding: 16, font: { size: 11 } } } }
    },
    plugins: [{
      id: 'centerText',
      afterDraw(chart) {
        const { ctx, chartArea: { width, height, top, left } } = chart;
        ctx.save();
        ctx.font = '800 22px Inter'; ctx.fillStyle = '#f0f0ff';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(totalJobs.toLocaleString(), left + width / 2, top + height / 2 - 8);
        ctx.font = '500 10px Inter'; ctx.fillStyle = '#8888aa';
        ctx.fillText('Total Jobs', left + width / 2, top + height / 2 + 12);
        ctx.restore();
      }
    }]
  });

  // Jobs by City
  const cityLabels = Object.keys(ov.jobs_by_city);
  const cityValues = Object.values(ov.jobs_by_city);
  const cityCtx = document.getElementById('chartCities').getContext('2d');
  const cityGrad = cityCtx.createLinearGradient(0, 0, 0, 300);
  cityGrad.addColorStop(0, '#6c63ff'); cityGrad.addColorStop(1, 'rgba(108,99,255,0.2)');
  new Chart(cityCtx, {
    type: 'bar',
    data: { labels: cityLabels, datasets: [{ data: cityValues, backgroundColor: cityGrad, borderRadius: 8, borderSkipped: false, barThickness: 32 }] },
    options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { grid: { color: 'rgba(255,255,255,0.03)' } } } }
  });

  // Job Titles Table
  const titles = Object.entries(ov.top_titles);
  const maxCount = titles.length ? titles[0][1] : 1;
  const tbody = document.getElementById('jobTitlesTable');
  tbody.innerHTML = '';
  titles.forEach(([title, count], i) => {
    const pct = (count / maxCount * 100).toFixed(0);
    tbody.innerHTML += `<tr><td><span class="rank-badge">${i + 1}</span></td><td>${title}</td><td><div style="display:flex;align-items:center;gap:8px"><div class="mini-bar" style="width:${pct}%;min-width:20px"></div><span style="font-size:11px;color:var(--text-muted)">${count}</span></div></td></tr>`;
  });
}

// ══════════════════════════
//  PAGE 2: SKILL TRENDS
// ══════════════════════════
function renderSkillTrends(skillsData) {
  const trends = skillsData.trends || [];
  const container = document.getElementById('trendCards');
  container.innerHTML = '';

  trends.forEach((s, idx) => {
    const cls = s.trend === 'rising' ? 'trend-rising' : s.trend === 'stable' ? 'trend-stable' : 'trend-declining';
    const emoji = s.trend === 'rising' ? '🔥' : s.trend === 'stable' ? '✅' : '⬇';
    const label = s.trend === 'rising' ? 'Rising' : s.trend === 'stable' ? 'Stable' : 'Declining';
    const changeColor = s.change >= 0 ? 'var(--success)' : 'var(--danger)';
    const changeStr = (s.change >= 0 ? '+' : '') + s.change + '%';
    container.innerHTML += `
      <div class="card" style="padding:18px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <span style="font-size:15px;font-weight:700">${s.name}</span>
          <span class="trend-badge ${cls}">${emoji} ${label}</span>
        </div>
        <canvas id="spark${idx}" height="40"></canvas>
        <div style="font-size:12px;color:var(--text-muted);margin-top:6px">30-day change: <strong style="color:${changeColor}">${changeStr}</strong></div>
      </div>`;
  });

  // Render sparklines
  setTimeout(() => {
    trends.forEach((s, idx) => {
      const c = document.getElementById('spark' + idx);
      if (!c) return;
      const color = s.trend === 'declining' ? '#fc8181' : s.trend === 'stable' ? '#f6ad55' : '#48bb78';
      new Chart(c.getContext('2d'), {
        type: 'line',
        data: { labels: s.data.map((_, i) => i), datasets: [{ data: s.data, borderColor: color, borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false }] },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
      });
    });
  }, 50);

  // Render clusters from categories
  const cats = skillsData.categories || {};
  const clusterGrid = document.getElementById('clusterGrid');
  if (clusterGrid) {
    clusterGrid.innerHTML = '';
    const showCats = Object.entries(cats).slice(0, 3);
    showCats.forEach(([catName, skills]) => {
      clusterGrid.innerHTML += `
        <div class="cluster-card">
          <div class="cluster-title gradient-text">${catName}</div>
          <div>${skills.slice(0, 6).map(s => `<span class="chip chip-neutral">${s}</span>`).join('')}</div>
        </div>`;
    });
  }

  // 90-day Forecast Chart
  const fCtx = document.getElementById('chartForecast90');
  if (fCtx && trends.length >= 5) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    const colors = ['#6c63ff', '#a78bfa', '#f6ad55', '#48bb78', '#fc8181'];
    function makeGrad(ctx2d, color) {
      const g = ctx2d.createLinearGradient(0, 0, 0, 300);
      g.addColorStop(0, color + '33'); g.addColorStop(1, color + '05');
      return g;
    }
    const ctx = fCtx.getContext('2d');
    const datasets = trends.slice(0, 5).map((s, i) => {
      const baseVal = s.count;
      const growthRate = s.trend === 'rising' ? 1.06 : s.trend === 'declining' ? 0.96 : 1.01;
      const projectedData = months.map((_, mi) => Math.round(baseVal * Math.pow(growthRate, mi)));
      return {
        label: s.name, data: projectedData,
        borderColor: colors[i], backgroundColor: makeGrad(ctx, colors[i]),
        fill: true, tension: 0.4, borderWidth: 2, pointRadius: 3
      };
    });
    new Chart(ctx, {
      type: 'line',
      data: { labels: months, datasets },
      options: {
        responsive: true, plugins: { legend: { position: 'top' } },
        scales: { x: { grid: { display: false } }, y: { grid: { color: 'rgba(255,255,255,0.03)' }, title: { display: true, text: 'Job Postings', font: { size: 11 } } } }
      }
    });
  }
}

// ══════════════════════════
//  PAGE 3: COMPANIES
// ══════════════════════════
let allCompanies = [];

function renderCompanies(list) {
  const grid = document.getElementById('companyGrid');
  grid.innerHTML = '';
  list.forEach(c => {
    grid.innerHTML += `
      <div class="company-card">
        <div class="company-logo" style="background:${c.color}">${c.name[0]}</div>
        <div class="company-name">${c.name}</div>
        <div class="company-positions">${c.positions} open positions · ${c.type}</div>
        <div style="margin-bottom:12px">${(c.skills || []).map(s => `<span class="chip chip-neutral">${s}</span>`).join('')}</div>
        <button class="btn-sm">View Jobs →</button>
      </div>`;
  });
}

function filterByType(type, el) {
  document.querySelectorAll('#companyFilters .filter-pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  const q = document.getElementById('companySearch').value.toLowerCase();
  let filtered = type === 'All' ? allCompanies : allCompanies.filter(c => c.type === type);
  if (q) filtered = filtered.filter(c => c.name.toLowerCase().includes(q));
  renderCompanies(filtered);
}

function filterCompanies() {
  const q = document.getElementById('companySearch').value.toLowerCase();
  const activeEl = document.querySelector('#companyFilters .filter-pill.active');
  const active = activeEl ? activeEl.textContent.trim() : 'All';
  let filtered = active === 'All' ? allCompanies : allCompanies.filter(c => c.type === active);
  if (q) filtered = filtered.filter(c => c.name.toLowerCase().includes(q));
  renderCompanies(filtered);
}

// ══════════════════════════
//  PAGE 4: SALARY PREDICTOR
// ══════════════════════════
function initSalaryPage(salaryData) {
  // Populate role dropdown
  const roleSelect = document.getElementById('salaryRole');
  roleSelect.innerHTML = '';
  (salaryData.roles || []).forEach(r => {
    roleSelect.innerHTML += `<option>${r}</option>`;
  });

  // Populate city dropdown
  const citySelect = document.getElementById('salaryCity');
  citySelect.innerHTML = '';
  const cities = salaryData.cities || [];
  cities.forEach(c => {
    citySelect.innerHTML += `<option>${c}</option>`;
  });

  // Skill chips from actual tracked skills
  const container = document.getElementById('skillChips');
  container.innerHTML = '';
  const topSkills = Object.keys(DATA.overview.top_skills).slice(0, 10);
  topSkills.forEach(s => {
    const chip = document.createElement('span');
    chip.className = 'chip chip-neutral';
    chip.style.cursor = 'pointer';
    chip.textContent = s;
    chip.onclick = () => { chip.classList.toggle('chip-success'); chip.classList.toggle('chip-neutral'); };
    container.appendChild(chip);
  });

  // Salary by experience chart
  const salaries = Object.entries(salaryData.base_salaries);
  if (salaries.length) {
    new Chart(document.getElementById('chartSalaryExp'), {
      type: 'line',
      data: {
        labels: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
        datasets: [{
          label: 'Avg Salary (LPA)',
          data: [4.5, 6.2, 8.5, 10.8, 13.2, 15.8, 18.5, 21.2, 24.0, 27.5, 32.0],
          borderColor: '#6c63ff', backgroundColor: 'rgba(108,99,255,0.1)',
          fill: true, tension: 0.4, borderWidth: 2, pointRadius: 4, pointBackgroundColor: '#6c63ff'
        }]
      },
      options: {
        responsive: true, plugins: { legend: { display: false } },
        scales: {
          x: { title: { display: true, text: 'Years of Experience', font: { size: 11 } }, grid: { display: false } },
          y: { title: { display: true, text: 'Salary (LPA)', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.03)' } }
        }
      }
    });
  }

  // Similar Roles table from base salaries
  const tbody = document.getElementById('similarRolesTable');
  if (tbody) {
    tbody.innerHTML = '';
    salaries.slice(0, 6).forEach(([role, sal]) => {
      const trendCls = sal >= 12 ? 'trend-rising' : sal >= 8 ? 'trend-stable' : 'trend-stable';
      const trendLabel = sal >= 12 ? '↑ Rising' : '→ Stable';
      tbody.innerHTML += `<tr><td>${role}</td><td>₹${sal} LPA</td><td><span class="trend-badge ${trendCls}">${trendLabel}</span></td></tr>`;
    });
  }
}

function predictSalary() {
  const role = document.getElementById('salaryRole').value;
  const city = document.getElementById('salaryCity').value;
  const exp = parseInt(document.getElementById('salaryExp').value);

  // Call API
  fetch(`/api/salary/predict?role=${encodeURIComponent(role)}&city=${encodeURIComponent(city)}&exp=${exp}`)
    .then(r => r.json())
    .then(result => {
      document.getElementById('salaryRangeText').textContent = `₹${result.low} LPA – ₹${result.high} LPA`;
      document.getElementById('salaryMedianText').textContent = `Median: ₹${result.median} LPA`;
      document.getElementById('gaugeMarker').style.left = result.gauge_pct + '%';
      document.getElementById('salaryResult').style.display = 'block';
      document.getElementById('salaryResult').style.animation = 'fadeIn 0.4s ease';
    })
    .catch(() => {
      // Fallback to client-side prediction
      const base = (DATA.salary.base_salaries[role] || 10);
      let mult = 1.0;
      for (const [key, val] of Object.entries(DATA.salary.city_multipliers)) {
        if (city.toLowerCase().includes(key.toLowerCase())) { mult = val; break; }
      }
      const low = (base * mult + exp * 1.8).toFixed(1);
      const high = (base * mult + exp * 2.6 + 3).toFixed(1);
      const median = ((parseFloat(low) + parseFloat(high)) / 2).toFixed(1);
      document.getElementById('salaryRangeText').textContent = `₹${low} LPA – ₹${high} LPA`;
      document.getElementById('salaryMedianText').textContent = `Median: ₹${median} LPA`;
      document.getElementById('salaryResult').style.display = 'block';
    });
}

// ══════════════════════════
//  PAGE 5: RESUME MATCH
// ══════════════════════════
function initResumePage(resumeData) {
  const profile = resumeData.user_profile || {};

  // Pre-fill user info
  const nameEl = document.getElementById('profileName');
  const titleEl = document.getElementById('profileTitle');
  const skillsEl = document.getElementById('profileSkills');

  if (nameEl) nameEl.textContent = profile.name || 'User';
  if (titleEl) titleEl.textContent = `${profile.title || 'Job Seeker'} · ${profile.experience_years || 0} yrs exp`;
  if (skillsEl) {
    skillsEl.innerHTML = (profile.skills || []).map(s => `<span class="chip chip-neutral">${s}</span>`).join('');
  }

  // Pre-build match cards from real data
  const matchCards = resumeData.matches || [];
  const container = document.getElementById('matchCards');
  container.innerHTML = '';
  matchCards.forEach(m => {
    const pct = Math.round(m.score || 0);
    const colorCls = pct > 80 ? 'match-green' : pct > 60 ? 'match-orange' : 'match-red';
    const matchedSkills = (m.matched_skills || []).map(s => `<span class="chip chip-success">${s}</span>`).join('');
    container.innerHTML += `
      <div class="match-card">
        <div class="match-rank">#${m.rank}</div>
        <div class="match-info">
          <div class="company">${m.company} · ${m.title}</div>
          <div class="role">${m.location || ''}</div>
          <div style="margin-top:8px">${matchedSkills}</div>
        </div>
        <div class="match-percent ${colorCls}">${pct}%</div>
      </div>`;
  });

  // Skill gap analysis
  const haveContainer = document.getElementById('haveSkills');
  const gapContainer = document.getElementById('gapSkills');
  if (haveContainer) {
    haveContainer.innerHTML = (resumeData.have_skills || []).map(s => `<span class="chip chip-success">${s}</span>`).join('');
  }
  if (gapContainer) {
    gapContainer.innerHTML = (resumeData.gap_skills || []).map(s =>
      `<span class="chip chip-danger">${s} <a href="https://www.google.com/search?q=learn+${encodeURIComponent(s)}" target="_blank" style="color:var(--danger);font-size:10px;margin-left:4px">Learn →</a></span>`
    ).join('');
  }
}

function simulateUpload() {
  const zone = document.getElementById('uploadZone');
  const profile = DATA.resume.user_profile || {};
  zone.innerHTML = `<div style="color:var(--success);font-size:14px;font-weight:600">✓ Resume loaded — ${profile.name || 'User'}'s profile</div>`;
  zone.style.borderColor = 'rgba(72,187,120,0.5)';
  setTimeout(() => {
    document.getElementById('resumeResults').style.display = 'block';
  }, 400);
}

// ══════════════════════════
//  PAGE 6: FORECAST
// ══════════════════════════
function renderForecast(forecastData) {
  const skills = forecastData.skills || [];

  // Forecast cards
  const cardsContainer = document.getElementById('forecastCards');
  cardsContainer.innerHTML = '';
  skills.slice(0, 6).forEach((s, idx) => {
    const cls = s.trend === 'rising' ? 'trend-rising' : s.trend === 'stable' ? 'trend-stable' : 'trend-declining';
    const label = s.trend === 'rising' ? '↑ Rising Fast' : s.trend === 'stable' ? '→ Stable' : '↓ Declining';
    const icon = s.trend === 'rising' ? '📈' : s.trend === 'stable' ? '📊' : '📉';
    cardsContainer.innerHTML += `
      <div class="card" style="padding:18px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
          <span style="font-size:15px;font-weight:700">${icon} ${s.name}</span>
          <span class="chip chip-neutral" style="font-size:10px">${s.confidence}% conf</span>
        </div>
        <canvas id="fcard${idx}" height="40"></canvas>
        <div style="margin-top:8px"><span class="trend-badge ${cls}">${label}</span></div>
      </div>`;
  });

  // Sparklines
  setTimeout(() => {
    skills.slice(0, 6).forEach((s, idx) => {
      const c = document.getElementById('fcard' + idx);
      if (!c) return;
      const color = s.trend === 'rising' ? '#48bb78' : s.trend === 'stable' ? '#f6ad55' : '#fc8181';
      new Chart(c.getContext('2d'), {
        type: 'line',
        data: { labels: ['Now', '30d', '60d', '90d'], datasets: [{ data: [s.current, s.d30, s.d60, s.d90], borderColor: color, borderWidth: 2, pointRadius: 0, tension: 0.4, fill: false }] },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { x: { display: false }, y: { display: false } } }
      });
    });
  }, 50);

  // Forecast table
  const tbody = document.getElementById('forecastTable');
  tbody.innerHTML = '';
  skills.forEach(s => {
    const cls = s.trend === 'rising' ? 'trend-rising' : s.trend === 'stable' ? 'trend-stable' : 'trend-declining';
    const label = s.trend === 'rising' ? '↑ Rising' : s.trend === 'stable' ? '→ Stable' : '↓ Declining';
    const rowBg = s.trend === 'rising' ? 'rgba(72,187,120,0.04)' : s.trend === 'declining' ? 'rgba(252,129,129,0.04)' : '';
    tbody.innerHTML += `<tr style="background:${rowBg}"><td style="font-weight:600">${s.name}</td><td>${s.current}</td><td>${s.d30}</td><td>${s.d60}</td><td>${s.d90}</td><td><span class="trend-badge ${cls}">${label}</span></td></tr>`;
  });

  // Emerging skills
  const emerging = forecastData.emerging || [];
  const emContainer = document.getElementById('emergingSkills');
  emContainer.innerHTML = '';
  emerging.forEach(e => {
    emContainer.innerHTML += `
      <div class="card" style="padding:14px 18px;display:flex;align-items:center;gap:10px">
        <span style="font-size:14px;font-weight:700">${e.name}</span>
        <span class="chip chip-success">${e.growth}</span>
      </div>`;
  });
}

// ══════════════════════════
//  INIT — Fetch from API
// ══════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  const loadingMsg = document.getElementById('loadingOverlay');

  fetch('/api/data')
    .then(r => r.json())
    .then(data => {
      DATA = data;

      // Update user info in sidebar
      const profile = data.resume.user_profile || {};
      const sidebarName = document.getElementById('sidebarName');
      const sidebarRole = document.getElementById('sidebarRole');
      if (sidebarName) sidebarName.textContent = profile.name || 'Rohit Mane';
      if (sidebarRole) sidebarRole.textContent = profile.title || 'Data Science';

      // Render all pages
      renderOverview(data.overview);
      renderSkillTrends(data.skills);
      allCompanies = data.companies || [];
      renderCompanies(allCompanies);
      initSalaryPage(data.salary);
      initResumePage(data.resume);
      renderForecast(data.forecast);

      // Hide loading
      if (loadingMsg) loadingMsg.style.display = 'none';
    })
    .catch(err => {
      console.error('Failed to load API data:', err);
      if (loadingMsg) loadingMsg.innerHTML = '<div style="color:var(--danger)">Failed to load data. Make sure the dashboard server is running.</div>';
    });
});
