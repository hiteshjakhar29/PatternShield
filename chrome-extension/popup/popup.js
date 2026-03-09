/**
 * PatternShield Popup v2.1
 * Powers the redesigned dark-theme dashboard UI.
 */

class PopupController {
  constructor() {
    this.detections = [];
    this.currentTab = null;
    this.settings = CONFIG.DEFAULT_SETTINGS;
    this.init();
  }

  async init() {
    this.currentTab = await this.getActiveTab();
    await this.loadSettings();
    this.renderDomainBar();
    this.setupTabs();
    this.setupEventListeners();
    this.populateSettings();
    await Promise.all([
      this.checkAPIStatus(),
      this.loadDetections(),
      this.loadStats(),
    ]);
  }

  async getActiveTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }

  // ── Domain bar ─────────────────────────────────────────────────────

  renderDomainBar() {
    const el = document.getElementById('domainName');
    try {
      const url = new URL(this.currentTab.url);
      el.textContent = url.hostname || this.currentTab.url;
    } catch {
      el.textContent = 'Unknown page';
    }
  }

  // ── API status ─────────────────────────────────────────────────────

  async checkAPIStatus() {
    const dot  = document.getElementById('statusDot');
    const text = document.getElementById('statusText');

    if (this.settings.offlineMode) {
      dot.className = 'status-dot offline';
      text.textContent = 'Offline Mode';
      return;
    }

    dot.className = 'status-dot pending';
    text.textContent = 'Checking…';

    const result = await this._bgProxy('/health', 'GET');
    if (result.success && result.data) {
      dot.className = 'status-dot';
      text.textContent = `Connected — v${result.data.version || '2.1'}`;
    } else {
      dot.className = 'status-dot offline';
      text.textContent = 'Backend offline';
      // Append hint as tooltip-style title on the status element rather than a console.warn
      document.getElementById('statusText').title = 'Start backend: cd backend && python3 app.py';
    }
  }

  // ── Settings ───────────────────────────────────────────────────────

  async loadSettings() {
    try {
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.SETTINGS);
      this.settings = { ...CONFIG.DEFAULT_SETTINGS, ...(r[CONFIG.STORAGE_KEYS.SETTINGS] || {}) };
    } catch {}
  }

  populateSettings() {
    const s = this.settings;

    const bind = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.checked = !!val;
    };
    bind('autoScanToggle',      s.autoScan);
    bind('highlightToggle',     s.highlightElements);
    bind('floatingPanelToggle', s.showFloatingPanel !== false);
    bind('temporalToggle',      s.enableTemporal !== false);
    bind('feedbackToggle',      s.enableFeedback !== false);
    bind('offlineToggle',       s.offlineMode || false);

    const slider = document.getElementById('thresholdSlider');
    const val    = Math.round((s.confidenceThreshold || 0.35) * 100);
    slider.value = val;
    document.getElementById('thresholdValue').textContent = `${val}%`;
    this._updateSliderTrack(slider);

    document.getElementById('apiUrlInput').value = s.apiUrl || CONFIG.API_URL;

    // Pattern category toggles
    const container = document.getElementById('patternToggles');
    container.innerHTML = '';
    const enabled = s.enabledPatterns || {};
    for (const [ptype, cfg] of Object.entries(CONFIG.PATTERNS)) {
      if (ptype === 'No Pattern') continue;
      const row = document.createElement('div');
      row.className = 'pattern-toggle-row';
      row.innerHTML = `
        <div class="pt-label">
          <span class="pt-dot" style="background:${cfg.color}"></span>
          <span>${cfg.icon || ''} ${cfg.label}</span>
        </div>
        <label class="toggle-switch">
          <input type="checkbox" data-pattern="${ptype}" ${enabled[ptype] !== false ? 'checked' : ''}>
          <span class="toggle-track"></span>
        </label>
      `;
      container.appendChild(row);
    }
  }

  async saveSetting(key, value) {
    this.settings[key] = value;
    await chrome.storage.sync.set({ [CONFIG.STORAGE_KEYS.SETTINGS]: this.settings });
    try {
      await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'updateSettings', settings: this.settings,
      });
    } catch {}
  }

  // ── Detections ─────────────────────────────────────────────────────

  async loadDetections() {
    try {
      const response = await chrome.tabs.sendMessage(
        this.currentTab.id, { action: 'getDetections' }
      );
      if (response) {
        this.detections = response.patterns || [];
        await this.renderScan();
      }
    } catch {
      this.showIdleState();
    }
  }

  async renderScan() {
    const siteScore = this.detections.length > 0 ? await this._getSiteScore() : null;
    this.renderTrustCard(siteScore);
    this.renderChips();
    this.renderDetectionList();
  }

  // ── Trust Score Card ───────────────────────────────────────────────

  // Tries /site-score API first; falls back to client-side formula if unavailable.
  async _getSiteScore() {
    const payload = {
      detections: this.detections.map(d => ({
        primary_pattern: d.pattern,
        confidence_scores: { [d.pattern]: d.confidence || 0 },
      })),
    };
    try {
      const domain = this.currentTab ? new URL(this.currentTab.url).hostname : '';
      if (domain) payload.domain = domain;
      const result = await this._bgProxy('/site-score', 'POST', payload);
      if (result.success && result.data && typeof result.data.score === 'number') {
        return result.data; // { score, grade, risk_level, pattern_breakdown }
      }
    } catch {}

    // Client-side fallback when API is unreachable
    const sevWeights = { critical: 0.9, high: 0.7, medium: 0.5, low: 0.3, none: 0 };
    const totalSev = this.detections.reduce((s, d) => s + (sevWeights[d.severity] || 0), 0);
    const score = Math.max(0, Math.min(100, Math.round(100 - totalSev * 18)));
    let grade, risk_level;
    if      (score >= 90) { grade = 'A'; risk_level = 'low'; }
    else if (score >= 75) { grade = 'B'; risk_level = 'low'; }
    else if (score >= 60) { grade = 'C'; risk_level = 'medium'; }
    else if (score >= 40) { grade = 'D'; risk_level = 'high'; }
    else                  { grade = 'F'; risk_level = 'critical'; }
    return { score, grade, risk_level };
  }

  renderTrustCard(siteScore) {
    const det = this.detections;
    if (det.length === 0 || !siteScore) return;

    const { score, grade, risk_level } = siteScore;

    const riskMap = {
      low:      { text: 'Low Risk',      cls: 'risk-low' },
      medium:   { text: 'Medium Risk',   cls: 'risk-medium' },
      high:     { text: 'High Risk',     cls: 'risk-high' },
      critical: { text: 'Critical Risk', cls: 'risk-critical' },
    };
    const { text: risk, cls: riskClass } = riskMap[risk_level] || riskMap.high;

    // SVG gauge: circumference = 2π×36 ≈ 226
    const circumference = 226;
    const offset = circumference - (score / 100) * circumference;
    const gaugeColor = score >= 75 ? '#22c55e' : score >= 55 ? '#f59e0b' : '#ef4444';

    document.getElementById('gaugeFill').style.strokeDashoffset = offset;
    document.getElementById('gaugeFill').style.stroke = gaugeColor;
    document.getElementById('gaugeGrade').textContent    = grade;
    document.getElementById('trustScoreNum').textContent = score;

    const badge = document.getElementById('trustRiskBadge');
    badge.textContent = risk;
    badge.className = `trust-risk-badge ${riskClass}`;

    const types = [...new Set(det.map(d => d.pattern))];
    document.getElementById('trustMeta').textContent =
      `${det.length} pattern${det.length !== 1 ? 's' : ''} across `
      + `${types.length} categor${types.length !== 1 ? 'ies' : 'y'}`;
  }

  // ── Pattern Chips ──────────────────────────────────────────────────

  renderChips() {
    const row = document.getElementById('patternChips');
    if (this.detections.length === 0) { row.style.display = 'none'; return; }

    const counts = {};
    this.detections.forEach(d => { counts[d.pattern] = (counts[d.pattern] || 0) + 1; });

    row.innerHTML = '';
    for (const [ptype, count] of Object.entries(counts).sort((a, b) => b[1] - a[1])) {
      const cfg = CONFIG.PATTERNS[ptype] || {};
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.style.color = cfg.color || '#6366f1';
      chip.innerHTML = `${cfg.icon || ''} ${cfg.label} <strong>×${count}</strong>`;
      row.appendChild(chip);
    }
    row.style.display = 'flex';
  }

  // ── Detection Cards ────────────────────────────────────────────────

  renderDetectionList() {
    const idle   = document.getElementById('idleState');
    const clean  = document.getElementById('cleanState');
    const list   = document.getElementById('detectionsList');
    const scroll = document.getElementById('detectionsScroll');

    idle.style.display  = 'none';
    clean.style.display = 'none';
    list.style.display  = 'none';

    if (this.detections.length === 0) {
      clean.style.display = 'flex';
      return;
    }

    list.style.display = 'block';
    document.getElementById('listCount').textContent = this.detections.length;

    const sorted = [...this.detections].sort((a, b) => b.confidence - a.confidence);
    scroll.innerHTML = '';

    sorted.slice(0, CONFIG.UI.POPUP_MAX_RESULTS).forEach(d => {
      const cfg   = CONFIG.PATTERNS[d.pattern] || CONFIG.PATTERNS['No Pattern'];
      const confPct = `${(d.confidence * 100).toFixed(0)}%`;
      const expl  = d.explanations && d.explanations[d.pattern]
        ? this.esc(d.explanations[d.pattern].slice(0, 130))
        : '';

      const card = document.createElement('div');
      card.className = 'det-card';
      card.style.setProperty('--pattern-color', cfg.color || '#6366f1');
      card.innerHTML = `
        <div class="det-header">
          <span class="det-pattern">${cfg.icon || ''} ${cfg.label}</span>
          <span class="det-badges">
            <span class="det-conf">${confPct}</span>
            <span class="sev-badge sev-${d.severity}">${d.severity}</span>
          </span>
        </div>
        <div class="det-text">${this.esc(d.text)}</div>
        ${expl ? `<div class="det-explanation">${expl}</div>` : ''}
        ${d.isCookieConsent ? '<div class="det-cookie-badge">🍪 Cookie Consent UI</div>' : ''}
        ${this.settings.enableFeedback !== false ? `
          <div class="det-feedback">
            <button class="fb-btn fb-correct"
              data-text="${this.escAttr(d.text)}" data-pattern="${this.escAttr(d.pattern)}">
              👍 Correct
            </button>
            <button class="fb-btn fb-wrong"
              data-text="${this.escAttr(d.text)}" data-pattern="${this.escAttr(d.pattern)}">
              👎 Wrong
            </button>
          </div>` : ''}
      `;
      scroll.appendChild(card);
    });

    if (this.detections.length > CONFIG.UI.POPUP_MAX_RESULTS) {
      const more = document.createElement('div');
      more.style.cssText = 'text-align:center;padding:8px 0;font-size:11px;color:#64748b';
      more.textContent = `+${this.detections.length - CONFIG.UI.POPUP_MAX_RESULTS} more patterns`;
      scroll.appendChild(more);
    }
  }

  showIdleState() {
    document.getElementById('idleState').style.display     = 'flex';
    document.getElementById('cleanState').style.display    = 'none';
    document.getElementById('detectionsList').style.display = 'none';
  }

  // ── Stats Tab ──────────────────────────────────────────────────────

  async loadStats() {
    try {
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.STATS);
      const stats = r[CONFIG.STORAGE_KEYS.STATS] || {
        totalScans: 0, totalDetections: 0, patternCounts: {}, sitesScanned: {},
      };

      document.getElementById('totalScans').textContent      = stats.totalScans || 0;
      document.getElementById('totalDetections').textContent = stats.totalDetections || 0;
      document.getElementById('uniqueSites').textContent     =
        Object.keys(stats.sitesScanned || {}).length;

      // Pattern breakdown bars
      const bd = document.getElementById('patternBreakdown');
      const counts = Object.entries(stats.patternCounts || {}).sort((a, b) => b[1] - a[1]);
      const maxCount = counts.length ? counts[0][1] : 1;

      if (counts.length === 0) {
        bd.innerHTML = '<div class="breakdown-empty">No data yet — scan a few pages</div>';
      } else {
        bd.innerHTML = '';
        counts.forEach(([pt, count]) => {
          const cfg = CONFIG.PATTERNS[pt] || {};
          const pct = Math.round((count / maxCount) * 100);
          const row = document.createElement('div');
          row.className = 'breakdown-row';
          row.innerHTML = `
            <div class="breakdown-label">
              <span class="breakdown-name">
                <span style="width:8px;height:8px;border-radius:50%;background:${cfg.color||'#6366f1'};display:inline-block;flex-shrink:0;margin-right:2px"></span>
                ${cfg.icon || ''} ${pt}
              </span>
              <span class="breakdown-count">${count}</span>
            </div>
            <div class="breakdown-bar-track">
              <div class="breakdown-bar-fill"
                   style="width:${pct}%;background:${cfg.color || '#6366f1'}"></div>
            </div>
          `;
          bd.appendChild(row);
        });
      }

      // Top sites list
      const ts = document.getElementById('topSites');
      const sites = Object.entries(stats.sitesScanned || {})
        .sort((a, b) => b[1] - a[1]).slice(0, 6);
      if (sites.length === 0) {
        ts.innerHTML = '<div class="breakdown-empty">No sites scanned yet</div>';
      } else {
        ts.innerHTML = '';
        sites.forEach(([domain, count]) => {
          const row = document.createElement('div');
          row.className = 'site-row';
          row.innerHTML = `
            <span class="site-domain">${this.esc(domain)}</span>
            <span class="site-count">${count}</span>
          `;
          ts.appendChild(row);
        });
      }
    } catch {}
  }

  // ── Tabs ───────────────────────────────────────────────────────────

  setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');
      });
    });
  }

  // ── Event Listeners ────────────────────────────────────────────────

  setupEventListeners() {
    document.getElementById('rescanBtn').addEventListener('click', () => this.handleRescan());
    document.getElementById('clearBtn').addEventListener('click',  () => this.handleClear());

    const toggleMap = {
      autoScanToggle:       'autoScan',
      highlightToggle:      'highlightElements',
      floatingPanelToggle:  'showFloatingPanel',
      temporalToggle:       'enableTemporal',
      feedbackToggle:       'enableFeedback',
      offlineToggle:        'offlineMode',
    };
    for (const [id, key] of Object.entries(toggleMap)) {
      document.getElementById(id).addEventListener('change', e => {
        this.saveSetting(key, e.target.checked);
      });
    }

    const slider = document.getElementById('thresholdSlider');
    slider.addEventListener('input', e => {
      document.getElementById('thresholdValue').textContent = `${e.target.value}%`;
      this._updateSliderTrack(slider);
    });
    slider.addEventListener('change', e => {
      this.saveSetting('confidenceThreshold', parseInt(e.target.value) / 100);
    });

    document.getElementById('saveUrlBtn').addEventListener('click', () => {
      const url = document.getElementById('apiUrlInput').value.trim();
      if (url) this.saveSetting('apiUrl', url);
    });

    document.getElementById('patternToggles').addEventListener('change', e => {
      const pt = e.target.dataset.pattern;
      if (pt) {
        const enabled = { ...(this.settings.enabledPatterns || {}) };
        enabled[pt] = e.target.checked;
        this.saveSetting('enabledPatterns', enabled);
      }
    });

    document.getElementById('whitelistBtn').addEventListener('click', () => this.addToWhitelist());

    document.getElementById('resetStatsBtn').addEventListener('click', async () => {
      if (!confirm('Reset all PatternShield statistics?')) return;
      await chrome.storage.sync.set({
        [CONFIG.STORAGE_KEYS.STATS]: {
          totalScans: 0, totalDetections: 0, patternCounts: {}, sitesScanned: {},
        }
      });
      await this.loadStats();
    });

    // Feedback buttons (event delegation on scroll container)
    document.getElementById('detectionsScroll').addEventListener('click', e => {
      const btn = e.target.closest('.fb-btn');
      if (!btn) return;
      const text    = btn.dataset.text    || '';
      const pattern = btn.dataset.pattern || '';
      const correct = btn.classList.contains('fb-correct');
      this._submitFeedback(btn, text, pattern, correct);
    });

    // Live update from content script
    chrome.runtime.onMessage.addListener(req => {
      if (req.action === 'updateDetections') {
        this.detections = (req.data && req.data.patterns) || [];
        this.renderScan();
      }
    });
  }

  async _submitFeedback(btn, text, pattern, isCorrect) {
    try {
      const domain = this.currentTab ? new URL(this.currentTab.url).hostname : '';
      await this._bgProxy('/feedback', 'POST', {
        text, detected_pattern: pattern, is_correct: isCorrect, domain,
      });
      const feedbackDiv = btn.closest('.det-feedback');
      if (feedbackDiv) {
        feedbackDiv.innerHTML =
          `<span class="fb-done">${isCorrect ? '✓ Correct' : '✗ Wrong'} — thank you!</span>`;
      }
    } catch {}
  }

  // ── Rescan / Clear ─────────────────────────────────────────────────

  async handleRescan() {
    const btn = document.getElementById('rescanBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Scanning…';

    try {
      await chrome.tabs.sendMessage(this.currentTab.id, { action: 'rescan' });
      setTimeout(async () => {
        await this.loadDetections();
        btn.disabled = false;
        btn.innerHTML = `
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
            <path d="M23 4v6h-6M1 20v-6h6M20.49 9A9 9 0 005.64 5.64L1 10M23 14l-4.64 4.36A9 9 0 013.51 15"
                  stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Scan`;
      }, 3500);
    } catch {
      btn.disabled = false;
      btn.textContent = 'Scan';
    }
  }

  async handleClear() {
    try {
      await chrome.tabs.sendMessage(this.currentTab.id, { action: 'clearHighlights' });
    } catch {}
    this.detections = [];
    this.showIdleState();
    document.getElementById('patternChips').style.display = 'none';
    // Reset gauge
    document.getElementById('gaugeGrade').textContent     = '—';
    document.getElementById('gaugeFill').style.strokeDashoffset = 226;
    document.getElementById('gaugeFill').style.stroke     = '#6366f1';
    document.getElementById('trustScoreNum').textContent  = '—';
    document.getElementById('trustRiskBadge').textContent = 'Run a scan';
    document.getElementById('trustRiskBadge').className   = 'trust-risk-badge';
    document.getElementById('trustMeta').textContent      = 'Click Scan to analyze this page';
  }

  // ── Whitelist ──────────────────────────────────────────────────────

  async addToWhitelist() {
    try {
      const domain = new URL(this.currentTab.url).hostname;
      const r  = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.WHITELIST);
      const wl = r[CONFIG.STORAGE_KEYS.WHITELIST] || [];
      if (!wl.includes(domain)) {
        wl.push(domain);
        await chrome.storage.sync.set({ [CONFIG.STORAGE_KEYS.WHITELIST]: wl });
      }
      document.getElementById('whitelistBtn').textContent = `✓ ${domain} whitelisted`;
    } catch {}
  }

  // ── Helpers ────────────────────────────────────────────────────────

  _bgProxy(endpoint, method = 'GET', body = null) {
    return new Promise(resolve => {
      chrome.runtime.sendMessage(
        { action: 'apiProxy', endpoint, method, body },
        res => {
          if (chrome.runtime.lastError) resolve({ success: false });
          else resolve(res || { success: false });
        }
      );
    });
  }

  _updateSliderTrack(slider) {
    const min = +slider.min, max = +slider.max, val = +slider.value;
    const pct = ((val - min) / (max - min)) * 100;
    slider.style.background =
      `linear-gradient(to right,#6366f1 ${pct}%,#263145 ${pct}%)`;
  }

  esc(t) {
    const d = document.createElement('div');
    d.textContent = t;
    return d.innerHTML;
  }

  escAttr(t) {
    return String(t)
      .replace(/&/g, '&amp;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }
}

document.addEventListener('DOMContentLoaded', () => new PopupController());
