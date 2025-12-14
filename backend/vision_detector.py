"""
Vision Detector for Dark Patterns
Screenshot-based visual pattern detection using OpenCV.
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import json

from cv_utils import (
    base64_to_image,
    image_to_base64,
    calculate_contrast_ratio,
    check_wcag_compliance,
    generate_saliency_map,
    extract_color_scheme,
    detect_buttons,
    calculate_visual_prominence,
    detect_fake_disabled_button,
    analyze_visual_hierarchy,
    create_heatmap_overlay,
    annotate_image,
)


class VisionDetector:
    """Detect visual dark patterns from screenshots."""

    def __init__(self):
        """Initialize vision detector."""
        self.deceptive_color_combinations = [
            # (fg_range, bg_range, pattern_type)
            ((0, 0, 200, 255, 0, 100), (200, 255, 200, 255, 200, 255), "urgent_red"),
            (
                (100, 150, 100, 150, 100, 150),
                (200, 255, 200, 255, 200, 255),
                "fake_disabled",
            ),
        ]

    def analyze_screenshot(
        self,
        base64_image: str,
        element_bbox: Optional[Tuple[int, int, int, int]] = None,
        viewport_size: Optional[Tuple[int, int]] = None,
    ) -> Dict:
        """
        Analyze screenshot for visual dark patterns.

        Args:
            base64_image: Base64-encoded screenshot
            element_bbox: Optional bounding box (x, y, w, h) of target element
            viewport_size: Optional (width, height) of viewport

        Returns:
            Dict with analysis results
        """
        # Convert to OpenCV image
        image = base64_to_image(base64_image)

        if viewport_size is None:
            viewport_size = (image.shape[1], image.shape[0])

        results = {"visual_patterns": [], "metrics": {}, "explanations": []}

        # Generate saliency map
        saliency_map = generate_saliency_map(image)
        results["saliency_map"] = image_to_base64(
            cv2.cvtColor(saliency_map, cv2.COLOR_GRAY2BGR)
        )

        # Extract color scheme
        colors = extract_color_scheme(image, n_colors=5)
        results["dominant_colors"] = colors

        # Detect buttons
        buttons = detect_buttons(image)
        results["detected_buttons"] = len(buttons)

        # If element bbox provided, analyze it
        if element_bbox:
            element_analysis = self._analyze_element(
                image, element_bbox, viewport_size, saliency_map
            )
            results.update(element_analysis)

        # Detect deceptive patterns
        patterns = self.detect_visual_deception(image, buttons)
        results["visual_patterns"].extend(patterns)

        # Generate explanation overlay
        results["annotated_image"] = self._create_explanation_overlay(image, results)

        return results

    def _analyze_element(
        self,
        image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        viewport_size: Tuple[int, int],
        saliency_map: np.ndarray,
    ) -> Dict:
        """Analyze specific element in screenshot."""
        x, y, w, h = bbox

        # Extract element region
        element_roi = image[y : y + h, x : x + w]

        results = {}

        # Visual prominence
        prominence = calculate_visual_prominence(bbox, viewport_size)
        results["prominence"] = prominence

        # Check if element is in high-saliency region
        element_saliency = saliency_map[y : y + h, x : x + w]
        avg_saliency = np.mean(element_saliency)
        results["attention_score"] = float(avg_saliency / 255.0)

        # Extract element colors
        element_colors = extract_color_scheme(element_roi, n_colors=2)
        results["element_colors"] = element_colors

        # Contrast analysis
        if len(element_colors) >= 2:
            fg_color = element_colors[0]
            bg_color = element_colors[1]

            contrast_ratio = calculate_contrast_ratio(fg_color, bg_color)
            compliance = check_wcag_compliance(contrast_ratio)

            results["contrast"] = {
                "ratio": contrast_ratio,
                "compliant_aa": compliance["compliant_aa"],
                "compliant_aaa": compliance["compliant_aaa"],
            }

            # Low contrast can be deceptive
            if not compliance["compliant_aa"]:
                results["contrast"]["is_deceptive"] = True
                results["contrast"]["reason"] = "Poor contrast (WCAG AA fail)"

        # Check for fake disabled appearance
        fake_disabled = detect_fake_disabled_button(image, bbox)
        if fake_disabled["appears_disabled"]:
            results["fake_disabled"] = fake_disabled

        return results

    def detect_visual_deception(
        self, image: np.ndarray, buttons: List[Dict]
    ) -> List[Dict]:
        """
        Detect visual deception patterns.

        Args:
            image: Screenshot image
            buttons: List of detected buttons

        Returns:
            List of detected patterns
        """
        patterns = []

        # 1. Fake disabled buttons
        for i, button in enumerate(buttons):
            fake_disabled = detect_fake_disabled_button(image, button["bbox"])

            if fake_disabled["appears_disabled"]:
                patterns.append(
                    {
                        "type": "fake_disabled",
                        "confidence": fake_disabled["confidence"],
                        "location": button["bbox"],
                        "description": "Button appears disabled but may be clickable",
                        "severity": "medium",
                    }
                )

        # 2. Deceptive color combinations
        for button in buttons:
            x, y, w, h = button["bbox"]
            roi = image[y : y + h, x : x + w]
            colors = extract_color_scheme(roi, n_colors=2)

            if len(colors) >= 2:
                # Check for urgent red on white
                fg, bg = colors[0], colors[1]

                # Red foreground (R > 200, G < 100, B < 100)
                if fg[0] > 200 and fg[1] < 100 and fg[2] < 100:
                    patterns.append(
                        {
                            "type": "urgent_color",
                            "confidence": 0.75,
                            "location": button["bbox"],
                            "description": "Urgent red color creates false urgency",
                            "severity": "high",
                        }
                    )

        # 3. Button prominence imbalance
        if len(buttons) >= 2:
            # Simple heuristic: check if one button is significantly larger
            areas = [b["area"] for b in buttons]
            max_area = max(areas)
            min_area = min(areas)

            if max_area > min_area * 3:
                patterns.append(
                    {
                        "type": "prominence_imbalance",
                        "confidence": 0.6,
                        "location": None,
                        "description": "Significant size difference between buttons",
                        "severity": "medium",
                    }
                )

        # 4. Low contrast text (poor readability)
        for button in buttons:
            x, y, w, h = button["bbox"]
            roi = image[y : y + h, x : x + w]
            colors = extract_color_scheme(roi, n_colors=2)

            if len(colors) >= 2:
                contrast = calculate_contrast_ratio(colors[0], colors[1])

                if contrast < 3.0:  # Below WCAG AA for any text
                    patterns.append(
                        {
                            "type": "poor_contrast",
                            "confidence": 0.8,
                            "location": button["bbox"],
                            "description": f"Poor contrast ratio: {contrast:.2f} (WCAG AA requires 4.5)",
                            "severity": "medium",
                        }
                    )

        return patterns

    def _create_explanation_overlay(self, image: np.ndarray, results: Dict) -> str:
        """Create annotated image showing detections."""
        annotated = image.copy()

        # Draw detected patterns
        for pattern in results["visual_patterns"]:
            if pattern["location"] is not None:
                x, y, w, h = pattern["location"]

                # Color based on severity
                if pattern["severity"] == "high":
                    color = (0, 0, 255)  # Red
                elif pattern["severity"] == "medium":
                    color = (0, 165, 255)  # Orange
                else:
                    color = (0, 255, 255)  # Yellow

                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 3)

                # Draw label
                label = pattern["type"]
                cv2.putText(
                    annotated,
                    label,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2,
                )

        # Draw saliency heatmap overlay if available
        if "saliency_map" in results:
            saliency_img = base64_to_image(results["saliency_map"])
            saliency_gray = cv2.cvtColor(saliency_img, cv2.COLOR_BGR2GRAY)
            annotated = create_heatmap_overlay(annotated, saliency_gray, alpha=0.3)

        return image_to_base64(annotated)

    def batch_analyze(self, screenshots: List[str]) -> List[Dict]:
        """
        Analyze multiple screenshots.

        Args:
            screenshots: List of base64-encoded images

        Returns:
            List of analysis results
        """
        results = []

        for screenshot in screenshots:
            try:
                result = self.analyze_screenshot(screenshot)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e), "visual_patterns": []})

        return results

    def compare_visual_methods(self, base64_image: str) -> Dict:
        """
        Compare different visual analysis methods.

        Args:
            base64_image: Screenshot to analyze

        Returns:
            Comparison results
        """
        image = base64_to_image(base64_image)

        results = {"saliency_methods": {}, "comparison": {}}

        # Try different saliency methods
        for method in ["spectral"]:  # Add more if available
            try:
                saliency_map = generate_saliency_map(image, method=method)
                results["saliency_methods"][method] = {
                    "success": True,
                    "avg_intensity": float(np.mean(saliency_map)),
                    "max_intensity": float(np.max(saliency_map)),
                }
            except Exception as e:
                results["saliency_methods"][method] = {
                    "success": False,
                    "error": str(e),
                }

        return results


def main():
    """Test vision detector."""
    print("=" * 80)
    print("VISION DETECTOR TEST")
    print("=" * 80)

    detector = VisionDetector()

    # Create test image
    print("\n1. Creating test image...")
    test_image = np.ones((600, 800, 3), dtype=np.uint8) * 255

    # Add some test elements
    # Red urgent button
    cv2.rectangle(test_image, (300, 200), (500, 250), (0, 0, 220), -1)
    cv2.putText(
        test_image,
        "BUY NOW",
        (330, 235),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )

    # Gray "disabled" button
    cv2.rectangle(test_image, (300, 300), (500, 350), (150, 150, 150), -1)
    cv2.putText(
        test_image,
        "No thanks",
        (320, 335),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (100, 100, 100),
        2,
    )

    # Convert to base64
    test_b64 = image_to_base64(test_image)

    # Analyze
    print("\n2. Analyzing screenshot...")
    results = detector.analyze_screenshot(test_b64, element_bbox=(300, 200, 200, 50))

    print(f"\n3. Results:")
    print(f"   Detected buttons: {results['detected_buttons']}")
    print(f"   Visual patterns found: {len(results['visual_patterns'])}")

    for pattern in results["visual_patterns"]:
        print(f"\n   Pattern: {pattern['type']}")
        print(f"      Severity: {pattern['severity']}")
        print(f"      Confidence: {pattern['confidence']:.2f}")
        print(f"      Description: {pattern['description']}")

    if "prominence" in results:
        print(f"\n4. Element Prominence:")
        prom = results["prominence"]
        print(f"   Area: {prom['relative_area']:.3f}")
        print(f"   Centrality: {prom['centrality']:.3f}")
        print(f"   Prominence score: {prom['prominence_score']:.3f}")

    if "contrast" in results:
        print(f"\n5. Contrast Analysis:")
        contrast = results["contrast"]
        print(f"   Ratio: {contrast['ratio']:.2f}")
        print(f"   WCAG AA: {'✓' if contrast['compliant_aa'] else '✗'}")
        print(f"   WCAG AAA: {'✓' if contrast['compliant_aaa'] else '✗'}")

    print("\n✓ Vision detector test complete")


if __name__ == "__main__":
    main()
