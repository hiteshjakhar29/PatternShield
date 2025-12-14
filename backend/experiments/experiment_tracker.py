"""
Experiment Tracker
Log and manage ML experiments with comprehensive metrics.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import hashlib


class ExperimentTracker:
    """Track ML experiments with comprehensive logging."""

    def __init__(self, log_file: str = "experiment_log.json"):
        """Initialize experiment tracker."""
        self.log_file = log_file
        self.experiments = self._load_experiments()

    def _load_experiments(self) -> List[Dict]:
        """Load existing experiments from file."""
        if os.path.exists(self.log_file):
            with open(self.log_file, "r") as f:
                return json.load(f)
        return []

    def _save_experiments(self):
        """Save experiments to file."""
        with open(self.log_file, "w") as f:
            json.dump(self.experiments, f, indent=2)

    def _generate_exp_id(self, name: str, config: Dict) -> str:
        """Generate unique experiment ID."""
        # Hash based on name and config
        config_str = json.dumps(config, sort_keys=True)
        hash_obj = hashlib.md5(f"{name}{config_str}".encode())
        return f"{name}_{hash_obj.hexdigest()[:8]}"

    def log_experiment(
        self,
        name: str,
        config: Dict,
        metrics: Dict,
        model_path: Optional[str] = None,
        dataset_version: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Log a new experiment.

        Args:
            name: Experiment name
            config: Configuration dict (hyperparameters, model type, etc.)
            metrics: Performance metrics (F1, accuracy, etc.)
            model_path: Path to saved model
            dataset_version: Version/hash of dataset used
            tags: Optional tags for categorization

        Returns:
            Experiment ID
        """
        exp_id = self._generate_exp_id(name, config)

        experiment = {
            "id": exp_id,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "config": config,
            "metrics": metrics,
            "model_path": model_path,
            "dataset_version": dataset_version,
            "tags": tags or [],
        }

        # Check if experiment already exists
        existing_idx = None
        for i, exp in enumerate(self.experiments):
            if exp["id"] == exp_id:
                existing_idx = i
                break

        if existing_idx is not None:
            # Update existing experiment
            self.experiments[existing_idx] = experiment
            print(f"Updated experiment: {exp_id}")
        else:
            # Add new experiment
            self.experiments.append(experiment)
            print(f"Logged new experiment: {exp_id}")

        self._save_experiments()
        return exp_id

    def get_experiment(self, exp_id: str) -> Optional[Dict]:
        """Get experiment by ID."""
        for exp in self.experiments:
            if exp["id"] == exp_id:
                return exp
        return None

    def get_best_model(
        self, metric: str = "f1", filter_tags: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """
        Get best model based on metric.

        Args:
            metric: Metric to optimize ('f1', 'accuracy', etc.)
            filter_tags: Optional tags to filter by

        Returns:
            Best experiment dict
        """
        filtered_exps = self.experiments

        # Filter by tags
        if filter_tags:
            filtered_exps = [
                exp
                for exp in filtered_exps
                if any(tag in exp.get("tags", []) for tag in filter_tags)
            ]

        # Filter by experiments that have the metric
        filtered_exps = [
            exp for exp in filtered_exps if metric in exp.get("metrics", {})
        ]

        if not filtered_exps:
            return None

        # Get best
        best = max(filtered_exps, key=lambda x: x["metrics"][metric])

        return best

    def compare_experiments(self, exp_ids: List[str]) -> Dict:
        """
        Compare multiple experiments.

        Args:
            exp_ids: List of experiment IDs to compare

        Returns:
            Comparison dict
        """
        experiments = [self.get_experiment(eid) for eid in exp_ids]
        experiments = [e for e in experiments if e is not None]

        if not experiments:
            return {}

        # Extract all metrics
        all_metrics = set()
        for exp in experiments:
            all_metrics.update(exp.get("metrics", {}).keys())

        comparison = {"experiment_ids": exp_ids, "metrics": {}}

        for metric in all_metrics:
            comparison["metrics"][metric] = {
                exp["id"]: exp["metrics"].get(metric, None) for exp in experiments
            }

        return comparison

    def export_leaderboard(self, metric: str = "f1", top_k: int = 10) -> List[Dict]:
        """
        Export leaderboard of top experiments.

        Args:
            metric: Metric to rank by
            top_k: Number of top experiments

        Returns:
            List of top experiments
        """
        # Filter experiments with the metric
        valid_exps = [
            exp for exp in self.experiments if metric in exp.get("metrics", {})
        ]

        # Sort by metric
        sorted_exps = sorted(
            valid_exps, key=lambda x: x["metrics"][metric], reverse=True
        )[:top_k]

        # Format leaderboard
        leaderboard = []
        for rank, exp in enumerate(sorted_exps, 1):
            leaderboard.append(
                {
                    "rank": rank,
                    "id": exp["id"],
                    "name": exp["name"],
                    "metric_value": exp["metrics"][metric],
                    "timestamp": exp["timestamp"],
                    "config_summary": {
                        k: v
                        for k, v in exp["config"].items()
                        if k in ["model_type", "learning_rate", "batch_size"]
                    },
                }
            )

        return leaderboard

    def get_experiments_by_tag(self, tag: str) -> List[Dict]:
        """Get all experiments with a specific tag."""
        return [exp for exp in self.experiments if tag in exp.get("tags", [])]

    def delete_experiment(self, exp_id: str) -> bool:
        """Delete an experiment."""
        for i, exp in enumerate(self.experiments):
            if exp["id"] == exp_id:
                del self.experiments[i]
                self._save_experiments()
                return True
        return False

    def generate_summary(self) -> Dict:
        """Generate summary statistics of all experiments."""
        if not self.experiments:
            return {"total_experiments": 0}

        # Collect all metrics
        all_metrics = {}
        for exp in self.experiments:
            for metric, value in exp.get("metrics", {}).items():
                if metric not in all_metrics:
                    all_metrics[metric] = []
                if isinstance(value, (int, float)):
                    all_metrics[metric].append(value)

        # Calculate statistics
        summary = {"total_experiments": len(self.experiments), "metric_statistics": {}}

        for metric, values in all_metrics.items():
            if values:
                summary["metric_statistics"][metric] = {
                    "mean": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values),
                }

        # Get unique tags
        all_tags = set()
        for exp in self.experiments:
            all_tags.update(exp.get("tags", []))
        summary["tags"] = list(all_tags)

        return summary

    def export_markdown_report(self, output_file: str = "EXPERIMENTS.md"):
        """Generate markdown report of experiments."""
        lines = []

        lines.append("# Experiment Log\n")
        lines.append("## Summary\n")

        summary = self.generate_summary()
        lines.append(f"**Total Experiments**: {summary['total_experiments']}\n")

        if summary.get("metric_statistics"):
            lines.append("### Metric Statistics\n")
            lines.append("| Metric | Mean | Min | Max | Count |")
            lines.append("|--------|------|-----|-----|-------|")

            for metric, stats in summary["metric_statistics"].items():
                lines.append(
                    f"| {metric} | {stats['mean']:.4f} | "
                    f"{stats['min']:.4f} | {stats['max']:.4f} | "
                    f"{stats['count']} |"
                )

        lines.append("\n## Leaderboard (by F1 Score)\n")

        leaderboard = self.export_leaderboard(metric="f1", top_k=10)

        if leaderboard:
            lines.append("| Rank | Experiment | F1 Score | Date | Config |")
            lines.append("|------|------------|----------|------|--------|")

            for entry in leaderboard:
                date = entry["timestamp"].split("T")[0]
                config = ", ".join(
                    f"{k}={v}" for k, v in entry["config_summary"].items()
                )
                lines.append(
                    f"| {entry['rank']} | {entry['name']} | "
                    f"{entry['metric_value']:.4f} | {date} | {config} |"
                )

        lines.append("\n## All Experiments\n")

        for exp in sorted(self.experiments, key=lambda x: x["timestamp"], reverse=True):
            lines.append(f"### {exp['name']} ({exp['id']})\n")
            lines.append(f"**Date**: {exp['timestamp'].split('T')[0]}\n")

            if exp.get("tags"):
                lines.append(f"**Tags**: {', '.join(exp['tags'])}\n")

            lines.append("**Config**:")
            for key, value in exp["config"].items():
                lines.append(f"- {key}: {value}")

            lines.append("\n**Metrics**:")
            for key, value in exp["metrics"].items():
                if isinstance(value, float):
                    lines.append(f"- {key}: {value:.4f}")
                else:
                    lines.append(f"- {key}: {value}")

            lines.append("")

        # Write to file
        with open(output_file, "w") as f:
            f.write("\n".join(lines))

        print(f"Report saved to {output_file}")


def main():
    """Test experiment tracker."""
    print("=" * 80)
    print("EXPERIMENT TRACKER TEST")
    print("=" * 80)

    tracker = ExperimentTracker()

    # Log some test experiments
    print("\n1. Logging experiments...")

    exp1_id = tracker.log_experiment(
        name="baseline_rf",
        config={"model_type": "random_forest", "n_estimators": 100, "max_depth": 10},
        metrics={
            "f1": 0.8243,
            "accuracy": 0.8356,
            "precision": 0.8189,
            "recall": 0.8301,
        },
        tags=["baseline", "random_forest"],
    )

    exp2_id = tracker.log_experiment(
        name="distilbert_v1",
        config={
            "model_type": "distilbert",
            "learning_rate": 2e-5,
            "batch_size": 16,
            "epochs": 10,
        },
        metrics={
            "f1": 0.8650,
            "accuracy": 0.8723,
            "precision": 0.8598,
            "recall": 0.8704,
        },
        tags=["transformer", "deep_learning"],
    )

    exp3_id = tracker.log_experiment(
        name="ensemble_v1",
        config={
            "model_type": "ensemble",
            "components": ["rule_based", "sentiment", "distilbert"],
            "weights": [0.2, 0.2, 0.6],
        },
        metrics={
            "f1": 0.8890,
            "accuracy": 0.8934,
            "precision": 0.8856,
            "recall": 0.8925,
        },
        tags=["ensemble", "production"],
    )

    # Get best model
    print("\n2. Best model:")
    best = tracker.get_best_model(metric="f1")
    if best:
        print(f"   {best['name']}: F1 = {best['metrics']['f1']:.4f}")

    # Compare experiments
    print("\n3. Comparing experiments:")
    comparison = tracker.compare_experiments([exp1_id, exp2_id, exp3_id])

    for metric, values in comparison["metrics"].items():
        print(f"   {metric}:")
        for exp_id, value in values.items():
            if value is not None:
                print(f"      {exp_id}: {value:.4f}")

    # Generate leaderboard
    print("\n4. Leaderboard (Top 3):")
    leaderboard = tracker.export_leaderboard(metric="f1", top_k=3)

    for entry in leaderboard:
        print(f"   {entry['rank']}. {entry['name']}: {entry['metric_value']:.4f}")

    # Export report
    print("\n5. Exporting report...")
    tracker.export_markdown_report("test_experiments.md")

    print("\n✓ Experiment tracker test complete")


if __name__ == "__main__":
    main()
