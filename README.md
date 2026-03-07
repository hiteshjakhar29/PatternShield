# PatternShield

**AI-powered Chrome Extension for real-time dark pattern detection.**

PatternShield scans web pages as you browse, identifies manipulative UI patterns across 10 categories, and gives you an explainable trust score — all without sending your browsing history anywhere.

---

## What it detects

| Category | Examples |
|---|---|
| **Urgency / Scarcity** | Fake countdown timers, "Only 2 left!", FOMO pressure |
| **Confirmshaming** | "No thanks, I hate saving money" opt-outs |
| **Obstruction** | Multi-step cancellation flows, mandatory phone calls |
| **Visual Interference** | Oversized accept buttons, hidden reject links |
| **Hidden Costs** | Processing fees revealed only at checkout |
| **Forced Continuity** | Auto-renewing trials, subscription traps |
| **Sneaking** | Pre-checked add-ons, items silently added to cart |
| **Social Proof** | Fake purchase popups, inflated review counts |
| **Misdirection** | "Best value" labels steering choices |
| **Price Comparison Prevention** | Confusing billing periods, per-unit price hiding |

---

## Architecture

```
PatternShieldFP/
├── backend/
│   ├── app.py                  # Flask app factory (create_app)
│   ├── config.py               # Central env-var config
│   ├── ml_detector.py          # Detection engine + DetectionResult
│   ├── api/
│   │   ├── health.py           # GET /health, /metrics, /pattern-types
│   │   ├── analysis.py         # POST /analyze, /batch/analyze
│   │   ├── feedback.py         # POST /feedback, GET /report/feedback
│   │   ├── temporal.py         # POST /temporal/record, /temporal/check
│   │   └── reports.py          # GET /site-score, /offline-rules
│   ├── services/
│   │   ├── feedback_service.py # Accuracy tracking, JSONL persistence
│   │   └── temporal_service.py # Cross-visit snapshot comparison
│   └── storage/
│       └── json_store.py       # Thread-safe JSONStore + JSONLStore
├── chrome-extension/
│   ├── manifest.json           # MV3
│   ├── background/
│   │   └── background.js       # Service worker — API proxy, badge, alarms
│   ├── content/
│   │   ├── content.js          # DOM scanner, batch analysis, highlighting
│   │   ├── content.css         # Highlight styles, rich tooltips, severity
│   │   ├── floating-panel.js   # Draggable in-page panel (PatternShieldPanel)
│   │   └── floating-panel.css  # Panel styles
│   ├── popup/
│   │   ├── popup.html          # Dashboard (Scan / Settings / Analytics tabs)
│   │   ├── popup.css           # Dark theme, SVG gauge, toggle switches
│   │   └── popup.js            # PopupController, trust score, breakdown bars
│   ├── options/
│   │   ├── options.html        # Full settings page (7 sections)
│   │   ├── options.css
│   │   └── options.js          # Settings CRUD, whitelist, connection test
│   └── utils/
│       ├── config.js           # CONFIG: endpoints, patterns, defaults
│       └── api.js              # PatternShieldAPI class (proxy wrapper)
└── docs/
    ├── architecture.md         # System design + data flow
    ├── api.md                  # Full API reference
    └── roadmap.md              # Planned features
```

### How a scan works

```
Browser tab loads
       │
       ▼
content.js — MutationObserver fires on DOM change
       │
       ├─ 1. Client-side keyword pre-filter (suspiciousRegex, 200-element cap)
       │
       ├─ 2. chrome.runtime.sendMessage → background.js service worker
       │         │
       │         └─ fetch() → Flask API /batch/analyze (bypasses mixed-content)
       │
       ├─ 3. ml_detector.py: rule scoring → sigmoid confidence → DetectionResult
       │
       ├─ 4. Results returned: highlight elements, inject rich tooltips
       │
       ├─ 5. floating-panel.js: update trust grade + pattern chips
       │
       └─ 6. popup.js: render gauge, detection cards, breakdown bars
```

---

## Trust Score

Each page receives an A–F grade computed from detected severity weights:

| Severity | Weight |
|---|---|
| Critical | 0.9 |
| High | 0.7 |
| Medium | 0.5 |
| Low | 0.3 |

Score = `max(0, 100 − Σ(weight × 30))`, clamped to [0, 100].

- **A (80–100)** — Clean or minor low-severity patterns
- **B (65–79)** — Some medium patterns, browsing is mostly safe
- **C (50–64)** — Notable manipulation present
- **D (35–49)** — Multiple high-severity patterns
- **F (0–34)** — Aggressive dark patterns, proceed carefully

---

## Explainability

Every detection includes:
- **Pattern category** with color-coded highlight
- **Confidence percentage** (sigmoid-normalized, 0–100%)
- **Severity badge** (low / medium / high / critical)
- **Natural-language explanation** shown in the rich tooltip on hover
- **Thumbs up/down feedback** on each highlight, sent to `/feedback`

---

## Temporal Fraud Detection

PatternShield records urgency element snapshots on each visit via `/temporal/record`. On subsequent visits, `/temporal/check` compares current elements against history to flag:

- **persistent_urgency** — same countdown text unchanged across multiple visits (fake timer)
- **resetting_timer** — numeric value changed but pattern text is the same (timer resets on refresh)

---

## Offline Mode

When the API is unreachable, PatternShield falls back to locally-cached rules fetched from `/offline-rules` on last successful connection. Rules are stored in `chrome.storage.local`. Detection runs synchronously in the content script using the same keyword patterns, with slightly lower confidence scores.

---

## Quick Start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
# API running at http://localhost:5000
```

Or with Docker:

```bash
cd backend
docker-compose up
```

Environment variables (copy `.env.example` → `.env`):

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | random | Flask secret |
| `API_KEY_REQUIRED` | `false` | Enable API key auth |
| `API_KEY` | — | Key if auth enabled |
| `CORS_ORIGINS` | `*` | Allowed CORS origins |
| `CONFIDENCE_THRESHOLD` | `0.35` | Minimum detection confidence |
| `MAX_BATCH_SIZE` | `100` | Max elements per batch request |
| `FEEDBACK_FILE` | `data/feedback.jsonl` | Feedback persistence path |
| `TEMPORAL_FILE` | `data/temporal.json` | Temporal snapshot persistence path |
| `LOG_LEVEL` | `INFO` | Logging level |

### Chrome Extension

1. Open `chrome://extensions`
2. Enable **Developer Mode** (top-right toggle)
3. Click **Load unpacked** → select `chrome-extension/`
4. Navigate to any e-commerce or SaaS site
5. Click the PatternShield icon to see the scan dashboard

To test all 10 pattern categories locally, open `chrome-extension/test-page.html` in Chrome.

---

## API Reference

See [docs/api.md](docs/api.md) for the full endpoint reference.

**Summary:**

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check + version |
| GET | `/metrics` | Detection + feedback stats |
| GET | `/pattern-types` | All 10 categories with metadata |
| GET | `/offline-rules` | Cached rules for offline mode |
| POST | `/analyze` | Single element analysis |
| POST | `/analyze/transformer` | Transformer-model analysis (if enabled) |
| POST | `/batch/analyze` | Batch analysis (up to 100 elements) |
| POST | `/site-score` | Site-level trust score |
| POST | `/feedback` | Submit accuracy feedback |
| GET | `/report/feedback` | Aggregated accuracy report |
| POST | `/temporal/record` | Record visit snapshot |
| POST | `/temporal/check` | Check for fake/resetting timers |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Extension | Chrome MV3, Vanilla JS, CSS custom properties |
| Backend | Python 3.12, Flask, Flask-CORS, Flask-Limiter, Flask-Talisman |
| Detection | Rule-based scoring, TextBlob sentiment, sigmoid normalization |
| Persistence | Thread-safe JSON / JSONL file store |
| Deployment | Docker, Gunicorn, Render / Railway compatible |

---

## Detection Engine

Detection uses a multi-signal scoring pipeline in `ml_detector.py`:

1. **Keyword matching** — weighted pattern-specific keyword lists
2. **Contextual adjustments** — element type, font size, color contrast, opacity boosts
3. **Sentiment analysis** — TextBlob polarity shifts confidence for borderline cases
4. **Sigmoid normalization** — raw score → [0, 1] probability via `1 / (1 + exp(-k(x - θ)))`
5. **Threshold filter** — results below `CONFIDENCE_THRESHOLD` (default 0.35) are discarded

The engine is modular: `analyze_element()` accepts arbitrary text + visual metadata, and `calculate_site_score()` aggregates results into the trust grade.

---

## Settings

Accessible via the extension options page (right-click icon → Options):

- **Auto-scan** — run on every page load
- **Dynamic scan** — rescan when DOM changes (MutationObserver)
- **Temporal detection** — track patterns across visits
- **Highlight elements** — outline detected elements on page
- **Floating panel** — draggable in-page summary panel
- **Rich tooltips** — hover tooltips with explanation + confidence
- **Feedback buttons** — thumbs up/down on each detection
- **Offline mode** — force local rule fallback
- **Cookie analysis** — flag asymmetric cookie consent UI
- **Confidence threshold** — slider from 10% to 90%
- **Per-pattern toggles** — enable/disable any of the 10 categories
- **Site whitelist** — skip detection on trusted domains
- **API URL** — point to your own backend

---

## Research Context

PatternShield is informed by recent work in automated dark pattern detection:

- **DPDGPT** (Lin et al., 2025) — Multimodal LLM-based dark pattern detection
- **YOLOv12x** (Jang et al., 2025) — Visual dark pattern detection via object detection
- **DeceptiLens** (Kocyigit et al., FAccT 2025) — RAG-augmented detection
- **DarkBench** (ICLR 2025) — LLM resistance to dark pattern manipulation
- **EU DSA / GDPR** — Regulatory context for dark pattern prohibition

---

## Contributing

See [docs/roadmap.md](docs/roadmap.md) for planned features. Pull requests welcome.

1. Fork the repo
2. Create a feature branch
3. Run the backend test suite: `python backend/test_production.py`
4. Submit a PR with a clear description of what the change does and why

---

## License

MIT
