# 🛡️ PatternShield v2.0

**AI-powered Chrome Extension that detects dark patterns on websites in real-time.**

Detects **10 categories** of manipulative UI design, provides cookie consent analysis, accessibility overlap detection, temporal pattern tracking, user feedback loops, and offline detection mode.

## Features

### Detection Categories (10)
| # | Pattern | Description |
|---|---------|-------------|
| 1 | **Urgency/Scarcity** | Fake countdown timers, low-stock warnings, FOMO pressure |
| 2 | **Confirmshaming** | Guilt-based opt-out text ("No, I don't want to save money") |
| 3 | **Obstruction** | Multi-step cancellation, hidden unsubscribe, mandatory phone calls |
| 4 | **Visual Interference** | Oversized accept buttons, hidden reject links, emoji manipulation |
| 5 | **Hidden Costs** | Processing fees, surcharges, charges revealed at checkout |
| 6 | **Forced Continuity** | Auto-renewing trials, subscription traps, recurring billing |
| 7 | **Sneaking** | Pre-checked add-ons, items added to cart without consent |
| 8 | **Social Proof** | Fake purchase notifications, inflated review counts |
| 9 | **Misdirection** | "Recommended" labels, highlighted options steering choices |
| 10 | **Price Comparison Prevention** | Confusing billing periods, hidden total prices |

### Key Capabilities
- **Offline Mode** — Local rule-based detection without API calls
- **Cookie Consent Analysis** — Detects asymmetric buttons, pre-selected categories
- **Temporal Detection** — Identifies fake timers that reset between visits
- **Accessibility Overlap** — Flags elements that are both dark patterns and WCAG violations
- **User Feedback** — 👍/👎 buttons on detected patterns for continuous improvement
- **Site Score** — A-F grade with risk level for each site
- **Real Settings Panel** — Confidence threshold, pattern toggles, API URL, whitelist

## Quick Start (Mac)

```bash
git clone <repo-url>
cd PatternShield-Production
chmod +x setup.sh
./setup.sh
```

This will:
1. Create a Python virtual environment
2. Install all dependencies
3. Start the API server on `http://localhost:5000`

### Load the Extension
1. Open `chrome://extensions` in Chrome
2. Enable **Developer Mode** (top right)
3. Click **Load unpacked** → select the `chrome-extension/` folder
4. Open `chrome-extension/test-page.html` to test all 10 pattern types

### Run Tests
```bash
source backend/venv/bin/activate
python backend/test_production.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check with version info |
| GET | `/pattern-types` | List all 10 pattern categories |
| GET | `/offline-rules` | Export rules for client-side detection |
| POST | `/analyze` | Analyze single element |
| POST | `/batch/analyze` | Batch analyze up to 100 elements |
| POST | `/site-score` | Calculate site-level dark pattern score |
| POST | `/feedback` | Submit detection accuracy feedback |
| POST | `/temporal/record` | Record element snapshot for temporal tracking |
| POST | `/temporal/check` | Check for persistent/resetting patterns |

## Architecture

```
PatternShield-Production/
├── backend/
│   ├── app.py              # Flask API (9 endpoints)
│   ├── ml_detector.py      # Detection engine (10 categories)
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── test_production.py   # 18-test suite
│   └── data/
├── chrome-extension/
│   ├── manifest.json        # MV3
│   ├── background/          # Service worker
│   ├── content/             # DOM scanner + highlighter
│   ├── popup/               # Tabbed UI (Scan/Settings/Stats)
│   ├── utils/               # Config + API client
│   └── test-page.html       # All 10 pattern test page
└── setup.sh                 # One-command Mac setup
```

## Tech Stack
- **Backend**: Python 3.12, Flask, TextBlob, NLTK
- **Extension**: Chrome MV3, Vanilla JS
- **Detection**: Rule-based + NLP sentiment, sigmoid confidence scoring
- **Deployment**: Docker, Gunicorn, Render/Railway ready

## Research References
- DPDGPT (Lin et al., 2025) — Multimodal LLM dark pattern detection
- YOLOv12x (Jang et al., 2025) — Visual dark pattern detection
- DeceptiLens (Kocyigit et al., FAccT 2025) — RAG-based detection
- DarkBench (ICLR 2025) — LLM dark pattern benchmarks
