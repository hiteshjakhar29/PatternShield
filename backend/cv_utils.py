"""
Computer Vision Utilities
Image processing for visual dark pattern detection.
"""

import cv2
import numpy as np
from PIL import Image
import base64
import io
from typing import Dict, List, Tuple, Optional


def base64_to_image(base64_string: str) -> np.ndarray:
    """Convert base64 string to OpenCV image."""
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    img_bytes = base64.b64decode(base64_string)
    img = Image.open(io.BytesIO(img_bytes))
    img_array = np.array(img)

    # Convert RGB to BGR for OpenCV
    if len(img_array.shape) == 3 and img_array.shape[2] == 3:
        img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    return img_array


def image_to_base64(image: np.ndarray) -> str:
    """Convert OpenCV image to base64 string."""
    # Convert BGR to RGB
    if len(image.shape) == 3 and image.shape[2] == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    pil_img = Image.fromarray(image)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return f"data:image/png;base64,{img_str}"


def calculate_contrast_ratio(
    color1: Tuple[int, int, int], color2: Tuple[int, int, int]
) -> float:
    """
    Calculate WCAG 2.1 contrast ratio between two colors.

    Args:
        color1: RGB tuple (0-255)
        color2: RGB tuple (0-255)

    Returns:
        Contrast ratio (1-21)
    """

    def relative_luminance(rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance (WCAG formula)."""
        r, g, b = [c / 255.0 for c in rgb]

        # Apply gamma correction
        channels = []
        for val in [r, g, b]:
            if val <= 0.03928:
                channels.append(val / 12.92)
            else:
                channels.append(((val + 0.055) / 1.055) ** 2.4)

        # Calculate luminance
        return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

    l1 = relative_luminance(color1)
    l2 = relative_luminance(color2)

    lighter = max(l1, l2)
    darker = min(l1, l2)

    return (lighter + 0.05) / (darker + 0.05)


def check_wcag_compliance(
    contrast_ratio: float, level: str = "AA", is_large_text: bool = False
) -> Dict[str, bool]:
    """
    Check if contrast ratio meets WCAG standards.

    Args:
        contrast_ratio: Calculated contrast ratio
        level: 'AA' or 'AAA'
        is_large_text: Whether text is large (18pt+ or 14pt+ bold)

    Returns:
        Dict with compliance status
    """
    thresholds = {
        "AA": {"normal": 4.5, "large": 3.0},
        "AAA": {"normal": 7.0, "large": 4.5},
    }

    text_size = "large" if is_large_text else "normal"

    return {
        "compliant_aa": contrast_ratio >= thresholds["AA"][text_size],
        "compliant_aaa": contrast_ratio >= thresholds["AAA"][text_size],
        "ratio": contrast_ratio,
        "threshold_aa": thresholds["AA"][text_size],
        "threshold_aaa": thresholds["AAA"][text_size],
    }


def generate_saliency_map(image: np.ndarray, method: str = "spectral") -> np.ndarray:
    """
    Generate visual saliency map showing attention-grabbing regions.

    Args:
        image: Input image (BGR)
        method: 'spectral' or 'fine_grained'

    Returns:
        Saliency map (grayscale)
    """
    if method == "spectral":
        # Spectral Residual method
        saliency = cv2.saliency.StaticSaliencySpectralResidual_create()
    else:
        # Fine-grained method
        saliency = cv2.saliency.StaticSaliencyFineGrained_create()

    (success, saliency_map) = saliency.computeSaliency(image)

    if success:
        # Normalize to 0-255
        saliency_map = (saliency_map * 255).astype("uint8")
        return saliency_map
    else:
        return np.zeros(image.shape[:2], dtype=np.uint8)


def extract_color_scheme(
    image: np.ndarray, n_colors: int = 5
) -> List[Tuple[int, int, int]]:
    """
    Extract dominant colors from image using k-means.

    Args:
        image: Input image (BGR)
        n_colors: Number of dominant colors

    Returns:
        List of RGB tuples
    """
    # Reshape image to list of pixels
    pixels = image.reshape(-1, 3).astype(np.float32)

    # K-means clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(
        pixels, n_colors, None, criteria, 10, cv2.KMEANS_PP_CENTERS
    )

    # Convert BGR to RGB
    colors = centers.astype(int)
    colors = [(int(c[2]), int(c[1]), int(c[0])) for c in colors]

    return colors


def detect_buttons(image: np.ndarray, min_area: int = 500) -> List[Dict]:
    """
    Detect button-like rectangular regions.

    Args:
        image: Input image (BGR)
        min_area: Minimum area for button detection

    Returns:
        List of detected button regions with metadata
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply threshold
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    buttons = []

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < min_area:
            continue

        # Get bounding box
        x, y, w, h = cv2.boundingRect(contour)

        # Calculate aspect ratio
        aspect_ratio = float(w) / h if h > 0 else 0

        # Buttons typically have aspect ratio between 1.5 and 5
        if 1.5 <= aspect_ratio <= 5:
            # Extract region
            roi = image[y : y + h, x : x + w]
            avg_color = cv2.mean(roi)[:3]

            buttons.append(
                {
                    "bbox": (x, y, w, h),
                    "area": area,
                    "aspect_ratio": aspect_ratio,
                    "avg_color": tuple(map(int, avg_color)),
                    "center": (x + w // 2, y + h // 2),
                }
            )

    return buttons


def calculate_visual_prominence(
    bbox: Tuple[int, int, int, int], viewport_size: Tuple[int, int]
) -> Dict[str, float]:
    """
    Calculate prominence metrics for a visual element.

    Args:
        bbox: Bounding box (x, y, w, h)
        viewport_size: (width, height) of viewport

    Returns:
        Dict with prominence metrics
    """
    x, y, w, h = bbox
    vw, vh = viewport_size

    # Size relative to viewport
    relative_width = w / vw
    relative_height = h / vh
    relative_area = (w * h) / (vw * vh)

    # Position (center of viewport is most prominent)
    center_x = x + w / 2
    center_y = y + h / 2

    # Distance from viewport center (0-1, normalized)
    dx = abs(center_x - vw / 2) / (vw / 2)
    dy = abs(center_y - vh / 2) / (vh / 2)
    centrality = 1.0 - np.sqrt(dx**2 + dy**2) / np.sqrt(2)

    return {
        "relative_width": relative_width,
        "relative_height": relative_height,
        "relative_area": relative_area,
        "centrality": centrality,
        "is_large": relative_area > 0.1,
        "is_central": centrality > 0.7,
        "prominence_score": (relative_area * 0.6 + centrality * 0.4),
    }


def detect_fake_disabled_button(
    image: np.ndarray, bbox: Tuple[int, int, int, int]
) -> Dict:
    """
    Detect if a button appears disabled (gray) but may be clickable.

    Args:
        image: Full screenshot
        bbox: Button bounding box (x, y, w, h)

    Returns:
        Dict with analysis results
    """
    x, y, w, h = bbox
    roi = image[y : y + h, x : x + w]

    # Calculate average color and saturation
    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    avg_hue, avg_sat, avg_val = cv2.mean(hsv)[:3]

    # Calculate color variance (low variance = uniform color)
    color_variance = np.var(roi)

    # Disabled buttons are typically:
    # - Low saturation (grayish)
    # - Medium-high value (not too dark)
    # - Uniform color (low variance)

    is_gray = avg_sat < 30
    is_medium_brightness = 100 < avg_val < 200
    is_uniform = color_variance < 500

    appears_disabled = is_gray and is_medium_brightness and is_uniform

    return {
        "appears_disabled": appears_disabled,
        "saturation": avg_sat,
        "brightness": avg_val,
        "color_variance": color_variance,
        "is_gray": is_gray,
        "confidence": 0.8 if appears_disabled else 0.2,
    }


def analyze_visual_hierarchy(buttons: List[Dict], labels: List[str]) -> Dict:
    """
    Analyze if visual hierarchy is inverted (accept subtle, decline prominent).

    Args:
        buttons: List of detected buttons with prominence data
        labels: Corresponding labels for each button

    Returns:
        Dict with hierarchy analysis
    """
    if len(buttons) < 2:
        return {"hierarchy_inverted": False, "confidence": 0.0}

    # Identify accept/decline buttons
    accept_idx = None
    decline_idx = None

    for i, label in enumerate(labels):
        label_lower = label.lower()
        if any(
            word in label_lower for word in ["accept", "yes", "agree", "ok", "continue"]
        ):
            accept_idx = i
        elif any(word in label_lower for word in ["decline", "no", "cancel", "skip"]):
            decline_idx = i

    if accept_idx is None or decline_idx is None:
        return {"hierarchy_inverted": False, "confidence": 0.0}

    # Compare prominence
    accept_prominence = buttons[accept_idx].get("prominence_score", 0)
    decline_prominence = buttons[decline_idx].get("prominence_score", 0)

    # Inverted if decline is more prominent
    inverted = decline_prominence > accept_prominence * 1.2

    prominence_diff = abs(decline_prominence - accept_prominence)
    confidence = min(prominence_diff * 2, 1.0)

    return {
        "hierarchy_inverted": inverted,
        "accept_prominence": accept_prominence,
        "decline_prominence": decline_prominence,
        "confidence": confidence,
    }


def create_heatmap_overlay(
    image: np.ndarray, saliency_map: np.ndarray, alpha: float = 0.5
) -> np.ndarray:
    """
    Create heatmap overlay on original image.

    Args:
        image: Original image
        saliency_map: Saliency/attention map
        alpha: Transparency of overlay

    Returns:
        Image with heatmap overlay
    """
    # Apply colormap to saliency
    heatmap = cv2.applyColorMap(saliency_map, cv2.COLORMAP_JET)

    # Blend with original image
    overlay = cv2.addWeighted(image, 1 - alpha, heatmap, alpha, 0)

    return overlay


def annotate_image(
    image: np.ndarray, detections: List[Dict], labels: List[str]
) -> np.ndarray:
    """
    Annotate image with detection results.

    Args:
        image: Input image
        detections: List of detection dicts with bbox
        labels: Labels for each detection

    Returns:
        Annotated image
    """
    annotated = image.copy()

    for detection, label in zip(detections, labels):
        bbox = detection.get("bbox")
        if bbox is None:
            continue

        x, y, w, h = bbox

        # Draw rectangle
        color = (0, 255, 0) if detection.get("is_safe", True) else (0, 0, 255)
        cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

        # Draw label
        cv2.putText(
            annotated, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2
        )

    return annotated


def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:
    """
    Preprocess image for better text extraction.

    Args:
        image: Input image

    Returns:
        Preprocessed image
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Denoise
    denoised = cv2.fastNlMeansDenoising(gray)

    # Increase contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # Threshold
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    return thresh


if __name__ == "__main__":
    print("=" * 80)
    print("Computer Vision Utilities Test")
    print("=" * 80)

    # Test contrast calculation
    print("\n1. WCAG Contrast Tests:")

    test_cases = [
        ((255, 255, 255), (0, 0, 0), "White on Black"),
        ((255, 255, 255), (128, 128, 128), "White on Gray"),
        ((0, 0, 0), (255, 255, 255), "Black on White"),
        ((255, 0, 0), (255, 255, 255), "Red on White"),
    ]

    for fg, bg, desc in test_cases:
        ratio = calculate_contrast_ratio(fg, bg)
        compliance = check_wcag_compliance(ratio)
        print(f"   {desc}: {ratio:.2f}")
        print(f"      AA: {'✓' if compliance['compliant_aa'] else '✗'}")
        print(f"      AAA: {'✓' if compliance['compliant_aaa'] else '✗'}")

    # Test visual prominence
    print("\n2. Visual Prominence Test:")
    viewport = (1920, 1080)

    test_elements = [
        ((860, 490, 200, 100), "Centered button"),
        ((50, 50, 100, 50), "Top-left button"),
        ((1770, 1000, 100, 50), "Bottom-right button"),
    ]

    for bbox, desc in test_elements:
        prominence = calculate_visual_prominence(bbox, viewport)
        print(f"   {desc}:")
        print(f"      Area: {prominence['relative_area']:.3f}")
        print(f"      Centrality: {prominence['centrality']:.3f}")
        print(f"      Prominence: {prominence['prominence_score']:.3f}")

    print("\n✓ CV utilities test complete")
