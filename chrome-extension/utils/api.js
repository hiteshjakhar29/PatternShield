/**
 * PatternShield API Client v2.1 (FIXED)
 * ALL fetch calls go through background.js proxy to avoid
 * Chrome's mixed-content blocking (HTTPS page → HTTP API).
 */

class PatternShieldAPI {
  constructor() {
    this.requestCache = new Map();
    this.cacheTimeout = 5 * 60 * 1000;
    this.offlineRules = null;
    this.apiAvailable = null; // null = unknown, true/false = tested
  }

  // ── Core: Send request via background service worker ──────────────

  async _proxy(endpoint, method = 'GET', body = null) {
    return new Promise((resolve) => {
      try {
        chrome.runtime.sendMessage(
          { action: 'apiProxy', endpoint, method, body },
          (response) => {
            if (chrome.runtime.lastError) {
              console.warn('PatternShield: runtime error:', chrome.runtime.lastError.message);
              resolve({ success: false, error: chrome.runtime.lastError.message });
            } else {
              resolve(response || { success: false, error: 'No response from background' });
            }
          }
        );
      } catch (e) {
        console.warn('PatternShield: sendMessage failed:', e.message);
        resolve({ success: false, error: e.message });
      }
    });
  }

  // ── Connection Test ───────────────────────────────────────────────

  async testConnection() {
    const res = await this._proxy('/health');
    this.apiAvailable = res.success;
    if (res.success) {
      console.log('PatternShield: ✅ API connected -', JSON.stringify(res.data));
    } else {
      console.warn('PatternShield: ❌ API unreachable -', res.error);
      console.warn('PatternShield: Make sure backend is running: python3 app.py');
    }
    return res.success;
  }

  // ── Settings ──────────────────────────────────────────────────────

  async getSettings() {
    try {
      const result = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.SETTINGS);
      return result[CONFIG.STORAGE_KEYS.SETTINGS] || CONFIG.DEFAULT_SETTINGS;
    } catch { return CONFIG.DEFAULT_SETTINGS; }
  }

  // ── Health Check ──────────────────────────────────────────────────

  async checkHealth() {
    return await this._proxy('/health');
  }

  // ── Single Element Analysis ───────────────────────────────────────

  async analyzeText(text, elementType = 'div', color = '#000000', extras = {}) {
    const settings = await this.getSettings();
    if (settings.offlineMode) {
      return this.analyzeOfflineSync(text, elementType, color);
    }

    const cacheKey = `${text}:${elementType}`;
    if (this.requestCache.has(cacheKey)) {
      const cached = this.requestCache.get(cacheKey);
      if (Date.now() - cached.ts < this.cacheTimeout) return cached.result;
      this.requestCache.delete(cacheKey);
    }

    const res = await this._proxy('/analyze', 'POST', {
      text, element_type: elementType, color,
      font_size: extras.fontSize, opacity: extras.opacity,
      use_enhanced: true,
    });

    if (res.success) {
      this.requestCache.set(cacheKey, { result: res.data, ts: Date.now() });
      return res.data;
    }

    console.warn('PatternShield: API failed, offline fallback:', res.error);
    return this.analyzeOfflineSync(text, elementType, color);
  }

  // ── Batch Analysis ────────────────────────────────────────────────

  async batchAnalyze(elements) {
    const settings = await this.getSettings();
    if (settings.offlineMode) {
      return elements.map(el => this.analyzeOfflineSync(
        el.text || el, el.element_type || 'div', el.color || '#000000'
      ));
    }

    const payload = elements.map(el => {
      if (typeof el === 'string') return { text: el };
      return {
        text: el.text,
        element_type: el.element_type || el.type || 'div',
        color: el.color || '#000000',
        font_size: el.fontSize,
        opacity: el.opacity,
      };
    });

    const res = await this._proxy('/batch/analyze', 'POST', { elements: payload });

    if (res.success && res.data && Array.isArray(res.data.results)) {
      return res.data.results;
    }

    // Fallback to offline
    console.warn('PatternShield: Batch failed, offline fallback:', res.error || 'no results');
    return elements.map(el => this.analyzeOfflineSync(
      el.text || el, el.element_type || el.type || 'div', el.color || '#000000'
    ));
  }

  // ── Site Score ────────────────────────────────────────────────────

  async getSiteScore(detections, domain) {
    const res = await this._proxy('/site-score', 'POST', { detections, domain });
    return res.success ? res.data : null;
  }

  // ── Feedback ──────────────────────────────────────────────────────

  async submitFeedback(text, detectedPattern, isCorrect, userLabel = '', domain = '') {
    const res = await this._proxy('/feedback', 'POST', {
      text, detected_pattern: detectedPattern,
      is_correct: isCorrect, user_label: userLabel, domain,
    });
    return res.success;
  }

  // ── Temporal ──────────────────────────────────────────────────────

  async recordTemporal(domain, elements) {
    await this._proxy('/temporal/record', 'POST', { domain, elements });
  }

  async checkTemporal(domain, elements) {
    const res = await this._proxy('/temporal/check', 'POST', { domain, elements });
    return res.success ? res.data : { flags: [] };
  }

  // ── Offline Rules ─────────────────────────────────────────────────

  async loadOfflineRules() {
    try {
      // Try loading from local storage first
      const stored = await chrome.storage.local.get(CONFIG.STORAGE_KEYS.OFFLINE_RULES);
      if (stored[CONFIG.STORAGE_KEYS.OFFLINE_RULES]) {
        this.offlineRules = stored[CONFIG.STORAGE_KEYS.OFFLINE_RULES];
        console.log('PatternShield: Offline rules loaded from cache');
        return;
      }
      // Fetch from API via proxy
      const res = await this._proxy('/offline-rules');
      if (res.success && res.data && res.data.rules) {
        this.offlineRules = res.data.rules;
        await chrome.storage.local.set({
          [CONFIG.STORAGE_KEYS.OFFLINE_RULES]: res.data.rules
        });
        console.log('PatternShield: Offline rules fetched from API');
      }
    } catch (e) {
      console.warn('PatternShield: Could not load offline rules:', e.message);
    }
  }

  // ── Offline Detection Engine ──────────────────────────────────────

  analyzeOfflineSync(text, elementType = 'div', color = '#000000') {
    if (!this.offlineRules) {
      return {
        text, primary_pattern: null, detected_patterns: [],
        confidence_scores: {}, explanations: {}, severity: 'none',
        sentiment: { score: 0, label: 'neutral' },
        is_cookie_consent: false, accessibility_issues: [],
        method: 'offline_fallback',
      };
    }

    const textLower = text.toLowerCase();
    const detected = [];
    const scores = {};
    const explanations = {};

    for (const [ptype, rules] of Object.entries(this.offlineRules)) {
      let score = 0;
      const matches = [];

      for (const kw of (rules.keywords || [])) {
        if (textLower.includes(kw)) {
          score += 1 + (kw.split(' ').length - 1) * 0.5;
          matches.push(kw);
        }
      }

      for (const pat of (rules.patterns || [])) {
        try {
          if (new RegExp(pat, 'i').test(textLower)) score += 2.5;
        } catch {}
      }

      for (const nk of (rules.negative_keywords || [])) {
        if (textLower.includes(nk)) score *= 0.3;
      }

      if (score > 0) {
        const confidence = 1.0 / (1.0 + Math.exp(-1.5 * (score - 2.0)));
        scores[ptype] = Math.round(confidence * 10000) / 10000;
        if (confidence >= 0.3) {
          detected.push(ptype);
          explanations[ptype] = `${rules.description || ptype}. Triggered by: ${matches.slice(0, 3).map(m => '"' + m + '"').join(', ')}`;
        }
      }
    }

    let primary = null;
    if (detected.length > 0) {
      primary = Object.entries(scores).sort((a, b) => b[1] - a[1])[0][0];
    }

    return {
      text, primary_pattern: primary, detected_patterns: detected,
      confidence_scores: scores, explanations,
      severity: this._calcSeverity(detected, scores),
      sentiment: { score: 0, label: 'neutral' },
      is_cookie_consent: false, accessibility_issues: [],
      method: 'offline_rules',
    };
  }

  _calcSeverity(detected, scores) {
    if (!detected.length) return 'none';
    const maxConf = Math.max(...Object.values(scores));
    if (maxConf >= 0.8) return 'critical';
    if (maxConf >= 0.6) return 'high';
    if (maxConf >= 0.4) return 'medium';
    if (maxConf >= 0.2) return 'low';
    return 'none';
  }

  clearCache() { this.requestCache.clear(); }
}

const api = new PatternShieldAPI();
if (typeof window !== 'undefined') window.PatternShieldAPI = api;
