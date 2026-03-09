/**
 * PatternShield Content Script v2.1
 * - Tests API connection on startup
 * - Client-side keyword pre-filter
 * - Batch analysis via background proxy
 * - Rich JS tooltips + floating panel integration
 * - Dynamic content rescanning via MutationObserver
 */

class PatternShieldScanner {
  constructor() {
    this.scannedElements = new Set();
    this.detectedPatterns = [];
    this.isScanning = false;
    this.settings = { ...CONFIG.DEFAULT_SETTINGS };
    this.observer = null;
    this.domain = window.location.hostname;
    this.panel = null;
    this._panelDismissed = false;

    // Fast client-side suspicious keyword regex (all 10 categories)
    this.suspiciousRegex = new RegExp([
      'only \\d', 'left in stock', 'hurry', 'limited time', 'last chance',
      'ends in', 'expires', 'act now', 'running out', 'almost gone',
      'selling fast', 'flash sale', 'countdown', "don't miss",
      'while supplies', 'sold out', 'few left', 'high demand',
      'deal expires', 'price increases', 'remaining', 'viewing this',
      'no thanks', "i don't want", "i don't care", 'decline',
      'continue without', 'proceed without', 'miss out', 'stay basic',
      'written request', 'headquarters', 'cancellation fee',
      'business days', 'early termination', 'to unsubscribe',
      'to cancel', 'speak to agent',
      'accept all', 'processing fee', 'service fee', 'handling fee',
      'convenience fee', 'booking fee', 'surcharge', 'additional charge',
      'fees apply', 'not include', 'plus tax', 'activation fee',
      'free trial', 'auto.renew', 'recurring',
      'unless cancel', 'will be charged', 'convert to paid',
      'renews at', 'cancel anytime', 'auto.charge',
      'pre.selected', 'pre.checked', 'added to cart', 'already selected',
      "we've added", 'opted in', 'by default',
      'people bought', 'people viewing', 'just purchased', 'trending',
      'bestseller', 'trusted by', 'customers chose', 'someone in',
      'just ordered', 'someone just',
      'recommended', 'best value', 'our pick', 'most popular',
      "editor's choice", 'perfect for you',
      'billed annually', 'custom pricing', 'contact for price',
      'starting at', 'request quote', 'price varies',
      'limited time deal', 'lightning deal', 'deal of the day',
      'lowest price', 'save \\d+%', 'off \\d+%',
    ].join('|'), 'i');

    this.init();
  }

  async init() {
    console.log('[PatternShield] Initializing on', this.domain);
    await this.loadSettings();

    if (await this.isWhitelisted()) {
      console.log('[PatternShield] Domain whitelisted, skipping');
      return;
    }

    // Initialize floating panel if enabled and not dismissed for this domain
    this._panelDismissed = await this._isPanelDismissed();
    if (this.settings.showFloatingPanel !== false && !this._panelDismissed && window.PatternShieldPanel) {
      this.panel = new window.PatternShieldPanel(() => this._dismissPanel());
    }

    // Test API connection and cache offline rules (api.js handles logging + cooldown)
    if (window.PatternShieldAPI) {
      await window.PatternShieldAPI.testConnection();
      window.PatternShieldAPI.loadOfflineRules().catch(() => {});
    }

    if (this.settings.autoScan) {
      // Delay to let dynamic pages load content
      setTimeout(() => this.scanPage(), 2000);
    }

    this.setupObserver();

    chrome.runtime.onMessage.addListener((req, sender, sendResponse) => {
      this.handleMessage(req, sender, sendResponse);
      return true;
    });

    console.log('[PatternShield] Ready');
  }

  async loadSettings() {
    try {
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.SETTINGS);
      this.settings = { ...CONFIG.DEFAULT_SETTINGS, ...(r[CONFIG.STORAGE_KEYS.SETTINGS] || {}) };
    } catch {}
  }

  async isWhitelisted() {
    try {
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.WHITELIST);
      return (r[CONFIG.STORAGE_KEYS.WHITELIST] || []).includes(this.domain);
    } catch { return false; }
  }

  setupObserver() {
    this.observer = new MutationObserver(
      this.debounce(() => {
        if (this.settings.dynamicScan !== false && this.settings.autoScan) {
          this.scanPage();
        }
      }, 3000)
    );
    this.observer.observe(document.body, { childList: true, subtree: true });
  }

  debounce(fn, wait) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), wait); };
  }

  // ── Page Scanning ─────────────────────────────────────────────────

  async scanPage() {
    if (this.isScanning) return;
    this.isScanning = true;

    if (this.panel && !this._panelDismissed) this.panel.setScanning();

    try {
      const elements = this.collectSuspiciousElements();
      console.log(`[PatternShield] Found ${elements.length} suspicious elements`);

      if (elements.length === 0) {
        this.finalizeScan();
        return;
      }

      // Process in batches of 20
      for (let i = 0; i < elements.length; i += 20) {
        await this.analyzeBatch(elements.slice(i, i + 20));
      }

      this.finalizeScan();
    } catch (e) {
      console.error('[PatternShield] Scan error:', e);
      if (this.panel && !this._panelDismissed) this.panel.update(this.detectedPatterns, this.domain);
    } finally {
      this.isScanning = false;
    }
  }

  finalizeScan() {
    this.sendUpdateToPopup();
    this.updateStats();

    if (this.panel && !this._panelDismissed) this.panel.update(this.detectedPatterns, this.domain);

    if (this.settings.enableTemporal && this.detectedPatterns.length > 0) {
      this.recordTemporalData();
    }

    if (this.settings.showNotifications !== false && this.detectedPatterns.length > 0) {
      this._sendNotification(this.detectedPatterns.length);
    }

    console.log(`[PatternShield] Detected ${this.detectedPatterns.length} dark patterns`);
    if (this.detectedPatterns.length > 0) {
      const summary = {};
      this.detectedPatterns.forEach(d => { summary[d.pattern] = (summary[d.pattern] || 0) + 1; });
      console.log('[PatternShield] Breakdown:', summary);
    }
  }

  /**
   * Collect elements matching suspicious keywords (client-side pre-filter).
   */
  collectSuspiciousElements() {
    const suspicious = [];
    const seen = new Set();

    const allElements = document.querySelectorAll(
      'span, div, p, small, a, button, label, li, td, strong, em, b, i, ' +
      'input[type="submit"], input[type="button"], [role="button"], ' +
      '[class*="cookie"], [class*="consent"], [class*="banner"], ' +
      '[class*="price"], [class*="deal"], [class*="offer"], ' +
      '[class*="timer"], [class*="countdown"], [class*="urgency"], ' +
      '[class*="review"], [class*="rating"], [class*="stock"], ' +
      '[class*="limited"], [class*="scarcity"], [class*="badge"]'
    );

    for (const el of allElements) {
      // Skip PatternShield's own UI elements
      if (el.closest('#ps-panel') || el.closest('.ps-tooltip') || el.closest('.ps-feedback')) continue;
      if (this.scannedElements.has(el) || seen.has(el)) continue;

      const text = this.getDirectText(el);
      if (!text || text.length < 4 || text.length > 300) continue;
      if (!this.suspiciousRegex.test(text)) continue;
      if (el.offsetWidth === 0 && el.offsetHeight === 0) continue;

      seen.add(el);
      this.scannedElements.add(el);

      const styles = window.getComputedStyle(el);
      suspicious.push({
        element: el,
        text,
        type: el.tagName.toLowerCase(),
        color: styles.color || '#000000',
        fontSize: parseFloat(styles.fontSize) || null,
        opacity: parseFloat(styles.opacity) || null,
      });

      if (suspicious.length >= 200) break;
    }

    return suspicious;
  }

  /**
   * Get direct text of an element without deep child inheritance.
   */
  getDirectText(el) {
    if (el.tagName === 'INPUT') {
      return (el.value || el.placeholder || '').trim();
    }

    // Leaf node
    if (el.children.length === 0) {
      return (el.innerText || el.textContent || '').trim();
    }

    // Collect direct text nodes only
    let text = '';
    for (const node of el.childNodes) {
      if (node.nodeType === Node.TEXT_NODE) text += node.textContent;
    }
    text = text.trim();

    if (!text && el.children.length <= 3) {
      const tag = el.tagName;
      if (['BUTTON', 'A', 'LABEL', 'SMALL', 'STRONG', 'EM', 'B', 'I', 'SPAN'].includes(tag)) {
        const inner = (el.innerText || '').trim();
        if (inner.length <= 150) text = inner;
      }
    }

    if (!text && el.children.length <= 2) {
      const inner = (el.innerText || '').trim();
      if (inner.length <= 80) text = inner;
    }

    return text;
  }

  // ── Batch Analysis ────────────────────────────────────────────────

  async analyzeBatch(batch) {
    const payload = batch.map(item => ({
      text: item.text,
      element_type: item.type,
      color: item.color,
      fontSize: item.fontSize,
      opacity: item.opacity,
    }));

    try {
      const results = await window.PatternShieldAPI.batchAnalyze(payload);
      if (!Array.isArray(results)) return;

      results.forEach((result, idx) => {
        if (idx >= batch.length) return;
        const item = batch[idx];
        const primaryPattern = result.primary_pattern;
        if (!primaryPattern) return;

        const confidence = result.confidence_scores
          ? (result.confidence_scores[primaryPattern] || 0)
          : 0;

        const enabledPatterns = this.settings.enabledPatterns || {};
        if (enabledPatterns[primaryPattern] === false) return;

        if (confidence >= (this.settings.confidenceThreshold || 0.35)) {
          const detection = {
            element: item.element,
            text: item.text,
            pattern: primaryPattern,
            confidence,
            allPatterns: result.detected_patterns || [],
            severity: result.severity || 'low',
            explanations: result.explanations || {},
            isCookieConsent: result.is_cookie_consent || false,
          };
          this.detectedPatterns.push(detection);

          if (this.settings.highlightElements) {
            this.highlightElement(item.element, detection);
          }
        }
      });
    } catch (e) {
      console.error('[PatternShield] Batch error:', e);
    }
  }

  // ── Highlighting ──────────────────────────────────────────────────

  highlightElement(el, detection) {
    const cfg = CONFIG.PATTERNS[detection.pattern] || {};
    el.setAttribute('data-patternshield', detection.pattern);
    el.setAttribute('data-patternshield-confidence', detection.confidence.toFixed(2));
    el.setAttribute('data-patternshield-severity', detection.severity);
    el.classList.add('patternshield-highlight');
    el.style.setProperty('--ps-color', cfg.color || '#EF4444', 'important');

    if (this.settings.richTooltips !== false) {
      this.injectTooltip(el, detection, cfg);
    }

    if (this.settings.enableFeedback !== false) {
      this.addFeedbackButtons(el, detection);
    }
  }

  /**
   * Inject a rich JS tooltip div with mouseenter/mouseleave handling.
   */
  injectTooltip(el, detection, cfg) {
    if (el.querySelector('.ps-tooltip')) return;

    const explanation = detection.explanations[detection.pattern] || '';
    const confPct = (detection.confidence * 100).toFixed(0);
    const sevClass = `ps-tt-sev-${detection.severity}`;

    const tip = document.createElement('div');
    tip.className = 'ps-tooltip';
    tip.style.setProperty('--ps-color', cfg.color || '#6366f1', 'important');
    tip.innerHTML = `
      <div class="ps-tt-header">
        <span class="ps-tt-pattern">${cfg.icon || '⚠️'} ${cfg.label || detection.pattern}</span>
        <div class="ps-tt-badges">
          <span class="ps-tt-conf">${confPct}%</span>
          <span class="ps-tt-sev ${sevClass}">${detection.severity}</span>
        </div>
      </div>
      ${explanation ? `<div class="ps-tt-explanation">${explanation}</div>` : ''}
    `;

    el.style.position = el.style.position || 'relative';
    el.appendChild(tip);

    el.addEventListener('mouseenter', () => tip.classList.add('ps-tooltip-visible'));
    el.addEventListener('mouseleave', () => tip.classList.remove('ps-tooltip-visible'));
  }

  addFeedbackButtons(el, detection) {
    if (el.querySelector('.ps-feedback')) return;
    const container = document.createElement('div');
    container.className = 'ps-feedback';
    container.innerHTML =
      '<button class="ps-fb-btn ps-fb-correct" title="Correct detection">👍</button>' +
      '<button class="ps-fb-btn ps-fb-wrong" title="Wrong detection">👎</button>';

    container.querySelector('.ps-fb-correct').addEventListener('click', e => {
      e.stopPropagation(); e.preventDefault();
      window.PatternShieldAPI.submitFeedback(detection.text, detection.pattern, true, '', this.domain);
      container.innerHTML = '<span class="ps-fb-thanks">✓ Thanks</span>';
    });
    container.querySelector('.ps-fb-wrong').addEventListener('click', e => {
      e.stopPropagation(); e.preventDefault();
      window.PatternShieldAPI.submitFeedback(detection.text, detection.pattern, false, '', this.domain);
      container.innerHTML = '<span class="ps-fb-thanks">✗ Noted</span>';
    });

    el.style.position = el.style.position || 'relative';
    el.appendChild(container);
  }

  async recordTemporalData() {
    const elements = this.detectedPatterns
      .filter(d => d.pattern === 'Urgency/Scarcity')
      .map(d => ({ text: d.text.substring(0, 300), pattern: d.pattern }));
    if (elements.length > 0) {
      await window.PatternShieldAPI.recordTemporal(this.domain, elements);
    }
  }

  async _isPanelDismissed() {
    try {
      const key = CONFIG.STORAGE_KEYS.DISMISSED_PANELS;
      const r = await chrome.storage.local.get(key);
      return !!((r[key] || {})[this.domain]);
    } catch { return false; }
  }

  async _dismissPanel() {
    this._panelDismissed = true;
    if (this.panel) { this.panel.destroy(); this.panel = null; }
    try {
      const key = CONFIG.STORAGE_KEYS.DISMISSED_PANELS;
      const r = await chrome.storage.local.get(key);
      const map = r[key] || {};
      map[this.domain] = true;
      await chrome.storage.local.set({ [key]: map });
    } catch {}
  }

  _sendNotification(count) {
    try {
      chrome.runtime.sendMessage(
        { action: 'showNotification', count, domain: this.domain },
        () => void chrome.runtime.lastError
      );
    } catch {}
  }

  // ── Clear ─────────────────────────────────────────────────────────

  removeAllHighlights() {
    document.querySelectorAll('.patternshield-highlight').forEach(el => {
      el.classList.remove('patternshield-highlight');
      el.removeAttribute('data-patternshield');
      el.removeAttribute('data-patternshield-confidence');
      el.removeAttribute('data-patternshield-severity');
      el.style.removeProperty('--ps-color');
      el.querySelector('.ps-tooltip')?.remove();
      el.querySelector('.ps-feedback')?.remove();
    });
    this.detectedPatterns = [];
    this.scannedElements.clear();
  }

  // ── Popup Communication ───────────────────────────────────────────

  sendUpdateToPopup() {
    const payload = {
      count: this.detectedPatterns.length,
      domain: this.domain,
      patterns: this.detectedPatterns.map(p => ({
        text: p.text.substring(0, 150),
        pattern: p.pattern,
        confidence: p.confidence,
        severity: p.severity,
        isCookieConsent: p.isCookieConsent,
        explanations: p.explanations,
      })),
    };
    // Callbacks are required to consume chrome.runtime.lastError and prevent the
    // extension error badge when the popup is closed or background is restarting.
    try { chrome.runtime.sendMessage({ action: 'updateDetections', data: payload }, () => void chrome.runtime.lastError); } catch {}
    try { chrome.runtime.sendMessage({ action: 'updateBadge', count: this.detectedPatterns.length }, () => void chrome.runtime.lastError); } catch {}
  }

  async updateStats() {
    try {
      const r = await chrome.storage.sync.get(CONFIG.STORAGE_KEYS.STATS);
      const stats = r[CONFIG.STORAGE_KEYS.STATS] || {
        totalScans: 0, totalDetections: 0, patternCounts: {},
        sitesScanned: {}, severityCounts: {},
      };
      stats.totalScans++;
      stats.totalDetections += this.detectedPatterns.length;
      this.detectedPatterns.forEach(p => {
        stats.patternCounts[p.pattern] = (stats.patternCounts[p.pattern] || 0) + 1;
        stats.severityCounts[p.severity] = (stats.severityCounts[p.severity] || 0) + 1;
      });
      if (this.detectedPatterns.length > 0) {
        stats.sitesScanned[this.domain] = (stats.sitesScanned[this.domain] || 0) + this.detectedPatterns.length;
      }
      await chrome.storage.sync.set({ [CONFIG.STORAGE_KEYS.STATS]: stats });
    } catch {}
  }

  async handleMessage(req, sender, sendResponse) {
    switch (req.action) {
      case 'getDetections':
        sendResponse({
          count: this.detectedPatterns.length,
          domain: this.domain,
          patterns: this.detectedPatterns.map(p => ({
            text: p.text.substring(0, 150),
            pattern: p.pattern,
            confidence: p.confidence,
            severity: p.severity,
            isCookieConsent: p.isCookieConsent,
            explanations: p.explanations,
          })),
        });
        break;
      case 'rescan':
        this.removeAllHighlights();
        await this.scanPage();
        sendResponse({ success: true });
        break;
      case 'clearHighlights':
        this.removeAllHighlights();
        if (this.panel && !this._panelDismissed) this.panel.update([], this.domain);
        sendResponse({ success: true });
        break;
      case 'updateSettings': {
        this.settings = { ...this.settings, ...(req.settings || {}) };
        // Show/hide floating panel based on new settings (never recreate if dismissed)
        if (this.panel) {
          if (this.settings.showFloatingPanel !== false) this.panel.show();
          else this.panel.hide();
        } else if (this.settings.showFloatingPanel !== false && !this._panelDismissed && window.PatternShieldPanel) {
          this.panel = new window.PatternShieldPanel(() => this._dismissPanel());
          this.panel.update(this.detectedPatterns, this.domain);
        }
        sendResponse({ success: true });
        break;
      }
      default:
        sendResponse({ error: 'Unknown action' });
    }
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => new PatternShieldScanner());
} else {
  new PatternShieldScanner();
}
