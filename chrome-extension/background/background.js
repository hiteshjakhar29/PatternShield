/**
 * PatternShield Background Service Worker v2.1
 * Proxies ALL API calls so content scripts on HTTPS pages
 * can reach the HTTP localhost API without mixed-content blocking.
 */

const DEFAULT_API_URL = 'http://127.0.0.1:5000';
const SETTINGS_KEY    = 'patternshield_settings'; // must match CONFIG.STORAGE_KEYS.SETTINGS

const DEFAULT_INSTALL_SETTINGS = {
  autoScan:            true,
  dynamicScan:         true,
  enableTemporal:      true,
  highlightElements:   true,
  showFloatingPanel:   true,
  richTooltips:        true,
  enableFeedback:      true,
  offlineMode:         false,
  cookieAnalysis:      true,
  confidenceThreshold: 0.35,
  apiUrl:              DEFAULT_API_URL,
  enabledPatterns:     {},
};

// ── API Proxy ────────────────────────────────────────────────────────

async function proxyAPICall(request) {
  const { endpoint, method, body } = request;

  try {
    let apiUrl = DEFAULT_API_URL;
    try {
      const result = await chrome.storage.sync.get(SETTINGS_KEY);
      const settings = result[SETTINGS_KEY];
      if (settings && settings.apiUrl) apiUrl = settings.apiUrl;
    } catch {}

    const url = `${apiUrl}${endpoint}`;
    const options = {
      method: method || 'GET',
      headers: { 'Content-Type': 'application/json' },
    };
    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    options.signal = controller.signal;

    const res = await fetch(url, options);
    clearTimeout(timeout);

    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}`, status: res.status };
    }
    const data = await res.json();
    return { success: true, data };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

// ── Message Listener ─────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.action === 'apiProxy') {
    proxyAPICall(msg)
      .then(result => sendResponse(result))
      .catch(e => sendResponse({ success: false, error: e.message }));
    return true; // keep channel open for async
  }

  if (msg.action === 'updateBadge') {
    const count = msg.count || 0;
    chrome.action.setBadgeText({ text: count > 0 ? String(count) : '' });
    chrome.action.setBadgeBackgroundColor({
      color: count >= 10 ? '#DC2626' : count > 4 ? '#EF4444' : count > 0 ? '#F59E0B' : '#10B981',
    });
    sendResponse({ success: true });
    return false;
  }

  if (msg.action === 'updateDetections') {
    sendResponse({ success: true });
    return false;
  }

  if (msg.action === 'showNotification') {
    const { count, domain } = msg;
    chrome.notifications.create(`ps-scan-${Date.now()}`, {
      type:    'basic',
      iconUrl: 'icons/icon48.png',
      title:   'PatternShield',
      message: `${count} dark pattern${count !== 1 ? 's' : ''} detected on ${domain}`,
      priority: 1,
    });
    sendResponse({ success: true });
    return false;
  }

  return false;
});

// ── Install / Upgrade ────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(({ reason }) => {
  console.log(`PatternShield v2.1 — ${reason}`);
  chrome.storage.sync.get(SETTINGS_KEY, result => {
    if (!result[SETTINGS_KEY]) {
      chrome.storage.sync.set({ [SETTINGS_KEY]: DEFAULT_INSTALL_SETTINGS });
      console.log('[PatternShield] Default settings initialised');
    } else {
      // Merge in any new keys added in this version without overwriting user prefs
      const merged = { ...DEFAULT_INSTALL_SETTINGS, ...result[SETTINGS_KEY] };
      chrome.storage.sync.set({ [SETTINGS_KEY]: merged });
    }
  });
});
