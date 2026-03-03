/**
 * PatternShield Popup v2.1 (FIXED)
 * FIX: Health check uses background proxy instead of direct fetch
 */

class PopupController {
  constructor() {
    this.detections = [];
    this.currentTab = null;
    this.settings = CONFIG.DEFAULT_SETTINGS;
    this.init();
  }

  async init() {
    this.currentTab = await this.getCurrentTab();
    await this.loadSettings();
    this.setupTabs();
    this.setupEventListeners();
    await this.checkAPIHealth();
    await this.loadDetections();
    this.populateSettings();
    await this.loadStats();
  }

  async getCurrentTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }

  // ── Tabs ──────────────────────────────────────────────────────────

  setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
      });
    });
  }

  // ── API Health (via background proxy) ─────────────────────────────

  async checkAPIHealth() {
    const dot = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    try {
      // Use background proxy instead of direct fetch
      const result = await new Promise((resolve) => {
        chrome.runtime.sendMessage(
          { action: 'apiProxy', endpoint: '/health', method: 'GET' },
          (response) => {
            if (chrome.runtime.lastError) {
              resolve({ success: false });
            } else {
              resolve(response || { success: false });
            }
          }
        );
      });

      if (result.success && result.data) {
        dot.classList.remove('offline');
        text.textContent = this.settings.offlineMode ? 'Offline Mode' : `v${result.data.version || '2.0'}`;
      } else {
        throw new Error('not reachable');
      }
    } catch {
      dot.classList.add('offline');
      text.textContent = this.settings.offlineMode ? 'Offline Mode' : 'API Offline';
    }
  }

  // ── Settings ──────────────────────────────────────────────────────

  async loadSettings() {
    try {
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.SETTINGS);
      this.settings = { ...CONFIG.DEFAULT_SETTINGS, ...(r[CONFIG.STORAGE_KEYS.SETTINGS] || {}) };
    } catch {}
  }

  populateSettings() {
    document.getElementById('autoScanToggle').checked = this.settings.autoScan;
    document.getElementById('highlightToggle').checked = this.settings.highlightElements;
    document.getElementById('offlineToggle').checked = this.settings.offlineMode || false;
    document.getElementById('feedbackToggle').checked = this.settings.enableFeedback !== false;
    document.getElementById('temporalToggle').checked = this.settings.enableTemporal !== false;
    document.getElementById('thresholdSlider').value = (this.settings.confidenceThreshold || 0.35) * 100;
    document.getElementById('thresholdValue').textContent = `${Math.round((this.settings.confidenceThreshold || 0.35) * 100)}%`;
    document.getElementById('apiUrlInput').value = this.settings.apiUrl || CONFIG.API_URL;

    // Pattern toggles
    const container = document.getElementById('patternToggles');
    container.innerHTML = '';
    const enabled = this.settings.enabledPatterns || {};
    for (const [ptype, cfg] of Object.entries(CONFIG.PATTERNS)) {
      if (ptype === 'No Pattern') continue;
      const label = document.createElement('label');
      label.className = 'toggle-setting compact';
      label.innerHTML = `
        <input type="checkbox" data-pattern="${ptype}" ${enabled[ptype] !== false ? 'checked' : ''}>
        <span style="color:${cfg.color}">${cfg.icon || ''}</span>
        <span>${cfg.label}</span>
      `;
      container.appendChild(label);
    }
  }

  async saveSetting(key, value) {
    this.settings[key] = value;
    await chrome.storage.sync.set({ [CONFIG.STORAGE_KEYS.SETTINGS]: this.settings });
    try {
      await chrome.tabs.sendMessage(this.currentTab.id, {
        action: 'updateSettings', settings: this.settings
      });
    } catch {}
  }

  // ── Detections ────────────────────────────────────────────────────

  async loadDetections() {
    try {
      const response = await chrome.tabs.sendMessage(this.currentTab.id, { action: 'getDetections' });
      if (response) {
        this.detections = response.patterns || [];
        this.updateUI();
      }
    } catch {
      this.showEmpty('Click Rescan to detect patterns');
    }
  }

  updateUI() {
    document.getElementById('detectionCount').textContent = this.detections.length;

    if (this.detections.length > 0) {
      const avgConf = this.detections.reduce((s, d) => s + d.confidence, 0) / this.detections.length;
      document.getElementById('confidenceAvg').textContent = `${(avgConf * 100).toFixed(0)}%`;

      const severities = ['critical', 'high', 'medium', 'low', 'none'];
      let maxSev = 'none';
      for (const s of severities) {
        if (this.detections.some(d => d.severity === s)) { maxSev = s; break; }
      }
      const sevEl = document.getElementById('severityMax');
      sevEl.textContent = maxSev.charAt(0).toUpperCase() + maxSev.slice(1);
      sevEl.style.color = CONFIG.SEVERITY_COLORS[maxSev] || '#6b7280';

      this.showSiteScore();
    } else {
      document.getElementById('confidenceAvg').textContent = '0%';
      document.getElementById('severityMax').textContent = '—';
    }

    const list = document.getElementById('detectionsList');
    if (this.detections.length === 0) {
      this.showEmpty('No patterns detected ✅');
      return;
    }

    list.innerHTML = '';
    const sorted = [...this.detections].sort((a, b) => b.confidence - a.confidence);
    sorted.slice(0, CONFIG.UI.POPUP_MAX_RESULTS).forEach(d => {
      const cfg = CONFIG.PATTERNS[d.pattern] || CONFIG.PATTERNS['No Pattern'];
      const item = document.createElement('div');
      item.className = 'detection-item';
      item.style.setProperty('--pattern-color', cfg.color);
      item.innerHTML = `
        <div class="detection-header">
          <span class="detection-pattern">${cfg.icon || ''} ${cfg.label}</span>
          <span class="detection-confidence severity-${d.severity}">${(d.confidence * 100).toFixed(0)}%</span>
        </div>
        <div class="detection-text">${this.esc(d.text)}</div>
        ${d.isCookieConsent ? '<div class="detection-badge">🍪 Cookie</div>' : ''}
      `;
      list.appendChild(item);
    });

    if (this.detections.length > CONFIG.UI.POPUP_MAX_RESULTS) {
      const more = document.createElement('div');
      more.className = 'empty-state compact';
      more.innerHTML = `<p>+${this.detections.length - CONFIG.UI.POPUP_MAX_RESULTS} more</p>`;
      list.appendChild(more);
    }
  }

  async showSiteScore() {
    const total = this.detections.length;
    if (total === 0) return;
    const sevSum = this.detections.reduce((s, d) => s + (d.confidence || 0), 0);
    const score = Math.max(0, 100 - Math.round(sevSum * 15));
    let grade = 'A', risk = 'Low';
    if (score < 40) { grade = 'F'; risk = 'Critical'; }
    else if (score < 60) { grade = 'D'; risk = 'High'; }
    else if (score < 75) { grade = 'C'; risk = 'Medium'; }
    else if (score < 90) { grade = 'B'; risk = 'Low'; }

    const card = document.getElementById('siteScoreCard');
    card.style.display = 'flex';
    document.getElementById('scoreGrade').textContent = grade;
    document.getElementById('scoreGrade').className = `score-badge grade-${grade}`;
    document.getElementById('scoreValue').textContent = score;
    document.getElementById('scoreRisk').textContent = `${risk} Risk`;
  }

  showEmpty(msg) {
    document.getElementById('detectionsList').innerHTML = `<div class="empty-state"><p>${msg}</p></div>`;
  }

  // ── Stats ─────────────────────────────────────────────────────────

  async loadStats() {
    try {
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.STATS);
      const stats = r[CONFIG.STORAGE_KEYS.STATS] || { totalScans: 0, totalDetections: 0, patternCounts: {}, sitesScanned: {} };

      document.getElementById('totalScans').textContent = stats.totalScans;
      document.getElementById('totalDetections').textContent = stats.totalDetections;

      const bd = document.getElementById('patternBreakdown');
      bd.innerHTML = '';
      const sorted = Object.entries(stats.patternCounts || {}).sort((a, b) => b[1] - a[1]);
      if (sorted.length === 0) {
        bd.innerHTML = '<div class="empty-state compact"><p>No data yet</p></div>';
      } else {
        sorted.forEach(([pt, count]) => {
          const cfg = CONFIG.PATTERNS[pt] || {};
          const row = document.createElement('div');
          row.className = 'stat-row';
          row.innerHTML = `<span style="color:${cfg.color || '#6b7280'}">${cfg.icon || ''} ${pt}</span><strong>${count}</strong>`;
          bd.appendChild(row);
        });
      }

      const ts = document.getElementById('topSites');
      ts.innerHTML = '';
      const sites = Object.entries(stats.sitesScanned || {}).sort((a, b) => b[1] - a[1]).slice(0, 5);
      if (sites.length === 0) {
        ts.innerHTML = '<div class="empty-state compact"><p>No data yet</p></div>';
      } else {
        sites.forEach(([domain, count]) => {
          const row = document.createElement('div');
          row.className = 'stat-row';
          row.innerHTML = `<span>${domain}</span><strong>${count}</strong>`;
          ts.appendChild(row);
        });
      }
    } catch {}
  }

  // ── Events ────────────────────────────────────────────────────────

  setupEventListeners() {
    document.getElementById('rescanBtn').addEventListener('click', () => this.handleRescan());
    document.getElementById('clearBtn').addEventListener('click', () => this.handleClear());

    const toggleMap = {
      autoScanToggle: 'autoScan',
      highlightToggle: 'highlightElements',
      offlineToggle: 'offlineMode',
      feedbackToggle: 'enableFeedback',
      temporalToggle: 'enableTemporal',
    };
    for (const [id, key] of Object.entries(toggleMap)) {
      document.getElementById(id).addEventListener('change', (e) => {
        this.saveSetting(key, e.target.checked);
      });
    }

    const slider = document.getElementById('thresholdSlider');
    slider.addEventListener('input', (e) => {
      document.getElementById('thresholdValue').textContent = `${e.target.value}%`;
    });
    slider.addEventListener('change', (e) => {
      this.saveSetting('confidenceThreshold', parseInt(e.target.value) / 100);
    });

    document.getElementById('saveUrlBtn').addEventListener('click', () => {
      const url = document.getElementById('apiUrlInput').value.trim();
      if (url) this.saveSetting('apiUrl', url);
    });

    document.getElementById('patternToggles').addEventListener('change', (e) => {
      if (e.target.dataset.pattern) {
        const enabled = { ...(this.settings.enabledPatterns || {}) };
        enabled[e.target.dataset.pattern] = e.target.checked;
        this.saveSetting('enabledPatterns', enabled);
      }
    });

    document.getElementById('whitelistBtn').addEventListener('click', () => this.addToWhitelist());

    document.getElementById('resetStatsBtn').addEventListener('click', async () => {
      await chrome.storage.sync.set({
        [CONFIG.STORAGE_KEYS.STATS]: { totalScans: 0, totalDetections: 0, patternCounts: {}, sitesScanned: {} }
      });
      await this.loadStats();
    });

    chrome.runtime.onMessage.addListener((req) => {
      if (req.action === 'updateDetections') {
        this.detections = req.data.patterns || [];
        this.updateUI();
      }
    });
  }

  async handleRescan() {
    const btn = document.getElementById('rescanBtn');
    btn.disabled = true; btn.textContent = '⏳ Scanning...';
    try {
      await chrome.tabs.sendMessage(this.currentTab.id, { action: 'rescan' });
      setTimeout(async () => {
        await this.loadDetections();
        btn.disabled = false; btn.textContent = '🔄 Rescan';
      }, 3000);
    } catch {
      btn.disabled = false; btn.textContent = '🔄 Rescan';
    }
  }

  async handleClear() {
    try {
      await chrome.tabs.sendMessage(this.currentTab.id, { action: 'clearHighlights' });
      this.detections = [];
      this.updateUI();
      document.getElementById('siteScoreCard').style.display = 'none';
    } catch {}
  }

  async addToWhitelist() {
    try {
      const domain = new URL(this.currentTab.url).hostname;
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.WHITELIST);
      const wl = r[CONFIG.STORAGE_KEYS.WHITELIST] || [];
      if (!wl.includes(domain)) {
        wl.push(domain);
        await chrome.storage.sync.set({ [CONFIG.STORAGE_KEYS.WHITELIST]: wl });
      }
      document.getElementById('whitelistBtn').textContent = `✓ ${domain} whitelisted`;
    } catch {}
  }

  esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
}

document.addEventListener('DOMContentLoaded', () => new PopupController());
