# PatternShield - Mac Installation Guide

## Quick Start (5 Minutes)

```bash
cd ~/Desktop/PatternShield/backend

# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Upgrade pip
pip install --upgrade pip

# 3. Install core dependencies (one by one for Python 3.13)
pip install numpy
pip install scipy
pip install scikit-learn
pip install Flask Flask-CORS
pip install textblob nltk textstat
pip install matplotlib seaborn
pip install pyyaml python-dotenv

# 4. Download NLTK data
python -c "import nltk; nltk.download('brown'); nltk.download('punkt'); nltk.download('punkt_tab')"

# 5. Test installation
python test_smoke.py
```

**Expected output**: At least 2-3 tests should pass ✓

---

## What Just Happened?

✓ **Stage 1 Installed**:
- NumPy, SciPy, scikit-learn (ML core)
- Flask (web framework)
- TextBlob, NLTK (NLP)
- Matplotlib, Seaborn (visualization)

This gives you **core functionality**:
- ✓ Experiment tracking
- ✓ Feature extraction
- ✓ Feature analysis
- ✓ Model training (when model files added)

---

## Optional: Install More Features

### Computer Vision (5-10 minutes)

```bash
pip install opencv-python
pip install opencv-contrib-python
pip install pillow

# Test it
python cv_utils.py
```

**What this enables**:
- Screenshot analysis
- WCAG contrast checking
- Visual pattern detection

### Deep Learning (10-20 minutes)

```bash
# PyTorch CPU version (smaller, faster)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Transformers
pip install transformers datasets accelerate tqdm

# Test it
python -c "import torch; import transformers; print('✓ Deep learning ready')"
```

**What this enables**:
- Transformer training
- DistilBERT model
- Advanced NLP

### MLOps Tools (5 minutes)

```bash
pip install mlflow
pip install shap
pip install tensorboard

# Test it
python experiments/experiment_tracker.py
```

**What this enables**:
- MLflow experiment tracking
- SHAP explainability
- TensorBoard visualization

---

## Automated Installation (Interactive)

```bash
chmod +x install.sh
./install.sh
```

This script:
1. Installs core dependencies
2. Asks if you want optional packages
3. Runs tests automatically
4. Shows what you can do next

---

## Verify Installation

### Option 1: Comprehensive Test

```bash
python test_installation.py
```

Shows detailed status of all dependencies.

### Option 2: Quick Smoke Test

```bash
python test_smoke.py
```

Tests that core components work.

### Option 3: Manual Tests

```bash
# Test experiment tracker (always works)
python experiments/experiment_tracker.py

# Test feature extraction (needs core deps)
python feature_extraction.py

# Test CV (needs opencv)
python cv_utils.py

# Test vision detector (needs opencv)
python vision_detector.py
```

---

## What Can I Run Now?

After **core installation only**:

```bash
# 1. Experiment tracking (demo)
python experiments/experiment_tracker.py

# 2. Feature extraction (demo)
python feature_extraction.py

# 3. Feature analysis (generates plots - takes 2-3 min)
python feature_analysis.py

# 4. Feature selection (generates plots - takes 3-5 min)
python feature_selection.py

# 5. Ablation study (generates plots - takes 5-7 min)
python experiments/feature_ablation.py
```

After **Computer Vision** installed:

```bash
# 1. CV utilities test
python cv_utils.py

# 2. Vision detector test
python vision_detector.py

# 3. Multimodal detector test
python multimodal_detector.py
```

After **Deep Learning** installed:

```bash
# 1. Train transformer (30-45 min on CPU)
bash scripts/train.sh

# 2. Model comparison
python model_comparison.py

# 3. Start Flask API
python app.py
```

---

## Troubleshooting

### Issue: scikit-learn won't compile

**Solution**: Install pre-built wheel
```bash
pip install --upgrade pip
pip install scikit-learn --no-build-isolation
```

Or use Python 3.11:
```bash
brew install pyenv
pyenv install 3.11.9
pyenv local 3.11.9
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: OpenCV fails to install

**Solution 1**: Use brew
```bash
brew install opencv
pip install opencv-python
```

**Solution 2**: Skip OpenCV
```bash
# Just use core features (no CV)
# Everything else still works!
```

### Issue: torch/transformers too large

**Solution**: Skip deep learning
```bash
# You can still:
# - Run experiments
# - Extract features
# - Analyze data
# - Use rule-based detection
```

### Issue: NLTK download fails

```bash
python -c "import nltk; nltk.download('all')"
```

Or manually:
```python
import nltk
nltk.download('brown')
nltk.download('punkt')
nltk.download('punkt_tab')
```

### Issue: Port 5000 in use

```bash
# Kill process
lsof -ti:5000 | xargs kill -9

# Or use different port
python app.py --port 5001
```

### Issue: "No module named 'X'"

```bash
# Check what's installed
pip list | grep -i <module>

# Install missing module
pip install <module>
```

---

## File Structure

```
backend/
├── test_installation.py      # Comprehensive test
├── test_smoke.py             # Quick smoke test
├── install.sh                # Automated installer
│
├── experiments/
│   └── experiment_tracker.py # ✓ Works immediately
│
├── feature_extraction.py     # ✓ After core install
├── feature_analysis.py       # ✓ After core install
├── feature_selection.py      # ✓ After core install
│
├── cv_utils.py               # ⚠ Needs OpenCV
├── vision_detector.py        # ⚠ Needs OpenCV
├── multimodal_detector.py    # ⚠ Needs OpenCV
│
├── train_transformer.py      # ⚠ Needs PyTorch
├── model_comparison.py       # ⚠ Needs PyTorch
│
└── app.py                    # ✓ After core install
```

---

## Python Version Compatibility

| Python | Status | Notes |
|--------|--------|-------|
| 3.13.x | ⚠ Works | Install packages one-by-one |
| 3.12.x | ✓ Works | All packages available |
| 3.11.x | ✓ Best | Recommended |
| 3.10.x | ✓ Works | Fully compatible |
| 3.9.x  | ✓ Works | Fully compatible |
| 3.8.x  | ⚠ Works | Some packages old |

**Recommendation**: Use Python 3.11 for smoothest experience.

---

## Dependencies Summary

### Required (Core Functionality)
- numpy, scipy, scikit-learn
- Flask, Flask-CORS
- textblob, nltk, textstat
- matplotlib, seaborn
- pyyaml, python-dotenv

### Optional (Enhanced Features)
- opencv-python, opencv-contrib-python, pillow (CV)
- torch, transformers, datasets (Deep Learning)
- mlflow, shap, tensorboard (MLOps)

---

## Quick Demo for Portfolio

```bash
# 1. Install core only (5 min)
pip install numpy scipy scikit-learn Flask textblob nltk matplotlib seaborn pyyaml

# 2. Run quick tests (1 min)
python test_smoke.py

# 3. Generate analysis plots (5 min)
python feature_analysis.py
python feature_selection.py

# 4. Show results
open analysis_plots/feature_importance.png
open analysis_plots/feature_selection_comparison.png

# 5. Read documentation
open ../FEATURES.md
open ../CV_ANALYSIS.md
open ../MLOPS.md
```

This is enough to demonstrate the project!

---

## Getting Help

1. **Check test results**: `python test_installation.py`
2. **Check smoke tests**: `python test_smoke.py`
3. **Check imports**: `python -c "import numpy; print('OK')"`
4. **Check pip list**: `pip list`
5. **Check Python version**: `python --version`

---

## Success Criteria

✓ **Minimum (for demo)**: 
- Core dependencies installed
- `test_smoke.py` passes 2+ tests
- Can generate analysis plots

✓ **Good (for development)**:
- Core + CV dependencies
- `test_smoke.py` passes 4+ tests
- Can run all analysis scripts

✓ **Complete (full functionality)**:
- All dependencies installed
- `test_smoke.py` passes all tests
- Can train models and run API

---

## Next Steps

1. **If tests pass**: Start using the project!
   ```bash
   python experiments/experiment_tracker.py
   python feature_analysis.py
   ```

2. **If some tests fail**: Install missing deps
   ```bash
   python test_installation.py  # Shows what's missing
   pip install <missing-package>
   ```

3. **If nothing works**: Use Python 3.11
   ```bash
   pyenv install 3.11.9
   # Start over with clean venv
   ```

---

## Support

- Documentation: See `*.md` files
- Tests: Run `test_installation.py` or `test_smoke.py`
- Manual: Read code comments

Good luck! 🚀
