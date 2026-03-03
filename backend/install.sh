#!/bin/bash
# PatternShield Installation Script for Mac
# Handles Python 3.13 compatibility issues

set -e  # Exit on error

echo "========================================"
echo "PatternShield Installation Script"
echo "========================================"
echo ""

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"
echo ""

# Upgrade pip first
echo "Upgrading pip..."
pip install --upgrade pip
echo "✓ pip upgraded"
echo ""

# Stage 1: Core ML dependencies
echo "========================================"
echo "Stage 1: Core ML Dependencies"
echo "========================================"
echo "Installing numpy, scipy, scikit-learn..."
pip install numpy
pip install scipy  
pip install scikit-learn
echo "✓ Core ML dependencies installed"
echo ""

# Stage 2: Web framework
echo "========================================"
echo "Stage 2: Web Framework"
echo "========================================"
echo "Installing Flask..."
pip install Flask Flask-CORS
echo "✓ Flask installed"
echo ""

# Stage 3: NLP
echo "========================================"
echo "Stage 3: NLP Dependencies"
echo "========================================"
echo "Installing textblob, nltk, textstat..."
pip install textblob nltk textstat
echo "✓ NLP dependencies installed"
echo ""

echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('brown', quiet=True); nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True)" 2>/dev/null || echo "NLTK data download: some packages may have failed (this is OK)"
echo "✓ NLTK data downloaded"
echo ""

# Stage 4: Visualization
echo "========================================"
echo "Stage 4: Visualization"
echo "========================================"
echo "Installing matplotlib, seaborn..."
pip install matplotlib seaborn
echo "✓ Visualization libraries installed"
echo ""

# Stage 5: Utilities
echo "========================================"
echo "Stage 5: Utilities"
echo "========================================"
echo "Installing pyyaml, python-dotenv..."
pip install pyyaml python-dotenv
echo "✓ Utilities installed"
echo ""

# Stage 6: Computer Vision (optional, may take time)
echo "========================================"
echo "Stage 6: Computer Vision (Optional)"
echo "========================================"
read -p "Install OpenCV? (takes 5-10 min) [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Installing opencv-python..."
    pip install opencv-python
    echo "Installing opencv-contrib-python..."
    pip install opencv-contrib-python
    pip install pillow
    echo "✓ OpenCV installed"
else
    echo "⊘ Skipping OpenCV (you can install later with: pip install opencv-python opencv-contrib-python pillow)"
fi
echo ""

# Stage 7: Deep Learning (optional, takes longest)
echo "========================================"
echo "Stage 7: Deep Learning (Optional)"
echo "========================================"
read -p "Install PyTorch and Transformers? (takes 10-20 min) [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Installing PyTorch (CPU version)..."
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    echo "Installing transformers and related packages..."
    pip install transformers datasets accelerate tqdm
    echo "✓ Deep Learning packages installed"
else
    echo "⊘ Skipping Deep Learning packages"
fi
echo ""

# Stage 8: MLOps (optional)
echo "========================================"
echo "Stage 8: MLOps Tools (Optional)"
echo "========================================"
read -p "Install MLflow, SHAP, TensorBoard? [y/N]: " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "Installing MLflow..."
    pip install mlflow
    echo "Installing SHAP..."
    pip install shap
    echo "Installing TensorBoard..."
    pip install tensorboard
    echo "✓ MLOps tools installed"
else
    echo "⊘ Skipping MLOps tools"
fi
echo ""

# Run tests
echo "========================================"
echo "Running Installation Tests"
echo "========================================"
python test_installation.py

echo ""
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Test core functionality:"
echo "     python experiments/experiment_tracker.py"
echo ""  
echo "  2. Test feature extraction:"
echo "     python feature_extraction.py"
echo ""
echo "  3. Read documentation:"
echo "     cat ../README.md"
echo ""
echo "  4. If you installed OpenCV, test CV:"
echo "     python cv_utils.py"
echo ""
echo "Happy coding!"
