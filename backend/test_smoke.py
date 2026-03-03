#!/usr/bin/env python3
"""
Quick Smoke Tests
Tests individual components can be imported and basic functions work.
"""

import sys

def test_experiment_tracker():
    """Test experiment tracker (no dependencies)."""
    print("\n1. Testing Experiment Tracker...")
    try:
        from experiments.experiment_tracker import ExperimentTracker
        tracker = ExperimentTracker(log_file='test_smoke.json')
        exp_id = tracker.log_experiment(
            name="smoke_test",
            config={'test': True},
            metrics={'accuracy': 0.95}
        )
        best = tracker.get_best_model('accuracy')
        assert best is not None
        print("   ✓ Experiment tracker works!")
        return True
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def test_feature_extraction():
    """Test feature extraction."""
    print("\n2. Testing Feature Extraction...")
    try:
        from feature_extraction import FeatureExtractor
        extractor = FeatureExtractor()
        features = extractor.extract_features(
            text="Only 2 left in stock!",
            element_type="span",
            color="#ff0000"
        )
        assert len(features) > 30  # Should have 40+ features
        print(f"   ✓ Feature extraction works! ({len(features)} features)")
        return True
    except ImportError as e:
        print(f"   ⊘ Skipped: Missing dependency ({e})")
        return None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def test_cv_utils():
    """Test CV utilities."""
    print("\n3. Testing CV Utilities...")
    try:
        from cv_utils import calculate_contrast_ratio, check_wcag_compliance
        ratio = calculate_contrast_ratio((255, 255, 255), (0, 0, 0))
        assert 20.9 < ratio < 21.1  # Should be 21
        compliance = check_wcag_compliance(ratio)
        assert compliance['compliant_aa']
        print(f"   ✓ CV utilities work! (contrast: {ratio:.2f})")
        return True
    except ImportError as e:
        print(f"   ⊘ Skipped: OpenCV not installed")
        return None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def test_vision_detector():
    """Test vision detector."""
    print("\n4. Testing Vision Detector...")
    try:
        from vision_detector import VisionDetector
        # Just test initialization
        detector = VisionDetector()
        print("   ✓ Vision detector initialized!")
        return True
    except ImportError:
        print("   ⊘ Skipped: OpenCV not installed")
        return None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def test_multimodal_detector():
    """Test multimodal detector."""
    print("\n5. Testing Multimodal Detector...")
    try:
        from multimodal_detector import MultimodalDetector
        detector = MultimodalDetector()
        print("   ✓ Multimodal detector initialized!")
        # Note: May show warnings about missing transformer, that's OK
        return True
    except ImportError as e:
        print(f"   ⊘ Skipped: Missing dependency ({e})")
        return None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def test_flask_app():
    """Test Flask app can be imported."""
    print("\n6. Testing Flask App...")
    try:
        import app
        print("   ✓ Flask app can be imported!")
        return True
    except ImportError as e:
        print(f"   ⊘ Skipped: Missing dependency ({e})")
        return None
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        return False

def main():
    print("="*60)
    print("PATTERNSHIELD SMOKE TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Experiment Tracker", test_experiment_tracker()))
    results.append(("Feature Extraction", test_feature_extraction()))
    results.append(("CV Utilities", test_cv_utils()))
    results.append(("Vision Detector", test_vision_detector()))
    results.append(("Multimodal Detector", test_multimodal_detector()))
    results.append(("Flask App", test_flask_app()))
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result is True)
    failed = sum(1 for _, result in results if result is False)
    skipped = sum(1 for _, result in results if result is None)
    
    print(f"\n✓ Passed:  {passed}")
    print(f"✗ Failed:  {failed}")
    print(f"⊘ Skipped: {skipped}")
    
    print("\nDetailed Results:")
    for name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"  {status}  {name}")
    
    if failed > 0:
        print("\n⚠ Some tests failed!")
        print("  Check error messages above and install missing dependencies.")
        sys.exit(1)
    elif passed == 0:
        print("\n⚠ No tests passed!")
        print("  Install core dependencies: pip install numpy scikit-learn Flask textblob nltk")
        sys.exit(1)
    else:
        print("\n✓ Core functionality working!")
        if skipped > 0:
            print(f"  ({skipped} optional tests skipped - install more dependencies to enable)")
        sys.exit(0)

if __name__ == '__main__':
    main()
