"""
ML-based Dark Pattern Detector
Combines rule-based detection with sentiment analysis for pattern identification.
"""

import re
from textblob import TextBlob
from typing import Dict, List, Tuple, Optional


class DarkPatternDetector:
    """Detects dark patterns using rule-based + sentiment analysis."""

    def __init__(self):
        """Initialize detector with pattern rules."""
        self.patterns = {
            "Urgency/Scarcity": {
                "keywords": [
                    "only",
                    "left",
                    "stock",
                    "hurry",
                    "limited",
                    "last",
                    "soon",
                    "now",
                    "today",
                    "hours",
                    "minutes",
                    "expires",
                    "ends",
                    "running out",
                    "almost gone",
                    "selling fast",
                    "few items",
                    "flash sale",
                    "countdown",
                    "timer",
                    "act now",
                    "quick",
                    "don't miss",
                    "while supplies",
                    "almost sold out",
                ],
                "patterns": [
                    r"\d+\s+(left|remaining|available)",
                    r"only\s+\d+",
                    r"sale ends in",
                    r"\d+\s+people (viewing|bought|purchased)",
                    r"timer:\s*\d+:\d+",
                ],
            },
            "Confirmshaming": {
                "keywords": [
                    "no thanks",
                    "i don't want",
                    "i don't like",
                    "i prefer",
                    "skip",
                    "decline",
                    "reject",
                    "i'd rather",
                    "i don't care",
                    "miss out",
                    "without",
                    "i enjoy",
                    "i don't deserve",
                    "no,",
                    "stay basic",
                    "inferior",
                    "overpaying",
                ],
                "patterns": [
                    r"no thanks.*i don\'t",
                    r"no.*i (don\'t|prefer|enjoy|like)",
                    r"skip.*\(.*\)",
                    r"decline (and|offer)",
                    r"continue without",
                    r"proceed without",
                ],
            },
            "Obstruction": {
                "keywords": [
                    "mail",
                    "written request",
                    "headquarters",
                    "contact",
                    "customer service",
                    "phone",
                    "call",
                    "fax",
                    "days to process",
                    "business days",
                    "form",
                    "visit store",
                    "in person",
                    "cancellation fee",
                    "minimum",
                    "certified mail",
                    "notarized",
                    "supervisor approval",
                    "disabled until",
                ],
                "patterns": [
                    r"mail.*request",
                    r"contact customer service",
                    r"\d+.*business days",
                    r"cancellation fee",
                    r"fax.*form",
                    r"requires.*phone",
                    r"only (available|by) (calling|mail|fax)",
                    r"in person",
                    r"must (keep|visit)",
                ],
            },
            "Visual Interference": {
                "keywords": [
                    "accept all",
                    "reject",
                    "yes please",
                    "get started",
                    "unlock",
                    "upgrade",
                    "premium",
                    "claim",
                    "start free",
                    "maybe later",
                    "dismiss",
                    "skip for now",
                    "not interested",
                    "close",
                    "later",
                    "no thanks",
                ],
                "visual_markers": [
                    r"[✓✗★⚡🎉]+",  # Emojis/symbols
                    r"[A-Z\s]{5,}",  # ALL CAPS
                ],
            },
        }

    def analyze_element(
        self,
        text: str,
        element_type: str = "div",
        color: str = "#000000",
        use_sentiment: bool = True,
        use_enhanced: bool = False,
    ) -> Dict:
        """
        Analyze a UI element for dark patterns.

        Args:
            text: Element text content
            element_type: HTML element type
            color: Element color
            use_sentiment: Whether to use sentiment analysis
            use_enhanced: Whether to use enhanced features

        Returns:
            Dictionary with detection results
        """
        text_lower = text.lower()
        detected_patterns = []
        confidence_scores = {}

        # Rule-based detection
        for pattern_type, rules in self.patterns.items():
            score = 0
            matches = []

            # Keyword matching
            for keyword in rules["keywords"]:
                if keyword in text_lower:
                    score += 1
                    matches.append(keyword)

            # Pattern matching
            if "patterns" in rules:
                for pattern in rules["patterns"]:
                    if re.search(pattern, text_lower):
                        score += 2
                        matches.append(f"pattern:{pattern}")

            # Visual markers (for Visual Interference)
            if "visual_markers" in rules:
                for marker in rules["visual_markers"]:
                    if re.search(marker, text):
                        score += 1.5
                        matches.append(f"visual:{marker}")

            # Confidence calculation
            if score > 0:
                confidence = min(score / 3.0, 1.0)  # Normalize to 0-1
                confidence_scores[pattern_type] = confidence

                if confidence >= 0.33:  # Threshold
                    detected_patterns.append(pattern_type)

        # Sentiment analysis
        sentiment_score = 0
        sentiment_label = "neutral"

        if use_sentiment:
            try:
                blob = TextBlob(text)
                sentiment_score = blob.sentiment.polarity

                if sentiment_score < -0.1:
                    sentiment_label = "negative"
                elif sentiment_score > 0.1:
                    sentiment_label = "positive"

                # Adjust confidence based on sentiment
                if sentiment_label == "negative":
                    # Negative sentiment boosts Confirmshaming and Obstruction
                    if "Confirmshaming" in confidence_scores:
                        confidence_scores["Confirmshaming"] *= 1.2
                    if "Obstruction" in confidence_scores:
                        confidence_scores["Obstruction"] *= 1.1

            except Exception:
                pass

        # Enhanced features
        if use_enhanced:
            # Length-based adjustments
            word_count = len(text.split())
            if word_count > 10:
                # Long obstruction descriptions
                if "Obstruction" in confidence_scores:
                    confidence_scores["Obstruction"] *= 1.15

            # Color-based detection
            if color and color != "#000000":
                color_lower = color.lower()
                # Red colors often indicate urgency
                if any(c in color_lower for c in ["#ef", "#dc", "#b9", "#f9", "#ea"]):
                    if "Urgency/Scarcity" in confidence_scores:
                        confidence_scores["Urgency/Scarcity"] *= 1.1
                # Grey colors often de-emphasize
                if any(
                    c in color_lower for c in ["#6b", "#4b", "#9c", "#d1", "#e5", "#f3"]
                ):
                    if "Visual Interference" in confidence_scores:
                        confidence_scores["Visual Interference"] *= 1.15

        # Determine primary pattern
        primary_pattern = None
        if detected_patterns:
            primary_pattern = max(confidence_scores.items(), key=lambda x: x[1])[0]

        return {
            "detected_patterns": detected_patterns,
            "primary_pattern": primary_pattern,
            "confidence_scores": confidence_scores,
            "sentiment": {"score": sentiment_score, "label": sentiment_label},
            "text_analyzed": text,
        }

    def get_pattern_explanation(self, pattern_type: str) -> str:
        """Get explanation for a specific pattern type."""
        explanations = {
            "Urgency/Scarcity": "Creates false sense of urgency or scarcity to pressure users",
            "Confirmshaming": "Uses guilt or shame to manipulate user decisions",
            "Obstruction": "Makes it difficult to perform desired actions like unsubscribing",
            "Visual Interference": "Uses visual design to manipulate attention and choices",
        }
        return explanations.get(pattern_type, "Unknown pattern type")


# Convenience function
def analyze_element(
    text: str,
    element_type: str = "div",
    color: str = "#000000",
    use_sentiment: bool = True,
    use_enhanced: bool = False,
) -> Dict:
    """Convenience function for analyzing elements."""
    detector = DarkPatternDetector()
    return detector.analyze_element(
        text, element_type, color, use_sentiment, use_enhanced
    )
