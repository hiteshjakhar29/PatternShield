# Baseline Comparison Report
## PatternShield Dark Pattern Detection Models

---

## Model Variants

### Model A: Rule-Based Only
- Uses only keyword and pattern matching
- No sentiment analysis
- Baseline approach

### Model B: Rule-Based + Sentiment
- Keyword and pattern matching
- TextBlob sentiment analysis
- Sentiment-adjusted confidence scores
- **Current production model**

### Model C: Rule-Based + Sentiment + Enhanced
- All features from Model B
- Color-based detection adjustments
- Text length-based heuristics
- Advanced feature engineering

---

## Overall Performance Comparison

| Model | Accuracy | Macro F1 | Weighted F1 |
|-------|----------|----------|-------------|
| Model A | 0.8100 | 0.8077 | 0.8077 |
| Model B | 0.8100 | 0.8077 | 0.8077 |
| Model C | 0.8000 | 0.8007 | 0.8007 |

---

## Improvement Analysis

### Model B vs Model A (Adding Sentiment Analysis)

- **Accuracy Improvement**: +0.00%
  - Baseline: 0.8100
  - With Sentiment: 0.8100
- **F1 Improvement**: +0.00%
  - Baseline: 0.8077
  - With Sentiment: 0.8077

**Statistical Significance (McNemar's Test)**:
- Test Statistic: 0.0000
- P-value: 1.0000
- Significant at α=0.05: No ✗
- Model B correct where A failed: 0 cases
- Model A correct where B failed: 0 cases

### Model C vs Model B (Adding Enhanced Features)

- **Accuracy Improvement**: -1.23%
  - Baseline: 0.8100
  - With Enhanced: 0.8000
- **F1 Improvement**: -0.86%
  - Baseline: 0.8077
  - With Enhanced: 0.8007

**Statistical Significance (McNemar's Test)**:
- Test Statistic: 0.0000
- P-value: 1.0000
- Significant at α=0.05: No ✗
- Model C correct where B failed: 2 cases
- Model B correct where C failed: 3 cases

### Model C vs Model A (Complete Enhancement)

- **Accuracy Improvement**: -1.23%
  - Baseline: 0.8100
  - Fully Enhanced: 0.8000
- **F1 Improvement**: -0.86%
  - Baseline: 0.8077
  - Fully Enhanced: 0.8007

**Statistical Significance (McNemar's Test)**:
- Test Statistic: 0.0000
- P-value: 1.0000
- Significant at α=0.05: No ✗
- Model C correct where A failed: 2 cases
- Model A correct where C failed: 3 cases

---

## Key Insights

1. **Best Overall Model**: Model A
   - Achieved 0.8100 accuracy on test set

2. **Feature Impact**:

3. **Statistical Validity**:
   - Improvements may not be statistically significant (small sample or marginal gains)

4. **Recommendations**:
   - Continue with baseline; focus on data collection and feature engineering

---

## Methodology

- **Test Set Size**: 100 examples
- **Evaluation Metrics**: Accuracy, Macro F1, Weighted F1
- **Statistical Test**: McNemar's Test (α = 0.05)
- **Random Seed**: 42 (for reproducibility)

---

*Report generated automatically by baseline_comparison.py*