/**
 * PatternShield Options Page v2.1
 * Full settings page with sections for scanning, detection, appearance,
 * privacy, network, whitelist, and about.
 */

const SETTINGS_KEY  = CONFIG.STORAGE_KEYS.SETTINGS;
const WHITELIST_KEY = CONFIG.STORAGE_KEYS.WHITELIST;
const STATS_KEY     = CONFIG.STORAGE_KEYS.STATS;
const OFFLINE_KEY   = CONFIG.STORAGE_KEYS.OFFLINE_RULES;

let settings  = { ...CONFIG.DEFAULT_SETTINGS };
let whitelist = [];

// ── Init ─────────────────────────────────────────────────────────

async function init() {
  await loadSettings();
  await loadWhitelist();
  renderSettings();
  renderPatternCategories();
  renderWhitelist();
  setupListeners();
  setupSidebarNav();
}

// ── Load / Save ───────────────────────────────────────────────────

async function loadSettings() {
  try {
    const r = await chrome.storage.sync.get(SETTINGS_KEY);
    settings = { ...CONFIG.DEFAULT_SETTINGS, ...(r[SETTINGS_KEY] || {}) };
  } catch {}
}

async function saveSettings() {
  try {
    await chrome.storage.sync.set({ [SETTINGS_KEY]: settings });
    showToast('Settings saved', 'success');
  } catch {
    showToast('Could not save settings', 'error');
  }
}

async function loadWhitelist() {
  try {
    const r = await chrome.storage.sync.get(WHITELIST_KEY);
    whitelist = r[WHITELIST_KEY] || [];
  } catch {}
}

// ── Render ────────────────────────────────────────────────────────

function renderSettings() {
  bind('autoScan',         settings.autoScan);
  bind('dynamicScan',      settings.dynamicScan !== false);
  bind('enableTemporal',   settings.enableTemporal !== false);
  bind('highlightElements', settings.highlightElements);
  bind('showFloatingPanel', settings.showFloatingPanel !== false);
  bind('richTooltips',     settings.richTooltips !== false);
  bind('enableFeedback',   settings.enableFeedback !== false);
  bind('offlineMode',      settings.offlineMode || false);
  bind('cookieAnalysis',   settings.cookieAnalysis !== false);

  const slider = document.getElementById('confidenceThreshold');
  const val    = Math.round((settings.confidenceThreshold || 0.35) * 100);
  slider.value = val;
  document.getElementById('thresholdDisplay').textContent = `${val}%`;
  updateSliderGradient(slider);

  document.getElementById('apiUrl').value = settings.apiUrl || CONFIG.API_URL;
}

function renderPatternCategories() {
  const list = document.getElementById('patternCategoryList');
  list.innerHTML = '';
  const enabled = settings.enabledPatterns || {};

  for (const [ptype, cfg] of Object.entries(CONFIG.PATTERNS)) {
    if (ptype === 'No Pattern') continue;
    const item = document.createElement('div');
    item.className = 'pattern-item';
    item.innerHTML = `
      <div class="pattern-item-left">
        <span class="pattern-dot" style="background:${cfg.color}"></span>
        <div>
          <div class="pattern-item-name">${cfg.icon || ''} ${cfg.label}</div>
          <div class="pattern-item-desc">${cfg.description}</div>
        </div>
      </div>
      <label class="toggle">
        <input type="checkbox" data-pattern="${ptype}"
               ${enabled[ptype] !== false ? 'checked' : ''}>
        <span class="toggle-slider"></span>
      </label>
    `;
    list.appendChild(item);
  }
}

function renderWhitelist() {
  const container = document.getElementById('whitelistItems');
  container.innerHTML = '';

  if (whitelist.length === 0) {
    container.innerHTML = '<div class="whitelist-empty">No sites whitelisted yet</div>';
    return;
  }

  whitelist.forEach(domain => {
    const item = document.createElement('div');
    item.className = 'whitelist-item';
    item.innerHTML = `
      <span>${esc(domain)}</span>
      <button class="wl-remove" data-domain="${escAttr(domain)}">Remove</button>
    `;
    container.appendChild(item);
  });
}

// ── Listeners ─────────────────────────────────────────────────────

function setupListeners() {
  // Save all
  document.getElementById('saveAllBtn').addEventListener('click', collectAndSave);

  // Reset
  document.getElementById('resetBtn').addEventListener('click', async () => {
    if (!confirm('Reset all PatternShield settings to defaults?')) return;
    settings = { ...CONFIG.DEFAULT_SETTINGS };
    renderSettings();
    renderPatternCategories();
    await saveSettings();
  });

  // Threshold slider live update
  const slider = document.getElementById('confidenceThreshold');
  slider.addEventListener('input', () => {
    document.getElementById('thresholdDisplay').textContent = `${slider.value}%`;
    updateSliderGradient(slider);
  });

  // Test connection
  document.getElementById('testConnectionBtn').addEventListener('click', async () => {
    const url    = document.getElementById('apiUrl').value.trim();
    const status = document.getElementById('connectionStatus');
    status.textContent = 'Testing…';
    status.className   = 'connection-status';
    try {
      const r = await fetch(`${url}/health`, { signal: AbortSignal.timeout(5000) });
      if (r.ok) {
        const data = await r.json();
        status.textContent = `Connected — PatternShield API v${data.version || '?'}`;
        status.className   = 'connection-status ok';
      } else {
        throw new Error(`HTTP ${r.status}`);
      }
    } catch (e) {
      status.textContent = `Connection failed: ${e.message}`;
      status.className   = 'connection-status fail';
    }
  });

  // Add to whitelist
  document.getElementById('addWhitelistBtn').addEventListener('click', async () => {
    const input  = document.getElementById('whitelistInput');
    const domain = input.value.trim().toLowerCase().replace(/^https?:\/\//, '').split('/')[0];
    if (!domain) return;
    if (!whitelist.includes(domain)) {
      whitelist.push(domain);
      await chrome.storage.sync.set({ [WHITELIST_KEY]: whitelist });
    }
    input.value = '';
    renderWhitelist();
    showToast(`${domain} added to whitelist`, 'success');
  });

  // Remove from whitelist (delegation)
  document.getElementById('whitelistItems').addEventListener('click', async e => {
    const btn = e.target.closest('.wl-remove');
    if (!btn) return;
    const domain = btn.dataset.domain;
    whitelist = whitelist.filter(d => d !== domain);
    await chrome.storage.sync.set({ [WHITELIST_KEY]: whitelist });
    renderWhitelist();
    showToast(`${domain} removed`, 'success');
  });

  // Pattern category toggles
  document.getElementById('patternCategoryList').addEventListener('change', e => {
    const pt = e.target.dataset.pattern;
    if (pt) {
      const enabled = { ...(settings.enabledPatterns || {}) };
      enabled[pt] = e.target.checked;
      settings.enabledPatterns = enabled;
    }
  });

  // Export stats
  document.getElementById('exportStatsBtn').addEventListener('click', async () => {
    try {
      const r = await chrome.storage.sync.get(STATS_KEY);
      const blob = new Blob([JSON.stringify(r[STATS_KEY] || {}, null, 2)], { type: 'application/json' });
      const url  = URL.createObjectURL(blob);
      const a    = document.createElement('a');
      a.href = url; a.download = 'patternshield-stats.json'; a.click();
      URL.revokeObjectURL(url);
    } catch { showToast('Export failed', 'error'); }
  });

  // Clear offline cache
  document.getElementById('clearCacheBtn').addEventListener('click', async () => {
    await chrome.storage.local.remove(OFFLINE_KEY);
    showToast('Offline cache cleared', 'success');
  });

  // Clear dismissed panel domains
  document.getElementById('clearDismissedBtn').addEventListener('click', async () => {
    await chrome.storage.local.remove(CONFIG.STORAGE_KEYS.DISMISSED_PANELS);
    showToast('Dismissed panel sites cleared — panels will show again', 'success');
  });

  // Reset all data
  document.getElementById('clearAllBtn').addEventListener('click', async () => {
    if (!confirm('This will clear ALL PatternShield data including stats and settings. Continue?')) return;
    await chrome.storage.sync.clear();
    await chrome.storage.local.clear();
    settings  = { ...CONFIG.DEFAULT_SETTINGS };
    whitelist = [];
    renderSettings();
    renderPatternCategories();
    renderWhitelist();
    showToast('All data cleared — settings reset to defaults', 'success');
  });
}

// ── Collect & Save ─────────────────────────────────────────────────

async function collectAndSave() {
  const g = id => document.getElementById(id);

  settings.autoScan          = g('autoScan').checked;
  settings.dynamicScan       = g('dynamicScan').checked;
  settings.enableTemporal    = g('enableTemporal').checked;
  settings.highlightElements = g('highlightElements').checked;
  settings.showFloatingPanel = g('showFloatingPanel').checked;
  settings.richTooltips      = g('richTooltips').checked;
  settings.enableFeedback    = g('enableFeedback').checked;
  settings.offlineMode       = g('offlineMode').checked;
  settings.cookieAnalysis    = g('cookieAnalysis').checked;
  settings.apiUrl            = g('apiUrl').value.trim() || CONFIG.API_URL;
  settings.confidenceThreshold = parseInt(g('confidenceThreshold').value) / 100;

  await saveSettings();
}

// ── Sidebar nav smooth scroll ──────────────────────────────────────

function setupSidebarNav() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const id = link.getAttribute('href').slice(1);
      const el = document.getElementById(id);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
      document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
      link.classList.add('active');
    });
  });
}

// ── Helpers ────────────────────────────────────────────────────────

function bind(id, val) {
  const el = document.getElementById(id);
  if (el) el.checked = !!val;
}

function updateSliderGradient(slider) {
  const min = +slider.min, max = +slider.max, val = +slider.value;
  const pct = ((val - min) / (max - min)) * 100;
  slider.style.background =
    `linear-gradient(to right,#6366f1 ${pct}%,#263145 ${pct}%)`;
}

function showToast(msg, type = '') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className   = `toast show ${type}`;
  setTimeout(() => { toast.className = 'toast'; }, 3000);
}

function esc(t) { const d = document.createElement('div'); d.textContent = t; return d.innerHTML; }
function escAttr(t) {
  return String(t).replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

document.addEventListener('DOMContentLoaded', init);
