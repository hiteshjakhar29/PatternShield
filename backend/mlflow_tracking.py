"""
MLflow Tracking Integration
Track experiments with MLflow for visualization and comparison.
"""

import mlflow
import mlflow.sklearn
import mlflow.pytorch
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix
import seaborn as sns
import os


class MLflowTracker:
    """MLflow experiment tracking wrapper."""

    def __init__(
        self, experiment_name: str = "patternshield", tracking_uri: Optional[str] = None
    ):
        """
        Initialize MLflow tracker.

        Args:
            experiment_name: Name of experiment
            tracking_uri: Optional custom tracking URI
        """
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)

        mlflow.set_experiment(experiment_name)
        self.experiment_name = experiment_name

    def start_run(
        self, run_name: Optional[str] = None, tags: Optional[Dict[str, str]] = None
    ):
        """Start a new MLflow run."""
        mlflow.start_run(run_name=run_name)

        if tags:
            mlflow.set_tags(tags)

    def log_params(self, params: Dict[str, Any]):
        """Log hyperparameters."""
        mlflow.log_params(params)

    def log_metrics(self, metrics: Dict[str, float], step: Optional[int] = None):
        """Log metrics."""
        mlflow.log_metrics(metrics, step=step)

    def log_metric(self, key: str, value: float, step: Optional[int] = None):
        """Log a single metric."""
        mlflow.log_metric(key, value, step=step)

    def log_model(
        self,
        model,
        artifact_path: str = "model",
        registered_model_name: Optional[str] = None,
    ):
        """
        Log model artifact.

        Args:
            model: Model to log (sklearn or pytorch)
            artifact_path: Path within run artifacts
            registered_model_name: Optional name for model registry
        """
        try:
            # Try sklearn first
            mlflow.sklearn.log_model(
                model, artifact_path, registered_model_name=registered_model_name
            )
        except:
            try:
                # Try pytorch
                mlflow.pytorch.log_model(
                    model, artifact_path, registered_model_name=registered_model_name
                )
            except Exception as e:
                print(f"Could not log model: {e}")

    def log_confusion_matrix(self, y_true, y_pred, labels=None):
        """
        Log confusion matrix as artifact.

        Args:
            y_true: True labels
            y_pred: Predicted labels
            labels: Optional label names
        """
        cm = confusion_matrix(y_true, y_pred)

        plt.figure(figsize=(10, 8))
        sns.heatmap(
            cm,
            annot=True,
            fmt="d",
            cmap="Blues",
            xticklabels=labels,
            yticklabels=labels,
        )
        plt.title("Confusion Matrix")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()

        # Save to temp file
        temp_file = "temp_confusion_matrix.png"
        plt.savefig(temp_file, dpi=300, bbox_inches="tight")
        plt.close()

        # Log artifact
        mlflow.log_artifact(temp_file, "plots")

        # Clean up
        if os.path.exists(temp_file):
            os.remove(temp_file)

    def log_training_curve(self, train_losses: list, val_losses: list = None):
        """
        Log training curves.

        Args:
            train_losses: Training losses per epoch
            val_losses: Optional validation losses
        """
        plt.figure(figsize=(10, 6))
        epochs = range(1, len(train_losses) + 1)

        plt.plot(epochs, train_losses, "b-", label="Training Loss")
        if val_losses:
            plt.plot(epochs, val_losses, "r-", label="Validation Loss")

        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.title("Training Curves")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        temp_file = "temp_training_curve.png"
        plt.savefig(temp_file, dpi=300, bbox_inches="tight")
        plt.close()

        mlflow.log_artifact(temp_file, "plots")

        if os.path.exists(temp_file):
            os.remove(temp_file)

    def log_feature_importance(
        self, feature_names: list, importances: np.ndarray, top_n: int = 20
    ):
        """
        Log feature importance plot.

        Args:
            feature_names: Names of features
            importances: Importance values
            top_n: Number of top features to plot
        """
        # Get top features
        indices = np.argsort(importances)[::-1][:top_n]

        plt.figure(figsize=(12, 8))
        plt.barh(range(top_n), importances[indices])
        plt.yticks(range(top_n), [feature_names[i] for i in indices])
        plt.xlabel("Importance")
        plt.title(f"Top {top_n} Feature Importances")
        plt.gca().invert_yaxis()
        plt.tight_layout()

        temp_file = "temp_feature_importance.png"
        plt.savefig(temp_file, dpi=300, bbox_inches="tight")
        plt.close()

        mlflow.log_artifact(temp_file, "plots")

        if os.path.exists(temp_file):
            os.remove(temp_file)

    def log_artifact(self, local_path: str, artifact_path: Optional[str] = None):
        """Log arbitrary artifact."""
        mlflow.log_artifact(local_path, artifact_path)

    def log_dict(self, dictionary: Dict, filename: str):
        """Log dictionary as JSON artifact."""
        import json

        temp_file = f"temp_{filename}"

        with open(temp_file, "w") as f:
            json.dump(dictionary, f, indent=2)

        mlflow.log_artifact(temp_file)

        if os.path.exists(temp_file):
            os.remove(temp_file)

    def end_run(self):
        """End current MLflow run."""
        mlflow.end_run()

    def get_experiment_runs(self, max_results: int = 100) -> list:
        """
        Get all runs for current experiment.

        Args:
            max_results: Maximum number of runs to return

        Returns:
            List of run info
        """
        experiment = mlflow.get_experiment_by_name(self.experiment_name)

        if experiment:
            runs = mlflow.search_runs(
                experiment_ids=[experiment.experiment_id], max_results=max_results
            )
            return runs

        return []

    def compare_runs(self, run_ids: list, metric: str = "f1") -> Dict:
        """
        Compare multiple runs.

        Args:
            run_ids: List of run IDs to compare
            metric: Metric to compare

        Returns:
            Comparison dict
        """
        runs = mlflow.search_runs(filter_string=f"run_id IN ({','.join(run_ids)})")

        comparison = {"run_ids": run_ids, "metrics": {}}

        for _, run in runs.iterrows():
            run_id = run["run_id"]
            comparison["metrics"][run_id] = run.get(f"metrics.{metric}", None)

        return comparison


def example_usage():
    """Example of using MLflow tracker."""
    print("=" * 80)
    print("MLFLOW TRACKER EXAMPLE")
    print("=" * 80)

    # Initialize
    tracker = MLflowTracker(experiment_name="patternshield_demo")

    # Start run
    tracker.start_run(
        run_name="random_forest_baseline",
        tags={"model_type": "random_forest", "version": "v1"},
    )

    # Log parameters
    tracker.log_params({"n_estimators": 100, "max_depth": 10, "random_state": 42})

    # Log metrics
    tracker.log_metrics(
        {"f1": 0.8243, "accuracy": 0.8356, "precision": 0.8189, "recall": 0.8301}
    )

    # Simulate training epochs
    print("\nLogging training curves...")
    train_losses = [0.5, 0.3, 0.2, 0.15, 0.12]
    val_losses = [0.55, 0.35, 0.25, 0.20, 0.18]

    for epoch, (train_loss, val_loss) in enumerate(zip(train_losses, val_losses)):
        tracker.log_metric("train_loss", train_loss, step=epoch)
        tracker.log_metric("val_loss", val_loss, step=epoch)

    tracker.log_training_curve(train_losses, val_losses)

    # Log confusion matrix (mock data)
    print("Logging confusion matrix...")
    y_true = np.random.randint(0, 3, 100)
    y_pred = np.random.randint(0, 3, 100)
    tracker.log_confusion_matrix(
        y_true, y_pred, labels=["Class A", "Class B", "Class C"]
    )

    # End run
    tracker.end_run()

    print("\n✓ MLflow tracking complete")
    print("\nTo view results, run: mlflow ui")
    print("Then navigate to http://localhost:5000")


if __name__ == "__main__":
    example_usage()
