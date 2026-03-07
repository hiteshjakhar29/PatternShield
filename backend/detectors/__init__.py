"""
PatternShield detectors package.

Defines the BaseDetector Protocol — any detector registered with the app
should satisfy this interface so it can be used interchangeably by API routes.
"""
from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class BaseDetector(Protocol):
    """
    Minimal interface every PatternShield detector must satisfy.

    The rule-based detector (DarkPatternDetector) and the optional
    transformer/ensemble detectors all implement these methods.
    """

    def analyze_element(
        self,
        text: str,
        element_type: str = "div",
        color: str = "#000000",
        **kwargs: Any,
    ) -> Dict:
        """
        Analyze a single DOM element and return a detection result dict.

        Expected keys in the returned dict:
            primary_pattern      (str | None)
            detected_patterns    (list[str])
            confidence_scores    (dict[str, float])
            severity             (str)   — "none" | "low" | "medium" | "high" | "critical"
            explanations         (dict[str, str])
            is_cookie_consent    (bool)
            text_analyzed        (str)
        """
        ...

    def get_all_pattern_types(self) -> List[Dict]:
        """Return metadata for all pattern categories."""
        ...
