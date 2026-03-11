# Contributing to PatternShield

Thanks for your interest in contributing! PatternShield is a backend-heavy project combining Flask, SQLAlchemy, and Anthropic Claude for dark pattern detection.

## Getting Started

```bash
git clone https://github.com/hiteshjakhar29/PatternShield.git
cd PatternShield/backend
pip install -r requirements.txt
pip install pytest pytest-cov flake8 black isort
cp .env.example .env  # edit as needed
python app.py
```

## Project Structure

| Layer | Location | Purpose |
|---|---|---|
| Detection pipeline | `services/pattern_pipeline.py` | rule + LLM → merge |
| LLM integration | `services/llm_analyzer.py` | Anthropic Claude calls |
| Database | `models/` + `database.py` | SQLAlchemy ORM |
| API routes | `api/*.py` | Flask blueprints |
| Rule engine | `ml_detector.py` | 10-category keyword/regex |

## Development Workflow

1. Fork and create a branch: `git checkout -b feat/my-feature`
2. Make changes — keep commits focused
3. Run tests: `make test` (all 98 must pass)
4. Lint: `make lint` (flake8 + black + isort)
5. Open a PR against `main`

## Running Tests

```bash
cd backend
make test          # full suite with coverage
make test-fast     # stop on first failure
make lint          # code style checks
make format        # auto-fix formatting
make full-check    # lint → test → security → docker
```

Tests use in-memory SQLite and LLM disabled — no API key needed.

## Adding a New Dark Pattern Category

1. Add entry to `ml_detector.py → PATTERNS` dict (keywords, patterns, severity_weight)
2. Add matching entry to `chrome-extension/utils/config.js → CONFIG.PATTERNS`
3. Update `api/health.py → pattern_categories` count
4. Add tests in `tests/test_detector.py`
5. Update the README detection table

Keys in `ml_detector.py` and `config.js` must match exactly.

## LLM Integration Notes

- `services/llm_analyzer.py` — `AnthropicLLMAnalyzer` makes the Claude API calls
- Set `ANTHROPIC_API_KEY` in `.env` to enable LLM locally
- LLM is always disabled in tests (`LLM_ENABLED=false`)
- To add OpenAI: subclass `BaseLLMAnalyzer` and implement `_call()`

## Database Schema Changes

- Add/modify models in `models/`
- SQLAlchemy auto-creates tables on startup (`init_db()`)
- For schema migrations, Alembic is the planned tool (see roadmap)

## Code Style

- Black (line length 100)
- isort for imports
- flake8 for errors
- Type hints encouraged on new public functions
- Docstrings on new modules and classes

## Questions?

Open a [discussion](https://github.com/hiteshjakhar29/PatternShield/discussions) or file an issue.
