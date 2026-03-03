#!/bin/bash

# PatternShield ML Evaluation - Complete Pipeline
# This script runs the full evaluation suite and generates all artifacts

echo "=========================================="
echo "PatternShield ML Evaluation Suite"
echo "=========================================="
echo ""

# Navigate to backend directory
cd backend || exit 1

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || . venv/Scripts/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Download NLTK data for TextBlob
echo ""
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('brown', quiet=True)"

# Run model evaluation
echo ""
echo "=========================================="
echo "Running Model Evaluation"
echo "=========================================="
python model_evaluation.py

# Run baseline comparison
echo ""
echo "=========================================="
echo "Running Baseline Comparison"
echo "=========================================="
python experiments/baseline_comparison.py

# Summary
echo ""
echo "=========================================="
echo "Evaluation Complete!"
echo "=========================================="
echo ""
echo "Generated files:"
echo "  ✓ evaluation_results.json"
echo "  ✓ confusion_matrix.png"
echo "  ✓ roc_curves.png"
echo "  ✓ experiments/comparison_report.md"
echo ""
echo "Documentation:"
echo "  📖 EVALUATION.md - Comprehensive evaluation report"
echo "  📖 ../README.md - Project overview"
echo ""
echo "View results:"
echo "  open confusion_matrix.png"
echo "  open roc_curves.png"
echo "  cat EVALUATION.md"
echo ""
