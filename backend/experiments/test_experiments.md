# Experiment Log

## Summary

**Total Experiments**: 3

### Metric Statistics

| Metric | Mean | Min | Max | Count |
|--------|------|-----|-----|-------|
| f1 | 0.8594 | 0.8243 | 0.8890 | 3 |
| accuracy | 0.8671 | 0.8356 | 0.8934 | 3 |
| precision | 0.8548 | 0.8189 | 0.8856 | 3 |
| recall | 0.8643 | 0.8301 | 0.8925 | 3 |

## Leaderboard (by F1 Score)

| Rank | Experiment | F1 Score | Date | Config |
|------|------------|----------|------|--------|
| 1 | ensemble_v1 | 0.8890 | 2025-11-26 | model_type=ensemble |
| 2 | distilbert_v1 | 0.8650 | 2025-11-26 | model_type=distilbert, learning_rate=2e-05, batch_size=16 |
| 3 | baseline_rf | 0.8243 | 2025-11-26 | model_type=random_forest |

## All Experiments

### ensemble_v1 (ensemble_v1_bf2db12b)

**Date**: 2025-11-26

**Tags**: ensemble, production

**Config**:
- model_type: ensemble
- components: ['rule_based', 'sentiment', 'distilbert']
- weights: [0.2, 0.2, 0.6]

**Metrics**:
- f1: 0.8890
- accuracy: 0.8934
- precision: 0.8856
- recall: 0.8925

### distilbert_v1 (distilbert_v1_0fde86f0)

**Date**: 2025-11-26

**Tags**: transformer, deep_learning

**Config**:
- model_type: distilbert
- learning_rate: 2e-05
- batch_size: 16
- epochs: 10

**Metrics**:
- f1: 0.8650
- accuracy: 0.8723
- precision: 0.8598
- recall: 0.8704

### baseline_rf (baseline_rf_92d1ba0f)

**Date**: 2025-11-26

**Tags**: baseline, random_forest

**Config**:
- model_type: random_forest
- n_estimators: 100
- max_depth: 10

**Metrics**:
- f1: 0.8243
- accuracy: 0.8356
- precision: 0.8189
- recall: 0.8301
