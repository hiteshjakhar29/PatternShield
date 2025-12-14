#!/usr/bin/env python3
"""
Comprehensive Test Suite for PatternShield
Tests all components and reports status.
"""

import sys
import importlib.util


def check_import(module_name, package=None):
    """Check if a module can be imported."""
    try:
        if package:
            __import__(f"{package}.{module_name}")
        else:
            __import__(module_name)
        return True, "OK"
    except ImportError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_file_import(filepath, module_name):
    """Check if a Python file can be imported."""
    try:
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return True, "OK"
        return False, "Could not load module"
    except ImportError as e:
        return False, f"Import error: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def main():
    print("=" * 80)
    print("PATTERNSHIELD COMPREHENSIVE TEST SUITE")
    print("=" * 80)

    # Test 1: Check Python version
    print("\n1. Python Version Check")
    print(f"   Python {sys.version}")
    if sys.version_info >= (3, 8):
        print("   ✓ Python version OK")
    else:
        print("   ✗ Python 3.8+ required")

    # Test 2: Check core dependencies
    print("\n2. Core Dependencies")
    core_deps = {
        "numpy": "NumPy",
        "scipy": "SciPy",
        "sklearn": "scikit-learn",
        "flask": "Flask",
        "yaml": "PyYAML",
    }

    core_ok = True
    for module, name in core_deps.items():
        ok, msg = check_import(module)
        status = "✓" if ok else "✗"
        print(f"   {status} {name}: {msg if not ok else 'OK'}")
        if not ok:
            core_ok = False

    # Test 3: Check NLP dependencies
    print("\n3. NLP Dependencies")
    nlp_deps = {
        "textblob": "TextBlob",
        "nltk": "NLTK",
        "textstat": "textstat",
    }

    nlp_ok = True
    for module, name in nlp_deps.items():
        ok, msg = check_import(module)
        status = "✓" if ok else "✗"
        print(f"   {status} {name}: {msg if not ok else 'OK'}")
        if not ok:
            nlp_ok = False

    # Test 4: Check visualization dependencies
    print("\n4. Visualization Dependencies")
    viz_deps = {
        "matplotlib": "Matplotlib",
        "seaborn": "Seaborn",
    }

    viz_ok = True
    for module, name in viz_deps.items():
        ok, msg = check_import(module)
        status = "✓" if ok else "✗"
        print(f"   {status} {name}: {msg if not ok else 'OK'}")
        if not ok:
            viz_ok = False

    # Test 5: Check CV dependencies (optional)
    print("\n5. Computer Vision Dependencies (Optional)")
    cv_deps = {
        "cv2": "OpenCV",
        "PIL": "Pillow",
    }

    cv_ok = True
    for module, name in cv_deps.items():
        ok, msg = check_import(module)
        status = "✓" if ok else "⚠"
        print(f"   {status} {name}: {msg if not ok else 'OK'}")
        if not ok:
            cv_ok = False

    # Test 6: Check Deep Learning dependencies (optional)
    print("\n6. Deep Learning Dependencies (Optional)")
    dl_deps = {
        "torch": "PyTorch",
        "transformers": "Transformers",
        "datasets": "Datasets",
    }

    dl_ok = True
    for module, name in dl_deps.items():
        ok, msg = check_import(module)
        status = "✓" if ok else "⚠"
        print(f"   {status} {name}: {msg if not ok else 'OK'}")
        if not ok:
            dl_ok = False

    # Test 7: Check MLOps dependencies (optional)
    print("\n7. MLOps Dependencies (Optional)")
    mlops_deps = {
        "mlflow": "MLflow",
        "shap": "SHAP",
        "tensorboard": "TensorBoard",
    }

    mlops_ok = True
    for module, name in mlops_deps.items():
        ok, msg = check_import(module)
        status = "✓" if ok else "⚠"
        print(f"   {status} {name}: {msg if not ok else 'OK'}")
        if not ok:
            mlops_ok = False

    # Test 8: Check PatternShield modules
    print("\n8. PatternShield Core Modules")

    modules = [
        ("experiments/experiment_tracker.py", "experiment_tracker", True),
        ("feature_extraction.py", "feature_extraction", core_ok and nlp_ok),
        ("cv_utils.py", "cv_utils", cv_ok),
        ("vision_detector.py", "vision_detector", cv_ok),
        ("multimodal_detector.py", "multimodal_detector", cv_ok),
    ]

    for filepath, name, should_work in modules:
        if should_work:
            ok, msg = check_file_import(filepath, name)
            status = "✓" if ok else "✗"
            print(f"   {status} {name}: {msg}")
        else:
            print(f"   ⊘ {name}: Skipped (missing dependencies)")

    # Test 9: Quick functional tests
    print("\n9. Functional Tests")

    # Test experiment tracker (no deps)
    print("   Testing experiment tracker...")
    try:
        from experiments.experiment_tracker import ExperimentTracker

        tracker = ExperimentTracker(log_file="test_log.json")
        print("   ✓ Experiment tracker works")
    except Exception as e:
        print(f"   ✗ Experiment tracker failed: {e}")

    # Test feature extraction if deps available
    if core_ok and nlp_ok:
        print("   Testing feature extraction...")
        try:
            from feature_extraction import FeatureExtractor

            extractor = FeatureExtractor()
            features = extractor.extract_features("Test text", "div", "#000000")
            if len(features) > 0:
                print(f"   ✓ Feature extraction works ({len(features)} features)")
            else:
                print("   ✗ Feature extraction returned no features")
        except Exception as e:
            print(f"   ✗ Feature extraction failed: {e}")
    else:
        print("   ⊘ Feature extraction skipped (missing dependencies)")

    # Test CV utils if deps available
    if cv_ok:
        print("   Testing CV utilities...")
        try:
            from cv_utils import calculate_contrast_ratio, check_wcag_compliance

            ratio = calculate_contrast_ratio((255, 255, 255), (0, 0, 0))
            if abs(ratio - 21.0) < 0.1:
                print(f"   ✓ CV utilities work (contrast ratio: {ratio:.2f})")
            else:
                print(f"   ⚠ CV utilities work but unexpected result: {ratio:.2f}")
        except Exception as e:
            print(f"   ✗ CV utilities failed: {e}")
    else:
        print("   ⊘ CV utilities skipped (OpenCV not installed)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\nRequired for core functionality:")
    print(
        f"  Core ML: {'✓ PASS' if core_ok else '✗ FAIL - Install: pip install numpy scipy scikit-learn'}"
    )
    print(
        f"  Flask: {'✓ PASS' if check_import('flask')[0] else '✗ FAIL - Install: pip install Flask Flask-CORS'}"
    )
    print(
        f"  NLP: {'✓ PASS' if nlp_ok else '✗ FAIL - Install: pip install textblob nltk textstat'}"
    )

    print("\nOptional for enhanced functionality:")
    print(
        f"  Visualization: {'✓ PASS' if viz_ok else '⚠ MISSING - Install: pip install matplotlib seaborn'}"
    )
    print(
        f"  Computer Vision: {'✓ PASS' if cv_ok else '⚠ MISSING - Install: pip install opencv-python opencv-contrib-python pillow'}"
    )
    print(
        f"  Deep Learning: {'✓ PASS' if dl_ok else '⚠ MISSING - Install: pip install torch transformers datasets'}"
    )
    print(
        f"  MLOps: {'✓ PASS' if mlops_ok else '⚠ MISSING - Install: pip install mlflow shap tensorboard'}"
    )

    print("\nWhat you can run now:")
    if core_ok:
        print("  ✓ Experiment tracking")
        print("  ✓ Feature extraction")
        print("  ✓ Feature analysis")
    if viz_ok:
        print("  ✓ Feature visualization")
    if cv_ok:
        print("  ✓ Computer vision detection")
    if dl_ok:
        print("  ✓ Transformer training")
        print("  ✓ Model comparison")

    if not (core_ok and nlp_ok):
        print("\n⚠ CRITICAL: Install core dependencies first!")
        print("  Run: pip install numpy scipy scikit-learn Flask textblob nltk")
    elif not viz_ok:
        print("\n⚠ Install visualization for plots:")
        print("  Run: pip install matplotlib seaborn")
    else:
        print("\n✓ All required dependencies installed!")
        print("  You can run all core features.")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
