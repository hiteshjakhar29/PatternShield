# PatternShield

[![CI/CD](https://github.com/hiteshjakhar29/PatternShield/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/hiteshjakhar29/PatternShield/actions/workflows/ci-cd.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-orange.svg)](https://www.sqlalchemy.org/)
[![Claude AI](https://img.shields.io/badge/Anthropic-Claude-blueviolet.svg)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**LLM-hybrid Chrome Extension and Flask backend for real-time dark pattern detection.**

PatternShield combines rule-based heuristics, an optional fine-tuned DistilBERT model, and Anthropic Claude to identify manipulative UI patterns across 10 categories. Every scan result is persisted to a SQLAlchemy database, enabling historical trust scoring and temporal fraud analysis across site visits.

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
| **Social Proof Manipulation** | Fake purchase popups, inflated review counts |
| **Misdirection** | "Best value" labels steering choices |
| **Price Comparison Prevention** | Confusing billing periods, per-unit price hiding |

---

## Architecture

```
PatternShieldFP/
├── backend/
│   ├── app.py                      # Flask app factory (create_app)
│   ├── config.py                   # Central env-var config (all tuning here)
│   ├── database.py                 # DB service layer (record_scan, trust history)
│   ├── ml_detector.py              # Rule-based engine: 10 patterns, sigmoid scoring
│   │
│   ├── models/                     # SQLAlchemy ORM (SQLite default → PostgreSQL)
│   │   ├── site.py                 # Domain registry (unique per domain)
│   │   ├── scan.py                 # One row per page scan
│   │   ├── detected_pattern.py     # Individual dark-pattern hit
│   │   ├── trust_score_history.py  # Time-series trust scores
│   │   └── user_feedback.py        # User corrections (DB version)
│   │
│   ├── services/
│   │   ├── llm_analyzer.py         # Anthropic Claude integration + fallback
│   │   ├── pattern_pipeline.py     # Hybrid pipeline: rule → LLM → merge
│   │   ├── feedback_service.py     # JSONL accuracy tracking
│   │   └── temporal_service.py     # Cross-visit snapshot comparison
│   │
│   ├── api/
│   │   ├── health.py               # GET /health, /metrics, /pattern-types
│   │   ├── analysis.py             # POST /analyze, /batch/analyze
│   │   ├── feedback.py             # POST /feedback, GET /report/feedback
│   │   ├── temporal.py             # POST /temporal/record, /temporal/check
│   │   └── reports.py              # POST /site-score, GET /site-score/history
│   │
│   ├── utils/
│   │   ├── validators.py           # Request validation helpers
│   │   └── task_queue.py           # Sync task runner (Celery-ready interface)
│   │
│   └── storage/
│       └── json_store.py           # Thread-safe JSONStore + JSONLStore
│
├── chrome-extension/
│   ├── manifest.json               # MV3
│   ├── background/background.js    # Service worker — API proxy, badge, alarms
│   ├── content/content.js          # DOM scanner, batch analysis, highlighting
│   ├── popup/popup.js              # Dashboard UI, trust gauge
│   ├── options/options.js          # Settings, whitelist, connection test
│   └── utils/
│       ├── api.js                  # PatternShieldAPI — proxy + offline fallback
│       └── config.js               # CONFIG: patterns, defaults, endpoints
│
└── docs/
    ├── architecture.md
    ├── api.md
    └── roadmap.md
```

---

## Detection Pipeline (v3.0)

Every `/analyze` request runs through a three-layer pipeline:

```
DOM element text
       │
       ▼
┌─────────────────────────────────────────────────────┐
│  Layer 1: Rule-Based Detector (ml_detector.py)      │
│  • 10-category keyword + regex engine               │
│  • Context-aware scoring (element type, color, etc.)│
│  • TextBlob sentiment adjustment                    │
│  • Sigmoid → 0–1 confidence                        │
│  Always runs. Results always returned.              │
└──────────────────────┬──────────────────────────────┘
                       │  confidence ≥ 0.25?
                       ▼  (LLM_TRIGGER_THRESHOLD)
┌─────────────────────────────────────────────────────┐
│  Layer 2: LLM Semantic Enrichment (llm_analyzer.py) │
│  • Sends text + element type + context to Claude    │
│  • Returns: pattern, confidence, explanation,       │
│             affected_element, remediation           │
│  Skipped if rule conf < threshold (no API cost).    │
│  Gracefully absent if ANTHROPIC_API_KEY not set.    │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  Layer 3: Merge & Verdict (pattern_pipeline.py)     │
│  • LLM conf ≥ 0.70 → LLM overrides pattern label   │
│  • Both agree → confidence averaged                 │
│  • LLM uncertain/absent → rule-based stands         │
│  • Response includes all three layers (transparent) │
└─────────────────────────────────────────────────────┘
       │
       ▼
  Flat keys (backward-compat) + rule_based / llm / merged blocks
```

### Fallback strategy when LLM is unavailable

PatternShield **never fails** because of LLM unavailability:

| Situation | Behaviour |
|---|---|
| `ANTHROPIC_API_KEY` not set | LLM layer silently skipped; rule-based result returned |
| `LLM_ENABLED=false` | LLM never initialised |
| `anthropic` package not installed | Warning logged; rule-based continues |
| LLM timeout / API error | `None` returned from `_call()`; rule-based result used as-is |
| JSON parse failure | Warning logged; rule-based result used |

All callers check `llm_analyzer.is_enabled` before making any API call.

---

## Persistence & Historical Trust Scoring

Every call to `POST /site-score` persists the result to the SQLAlchemy database:

```
sites  ←─── scans  ←─── detected_patterns
  │            │
  └─── trust_score_history
```

- `sites` — one row per domain, first/last seen timestamps
- `scans` — full scan metadata (score, grade, method, llm_used, pattern_breakdown)
- `detected_patterns` — per-element hits with explanation and remediation
- `trust_score_history` — time-series scores used for trend analysis
- `user_feedback` — DB-backed accuracy corrections (JSONL kept as fast append-log)

`GET /site-score/history?domain=example.com` returns:
- `summary.trend` — `improving` / `stable` / `declining` (first-half vs second-half avg)
- `summary.avg_score`, `min_score`, `max_score`, `scan_count`
- `history` — list of timestamped score snapshots

---

## Temporal Fraud Detection

`POST /temporal/check` detects suspicious patterns across visits to the same domain:

| Flag | Description |
|---|---|
| `persistent_urgency` | Identical urgency text appears in >50% of visits |
| `resetting_timer` | Countdown patterns re-appear across separate visits |

This catches sites that reset fake timers between page loads — a common e-commerce manipulation tactic invisible to single-scan analysis.

---

## Why this is backend-heavy

- **Three-layer detection pipeline** — independent service classes, clean merge logic
- **SQLAlchemy ORM** — swap SQLite for PostgreSQL with one env var change
- **Database schema** — 5 normalised tables, FK constraints, time-series history
- **LLM integration** — structured JSON output, timeout handling, graceful degradation
- **Service layer** — routes never touch persistence directly (`database.py` handles it)
- **Task queue abstraction** — `utils/task_queue.py` wraps sync execution; Celery swap is 1-file change
- **Blueprint architecture** — modular Flask, each concern in its own module
- **Request validation** — centralised in `utils/validators.py`
- **Structured logging** — per-request IDs, latency headers, file + stream logging

---

## Request flow (Chrome extension → backend → response)

```
1. content.js   — collects DOM element texts via TreeWalker
2. content.js   — batches elements (≤20 per call), calls api.batchAnalyze()
3. api.js       — posts {elements:[...]} to background.js via chrome.runtime.sendMessage
4. background.js— proxies to Flask /batch/analyze (avoids HTTPS→HTTP CORS block)
5. analysis.py  — for each element:
                    PatternPipeline.analyze() →
                      rule.analyze_element() (always)
                      llm.analyze() (if rule conf ≥ 0.25 and LLM enabled)
                      _merge() → unified result
6. analysis.py  — returns {results:[...], count, method, latency_ms}
7. content.js   — highlights flagged elements, attaches tooltips
8. popup.js     — calls /site-score → trust grade + pattern breakdown displayed
9. reports.py   — persists scan to DB, returns historical trend
```

---

## Running locally

```bash
# 1. Clone and install
cd backend
pip install -r requirements.txt

# 2. Configure (optional — sensible defaults work out of the box)
cp .env.example .env
# Edit .env: add ANTHROPIC_API_KEY for LLM features

# 3. Run
python app.py
# or: gunicorn -w 4 app:app

# 4. Verify
curl http://localhost:5000/health
```

### With PostgreSQL

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/patternshield python app.py
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///data/patternshield.db` | SQLAlchemy DSN |
| `ANTHROPIC_API_KEY` | _(none)_ | Enables LLM hybrid detection |
| `LLM_MODEL` | `claude-haiku-4-5-20251001` | Claude model ID |
| `LLM_ENABLED` | `true` | Toggle LLM without removing key |
| `LLM_TIMEOUT` | `15` | Max seconds for LLM call |
| `LLM_TRIGGER_THRESHOLD` | `0.25` | Min rule conf to invoke LLM |
| `FLASK_ENV` | `production` | |
| `PORT` | `5000` | |
| `API_KEY_REQUIRED` | `false` | Require `X-API-Key` header |
| `RATE_LIMIT_ENABLED` | `true` | 500/hr, 60/min per IP |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins |

---

## Sample API response — `/analyze` (LLM enabled)

```json
{
  "primary_pattern": "Urgency/Scarcity",
  "detected_patterns": ["Urgency/Scarcity"],
  "confidence": 0.91,
  "severity": "high",
  "explanation": "The phrase 'Only 2 left' combined with a countdown creates artificial scarcity to pressure the user into an immediate purchase.",
  "is_cookie_consent": false,

  "rule_based": {
    "primary_pattern": "Urgency/Scarcity",
    "confidence_scores": { "Urgency/Scarcity": 0.87 },
    "severity": "high",
    "explanations": { "Urgency/Scarcity": "Keywords: 'only', 'left', 'hurry'" }
  },

  "llm": {
    "pattern": "Urgency/Scarcity",
    "confidence": 0.94,
    "explanation": "The phrase 'Only 2 left' combined with a countdown creates artificial scarcity...",
    "affected_element": "Product availability notice",
    "remediation": "Display accurate real-time stock levels without psychological pressure framing.",
    "model": "claude-haiku-4-5-20251001",
    "latency_ms": 412.3
  },

  "merged": {
    "primary_pattern": "Urgency/Scarcity",
    "confidence": 0.905,
    "merge_strategy": "consensus"
  },

  "method": "llm_hybrid",
  "llm_triggered": true,
  "pipeline_latency_ms": 418.7,
  "latency_ms": 418.7
}
```

## Sample API response — `/site-score` (with history)

```json
{
  "score": 62,
  "grade": "C",
  "risk_level": "medium",
  "total_elements": 48,
  "flagged_elements": 7,
  "pattern_breakdown": {
    "Urgency/Scarcity": 3,
    "Hidden Costs": 2,
    "Social Proof Manipulation": 2
  },
  "density": 0.146,
  "domain": "example-shop.com",
  "timestamp": "2026-03-11T09:14:00Z",

  "history": {
    "scan_count": 5,
    "avg_score": 58.4,
    "min_score": 49.0,
    "max_score": 68.0,
    "latest_score": 62.0,
    "trend": "improving",
    "first_seen": "2026-01-15T08:00:00Z",
    "last_seen": "2026-03-11T09:14:00Z"
  },

  "persisted": true,
  "scan_id": 42
}
```

---

## Trust score grades

| Grade | Score | Meaning |
|---|---|---|
| **A** | ≥ 90 | Clean — no significant dark patterns |
| **B** | ≥ 75 | Minor issues |
| **C** | ≥ 60 | Moderate concerns |
| **D** | ≥ 40 | Multiple serious patterns |
| **F** | < 40 | Highly manipulative site |

---

## Testing

```bash
cd backend
make test           # pytest with coverage
make test-fast      # stop on first failure
make lint           # flake8 + black + isort
make full-check     # lint → test → security → docker build → smoke test
```

98 tests passing across:
- `tests/test_detector.py` — 40+ unit tests for all 10 pattern categories
- `tests/test_api.py` — integration tests for all endpoints
- `tests/test_services.py` — FeedbackService, TemporalService, storage layer

LLM is disabled in tests (`LLM_ENABLED=false`) — CI has no API key and
the rule-based pipeline is the primary detection surface.

---

## CI/CD

Six-job GitHub Actions pipeline: **lint → security → test → docker → deploy → summary**

- Tests run with `DATABASE_URL=sqlite:////tmp/ci_patternshield.db` and `LLM_ENABLED=false`
- Docker multi-stage build (python:3.12-slim, non-root appuser)
- Auto-deploy to Render on push to `main` via deploy hook

---

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for planned improvements including:
- Async batch analysis via Celery + Redis (task_queue.py pre-wired)
- Alembic migrations for schema evolution
- OpenAI compatibility layer (`BaseLLMAnalyzer` subclass)
- Per-pattern LLM confidence calibration
- Extension telemetry dashboard
