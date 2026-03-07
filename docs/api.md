# API Reference

Base URL: `http://localhost:5000` (development) or your deployed backend URL.

All requests and responses use `application/json`. Rate limit: 60 requests/minute per IP (configurable).

---

## Health & Metadata

### GET /health

Health check. Returns version, uptime, and service status.

**Response 200**
```json
{
  "status": "healthy",
  "version": "2.1.0",
  "services": {
    "detector": true,
    "feedback": true,
    "temporal": true
  }
}
```

---

### GET /metrics

Aggregated statistics across all detections and feedback.

**Response 200**
```json
{
  "detections": {
    "total_requests": 1024,
    "patterns_detected": 387
  },
  "feedback": {
    "total": 42,
    "correct": 36,
    "accuracy": 0.857
  }
}
```

---

### GET /pattern-types

List of all 10 detectable dark pattern categories with metadata.

**Response 200**
```json
{
  "patterns": [
    {
      "type": "Urgency/Scarcity",
      "label": "Urgency / Scarcity",
      "icon": "⏰",
      "color": "#ef4444",
      "description": "Fake countdown timers, low-stock warnings, FOMO pressure"
    }
  ],
  "count": 10
}
```

---

### GET /offline-rules

Export detection rules for client-side offline fallback.

**Response 200**
```json
{
  "version": "2.1.0",
  "patterns": {
    "Urgency/Scarcity": {
      "keywords": ["only \\d", "left in stock", "hurry"],
      "threshold": 0.35
    }
  }
}
```

---

## Detection

### POST /analyze

Analyze a single UI element.

**Request body**
```json
{
  "text": "Only 2 left in stock!",
  "element_type": "span",
  "color": "#ff0000",
  "fontSize": 14,
  "opacity": 1.0
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | yes | Element text content (max 2000 chars) |
| `element_type` | string | no | HTML tag name (`span`, `button`, etc.) |
| `color` | string | no | Computed CSS color |
| `fontSize` | number | no | Font size in px |
| `opacity` | number | no | Element opacity (0–1) |

**Response 200**
```json
{
  "primary_pattern": "Urgency/Scarcity",
  "detected_patterns": ["Urgency/Scarcity"],
  "confidence_scores": {
    "Urgency/Scarcity": 0.87
  },
  "severity": "high",
  "explanations": {
    "Urgency/Scarcity": "Low-stock warning creates artificial scarcity pressure."
  },
  "is_cookie_consent": false,
  "processing_time_ms": 12
}
```

**Response 200 (no pattern)**
```json
{
  "primary_pattern": null,
  "detected_patterns": [],
  "confidence_scores": {},
  "severity": "none",
  "explanations": {},
  "is_cookie_consent": false
}
```

---

### POST /analyze/transformer

Same interface as `/analyze` but routes through the transformer-based classifier (requires `TRANSFORMER_ENABLED=true` and model installed).

---

### POST /batch/analyze

Analyze multiple elements in one request. More efficient than individual calls.

**Request body**
```json
{
  "elements": [
    {"text": "Hurry! Deal ends in 10 minutes", "element_type": "div"},
    {"text": "Add to cart", "element_type": "button"},
    {"text": "No thanks, I hate saving money", "element_type": "a"}
  ]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `elements` | array | yes | Array of element objects (max 100) |

Each element object accepts the same fields as `/analyze`.

**Response 200**
```json
[
  {
    "primary_pattern": "Urgency/Scarcity",
    "confidence_scores": { "Urgency/Scarcity": 0.92 },
    "severity": "critical",
    "explanations": { "Urgency/Scarcity": "Time-limited pressure with countdown." },
    "is_cookie_consent": false
  },
  {
    "primary_pattern": null,
    "detected_patterns": [],
    "confidence_scores": {}
  },
  {
    "primary_pattern": "Confirmshaming",
    "confidence_scores": { "Confirmshaming": 0.78 },
    "severity": "high",
    "explanations": { "Confirmshaming": "Guilt-inducing opt-out language." }
  }
]
```

**Error 400**
```json
{ "error": "elements must be a non-empty array" }
```

**Error 429**
```json
{ "error": "Rate limit exceeded" }
```

---

### POST /site-score

Calculate a site-level trust score from a list of detections.

**Request body**
```json
{
  "domain": "example.com",
  "detections": [
    {"pattern": "Urgency/Scarcity", "confidence": 0.87, "severity": "high"},
    {"pattern": "Hidden Costs", "confidence": 0.65, "severity": "medium"}
  ]
}
```

**Response 200**
```json
{
  "domain": "example.com",
  "score": 58,
  "grade": "C",
  "risk_level": "medium",
  "pattern_count": 2,
  "breakdown": {
    "Urgency/Scarcity": 1,
    "Hidden Costs": 1
  }
}
```

Grade thresholds: A (≥80), B (≥65), C (≥50), D (≥35), F (<35).

---

## Feedback

### POST /feedback

Record user accuracy feedback on a detection.

**Request body**
```json
{
  "text": "Only 2 left in stock!",
  "detected_pattern": "Urgency/Scarcity",
  "is_correct": true,
  "user_label": "",
  "domain": "amazon.com"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `text` | string | yes | The detected element text |
| `detected_pattern` | string | yes | Pattern category that was flagged |
| `is_correct` | boolean | yes | Whether the detection was accurate |
| `user_label` | string | no | User-provided correct label (if wrong) |
| `domain` | string | no | Page domain |

**Response 200**
```json
{
  "success": true,
  "entry": {
    "id": "abc123",
    "timestamp": "2025-03-06T12:00:00Z",
    "text": "Only 2 left in stock!",
    "detected_pattern": "Urgency/Scarcity",
    "is_correct": true,
    "domain": "amazon.com"
  },
  "total_feedback": 43
}
```

---

### GET /report/feedback

Aggregated accuracy report across all submitted feedback.

**Response 200**
```json
{
  "overall": {
    "total": 43,
    "correct": 37,
    "accuracy": 0.86
  },
  "by_pattern": {
    "Urgency/Scarcity": { "total": 20, "correct": 18, "accuracy": 0.90 },
    "Confirmshaming": { "total": 8, "correct": 6, "accuracy": 0.75 }
  }
}
```

---

## Temporal Detection

### POST /temporal/record

Store element snapshots from a page visit for later comparison.

**Request body**
```json
{
  "domain": "example.com",
  "elements": [
    {"text": "Sale ends in 02:34:12", "pattern": "Urgency/Scarcity"},
    {"text": "Only 3 left!", "pattern": "Urgency/Scarcity"}
  ]
}
```

**Response 200**
```json
{
  "success": true,
  "domain": "example.com",
  "stored": 2
}
```

---

### POST /temporal/check

Compare current elements against historical snapshots. Returns fraud signals.

**Request body**
```json
{
  "domain": "example.com",
  "elements": [
    {"text": "Sale ends in 02:34:12", "pattern": "Urgency/Scarcity"}
  ]
}
```

**Response 200**
```json
{
  "domain": "example.com",
  "temporal_issues": 1,
  "history_size": 3,
  "flags": [
    {
      "type": "resetting_timer",
      "text": "Sale ends in 02:34:12",
      "description": "Timer text matches a previous visit but numeric value changed — likely a fake countdown that resets."
    }
  ]
}
```

**Flag types:**

| Type | Description |
|---|---|
| `persistent_urgency` | Exact same urgency text seen on a previous visit (fake scarcity) |
| `resetting_timer` | Timer pattern matches but value changed (resetting countdown) |

---

## Error Codes

| Status | Meaning |
|---|---|
| 400 | Invalid request body or missing required fields |
| 401 | Invalid or missing API key (when `API_KEY_REQUIRED=true`) |
| 404 | Endpoint not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Requested service not initialized |
