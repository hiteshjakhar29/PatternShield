"""
Multimodal Detector
Combines text analysis + computer vision for enhanced detection.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import json

from vision_detector import VisionDetector
from feature_extraction import FeatureExtractor

# Try to import transformer detector (optional)
try:
    from transformer_detector import TransformerDetector

    HAS_TRANSFORMER = True
except ImportError:
    TransformerDetector = None
    HAS_TRANSFORMER = False


class MultimodalDetector:
    """Multimodal dark pattern detector (Text + Vision)."""

    def __init__(self, fusion_strategy: str = "late"):
        """
        Initialize multimodal detector.

        Args:
            fusion_strategy: 'early', 'late', or 'hybrid'
        """
        self.fusion_strategy = fusion_strategy

        # Initialize component models
        self.vision_detector = VisionDetector()
        self.feature_extractor = FeatureExtractor()

        # Try to load transformer if available
        self.text_detector = None
        self.has_transformer = False

        if HAS_TRANSFORMER:
            try:
                self.text_detector = TransformerDetector()
                self.has_transformer = True
                print("✓ Transformer model loaded")
            except Exception as e:
                print(f"⚠ Transformer not available: {e}")
                self.has_transformer = False
        else:
            print("⚠ Transformer dependencies not installed")

        # Fusion weights (tuned on validation set)
        self.weights = {"text": 0.6, "vision": 0.4}

    def predict(
        self,
        text: str,
        element_type: str = "div",
        color: str = "#000000",
        screenshot: Optional[str] = None,
        element_bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> Dict:
        """
        Multimodal prediction combining text and vision.

        Args:
            text: Element text
            element_type: HTML element type
            color: Element color
            screenshot: Optional base64 screenshot
            element_bbox: Optional bounding box in screenshot

        Returns:
            Combined prediction with explanations
        """
        result = {
            "modalities": {},
            "combined_prediction": None,
            "confidence": 0.0,
            "explanations": [],
        }

        # Text analysis
        text_result = self._analyze_text(text, element_type, color)
        result["modalities"]["text"] = text_result

        # Vision analysis (if screenshot provided)
        if screenshot:
            vision_result = self._analyze_vision(screenshot, element_bbox)
            result["modalities"]["vision"] = vision_result

        # Fusion
        if self.fusion_strategy == "early":
            combined = self._early_fusion(result["modalities"])
        elif self.fusion_strategy == "late":
            combined = self._late_fusion(result["modalities"])
        else:
            combined = self._hybrid_fusion(result["modalities"])

        result.update(combined)

        return result

    def _analyze_text(self, text: str, element_type: str, color: str) -> Dict:
        """Analyze text using NLP models."""
        result = {"features": None, "prediction": None, "confidence": 0.0}

        # Extract features
        features = self.feature_extractor.extract_features(
            text, element_type, color, include_tfidf=False
        )
        result["features"] = features

        # Get transformer prediction if available
        if self.has_transformer:
            pred_label, confidence = self.text_detector.predict(text)
            result["prediction"] = pred_label
            result["confidence"] = confidence
        else:
            # Fallback to rule-based
            result["prediction"] = "No Pattern"
            result["confidence"] = 0.5

        return result

    def _analyze_vision(
        self, screenshot: str, bbox: Optional[Tuple[int, int, int, int]]
    ) -> Dict:
        """Analyze visual patterns."""
        vision_results = self.vision_detector.analyze_screenshot(
            screenshot, element_bbox=bbox
        )

        # Convert patterns to prediction
        pattern_scores = {
            "Urgency/Scarcity": 0.0,
            "Confirmshaming": 0.0,
            "Obstruction": 0.0,
            "Visual Interference": 0.0,
            "Sneaking": 0.0,
            "No Pattern": 0.5,
        }

        for pattern in vision_results["visual_patterns"]:
            if pattern["type"] == "urgent_color":
                pattern_scores["Urgency/Scarcity"] += pattern["confidence"] * 0.5
            elif pattern["type"] == "fake_disabled":
                pattern_scores["Obstruction"] += pattern["confidence"] * 0.5
            elif pattern["type"] == "poor_contrast":
                pattern_scores["Visual Interference"] += pattern["confidence"] * 0.5
            elif pattern["type"] == "prominence_imbalance":
                pattern_scores["Visual Interference"] += pattern["confidence"] * 0.3

        # Get top prediction
        pred_label = max(pattern_scores.items(), key=lambda x: x[1])[0]
        confidence = pattern_scores[pred_label]

        return {
            "patterns": vision_results["visual_patterns"],
            "prediction": pred_label,
            "confidence": confidence,
            "visual_features": vision_results,
        }

    def _early_fusion(self, modalities: Dict) -> Dict:
        """
        Early fusion: Combine features before classification.

        Note: This is conceptual - would need a trained classifier
        on combined features.
        """
        # Extract all features
        all_features = []

        if "text" in modalities and modalities["text"]["features"]:
            text_features = list(modalities["text"]["features"].values())
            all_features.extend(text_features)

        if "vision" in modalities:
            # Add visual features
            vision = modalities["vision"]["visual_features"]
            if "prominence" in vision:
                all_features.append(vision["prominence"]["prominence_score"])
            if "attention_score" in vision:
                all_features.append(vision["attention_score"])
            if "contrast" in vision:
                all_features.append(vision["contrast"]["ratio"])

        # For now, return text prediction
        # In production, would train classifier on combined features
        if "text" in modalities:
            return {
                "combined_prediction": modalities["text"]["prediction"],
                "confidence": modalities["text"]["confidence"],
                "method": "early_fusion",
                "feature_count": len(all_features),
            }

        return {
            "combined_prediction": "No Pattern",
            "confidence": 0.5,
            "method": "early_fusion",
        }

    def _late_fusion(self, modalities: Dict) -> Dict:
        """
        Late fusion: Weighted average of predictions.
        """
        predictions = {}
        total_weight = 0.0

        # Text prediction
        if "text" in modalities:
            text_pred = modalities["text"]["prediction"]
            text_conf = modalities["text"]["confidence"]
            predictions[text_pred] = (
                predictions.get(text_pred, 0.0) + text_conf * self.weights["text"]
            )
            total_weight += self.weights["text"]

        # Vision prediction
        if "vision" in modalities:
            vision_pred = modalities["vision"]["prediction"]
            vision_conf = modalities["vision"]["confidence"]
            predictions[vision_pred] = (
                predictions.get(vision_pred, 0.0) + vision_conf * self.weights["vision"]
            )
            total_weight += self.weights["vision"]

        # Normalize
        if total_weight > 0:
            predictions = {k: v / total_weight for k, v in predictions.items()}

        # Get top prediction
        if predictions:
            pred_label = max(predictions.items(), key=lambda x: x[1])[0]
            confidence = predictions[pred_label]
        else:
            pred_label = "No Pattern"
            confidence = 0.5

        return {
            "combined_prediction": pred_label,
            "confidence": confidence,
            "method": "late_fusion",
            "all_predictions": predictions,
        }

    def _hybrid_fusion(self, modalities: Dict) -> Dict:
        """
        Hybrid fusion: Adaptive weighting based on confidence.
        """
        # Use late fusion but adjust weights by confidence
        predictions = {}

        if "text" in modalities:
            text_pred = modalities["text"]["prediction"]
            text_conf = modalities["text"]["confidence"]
            # Weight by confidence
            weight = self.weights["text"] * text_conf
            predictions[text_pred] = predictions.get(text_pred, 0.0) + weight

        if "vision" in modalities:
            vision_pred = modalities["vision"]["prediction"]
            vision_conf = modalities["vision"]["confidence"]
            weight = self.weights["vision"] * vision_conf
            predictions[vision_pred] = predictions.get(vision_pred, 0.0) + weight

        # Get top prediction
        if predictions:
            pred_label = max(predictions.items(), key=lambda x: x[1])[0]
            confidence = predictions[pred_label]
        else:
            pred_label = "No Pattern"
            confidence = 0.5

        return {
            "combined_prediction": pred_label,
            "confidence": confidence,
            "method": "hybrid_fusion",
            "all_predictions": predictions,
        }

    def compare_fusion_strategies(
        self,
        text: str,
        screenshot: Optional[str] = None,
        element_bbox: Optional[Tuple[int, int, int, int]] = None,
    ) -> Dict:
        """
        Compare all fusion strategies.

        Args:
            text: Element text
            screenshot: Optional screenshot
            element_bbox: Optional bounding box

        Returns:
            Comparison of all strategies
        """
        results = {}

        for strategy in ["early", "late", "hybrid"]:
            old_strategy = self.fusion_strategy
            self.fusion_strategy = strategy

            result = self.predict(
                text, screenshot=screenshot, element_bbox=element_bbox
            )

            results[strategy] = {
                "prediction": result["combined_prediction"],
                "confidence": result["confidence"],
            }

            self.fusion_strategy = old_strategy

        return results

    def explain_prediction(self, prediction_result: Dict) -> str:
        """
        Generate human-readable explanation.

        Args:
            prediction_result: Result from predict()

        Returns:
            Explanation string
        """
        explanations = []

        # Text analysis
        if "text" in prediction_result["modalities"]:
            text_result = prediction_result["modalities"]["text"]
            explanations.append(
                f"Text analysis: {text_result['prediction']} "
                f"(confidence: {text_result['confidence']:.2f})"
            )

        # Vision analysis
        if "vision" in prediction_result["modalities"]:
            vision_result = prediction_result["modalities"]["vision"]
            patterns = vision_result["patterns"]

            if patterns:
                explanations.append(f"Visual patterns detected: {len(patterns)}")
                for pattern in patterns:
                    explanations.append(
                        f"  - {pattern['type']}: {pattern['description']}"
                    )

        # Combined result
        explanations.append(
            f"\nCombined prediction: {prediction_result['combined_prediction']} "
            f"(confidence: {prediction_result['confidence']:.2f})"
        )
        explanations.append(
            f"Fusion method: {prediction_result.get('method', 'unknown')}"
        )

        return "\n".join(explanations)


def main():
    """Test multimodal detector."""
    print("=" * 80)
    print("MULTIMODAL DETECTOR TEST")
    print("=" * 80)

    # Initialize
    detector = MultimodalDetector(fusion_strategy="late")

    # Test text-only
    print("\n1. Text-only prediction:")
    result = detector.predict(
        text="Only 2 left in stock! Buy now!", element_type="span", color="#ff0000"
    )
    print(f"   Prediction: {result['combined_prediction']}")
    print(f"   Confidence: {result['confidence']:.2f}")

    # Test with mock screenshot (in production, would be real screenshot)
    print("\n2. Multimodal prediction (conceptual):")
    print("   [Would use real screenshot in production]")

    # Compare fusion strategies
    print("\n3. Fusion strategy comparison:")
    comparison = detector.compare_fusion_strategies(text="Only 2 left in stock!")

    for strategy, result in comparison.items():
        print(f"   {strategy}: {result['prediction']} ({result['confidence']:.2f})")

    print("\n✓ Multimodal detector test complete")


if __name__ == "__main__":
    main()
