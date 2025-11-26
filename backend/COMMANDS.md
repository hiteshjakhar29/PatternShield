# PatternShield - Command Reference

## Initial Setup

```bash
# Navigate to project
cd ~/Desktop/PatternShield/backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Your prompt should now show (venv)
```

---

## Installation Commands

### Method 1: Automated (Recommended)

```bash
./install.sh
```

Installs everything with prompts for optional packages.

### Method 2: Manual Core Only (Fastest)

```bash
pip install --upgrade pip
pip install numpy scipy scikit-learn
pip install Flask Flask-CORS
pip install textblob nltk textstat
pip install matplotlib seaborn
pip install pyyaml python-dotenv
python -c "import nltk; nltk.download('brown'); nltk.download('punkt'); nltk.download('punkt_tab')"
```

### Method 3: From requirements.txt (May fail on Python 3.13)

```bash
pip install -r requirements.txt
```

---

## Testing Commands

### Quick Check

```bash
# Smoke test (tests core components)
python test_smoke.py

# Expected: 2-6 tests pass
```

### Comprehensive Check

```bash
# Full dependency check
python test_installation.py

# Shows what's installed and what's missing
```

### Manual Tests

```bash
# Test experiment tracker
python experiments/experiment_tracker.py

# Test feature extraction
python feature_extraction.py

# Test CV utilities (needs OpenCV)
python cv_utils.py

# Test vision detector (needs OpenCV)
python vision_detector.py
```

---

## Running Analysis

### Feature Engineering

```bash
# Generate feature analysis plots (2-3 min)
python feature_analysis.py

# Output: analysis_plots/
#   - feature_importance.png
#   - correlation_matrix_pearson.png
#   - mutual_information.png
#   - shap_summary.png (if SHAP installed)
#   - tsne_visualization.png
```

### Feature Selection

```bash
# Compare selection methods (3-5 min)
python feature_selection.py

# Output: 
#   - analysis_plots/feature_selection_comparison.png
#   - FEATURE_SELECTION_RESULTS.md
```

### Ablation Study

```bash
# Systematic feature ablation (5-7 min)
python experiments/feature_ablation.py

# Output:
#   - experiments/ablation_results.png
#   - experiments/ablation_results.json
```

---

## Training Models

### Train Transformer

```bash
# Full training (30-45 min CPU, 5-10 min GPU)
bash scripts/train.sh

# Custom parameters
bash scripts/train.sh --epochs 15 --batch_size 32 --lr 3e-5

# Monitor with TensorBoard (in new terminal)
tensorboard --logdir=training_logs
# Open: http://localhost:6006
```

### Compare Models

```bash
# Benchmark all models (needs trained transformer)
python model_comparison.py

# Output: MODEL_COMPARISON.md
```

---

## Running Flask API

```bash
# Start server
python app.py

# Server runs on: http://localhost:5000
```

### Test API (in new terminal)

```bash
# Rule-based detection
curl -X POST http://localhost:5000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "Only 2 left in stock!", "element_type": "span", "color": "#ff0000"}'

# Transformer detection
curl -X POST http://localhost:5000/analyze/transformer \
  -H "Content-Type: application/json" \
  -d '{"text": "Only 2 left in stock!"}'

# Ensemble detection
curl -X POST http://localhost:5000/analyze/ensemble \
  -H "Content-Type: application/json" \
  -d '{"text": "Only 2 left in stock!"}'
```

---

## MLflow Commands

```bash
# Start MLflow UI
mlflow ui

# Open browser: http://localhost:5000

# Use custom port
mlflow ui --port 5001
```

---

## Computer Vision

### Test CV Utilities

```bash
python cv_utils.py

# Expected output:
#   WCAG contrast tests
#   Visual prominence tests
```

### Test Vision Detector

```bash
python vision_detector.py

# Creates test image and analyzes it
```

### Test Multimodal Detector

```bash
python multimodal_detector.py

# Tests text+vision fusion
```

---

## Chrome Extension

```bash
# Navigate to extension directory
cd ../extension

# In Chrome:
# 1. Go to chrome://extensions/
# 2. Enable "Developer mode"
# 3. Click "Load unpacked"
# 4. Select the extension/ folder
```

Make sure Flask API is running first!

---

## Viewing Documentation

```bash
# Open markdown files
open INSTALL_MAC.md
open ../FEATURES.md
open ../CV_ANALYSIS.md
open ../MLOPS.md
open ../README.md

# Or use any text editor
code FEATURES.md
```

---

## Viewing Generated Files

```bash
# Analysis plots
open analysis_plots/feature_importance.png
open analysis_plots/correlation_matrix_pearson.png

# Ablation results
open experiments/ablation_results.png

# Selection results
open FEATURE_SELECTION_RESULTS.md

# Experiment log
cat experiments/experiment_log.json
```

---

## Troubleshooting Commands

### Check Installation

```bash
# Python version
python --version

# Installed packages
pip list

# Test specific import
python -c "import numpy; print('numpy OK')"
python -c "import sklearn; print('sklearn OK')"
python -c "import flask; print('flask OK')"
python -c "import cv2; print('opencv OK')"
python -c "import torch; print('pytorch OK')"
```

### Fix Common Issues

```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall package
pip uninstall <package>
pip install <package>

# Clear pip cache
pip cache purge

# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### Clean Start

```bash
# Deactivate venv
deactivate

# Remove old venv
cd ~/Desktop/PatternShield
rm -rf venv

# Create fresh venv
python3 -m venv venv
source venv/bin/activate

# Install from scratch
cd backend
./install.sh
```

---

## Quick Workflows

### Demo Preparation (10 minutes)

```bash
# 1. Install core
pip install numpy scipy scikit-learn Flask textblob nltk matplotlib seaborn pyyaml

# 2. Test
python test_smoke.py

# 3. Generate plots
python feature_analysis.py
python feature_selection.py

# 4. View results
open analysis_plots/feature_importance.png
```

### Full Development Setup (30 minutes)

```bash
# 1. Run automated install
./install.sh

# Answer 'y' to all prompts

# 2. Run all tests
python test_installation.py
python test_smoke.py

# 3. Generate all analysis
python feature_analysis.py
python feature_selection.py
python experiments/feature_ablation.py

# 4. Test CV
python cv_utils.py
python vision_detector.py
```

### Model Training Workflow

```bash
# 1. Train transformer
bash scripts/train.sh

# 2. Monitor (new terminal)
tensorboard --logdir=training_logs

# 3. After training, compare models
python model_comparison.py

# 4. Start API
python app.py
```

---

## Environment Management

### Activate Virtual Environment

```bash
cd ~/Desktop/PatternShield
source venv/bin/activate
```

### Deactivate

```bash
deactivate
```

### Check Active Environment

```bash
# Shows venv path
which python

# Shows venv packages only
pip list
```

---

## File Generation

### Create Documentation

```bash
# Feature selection report
python feature_selection.py
# Creates: FEATURE_SELECTION_RESULTS.md

# Model comparison report
python model_comparison.py
# Creates: MODEL_COMPARISON.md

# Experiment report
python experiments/experiment_tracker.py
# Creates: test_experiments.md
```

### Create Visualizations

```bash
# All feature plots
python feature_analysis.py

# Selection comparison
python feature_selection.py

# Ablation results
python experiments/feature_ablation.py
```

---

## Git Commands (Optional)

```bash
# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial PatternShield implementation"

# Add remote (replace with your repo)
git remote add origin <your-repo-url>

# Push
git push -u origin main
```

---

## Performance Benchmarks

| Command | Time (CPU) | Output |
|---------|-----------|--------|
| `test_smoke.py` | <30s | Test results |
| `feature_extraction.py` | <10s | Feature demo |
| `feature_analysis.py` | 2-3 min | 5 plots |
| `feature_selection.py` | 3-5 min | Comparison |
| `feature_ablation.py` | 5-7 min | Ablation results |
| `train_transformer.py` | 30-45 min | Trained model |
| `model_comparison.py` | 1-2 min | Comparison report |

---

## Directory Navigation

```bash
# Main project
cd ~/Desktop/PatternShield

# Backend
cd ~/Desktop/PatternShield/backend

# Experiments
cd ~/Desktop/PatternShield/backend/experiments

# Extension
cd ~/Desktop/PatternShield/extension

# Back to backend
cd ~/Desktop/PatternShield/backend
```

---

## Quick Reference

**Most Used Commands:**
```bash
source venv/bin/activate           # Start working
python test_smoke.py              # Quick test
python feature_analysis.py        # Generate plots
python app.py                     # Start API
deactivate                        # Stop working
```

**For Demo:**
```bash
python experiments/experiment_tracker.py  # Show MLOps
python feature_extraction.py              # Show features
python cv_utils.py                        # Show CV
```

**For Development:**
```bash
./install.sh                      # Setup
python test_installation.py       # Check status
bash scripts/train.sh            # Train models
mlflow ui                        # View experiments
```

---

That's it! Use this as your command reference.
