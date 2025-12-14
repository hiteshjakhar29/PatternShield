# PatternShield ML Evaluation Suite

Rigorous machine learning evaluation framework for dark pattern detection, demonstrating quantitative analysis skills for AI/ML roles.

## 🎯 Project Overview

PatternShield is a dark pattern detection system that identifies manipulative UI elements in e-commerce sites. This evaluation suite provides comprehensive, production-grade ML evaluation with:

- ✅ 100 hand-labeled test examples across 5 categories
- ✅ Complete metrics: accuracy, precision, recall, F1, ROC curves
- ✅ Statistical significance testing (McNemar's test)
- ✅ Professional visualizations (confusion matrix, ROC curves)
- ✅ Detailed error analysis with actionable insights
- ✅ Baseline comparison experiments

## 📊 Key Results

| Metric | Score |
|--------|-------|
| **Accuracy** | 81.0% |
| **Macro F1** | 0.8077 |
| **Best Category** | Confirmshaming (F1: 0.976) |
| **Test Set Size** | 100 examples |

### Performance by Category
- **Confirmshaming**: 97.6% F1 (perfect recall!)
- **Urgency/Scarcity**: 84.4% F1
- **Visual Interference**: 77.8% F1
- **Obstruction**: 74.3% F1
- **No Pattern**: 69.8% F1

## 📁 Project Structure

```
backend/
├── data/
│   └── test_dataset.json          # 100 labeled examples
├── experiments/
│   ├── baseline_comparison.py     # Compare 3 model variants
│   └── comparison_report.md       # Statistical comparison results
├── ml_detector.py                 # Core detection model
├── model_evaluation.py            # Full evaluation pipeline
├── requirements.txt               # Python dependencies
├── EVALUATION.md                  # Comprehensive documentation
├── evaluation_results.json        # Detailed metrics (generated)
├── confusion_matrix.png           # Confusion matrix plot (generated)
└── roc_curves.png                 # ROC curves (generated)
```

## 🚀 Quick Start

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Run Evaluation

```bash
# Full evaluation with metrics and visualizations
python model_evaluation.py

# Outputs:
# - evaluation_results.json
# - confusion_matrix.png
# - roc_curves.png
```

### Run Baseline Comparison

```bash
# Compare 3 model variants
python experiments/baseline_comparison.py

# Outputs:
# - experiments/comparison_report.md
```

## 📈 Evaluation Features

### 1. Comprehensive Metrics
- Overall: Accuracy, Macro F1, Weighted F1
- Per-class: Precision, Recall, F1-Score
- Support counts for each category

### 2. Visual Analysis
- **Confusion Matrix**: Professional heatmap showing prediction patterns
- **ROC Curves**: Per-class receiver operating characteristic curves
- Publication-quality matplotlib styling

### 3. Error Analysis
- **Top 5 False Positives**: Why model over-triggers
- **Top 5 False Negatives**: Why model misses patterns
- **Misclassification Analysis**: Pattern confusion patterns
- **Difficulty Breakdown**: Easy (93%), Medium (73%), Hard (70%)

### 4. Statistical Testing
- McNemar's test for model comparison
- P-values and significance at α=0.05
- Contingency tables and test statistics

### 5. Baseline Comparison
Three model variants tested:
- **Model A**: Rule-based only
- **Model B**: Rule-based + Sentiment (current)
- **Model C**: Rule-based + Sentiment + Enhanced features

Results: No significant differences (all ~81% accuracy)

## 🔍 Test Dataset

### Composition
- **100 examples** balanced across 5 categories
- **Difficulty levels**: 43 easy, 37 medium, 20 hard
- **Realistic scenarios**: Real e-commerce text patterns

### Categories
1. **Urgency/Scarcity** (20): "Only 2 left in stock!"
2. **Confirmshaming** (20): "No thanks, I don't want to save money"
3. **Obstruction** (20): "To unsubscribe, mail written request..."
4. **Visual Interference** (20): Asymmetric buttons, hidden options
5. **No Pattern** (20): Legitimate UI elements

## 🎓 Demonstrates ML Skills

This evaluation showcases:

### Quantitative Analysis
- Multiple evaluation metrics (precision, recall, F1, ROC-AUC)
- Confusion matrix interpretation
- Performance stratification by difficulty

### Statistical Rigor
- Hypothesis testing (McNemar's test)
- P-value interpretation
- Reproducible experiments (random seed: 42)

### Error Analysis
- Systematic false positive/negative categorization
- Root cause identification
- Actionable improvement recommendations

### Experiment Design
- Baseline comparison methodology
- Controlled variant testing
- Statistical significance validation

### Documentation
- Academic-level methodology description
- Clear results presentation
- Comprehensive insights and recommendations

## 📊 Key Findings

### Strengths ✅
- **81% overall accuracy** on diverse test set
- **Perfect recall** on confirmshaming (100%)
- **Strong precision** across most categories (>85%)
- **Predictable performance** by difficulty level

### Weaknesses ⚠️
- **Context-dependent patterns** challenging (single words)
- **Domain knowledge** required for subtle obstruction
- **False positives** on "No Pattern" (65% precision)
- **Obstruction recall** needs improvement (65%)

### Recommendations 📈
1. Add context-aware features (surrounding elements)
2. Build domain knowledge base (obsolete tech, patterns)
3. Expand test set to 500+ examples
4. Consider multi-modal features (visual + text)

## 📖 Documentation

See [EVALUATION.md](EVALUATION.md) for:
- Detailed methodology
- Complete results tables
- Error analysis deep-dive
- Baseline comparison
- Future improvement roadmap

## 🔧 Technologies Used

- **Python 3.12**
- **scikit-learn**: Metrics, confusion matrix, classification report
- **matplotlib/seaborn**: Professional visualizations
- **scipy**: Statistical testing (McNemar's test)
- **numpy**: Numerical operations
- **TextBlob**: Sentiment analysis

## 📝 Citation

If using this evaluation framework:

```
PatternShield ML Evaluation Suite
Dark Pattern Detection Evaluation Framework
November 2025
```

## 🎯 Use Cases

This evaluation suite is ideal for:
- **Portfolio projects** demonstrating ML evaluation skills
- **Job applications** for AI/ML roles
- **Academic projects** requiring rigorous evaluation
- **Production ML systems** needing comprehensive testing

## 🤝 Contact

Created as a demonstration of ML evaluation capabilities for AI/ML role applications.

---

**Last Updated**: November 25, 2025  
**Version**: 1.0  
**Status**: Production-ready evaluation framework

## 🐳 Containerized API
- Build and run locally with Docker: `make docker-compose-up`
- Health checks available at `/health` and `/health/ready`.
- Metrics exposed at `/metrics` for Prometheus scraping.

## 🔐 Security & Configuration
- All secrets come from environment variables; see `.env.example`.
- API key header defaults to `X-API-Key`; JWT required for transformer endpoints.
- CORS whitelist configurable via `CORS_ORIGINS`.

## 📦 Deployment
- Use `make docker-build` to produce the production image.
- `scripts/deploy.sh` offers an interactive deployment helper for staging/production.
- `DEPLOYMENT.md` contains more detailed guidance.
