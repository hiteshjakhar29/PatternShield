"""
PatternShield — LLM Analyzer Service

Integrates Anthropic Claude for semantic dark pattern detection.

Design decisions:
  - Uses claude-haiku by default: fastest, cheapest, still highly accurate
    for structured classification tasks like this.
  - Returns None on ANY failure (network, timeout, bad JSON, missing key)
    so the calling pipeline always has a safe fallback path.
  - LLM is only called when the rule-based detector already shows signal
    (controlled by PatternPipeline), keeping API cost proportional to
    actual detection activity.
  - Structured JSON output enforced via system prompt + validation.
  - Model can be swapped to OpenAI by subclassing BaseLLMAnalyzer and
    implementing the _call() method (open/closed principle).
"""
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# ── Response schema ────────────────────────────────────────────────────────────

@dataclass
class LLMAnalysisResult:
    pattern: Optional[str]          # one of the 10 categories, or None
    confidence: float               # 0.0–1.0
    explanation: str                # one-sentence reasoning
    affected_element: str           # what part of the UI is problematic
    remediation: str                # one-sentence fix suggestion
    model: str                      # model ID used
    latency_ms: float

    def to_dict(self) -> dict:
        return asdict(self)


# ── System prompt ──────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are an expert in identifying dark patterns in web UI.
Your job is to classify a given UI element and explain why it is (or is not) manipulative.

Respond ONLY with valid JSON matching this exact schema — no markdown, no prose:
{
  "pattern": "<category or null>",
  "confidence": <0.0 to 1.0>,
  "explanation": "<one concise sentence>",
  "affected_element": "<which part of the UI is problematic>",
  "remediation": "<one sentence on how to fix it>"
}

Valid dark pattern categories (use exact strings):
  "Urgency/Scarcity"            — fake countdown timers, false limited stock
  "Confirmshaming"              — guilt-tripping opt-out copy ("No thanks, I hate saving money")
  "Obstruction"                 — intentionally hard cancellation or unsubscribe flows
  "Visual Interference"         — misleading visual hierarchy, confusing button placement
  "Hidden Costs"                — fees revealed only at final checkout step
  "Forced Continuity"           — subscription traps, automatic renewals without clear notice
  "Sneaking"                    — items added to cart without explicit user action
  "Social Proof Manipulation"   — fake reviews, inflated user counts, fabricated testimonials
  "Misdirection"                — distracting users from important information
  "Price Comparison Prevention" — hiding unit prices, obfuscating competitor comparisons

If the element is NOT a dark pattern, set "pattern" to null and "confidence" below 0.3.
"""

_USER_TEMPLATE = """\
Analyze this web UI element:

Text: {text}
Element type: {element_type}
Page context (parent text): {context}

Return JSON only.
"""


# ── Base class for testability / OpenAI swap ──────────────────────────────────

class BaseLLMAnalyzer:
    """Subclass this and implement _call() to plug in a different LLM provider."""

    def _call(self, text: str, element_type: str, context: str) -> Optional[str]:
        raise NotImplementedError

    def analyze(self, text: str, element_type: str = "div",
                context: str = "") -> Optional[LLMAnalysisResult]:
        t0 = time.time()
        try:
            raw = self._call(text, element_type, context)
            if raw is None:
                return None
            # Strip code fences that some models add despite the prompt
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.lower().startswith("json"):
                    raw = raw[4:]
                raw = raw.strip()
            parsed = json.loads(raw)
            return LLMAnalysisResult(
                pattern=parsed.get("pattern"),
                confidence=float(parsed.get("confidence", 0.0)),
                explanation=parsed.get("explanation", ""),
                affected_element=parsed.get("affected_element", text[:100]),
                remediation=parsed.get("remediation", ""),
                model=self._model_name(),
                latency_ms=round((time.time() - t0) * 1000, 2),
            )
        except json.JSONDecodeError as e:
            logger.warning(f"LLM returned non-JSON: {e}")
            return None
        except Exception as e:
            logger.warning(f"LLM analysis failed ({type(e).__name__}): {e}")
            return None

    def _model_name(self) -> str:
        return "unknown"

    @property
    def is_enabled(self) -> bool:
        return False


# ── Anthropic implementation ───────────────────────────────────────────────────

class AnthropicLLMAnalyzer(BaseLLMAnalyzer):
    """
    Claude-backed dark pattern detector.

    Environment variables:
      ANTHROPIC_API_KEY  — required
      LLM_MODEL          — default: claude-haiku-4-5-20251001
      LLM_TIMEOUT        — default: 15 (seconds)
    """

    DEFAULT_MODEL = "claude-haiku-4-5-20251001"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 15,
    ):
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self._model = model or os.getenv("LLM_MODEL", self.DEFAULT_MODEL)
        self._timeout = timeout
        self._client = None
        self._ready = False

        if not self._api_key:
            logger.info(
                "ANTHROPIC_API_KEY not set — LLM analysis disabled (rule-based only)"
            )
            return

        try:
            import anthropic  # noqa: F401 (validate import at init)
            self._client = anthropic.Anthropic(api_key=self._api_key)
            self._ready = True
            logger.info(f"✓ LLM analyzer ready  model={self._model}")
        except ImportError:
            logger.warning(
                "anthropic package not installed — "
                "run: pip install anthropic  (LLM analysis disabled)"
            )
        except Exception as e:
            logger.warning(f"LLM analyzer init failed: {e}")

    @property
    def is_enabled(self) -> bool:
        return self._ready and self._client is not None

    def _model_name(self) -> str:
        return self._model

    def _call(self, text: str, element_type: str, context: str) -> Optional[str]:
        if not self.is_enabled:
            return None
        prompt = _USER_TEMPLATE.format(
            text=text[:1000],
            element_type=element_type,
            context=context[:300] if context else "none",
        )
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=300,
                system=_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                timeout=self._timeout,
            )
            return message.content[0].text
        except Exception as e:
            logger.warning(f"Anthropic API error ({type(e).__name__}): {e}")
            return None


# ── Convenience alias ─────────────────────────────────────────────────────────

# Default public interface — swap to OpenAILLMAnalyzer when available
LLMAnalyzer = AnthropicLLMAnalyzer
