# Mac Installation Fix for Python 3.13

## The Problem

Python 3.13 is very new (released Oct 2024) and some packages don't have pre-built wheels yet, causing compilation errors.

## Solution: Install in Stages

### Stage 1: Core Dependencies (Fast)

```bash
cd backend

# Install minimal requirements first
pip install --upgrade pip
pip install numpy scipy
pip install scikit-learn
pip install Flask Flask-CORS
pip install textblob nltk
pip install matplotlib seaborn
pip install pyyaml python-dotenv
```

### Stage 2: Computer Vision (May take time)

```bash
# OpenCV - may need to compile
pip install opencv-python
pip install opencv-contrib-python

# Alternative: Use brew-installed OpenCV
# brew install opencv
```

### Stage 3: Deep Learning (Optional, takes longest)

```bash
# PyTorch - large download
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Transformers
pip install transformers datasets accelerate

# TensorBoard
pip install tensorboard

# SHAP
pip install shap
```

### Stage 4: MLOps (Optional)

```bash
pip install mlflow
pip install textstat
```

## Quick Test After Stage 1

```bash
# Test feature extraction
python feature_extraction.py

# Test experiment tracker (no dependencies needed)
python experiments/experiment_tracker.py
```

## Alternative: Use Python 3.11

If you continue having issues, use Python 3.11 (most stable):

```bash
# Install Python 3.11 using pyenv
brew install pyenv
pyenv install 3.11.6
pyenv local 3.11.6

# Create new venv
python -m venv venv
source venv/bin/activate

# Install all requirements
pip install -r requirements.txt
```

## Skip Heavy Dependencies

If you just want to see the code working:

```bash
# Install only what's needed for basic tests
pip install -r requirements-minimal.txt

# Download NLTK data
python -c "import nltk; nltk.download('brown'); nltk.download('punkt')"
```

## What Works Without Full Installation

These components work with minimal dependencies:

✅ **Experiment Tracker** - No ML dependencies needed
```bash
python experiments/experiment_tracker.py
```

✅ **Configuration Management** - Just needs PyYAML
```bash
pip install pyyaml
cat config/experiment_config.yaml
```

✅ **Documentation** - Read without running
```bash
open FEATURES.md
open CV_ANALYSIS.md
open MLOPS.md
```

## What Needs Full Installation

These need all dependencies:

❌ Feature Analysis (needs sklearn, shap, matplotlib)
❌ Computer Vision (needs opencv)
❌ Transformer Training (needs torch, transformers)
❌ Model Comparison (needs sklearn, transformers)

## Recommended Approach for Demo

1. **Install minimal requirements** (5 min)
2. **Run experiment tracker** (works immediately)
3. **Read documentation** (no installation needed)
4. **Show code quality** (no need to run)

This is sufficient for portfolio/interview demos!

## If Compilation Errors Persist

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Update Homebrew
brew update

# Install OpenMP support
brew install libomp

# Try again
pip install scikit-learn
```

## Current Status Check

```bash
# See what's installed
pip list

# Test imports
python -c "import numpy; print('numpy OK')"
python -c "import sklearn; print('sklearn OK')"
python -c "import flask; print('flask OK')"
```
