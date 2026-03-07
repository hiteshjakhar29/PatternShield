# Roadmap

## v2.1 (current)

- 10-category dark pattern detection with sigmoid confidence scoring
- Modular Flask backend with blueprints (analysis, feedback, temporal, reports, health)
- Thread-safe JSON/JSONL persistence layer
- Rich JS tooltips with explanation text and severity badges
- Draggable floating in-page panel with trust grade
- SVG gauge trust score in popup (A–F with animated fill)
- Full options page (7 sections: scanning, detection, appearance, privacy, network, whitelist, about)
- Temporal fraud detection (persistent urgency + resetting timer flags)
- User feedback loop (thumbs up/down → `/feedback`)
- Offline mode with cached rule fallback
- Site whitelist with domain CRUD
- Per-pattern enable/disable toggles
- Cookie consent analysis flag
- Dynamic DOM rescanning via MutationObserver

---

## Planned

### Detection improvements

- **Transformer classifier** — Fine-tuned DistilBERT on dark pattern corpus as second-pass filter after rule engine. Toggle via `TRANSFORMER_ENABLED=true`.
- **Visual heuristics** — Detect asymmetric button sizing (accept vs. reject) using element bounding boxes via the Accessibility Tree API.
- **Screenshot analysis hook** — Optional integration with a vision model to detect purely visual dark patterns (e.g., hidden close buttons, misleading icon placement).
- **Cookie banner classifier** — Dedicated sub-classifier for cookie consent UIs: pre-selected categories, reject buried in settings, etc.
- **Subscription trap detector** — Specialized rules for free trial → paid conversion flows.
- **LLM reasoning scaffold** — Optionally call a Claude API endpoint with element context to produce a more nuanced explanation (opt-in, privacy-preserving).

### Analytics & research

- **Site history panel** — Timeline of past scans for a domain with trend chart.
- **Industry comparison** — Benchmark a site's trust score against retail / SaaS / travel category averages.
- **Leaderboard** — Opt-in community ranking of most-detected dark pattern sites.
- **Experiment framework** — A/B test detection rule changes against feedback accuracy data.
- **Dataset export** — CLI tool to export labeled feedback as CSV for model training.

### Extension UX

- **Keyboard accessibility** — Full keyboard navigation of popup, panel, and options.
- **Light mode** — CSS custom property theme swap.
- **Heatmap overlay** — Color-intensity overlay on page showing detection density zones.
- **Auto-protection mode** — Automatically dismiss manipulative popups (configurable, opt-in only).
- **Inline summary badge** — Small badge injected near detected elements with pattern count.

### Infrastructure

- **Active learning queue** — Surface low-confidence detections to users for labeling.
- **PostgreSQL persistence** — Replace file-backed stores with a proper DB for multi-instance deployments.
- **Prometheus metrics** — `/metrics` endpoint emitting Prometheus-compatible counters.
- **OpenTelemetry tracing** — Request traces for backend performance analysis.
- **GitHub Actions CI** — Lint + test pipeline on every PR.
- **Type annotations** — Full mypy coverage on backend Python.

---

## Research integration opportunities

- Fine-tune on the DPDGPT dataset (Lin et al., 2025) for improved category coverage
- Incorporate DeceptiLens RAG approach for retrieval-augmented explanations
- Benchmark against DarkBench (ICLR 2025) to measure LLM resistance improvement after user is warned
- Regulatory alignment mapping: tag each detection with relevant GDPR / DSA article
