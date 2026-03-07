/**
 * PatternShield Floating Panel
 * A draggable in-page mini dashboard showing live detection results.
 * Injected by content.js after scanning.
 */

class PatternShieldPanel {
  constructor() {
    this.el       = null;
    this.isDragging = false;
    this.dragOffset = { x: 0, y: 0 };
    this.collapsed  = false;
    this.detections = [];
    this.trustScore = null;
    this._build();
  }

  // ── Build DOM ────────────────────────────────────────────────────

  _build() {
    if (document.getElementById('ps-panel')) return;

    this.el = document.createElement('div');
    this.el.id = 'ps-panel';
    this.el.className = 'ps-panel';
    this.el.setAttribute('data-ps-ui', 'true');
    this.el.innerHTML = `
      <div class="ps-panel-header" id="ps-panel-header">
        <div class="ps-panel-brand">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L3 6.5V12C3 16.418 7.03 20.572 12 22C16.97 20.572 21 16.418 21 12V6.5L12 2Z"
                  fill="rgba(99,102,241,0.9)" stroke="rgba(255,255,255,0.3)" stroke-width="0.5"/>
            <path d="M8.5 12L10.5 14L15.5 9" stroke="white" stroke-width="1.8"
                  stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span class="ps-panel-title">PatternShield</span>
        </div>
        <div class="ps-panel-controls">
          <button class="ps-panel-btn" id="ps-collapse-btn" title="Collapse">▾</button>
          <button class="ps-panel-btn" id="ps-close-btn" title="Close">✕</button>
        </div>
      </div>
      <div class="ps-panel-body" id="ps-panel-body">
        <div class="ps-panel-status" id="ps-panel-status">
          <span class="ps-status-dot ps-scanning"></span>
          <span id="ps-status-text">Scanning…</span>
        </div>
        <div class="ps-panel-score" id="ps-panel-score" style="display:none">
          <div class="ps-score-grade" id="ps-score-grade">A</div>
          <div class="ps-score-info">
            <div class="ps-score-num" id="ps-score-num">100<span class="ps-score-max">/100</span></div>
            <div class="ps-score-risk" id="ps-score-risk">Low Risk</div>
          </div>
        </div>
        <div class="ps-panel-chips" id="ps-panel-chips"></div>
        <div class="ps-panel-counts" id="ps-panel-counts"></div>
      </div>
    `;

    document.body.appendChild(this.el);
    this._restorePosition();
    this._setupDrag();
    this._setupButtons();
  }

  // ── Update with scan results ─────────────────────────────────────

  update(detections, domain) {
    this.detections = detections || [];
    const n = this.detections.length;

    const statusEl   = document.getElementById('ps-panel-status');
    const scoreEl    = document.getElementById('ps-panel-score');
    const chipsEl    = document.getElementById('ps-panel-chips');
    const countsEl   = document.getElementById('ps-panel-counts');
    const statusText = document.getElementById('ps-status-text');
    const dot        = statusEl.querySelector('.ps-status-dot');

    if (n === 0) {
      dot.className = 'ps-status-dot ps-clean';
      statusText.textContent = 'No patterns detected';
      scoreEl.style.display  = 'none';
      chipsEl.innerHTML = '';
      countsEl.innerHTML = '';
      return;
    }

    // Status dot
    dot.className = 'ps-status-dot ps-warn';
    statusText.textContent = `${n} pattern${n !== 1 ? 's' : ''} detected`;

    // Trust score
    const sevWeights = { critical: 0.9, high: 0.7, medium: 0.5, low: 0.3, none: 0 };
    const totalSev = this.detections.reduce((s, d) => s + (sevWeights[d.severity] || 0), 0);
    const score = Math.max(0, Math.min(100, Math.round(100 - totalSev * 18)));

    let grade, risk, gradeColor;
    if      (score >= 90) { grade = 'A'; risk = 'Low';      gradeColor = '#22c55e'; }
    else if (score >= 75) { grade = 'B'; risk = 'Low';      gradeColor = '#4ade80'; }
    else if (score >= 60) { grade = 'C'; risk = 'Medium';   gradeColor = '#f59e0b'; }
    else if (score >= 40) { grade = 'D'; risk = 'High';     gradeColor = '#ef4444'; }
    else                  { grade = 'F'; risk = 'Critical'; gradeColor = '#dc2626'; }

    scoreEl.style.display = 'flex';
    const gradeEl = document.getElementById('ps-score-grade');
    gradeEl.textContent = grade;
    gradeEl.style.background = gradeColor;
    document.getElementById('ps-score-num').innerHTML =
      `${score}<span class="ps-score-max">/100</span>`;
    document.getElementById('ps-score-risk').textContent = `${risk} Risk`;

    // Pattern chips
    const counts = {};
    this.detections.forEach(d => { counts[d.pattern] = (counts[d.pattern] || 0) + 1; });

    chipsEl.innerHTML = '';
    const patternCfg = (typeof CONFIG !== 'undefined') ? CONFIG.PATTERNS : {};
    for (const [ptype, c] of Object.entries(counts)) {
      const cfg   = patternCfg[ptype] || {};
      const chip  = document.createElement('span');
      chip.className = 'ps-chip';
      chip.style.borderColor = cfg.color || '#6366f1';
      chip.style.color       = cfg.color || '#6366f1';
      chip.textContent       = `${cfg.icon || ''} ×${c}`;
      chip.title             = ptype;
      chipsEl.appendChild(chip);
    }
  }

  // ── Scanning state ───────────────────────────────────────────────

  setScanning() {
    const dot  = this.el.querySelector('.ps-status-dot');
    const text = document.getElementById('ps-status-text');
    if (dot)  dot.className = 'ps-status-dot ps-scanning';
    if (text) text.textContent = 'Scanning…';
    document.getElementById('ps-panel-score').style.display = 'none';
    document.getElementById('ps-panel-chips').innerHTML = '';
  }

  // ── Show / hide ──────────────────────────────────────────────────

  show() { if (this.el) this.el.style.display = 'flex'; }
  hide() { if (this.el) this.el.style.display = 'none'; }

  destroy() {
    if (this.el) { this.el.remove(); this.el = null; }
  }

  // ── Drag ─────────────────────────────────────────────────────────

  _setupDrag() {
    const header = document.getElementById('ps-panel-header');
    header.style.cursor = 'grab';

    header.addEventListener('mousedown', e => {
      if (e.target.closest('.ps-panel-btn')) return;
      this.isDragging = true;
      const rect = this.el.getBoundingClientRect();
      this.dragOffset.x = e.clientX - rect.left;
      this.dragOffset.y = e.clientY - rect.top;
      header.style.cursor = 'grabbing';
      e.preventDefault();
    });

    document.addEventListener('mousemove', e => {
      if (!this.isDragging) return;
      const x = e.clientX - this.dragOffset.x;
      const y = e.clientY - this.dragOffset.y;
      const maxX = window.innerWidth  - this.el.offsetWidth;
      const maxY = window.innerHeight - this.el.offsetHeight;
      this.el.style.left = `${Math.max(0, Math.min(x, maxX))}px`;
      this.el.style.top  = `${Math.max(0, Math.min(y, maxY))}px`;
      this.el.style.right  = 'auto';
      this.el.style.bottom = 'auto';
    });

    document.addEventListener('mouseup', () => {
      if (!this.isDragging) return;
      this.isDragging = false;
      header.style.cursor = 'grab';
      this._savePosition();
    });
  }

  _savePosition() {
    try {
      localStorage.setItem('ps-panel-pos', JSON.stringify({
        left: this.el.style.left,
        top:  this.el.style.top,
      }));
    } catch {}
  }

  _restorePosition() {
    try {
      const pos = JSON.parse(localStorage.getItem('ps-panel-pos') || 'null');
      if (pos && pos.left && pos.top) {
        this.el.style.left   = pos.left;
        this.el.style.top    = pos.top;
        this.el.style.right  = 'auto';
        this.el.style.bottom = 'auto';
      }
    } catch {}
  }

  // ── Collapse / close ─────────────────────────────────────────────

  _setupButtons() {
    document.getElementById('ps-collapse-btn').addEventListener('click', () => {
      this.collapsed = !this.collapsed;
      const body = document.getElementById('ps-panel-body');
      const btn  = document.getElementById('ps-collapse-btn');
      body.style.display = this.collapsed ? 'none' : 'block';
      btn.textContent    = this.collapsed ? '▸' : '▾';
    });

    document.getElementById('ps-close-btn').addEventListener('click', () => {
      this.hide();
    });
  }
}

// Export for use in content.js
if (typeof window !== 'undefined') {
  window.PatternShieldPanel = PatternShieldPanel;
}
