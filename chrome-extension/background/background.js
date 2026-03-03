/**
 * PatternShield Background Service Worker v2.1 (FIXED)
 * Proxies ALL API calls so content scripts on HTTPS pages
 * can reach the HTTP localhost API without mixed-content blocking.
 *
 * FIX: Storage key now matches config.js ('patternshield_settings')
 */

const DEFAULT_API_URL = 'http://127.0.0.1:5000';
const SETTINGS_KEY = 'patternshield_settings'; // MUST match CONFIG.STORAGE_KEYS.SETTINGS

// ── API Proxy ───────────────────────────────────────────────────────

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

// ── Message Listener ────────────────────────────────────────────────

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
      color: count > 5 ? '#EF4444' : count > 0 ? '#F59E0B' : '#10B981'
    });
    sendResponse({ success: true });
    return false;
  }

  if (msg.action === 'updateDetections') {
    sendResponse({ success: true });
    return false;
  }

  return false;
});

// ── Install ─────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  console.log('PatternShield v2.1 installed');
  chrome.storage.sync.get(SETTINGS_KEY, (result) => {
    if (!result[SETTINGS_KEY]) {
      chrome.storage.sync.set({
        [SETTINGS_KEY]: {
          autoScan: true,
          highlightElements: true,
          offlineMode: false,
          enableFeedback: true,
          enableTemporal: true,
          confidenceThreshold: 0.35,
          apiUrl: DEFAULT_API_URL,
          enabledPatterns: {},
        }
      });
    }
  });
});
