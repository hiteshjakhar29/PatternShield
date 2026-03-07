# Architecture

## Overview

PatternShield is a Chrome extension with a companion Flask API. The extension scans page DOM, proxies analysis requests through the background service worker to avoid mixed-content restrictions, and renders results in both the popup and an in-page floating panel.

---

## Component Map

```
┌────────────────────────────────────────────────────────────────┐
│  Chrome Extension (MV3)                                        │
│                                                                │
│  ┌──────────────┐    message    ┌──────────────────────────┐   │
│  │ content.js   │ ──────────── │ background.js            │   │
│  │              │              │ (service worker)          │   │
│  │ DOM scanner  │              │                           │   │
│  │ Highlights   │ ◄─────────── │ fetch() proxy             │   │
│  │ Tooltips     │              │ Badge updater             │   │
│  │              │              │ Alarm scheduler           │   │
│  └──────┬───────┘              └───────────┬──────────────┘   │
│         │                                  │                   │
│  ┌──────▼───────┐              ┌───────────▼──────────────┐   │
│  │floating-     │              │ popup.js / options.js    │   │
│  │panel.js      │              │                           │   │
│  │ Trust grade  │              │ PopupController           │   │
│  │ Pattern chips│              │ SVG gauge                 │   │
│  │ Draggable    │              │ Settings CRUD             │   │
│  └──────────────┘              └──────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                                       │ HTTP
                                       ▼
┌────────────────────────────────────────────────────────────────┐
│  Flask Backend                                                 │
│                                                                │
│  app.py (create_app factory)                                   │
│    ├── Flask-CORS                                              │
│    ├── Flask-Limiter (60 req/min default)                      │
│    ├── Flask-Talisman (security headers)                       │
│    │                                                           │
│    ├── api/health.py      → /health, /metrics, /pattern-types  │
│    ├── api/analysis.py    → /analyze, /batch/analyze           │
│    ├── api/feedback.py    → /feedback, /report/feedback        │
│    ├── api/temporal.py    → /temporal/record, /temporal/check  │
│    └── api/reports.py     → /site-score, /offline-rules        │
│                                                                │
│  services/                                                     │
│    ├── FeedbackService    (JSONL append-only store)            │
│    └── TemporalService    (JSON keyed by domain)               │
│                                                                │
│  storage/                                                      │
│    └── JSONStore / JSONLStore (thread-safe, atomic write)      │
│                                                                │
│  ml_detector.py                                                │
│    └── DarkPatternDetector.analyze_element()                   │
└────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Page Scan

```
1. Page loads / DOM mutates
        │
        ▼
2. content.js: collectSuspiciousElements()
   - querySelectorAll over 30+ selectors
   - Client-side keyword regex pre-filter
   - Skip elements already scanned (Set)
   - Cap at 200 elements
        │
        ▼
3. Batch(es) of 20 elements →
   chrome.runtime.sendMessage({action: 'apiProxy', endpoint: '/batch/analyze', ...})
        │
        ▼
4. background.js service worker:
   fetch(`${API_URL}/batch/analyze`, {method:'POST', body: JSON.stringify(payload)})
        │
        ▼
5. Flask /batch/analyze:
   for each element:
     a. DarkPatternDetector.analyze_element(text, element_type, color, fontSize, opacity)
     b. Keyword scoring (weighted pattern keyword lists)
     c. Contextual adjustment (element type, visual metadata boosts)
     d. TextBlob sentiment adjustment
     e. Sigmoid normalization → confidence [0,1]
     f. Threshold filter (default 0.35)
   Return: [{primary_pattern, confidence_scores, severity, explanations, is_cookie_consent}]
        │
        ▼
6. content.js: for each result above threshold:
   - highlightElement() — CSS outline + --ps-color custom property
   - injectTooltip()   — .ps-tooltip div with mouseenter/leave
   - addFeedbackButtons() — 👍👎 overlay
   - Push to this.detectedPatterns[]
        │
        ├─→ floating-panel.js: panel.update(detectedPatterns, domain)
        │     - Compute trust score from severity weights
        │     - Render grade chip + pattern count chips
        │
        └─→ sendUpdateToPopup()
              - chrome.runtime.sendMessage({action: 'updateDetections'})
              - chrome.runtime.sendMessage({action: 'updateBadge', count})
```

---

## Key Design Decisions

### Service Worker Proxy
Chrome MV3 content scripts run in the page's security context and cannot make cross-origin HTTP requests to `http://localhost:5000` from `https://` pages (mixed-content block). All API calls go through `background.js` which runs in the extension's own context and can fetch any URL listed in `host_permissions`.

### Sigmoid Confidence
Raw rule scores (integer sums) are normalized via sigmoid:
```
confidence = 1 / (1 + exp(-steepness * (raw_score - midpoint)))
```
This maps unbounded scores to [0, 1] with a smooth S-curve, avoiding the hard threshold problem of raw score comparisons.

### Thread-Safe Storage
`JSONStore` (for mutable JSON objects) and `JSONLStore` (for append-only logs) both write to a `.tmp` file then `os.replace()` (atomic rename) to prevent partial-write corruption under concurrent requests.

### Client-Side Pre-Filter
The `suspiciousRegex` (50+ keyword patterns) filters the DOM to at most 200 candidate elements before any API call. This reduces network traffic by ~80% on typical pages and keeps the extension fast on complex sites.

### CSS Custom Properties for Theming
Each detection type has a `--ps-color` property set inline. All highlight styles, tooltip borders, and panel chips read from this property, so adding a new pattern category requires only a config entry — no new CSS rules.

---

## Storage Schema

### chrome.storage.sync
```json
{
  "ps_settings": {
    "autoScan": true,
    "dynamicScan": true,
    "enableTemporal": true,
    "highlightElements": true,
    "showFloatingPanel": true,
    "richTooltips": true,
    "enableFeedback": true,
    "offlineMode": false,
    "cookieAnalysis": true,
    "confidenceThreshold": 0.35,
    "apiUrl": "http://localhost:5000",
    "enabledPatterns": {}
  },
  "ps_whitelist": ["example.com"],
  "ps_stats": {
    "totalScans": 42,
    "totalDetections": 138,
    "patternCounts": { "Urgency/Scarcity": 55 },
    "severityCounts": { "high": 20 },
    "sitesScanned": { "amazon.com": 12 }
  }
}
```

### chrome.storage.local
```json
{
  "ps_offline_rules": {
    "patterns": [...],
    "cached_at": 1700000000000
  }
}
```

### Backend: data/feedback.jsonl (one JSON object per line)
```json
{"id": "uuid4", "text": "...", "detected_pattern": "Urgency/Scarcity", "is_correct": true, "domain": "amazon.com", "timestamp": "..."}
```

### Backend: data/temporal.json
```json
{
  "amazon.com": [
    {"timestamp": "...", "elements": [{"text": "Only 3 left!", "pattern": "Urgency/Scarcity"}]}
  ]
}
```
