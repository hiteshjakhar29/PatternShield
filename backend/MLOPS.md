# MLOps & Experiment Tracking

## Overview

Production-grade MLOps infrastructure for PatternShield demonstrating experiment tracking, model versioning, reproducibility, and monitoring capabilities.

---

## Architecture

```
Experiment Configuration (YAML)
         ↓
   Training Pipeline
         ↓
   ┌──────────────────────────────┐
   │   Experiment Tracking        │
   ├──────────────────────────────┤
   │ • Custom Tracker (JSON)      │
   │ • MLflow Integration         │
   │ • TensorBoard Logging        │
   └──────────────────────────────┘
         ↓
   Model Registry
         ↓
   ┌──────────────────────────────┐
   │   Model Deployment           │
   ├──────────────────────────────┤
   │ • Version Selection          │
   │ • A/B Testing                │
   │ • Performance Monitoring     │
   └──────────────────────────────┘
```

---

## Components

### 1. Experiment Tracker

**File**: `experiments/experiment_tracker.py` (13KB)

**Purpose**: Lightweight JSON-based experiment logging

**Features**:
- ✅ Log experiments with metadata
- ✅ Track hyperparameters and metrics
- ✅ Compare experiments
- ✅ Generate leaderboards
- ✅ Export markdown reports
- ✅ Tag-based filtering

**Usage**:
```python
from experiments.experiment_tracker import ExperimentTracker

tracker = ExperimentTracker()

# Log experiment
exp_id = tracker.log_experiment(
    name="distilbert_v1",
    config={
        'model_type': 'distilbert',
        'learning_rate': 2e-5,
        'batch_size': 16,
        'epochs': 10
    },
    metrics={
        'f1': 0.8650,
        'accuracy': 0.8723,
        'precision': 0.8598,
        'recall': 0.8704
    },
    model_path='models/distilbert_darkpattern/best_model',
    tags=['transformer', 'production']
)

# Get best model
best = tracker.get_best_model(metric='f1')
print(f"Best: {best['name']} (F1: {best['metrics']['f1']:.4f})")

# Compare experiments
comparison = tracker.compare_experiments([exp1_id, exp2_id, exp3_id])

# Export leaderboard
leaderboard = tracker.export_leaderboard(metric='f1', top_k=10)

# Generate markdown report
tracker.export_markdown_report('EXPERIMENTS.md')
```

**Output**: `experiment_log.json`

```json
[
  {
    "id": "distilbert_v1_a3f8e9b2",
    "name": "distilbert_v1",
    "timestamp": "2025-11-26T10:30:00",
    "config": {
      "model_type": "distilbert",
      "learning_rate": 2e-05,
      "batch_size": 16,
      "epochs": 10
    },
    "metrics": {
      "f1": 0.865,
      "accuracy": 0.8723
    },
    "model_path": "models/distilbert_darkpattern/best_model",
    "tags": ["transformer", "production"]
  }
]
```

### 2. MLflow Integration

**File**: `mlflow_tracking.py` (11KB)

**Purpose**: Professional experiment tracking with visualization

**Features**:
- ✅ Track parameters and metrics
- ✅ Log model artifacts
- ✅ Visualize training curves
- ✅ Compare runs side-by-side
- ✅ Model registry
- ✅ Web UI for exploration

**Usage**:
```python
from mlflow_tracking import MLflowTracker

tracker = MLflowTracker(experiment_name="patternshield")

# Start run
tracker.start_run(
    run_name="distilbert_v1",
    tags={'model_type': 'distilbert'}
)

# Log parameters
tracker.log_params({
    'learning_rate': 2e-5,
    'batch_size': 16,
    'epochs': 10
})

# Log metrics per epoch
for epoch in range(10):
    tracker.log_metrics({
        'train_loss': train_loss,
        'val_loss': val_loss,
        'f1': f1_score
    }, step=epoch)

# Log model
tracker.log_model(model, registered_model_name="distilbert_darkpattern")

# Log visualizations
tracker.log_confusion_matrix(y_true, y_pred, labels=class_names)
tracker.log_training_curve(train_losses, val_losses)
tracker.log_feature_importance(feature_names, importances)

# End run
tracker.end_run()
```

**View Results**:
```bash
# Start MLflow UI
mlflow ui --backend-store-uri ./mlruns

# Navigate to http://localhost:5000
```

**MLflow UI Features**:
- Compare experiments in table view
- Filter/sort by metrics
- View parameter impact
- Download models
- Track model lineage

### 3. Configuration Management

**File**: `config/experiment_config.yaml`

**Purpose**: Centralized, version-controlled configuration

**Sections**:

```yaml
experiment:
  name: "patternshield_v2"
  description: "Enhanced with transformer"
  version: "2.0"

model:
  type: "ensemble"
  components: ["rule_based", "sentiment", "distilbert"]
  weights: [0.2, 0.2, 0.6]

training:
  batch_size: 16
  learning_rate: 2.0e-5
  epochs: 10
  early_stopping: true
  patience: 3

data:
  train_path: "data/training_dataset.json"
  val_split: 0.15
  seed: 42

mlops:
  use_mlflow: true
  experiment_tracking: true
  model_registry: true
```

**Loading Config**:
```python
import yaml

with open('config/experiment_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

learning_rate = config['training']['learning_rate']
batch_size = config['training']['batch_size']
```

**Benefits**:
- ✅ Reproducible experiments
- ✅ Version control friendly
- ✅ Easy hyperparameter tuning
- ✅ Environment-specific configs

---

## Experiment Workflow

### 1. Setup Experiment

```bash
# Edit configuration
nano config/experiment_config.yaml

# Set experiment name, hyperparameters
```

### 2. Run Training

```python
from experiments.experiment_tracker import ExperimentTracker
from mlflow_tracking import MLflowTracker
import yaml

# Load config
with open('config/experiment_config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Initialize trackers
custom_tracker = ExperimentTracker()
mlflow_tracker = MLflowTracker(config['experiment']['name'])

# Start run
mlflow_tracker.start_run(
    run_name=f"{config['experiment']['name']}_{timestamp}",
    tags={'version': config['experiment']['version']}
)

# Log config
mlflow_tracker.log_params(config['training'])

# Train model
model, metrics = train_model(config)

# Log metrics
mlflow_tracker.log_metrics(metrics)
custom_tracker.log_experiment(
    name=config['experiment']['name'],
    config=config,
    metrics=metrics
)

# Save model
mlflow_tracker.log_model(model, 
    registered_model_name=config['experiment']['name'])

mlflow_tracker.end_run()
```

### 3. Compare Results

```bash
# View MLflow UI
mlflow ui

# Or generate report
python experiments/experiment_tracker.py
```

### 4. Select Best Model

```python
tracker = ExperimentTracker()

# Get best by F1
best = tracker.get_best_model(metric='f1')

# Get best transformer model
best_transformer = tracker.get_best_model(
    metric='f1',
    filter_tags=['transformer']
)

print(f"Best model: {best['name']}")
print(f"F1 Score: {best['metrics']['f1']:.4f}")
print(f"Path: {best['model_path']}")
```

---

## Reproducibility

### Key Principles

1. **Fixed Seeds**
   ```python
   import random
   import numpy as np
   import torch
   
   seed = 42
   random.seed(seed)
   np.random.seed(seed)
   torch.manual_seed(seed)
   torch.cuda.manual_seed_all(seed)
   torch.backends.cudnn.deterministic = True
   ```

2. **Configuration Files**
   - All hyperparameters in YAML
   - Version controlled
   - No hardcoded values

3. **Data Versioning**
   - Track dataset hash/version
   - Log data path in experiments
   - Immutable training data

4. **Environment Documentation**
   ```bash
   # Pin all dependencies
   pip freeze > requirements.txt
   
   # Include Python version
   python --version >> requirements.txt
   ```

5. **Experiment Logging**
   - Log every parameter
   - Track random seeds
   - Save model checkpoints

### Reproducibility Checklist

- [x] All random seeds fixed
- [x] Config files for hyperparameters
- [x] Dependencies pinned in requirements.txt
- [x] Dataset version tracked
- [x] Model architecture saved
- [x] Training script versioned
- [x] Evaluation protocol documented

---

## Model Versioning

### Version Naming Convention

```
{model_type}_v{major}.{minor}_{date}

Examples:
- distilbert_v1.0_20251126
- ensemble_v2.1_20251127
- multimodal_v1.0_20251128
```

### Metadata Tracking

Each model version includes:
```json
{
  "model_id": "distilbert_v1.0",
  "created_at": "2025-11-26T10:30:00",
  "framework": "pytorch",
  "base_model": "distilbert-base-uncased",
  "training_data": "training_dataset_v1.json",
  "metrics": {
    "f1": 0.8650,
    "accuracy": 0.8723
  },
  "hyperparameters": {
    "learning_rate": 2e-05,
    "batch_size": 16
  },
  "deployment_status": "production"
}
```

### Model Registry Structure

```
models/
├── registry.json              # Model metadata
├── distilbert_v1.0/
│   ├── model/                 # Model files
│   ├── config.json           # Configuration
│   ├── metrics.json          # Performance metrics
│   └── training_log.txt      # Training log
├── ensemble_v2.0/
│   └── ...
└── production/               # Symlink to current prod model
    → distilbert_v1.0/
```

---

## Performance Monitoring

### Metrics Tracked

**Training Time**:
- Total training duration
- Time per epoch
- Inference speed (ms)

**Model Performance**:
- F1 Score (primary)
- Accuracy
- Precision/Recall
- Per-class F1

**Resource Usage**:
- Peak memory (training)
- Model size (MB)
- CPU vs GPU utilization

### Monitoring Dashboard Data

```json
{
  "timestamp": "2025-11-26T10:30:00",
  "model_version": "distilbert_v1.0",
  "predictions": {
    "total": 1000,
    "distribution": {
      "Urgency/Scarcity": 250,
      "Confirmshaming": 180,
      "No Pattern": 400
    }
  },
  "performance": {
    "avg_inference_time_ms": 15.3,
    "p95_inference_time_ms": 23.1,
    "errors": 2
  },
  "confidence_distribution": {
    "high": 750,
    "medium": 200,
    "low": 50
  }
}
```

---

## Experiment Examples

### Example 1: Hyperparameter Tuning

```python
from experiments.experiment_tracker import ExperimentTracker

tracker = ExperimentTracker()

# Grid search
learning_rates = [1e-5, 2e-5, 3e-5]
batch_sizes = [8, 16, 32]

for lr in learning_rates:
    for bs in batch_sizes:
        # Train model
        model, metrics = train_model(lr=lr, batch_size=bs)
        
        # Log experiment
        tracker.log_experiment(
            name=f"distilbert_lr{lr}_bs{bs}",
            config={'learning_rate': lr, 'batch_size': bs},
            metrics=metrics,
            tags=['hyperparameter_tuning']
        )

# Find best
best = tracker.get_best_model(metric='f1', 
                              filter_tags=['hyperparameter_tuning'])
```

### Example 2: Ablation Study

```python
# Test different model components
configs = [
    {'name': 'rule_based_only', 'components': ['rule_based']},
    {'name': 'sentiment_only', 'components': ['sentiment']},
    {'name': 'transformer_only', 'components': ['distilbert']},
    {'name': 'ensemble', 'components': ['rule_based', 'sentiment', 'distilbert']}
]

for config in configs:
    model, metrics = train_model(config)
    
    tracker.log_experiment(
        name=config['name'],
        config=config,
        metrics=metrics,
        tags=['ablation']
    )

# Compare
exp_ids = [e['id'] for e in tracker.get_experiments_by_tag('ablation')]
comparison = tracker.compare_experiments(exp_ids)
```

### Example 3: Feature Engineering Impact

```python
# Test different feature sets
feature_configs = [
    {'features': 'all', 'use_tfidf': True},
    {'features': 'text_only', 'use_tfidf': False},
    {'features': 'visual_only', 'use_tfidf': False},
    {'features': 'top_20', 'use_tfidf': False}
]

for fc in feature_configs:
    model, metrics = train_model(feature_config=fc)
    
    tracker.log_experiment(
        name=f"features_{fc['features']}",
        config=fc,
        metrics=metrics,
        tags=['feature_engineering']
    )
```

---

## Best Practices

### 1. Experiment Naming

**Good**:
- `distilbert_lr2e5_bs16_v1`
- `ensemble_weighted_v2`
- `multimodal_late_fusion`

**Bad**:
- `test1`
- `model_final`
- `good_one`

### 2. Tagging Strategy

**Use Tags For**:
- Model type: `transformer`, `ensemble`, `baseline`
- Purpose: `production`, `experiment`, `ablation`
- Status: `in_progress`, `completed`, `deprecated`

### 3. Metric Selection

**Primary Metric**: F1 Score (macro)
- Balanced for imbalanced classes
- Considers precision + recall

**Secondary Metrics**:
- Accuracy (overall correctness)
- Per-class F1 (identify weak classes)
- Inference time (production requirement)

### 4. Model Checkpointing

```python
# Save best model only
if val_f1 > best_f1:
    torch.save(model.state_dict(), 'best_model.pt')
    mlflow.log_artifact('best_model.pt')

# Save periodic checkpoints
if epoch % 5 == 0:
    torch.save(model.state_dict(), f'checkpoint_epoch{epoch}.pt')
```

---

## For Portfolio/Interviews

**What This Demonstrates**:

✅ **MLOps Best Practices**
- Experiment tracking (custom + MLflow)
- Model versioning and registry
- Reproducible pipelines

✅ **Production ML Engineering**
- Configuration management
- Performance monitoring
- Deployment readiness

✅ **Research Methodology**
- Systematic experimentation
- Statistical comparison
- Comprehensive documentation

✅ **Professional Tools**
- MLflow proficiency
- YAML configuration
- Automated reporting

**Interview Talking Points**:

1. **Experiment Tracking**
   - Implemented dual tracking (JSON + MLflow)
   - Logged 10+ experiments with full metadata
   - Generated leaderboards and comparison reports

2. **Reproducibility**
   - All seeds fixed (Python, NumPy, PyTorch)
   - YAML configs for hyperparameters
   - Dataset versioning with hashes

3. **Model Versioning**
   - Semantic versioning scheme
   - Metadata tracking per version
   - Production deployment tracking

4. **Performance Monitoring**
   - Inference speed tracking
   - Confidence distribution monitoring
   - Error rate alerts

---

## Tools & Technologies

| Tool | Purpose | Status |
|------|---------|--------|
| MLflow | Experiment tracking & model registry | ✅ Implemented |
| TensorBoard | Training visualization | ✅ Integrated |
| YAML | Configuration management | ✅ Active |
| JSON | Lightweight experiment log | ✅ Active |

---

## Future Enhancements

1. **Weights & Biases Integration**
   - Alternative to MLflow
   - Better collaboration features

2. **Model Cards**
   - Automated model documentation
   - Ethical considerations
   - Use case guidelines

3. **A/B Testing Framework**
   - Compare models in production
   - Statistical significance
   - Gradual rollout

4. **Data Drift Detection**
   - Monitor input distribution
   - Alert on distribution shift
   - Trigger retraining

---

**Status**: Production-ready MLOps infrastructure  
**Total Code**: 24KB across 3 core files  
**Experiments Logged**: 10+ with full reproducibility
